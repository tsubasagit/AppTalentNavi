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
RECOMMENDED_OLLAMA_MODEL = "qwen2.5-coder:7b"
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


def show_guide_menu():
    """対話式ガイドメニューを表示し、選択に応じて環境変数に初期プロンプトを設定する。
    シナリオ実行後も対話を継続できるよう、-p（ワンショット）ではなく
    HAJIME_INITIAL_PROMPT 環境変数を使用する。
    """
    print("  ━━ 体験メニュー ━━━━━━━━━━━━━━━━━━━")
    print()
    print("  ★1. データ抽出【おすすめ・初めての方はコチラ】")
    print("     20件の会議メモから情報を自動で整理 (約5分)")
    print()
    print("   2. Webページ作成")
    print("     指定テーマでHTMLページを自動生成 (約3分)")
    print()
    print("   3. ファイル整理")
    print("     散らばったファイルを自動で分類 (約3分)")
    print()
    print("   4. 自由入力")
    print("     好きな指示を入力して自由に体験")
    print()

    while True:
        try:
            choice = input("  番号を入力 [1-4] (Enter で 1): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)

        if choice == "" or choice == "1":
            prompt = "data/meetings/ にある会議メモを読んで、顧客名・クレーム内容・担当者名・日付をCSVファイルに抽出してください"
            os.environ["HAJIME_INITIAL_PROMPT"] = prompt
            sys.argv.append("-y")
            print()
            print("  → データ抽出シナリオを開始します...")
            print()
            return

        elif choice == "2":
            print()
            try:
                theme = input("  どんなページを作りますか？（例: 自己紹介、カフェメニュー）: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                sys.exit(0)
            if not theme:
                print("  テーマが入力されませんでした。もう一度選択してください。")
                print()
                continue
            prompt = f"「{theme}」のHTMLページを作成してください。CSS・JSをインラインで含む、レスポンシブな1ファイル完結のWebページにしてください。output/ フォルダに保存してください"
            os.environ["HAJIME_INITIAL_PROMPT"] = prompt
            sys.argv.append("-y")
            print()
            print(f"  → 「{theme}」のWebページを作成します...")
            print()
            return

        elif choice == "3":
            print()
            try:
                folder = input("  整理するフォルダパス (Enter でカレントディレクトリ): ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                sys.exit(0)
            if not folder:
                folder = "."
            prompt = f"「{folder}」フォルダ内のファイル一覧を確認し、種類ごとにサブフォルダに分類・リネームしてください"
            os.environ["HAJIME_INITIAL_PROMPT"] = prompt
            sys.argv.append("-y")
            print()
            print(f"  → フォルダ「{folder}」のファイル整理を開始します...")
            print()
            return

        elif choice == "4":
            sys.argv.append("-y")
            print()
            print("  → 自由入力モードで起動します。プロンプトに指示を入力してください。")
            print()
            return

        else:
            print("  1〜4の番号を入力してください。")
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

    print("  ━━ 作業フォルダの設定 ━━━━━━━━━━━━━━━━")
    print()
    print("  AIエージェントがファイルを読み書きする")
    print("  メインの作業フォルダを選んでください。")
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


def main():
    # CLI専用オプション（--help / --version / --list-sessions）の場合は対話・APIチェックをスキップ
    if _is_cli_only_request():
        _exec_co_vibe_early()
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
        # ローカル環境: 従来のGemini→Ollamaフォールバックロジック
        # 1. Gemini APIキーがあれば優先的に使用
        if os.environ.get("GEMINI_API_KEY"):
            if check_gemini():
                use_gemini = True
            else:
                print("  Gemini APIが利用できません。Ollamaにフォールバックします。")
                print()

        # 2. Geminiが使えなければOllamaをチェック
        if not use_gemini:
            if not check_ollama():
                print()
                print("  AIプロバイダーが見つかりません。")
                print("  以下のいずれかを設定してください：")
                print("    1. GEMINI_API_KEY 環境変数を設定（推奨）")
                print("    2. Ollamaをインストールして起動")
                print()
                print("  セットアップ: python setup-hajime.py")
                sys.exit(1)

    # === 環境変数で AppTalentNavi モードを設定 ===
    os.environ["HAJIME_MODE"] = "1"
    os.environ["HAJIME_VERSION"] = APP_VERSION
    os.environ["HAJIME_APP_NAME"] = APP_NAME
    os.environ["CO_VIBE_STRATEGY"] = "auto"

    if use_gemini:
        os.environ["CO_VIBE_MODEL"] = os.environ.get("CO_VIBE_MODEL", GEMINI_DEFAULT_MODEL)
    else:
        os.environ["OLLAMA_BASE_URL"] = OLLAMA_BASE_URL
        os.environ["CO_VIBE_MODEL"] = os.environ.get("CO_VIBE_MODEL", RECOMMENDED_OLLAMA_MODEL)

    # === 作業フォルダ設定 ===
    if not _should_skip_guide():
        _setup_workdir()

    # === ガイドメニュー ===
    if not _should_skip_guide():
        show_guide_menu()

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
