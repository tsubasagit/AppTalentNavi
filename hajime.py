#!/usr/bin/env python3
"""AppTalentNavi v2 — AIエージェント体験 研修ツール
Gemini API（優先）またはOllama（ローカルLLM）を使って、
自律型AIエージェントにビジネスタスクを丸投げする体験を提供。
ビジネスパーソン向け研修用。

Usage:
    python hajime.py                    # 対話モード
    python hajime.py -p "会議メモからデータを抽出して"  # ワンショット
    python hajime.py -y                 # 自動承認モード
"""
import signal
import sys
import os
import traceback
import urllib.request
import json

# === Windows patches (from start.py) ===

# Patch 1: Add missing SIGHUP for Windows
if not hasattr(signal, 'SIGHUP'):
    signal.SIGHUP = None
    _original_signal = signal.signal
    def _patched_signal(signalnum, handler):
        if signalnum is None:
            return signal.SIG_DFL
        return _original_signal(signalnum, handler)
    signal.signal = _patched_signal

# Patch 2: Fix encoding for Windows Japanese console (prevent cp932 errors)
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONUTF8', '1')
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

# === AppTalentNavi configuration ===

APP_VERSION = "2.0.0"
APP_NAME = "AppTalentNavi"
RECOMMENDED_OLLAMA_MODEL = "qwen2.5-coder:3b"
GEMINI_DEFAULT_MODEL = "gemini-2.5-flash-lite"
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


def _get_base_path():
    """PyInstaller exe時はsys._MEIPASS、通常時はスクリプトディレクトリ"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _get_user_data_dir():
    """ユーザーデータディレクトリを取得（exe実行時用）"""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(base, APP_NAME)
    elif sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    else:
        return os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}")


_BASE_PATH = _get_base_path()
_USER_DATA_DIR = _get_user_data_dir()


def _crash_excepthook(exc_type, exc_value, exc_tb):
    """exe 実行時に未捕捉例外でターミナルが即閉じないよう、ログ出力して Enter 待ちにする"""
    lines = traceback.format_exception(exc_type, exc_value, exc_tb)
    msg = "".join(lines)
    is_frozen = getattr(sys, "frozen", False)
    log_path = None
    if is_frozen:
        try:
            os.makedirs(_USER_DATA_DIR, exist_ok=True)
            log_path = os.path.join(_USER_DATA_DIR, "crash.log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(msg)
        except Exception:
            pass
    try:
        sys.__stderr__.write(msg)
        sys.__stderr__.flush()
    except Exception:
        pass
    if is_frozen and sys.__stderr__.isatty():
        try:
            sys.__stderr__.write("\n  エラーが発生しました。上記を確認してください。\n")
            if log_path:
                sys.__stderr__.write(f"  ログファイル: {log_path}\n")
            sys.__stderr__.write("  閉じるには Enter キーを押してください。\n")
            input()
        except Exception:
            pass
    else:
        if log_path:
            sys.__stderr__.write(f"\n  Error logged to: {log_path}\n")


def _install_crash_handler():
    """exe 時のみクラッシュ用 excepthook を設定"""
    if getattr(sys, "frozen", False):
        sys.excepthook = _crash_excepthook


# Load .env file if present (for GEMINI_API_KEY etc.)
def _load_dotenv():
    """Load .env file — exe時はユーザーデータDir、通常時はスクリプトDir"""
    # exe時はユーザーデータディレクトリの.envを優先
    if getattr(sys, 'frozen', False):
        env_path = os.path.join(_USER_DATA_DIR, ".env")
        # 初回起動時: .env.exampleをコピー
        if not os.path.exists(env_path):
            os.makedirs(_USER_DATA_DIR, exist_ok=True)
            example = os.path.join(_BASE_PATH, ".env.example")
            if os.path.exists(example):
                import shutil
                shutil.copy2(example, env_path)
    else:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    # Don't override existing env vars
                    if key and not os.environ.get(key):
                        os.environ[key] = value
    except Exception:
        pass

_load_dotenv()


def detect_cloud_ide():
    """クラウドIDE環境を検出する。"""
    if os.environ.get("CODESPACES"):
        return "codespaces"
    if os.environ.get("GITPOD_WORKSPACE_ID"):
        return "gitpod"
    return None


def print_header():
    """シンプルなヘッダーを表示"""
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║  AppTalentNavi v2.0                          ║")
    print("  ║  AIエージェント体験 研修ツール                ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    print("  AIエージェントが自動でタスクを実行します。")
    print("  あなたは指示を入力するだけ。あとはAIにお任せ！")
    if sys.platform == "win32":
        print("  ※ 推奨: PowerShell を開き、このフォルダで起動すると安定します。")
    print()


def check_gemini():
    """Gemini APIキーの確認と接続テスト"""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key or len(api_key) < 10:
        return False

    print("  Gemini APIを確認中...")
    try:
        # Simple models.list call to verify the key works
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": f"AppTalentNavi/{APP_VERSION}"})
        ctx = None
        try:
            import ssl
            ctx = ssl.create_default_context()
        except Exception:
            pass
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        data = json.loads(resp.read().decode("utf-8"))
        models = data.get("models", [])
        if models:
            print(f"  OK: Gemini API 接続成功（{len(models)} モデル利用可能）")
            print(f"  → {GEMINI_DEFAULT_MODEL} を使用します")
            print()
            return True
    except Exception as e:
        print(f"  Gemini API接続エラー: {e}")
        print()
    return False


def check_ollama():
    """Ollamaの自動セットアップ（インストール・起動・モデルDL）"""
    # ollama_setup.py を同一ディレクトリからインポート
    try:
        setup_dir = _BASE_PATH
        if setup_dir not in sys.path:
            sys.path.insert(0, setup_dir)
        from ollama_setup import ensure_ollama_ready
        return ensure_ollama_ready(RECOMMENDED_OLLAMA_MODEL)
    except ImportError:
        # ollama_setup.py が見つからない場合はフォールバック
        print("  Ollamaを確認中...")
        try:
            req = urllib.request.Request(
                f"{OLLAMA_BASE_URL}/api/tags",
                headers={"User-Agent": f"AppTalentNavi/{APP_VERSION}"}
            )
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            if models:
                print(f"  OK: Ollama接続成功（{len(models)} モデル利用可能）")
                print()
                return True
        except Exception:
            pass
        print()
        print("  Ollamaに接続できません。")
        print("  https://ollama.com からインストールしてください。")
        print()
        return False


def show_sample_prompts():
    """サンプルプロンプトを表示する。ユーザーは自由入力で指示を行う。"""
    print("  ━━ こんなことを頼めます ━━━━━━━━━━━━━━━")
    print()
    print("  たとえば、こんな指示を入力してみましょう：")
    print()
    print('    「Helloというテキストファイルを作って」')
    print()
    print('    「コーヒーショップのLPページを作って」')
    print()
    print('    「data/meetings にあるファイルを整理して」')
    print()
    print("  ※ 日本語でそのまま入力できます。何でも頼んでみましょう！")
    print()
    print("  ヒント: 最初は「Helloというテキストファイルを作って」がおすすめです。")
    print("          AIが「許可していいですか？」と聞いてきたら、y を押してEnterしてください。")
    print()


def _setup_workdir():
    """作業フォルダを対話的に設定する。"""
    # プラットフォームに応じたデフォルトパスを表示
    home = os.path.expanduser("~")
    if sys.platform == "win32":
        downloads = os.path.join(home, "Downloads")
        desktop = os.path.join(home, "Desktop")
        documents = os.path.join(home, "Documents")
    elif sys.platform == "darwin":
        downloads = os.path.join(home, "Downloads")
        desktop = os.path.join(home, "Desktop")
        documents = os.path.join(home, "Documents")
    else:
        downloads = os.path.join(home, "Downloads")
        desktop = os.path.join(home, "Desktop")
        documents = os.path.join(home, "Documents")

    print("  ━━ どこにファイルをつくりますか？ ━━━━━━━━")
    print()
    print("  AIが作るファイルの保存先を選んでください。")
    print()
    print(f"   1. ダウンロード   {downloads}")
    print(f"   2. デスクトップ   {desktop}")
    print(f"   3. ドキュメント   {documents}")
    print(f"   4. 現在のフォルダ {os.getcwd()}")
    print("   5. パスを直接入力")
    print()

    while True:
        try:
            choice = input("  番号を入力 [1-5] (Enter で 4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if choice == "1":
            workdir = downloads
        elif choice == "2":
            workdir = desktop
        elif choice == "3":
            workdir = documents
        elif choice == "" or choice == "4":
            workdir = os.getcwd()
        elif choice == "5":
            print()
            try:
                workdir = input("  フォルダのパスを入力: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                sys.exit(0)
            if not workdir:
                print("  パスが入力されませんでした。もう一度選択してください。")
                print()
                continue
        else:
            print("  1〜5の番号を入力してください。")
            print()
            continue

        # パスの存在確認
        if os.path.isdir(workdir):
            os.chdir(workdir)
            print()
            print(f"  → 作業フォルダ: {workdir}")
            print("  ※ このフォルダの中にAIがファイルを作成します。安心してください、他の場所には影響しません。")
            print()
            return
        else:
            print(f"  フォルダが見つかりません: {workdir}")
            print("  もう一度選択してください。")
            print()


def _should_skip_guide():
    """ガイドメニュー・作業フォルダ入力をスキップすべきか判定する。"""
    for arg in sys.argv[1:]:
        if arg in ("-p", "--prompt"):
            return True
        if arg.startswith("-p=") or arg.startswith("--prompt="):
            return True
        if arg == "--skip-guide":
            return True
    return False


def _is_cli_only_request():
    """LLM不要のCLI専用オプション（--help / --version / --list-sessions）のみか判定する。
    研修で「コマンドでエラーが出ないか」を確認するため、対話なしで co-vibe に渡す。"""
    cli_only = {"-h", "--help", "--version", "--list-sessions"}
    for arg in sys.argv[1:]:
        if arg in cli_only:
            return True
        if arg.startswith("--session-id"):  # --session-id は値が必要なので単体では判定しない
            continue
    return False


def _exec_co_vibe_early():
    """CLI専用オプション用に、対話・APIチェックをスキップして co-vibe を実行する。"""
    os.environ["HAJIME_MODE"] = "1"
    os.environ["HAJIME_VERSION"] = APP_VERSION
    os.environ["HAJIME_APP_NAME"] = APP_NAME
    if getattr(sys, "frozen", False):
        os.environ["HAJIME_USER_DATA_DIR"] = _USER_DATA_DIR
        os.environ["HAJIME_BASE_PATH"] = _BASE_PATH
    co_vibe_path = os.path.join(_BASE_PATH, "co-vibe.py")
    if not os.path.exists(co_vibe_path):
        print(f"  エラー: co-vibe.py が見つかりません: {co_vibe_path}")
        sys.exit(1)
    sys.argv[0] = co_vibe_path
    code = open(co_vibe_path, encoding="utf-8").read()
    exec(compile(code, co_vibe_path, "exec"), globals())


def _is_exe_first_run():
    """exe直接起動かつ初回（インストール先が存在しない）か判定する。"""
    if not getattr(sys, "frozen", False):
        return False
    install_dir = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
        APP_NAME,
    )
    return not os.path.isfile(os.path.join(install_dir, "AppTalentNavi.exe"))


def _install_to_path():
    """install-path.ps1 相当の処理: exeコピー・appnavi.cmdを作成・PATHに登録する。"""
    import shutil

    install_dir = os.path.join(
        os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
        APP_NAME,
    )
    os.makedirs(install_dir, exist_ok=True)

    # exe をインストール先にコピー
    src_exe = sys.executable
    dst_exe = os.path.join(install_dir, "AppTalentNavi.exe")
    try:
        shutil.copy2(src_exe, dst_exe)
    except Exception as e:
        print(f"  警告: exeのコピーに失敗しました: {e}")

    # appnavi.cmd を作成
    cmd_path = os.path.join(install_dir, "appnavi.cmd")
    try:
        with open(cmd_path, "w", encoding="ascii") as f:
            f.write('@echo off\n"%~dp0AppTalentNavi.exe" %*\n')
    except Exception as e:
        print(f"  警告: appnavi.cmdの作成に失敗しました: {e}")

    # ユーザーPATHに追加
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Environment",
            0,
            winreg.KEY_READ | winreg.KEY_WRITE,
        ) as key:
            try:
                user_path, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                user_path = ""
            if install_dir.lower() not in user_path.lower():
                new_path = f"{user_path};{install_dir}" if user_path else install_dir
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
    except Exception as e:
        print(f"  警告: PATH登録に失敗しました: {e}")


def _show_exe_first_run_message():
    """exe初回起動時のPowerShell誘導メッセージを表示して待機する。"""
    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║  セットアップ完了！                          ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    print("  次のステップ:")
    print()
    print('  1. PowerShellを開きましょう！')
    print('     (スタートメニューで「PowerShell」と入力)')
    print()
    print("  2. 以下のコマンドを入力してください:")
    print()
    print("     appnavi")
    print()
    try:
        input("  Enterキーで終了...")
    except (EOFError, KeyboardInterrupt):
        pass
    sys.exit(0)


def main():
    _install_crash_handler()  # exe 時: 未捕捉例外でターミナルが即閉じないようにする
    # CLI専用オプション（--help / --version / --list-sessions）の場合は対話・APIチェックをスキップ
    if _is_cli_only_request():
        _exec_co_vibe_early()
        return

    # exe初回起動: インストール + PowerShell誘導
    if _is_exe_first_run():
        print_header()
        print("  環境をセットアップ中...")
        _install_to_path()
        _show_exe_first_run_message()
        return

    print_header()

    use_gemini = False
    cloud_ide = detect_cloud_ide()

    if cloud_ide:
        # クラウドIDEではAPIキーはSecrets経由で設定済み前提
        print(f"  クラウドIDE検出: {cloud_ide}")
        os.environ["HAJIME_CLOUD_IDE"] = cloud_ide
        if os.environ.get("GEMINI_API_KEY"):
            if check_gemini():
                use_gemini = True
            else:
                print("  Gemini APIが利用できません。")
                print("  Codespaces Secrets に GEMINI_API_KEY を設定してください。")
                sys.exit(1)
        else:
            print("  GEMINI_API_KEY が設定されていません。")
            print("  Codespaces Secrets に GEMINI_API_KEY を設定してください。")
            sys.exit(1)
    else:
        # ローカル環境: Ollama優先 → Geminiキーがあれば追加確認
        # 1. まずOllamaをチェック（ローカルなので高速）
        ollama_ok = check_ollama()

        # 2. Gemini APIキーがあれば接続確認し、使えればGeminiを優先
        if os.environ.get("GEMINI_API_KEY"):
            if check_gemini():
                use_gemini = True
            else:
                if ollama_ok:
                    print("  Gemini APIが利用できません。Ollamaを使用します。")
                    print()

        # 3. どちらも使えない場合はエラー
        if not use_gemini and not ollama_ok:
            print()
            print("  AIプロバイダーが見つかりません。")
            print("  以下のいずれかを設定してください：")
            print("    1. Ollamaをインストールして起動（推奨・高速）")
            print("    2. GEMINI_API_KEY 環境変数を設定")
            print()
            print("  セットアップ: python setup-hajime.py")
            sys.exit(1)

    # === 環境変数で AppTalentNavi モードを設定 ===
    os.environ["HAJIME_MODE"] = "1"
    os.environ["HAJIME_VERSION"] = APP_VERSION
    os.environ["HAJIME_APP_NAME"] = APP_NAME
    os.environ["CO_VIBE_STRATEGY"] = "fast"

    if use_gemini:
        os.environ["CO_VIBE_MODEL"] = os.environ.get("CO_VIBE_MODEL", GEMINI_DEFAULT_MODEL)
    else:
        os.environ["OLLAMA_BASE_URL"] = OLLAMA_BASE_URL
        os.environ["CO_VIBE_MODEL"] = os.environ.get("CO_VIBE_MODEL", RECOMMENDED_OLLAMA_MODEL)

    # === 作業フォルダ設定 ===
    if not _should_skip_guide():
        _setup_workdir()

    # === サンプルプロンプト表示 ===
    if not _should_skip_guide():
        show_sample_prompts()

    # exe時はユーザーデータディレクトリ情報を環境変数に設定
    if getattr(sys, 'frozen', False):
        os.environ["HAJIME_USER_DATA_DIR"] = _USER_DATA_DIR
        os.environ["HAJIME_BASE_PATH"] = _BASE_PATH

    # co-vibe.py に渡す前に hajime 専用オプションを除去（co-vibe の argparse が未知オプションで落ちないように）
    while "--skip-guide" in sys.argv:
        sys.argv.remove("--skip-guide")

    # co-vibe.py を実行
    co_vibe_path = os.path.join(_BASE_PATH, "co-vibe.py")
    if not os.path.exists(co_vibe_path):
        print(f"  エラー: co-vibe.py が見つかりません: {co_vibe_path}")
        sys.exit(1)

    sys.argv[0] = co_vibe_path
    # exec in global scope so co-vibe.py's imports work correctly
    code = open(co_vibe_path, encoding='utf-8').read()
    exec(compile(code, co_vibe_path, 'exec'), globals())


if __name__ == "__main__":
    main()
