#!/usr/bin/env python3
"""AppTalentNavi セットアップ
Gemini APIキーの設定、またはOllamaのインストール・起動確認と推奨モデルのダウンロードを行います。
"""
import os
import sys
import json
import subprocess
import urllib.request
import time

# Windows UTF-8
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

APP_NAME = "AppTalentNavi"
APP_VERSION = "2.0.0"
RECOMMENDED_MODEL = "qwen2.5-coder:7b"
GEMINI_DEFAULT_MODEL = "gemini-2.5-flash-lite"
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, ".env")


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║    AppTalentNavi セットアップ v2.0    ║")
    print("  ╚══════════════════════════════════════╝")
    print()


def check_python():
    print("  [1/5] Python バージョン確認...")
    ver = sys.version_info
    if ver >= (3, 8):
        print(f"    OK: Python {ver.major}.{ver.minor}.{ver.micro}")
        return True
    else:
        print(f"    NG: Python {ver.major}.{ver.minor} (3.8以上が必要です)")
        return False


def setup_gemini_key():
    """Gemini APIキーの設定（任意）"""
    print("\n  [2/5] Gemini APIキー設定（任意）...")
    print()
    print("    Gemini APIを使うと、クラウドAI（高品質）でAIエージェント体験ができます。")
    print("    無料枠あり: https://aistudio.google.com/apikey")
    print()
    print("    スキップする場合はそのまま Enter を押してください。")
    print("    （スキップした場合、Ollama（ローカルAI）を使用します）")
    print()

    # Check if already set in environment or .env
    existing_key = os.environ.get("GEMINI_API_KEY", "")
    if existing_key:
        masked = existing_key[:8] + "..." + existing_key[-4:] if len(existing_key) > 12 else "***"
        print(f"    現在のキー: {masked}")
        answer = input("    新しいキーを入力しますか？ (y/n): ").strip().lower()
        if answer != 'y':
            print("    既存のキーを使用します。")
            return existing_key

    api_key = input("    Gemini APIキー: ").strip()

    if not api_key:
        print("    スキップしました。Ollamaを使用します。")
        return ""

    # Validate the key
    print("    APIキーを確認中...")
    try:
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
            print(f"    OK: APIキーが有効です（{len(models)} モデル利用可能）")
        else:
            print("    警告: APIキーは受け付けられましたが、モデルが見つかりません。")
    except Exception as e:
        print(f"    エラー: APIキーが無効です ({e})")
        retry = input("    やり直しますか？ (y/n): ").strip().lower()
        if retry == 'y':
            return setup_gemini_key()
        print("    スキップします。Ollamaを使用します。")
        return ""

    # Save to .env file
    _save_env_key("GEMINI_API_KEY", api_key)
    os.environ["GEMINI_API_KEY"] = api_key
    print(f"    APIキーを .env に保存しました。")
    return api_key


def _save_env_key(key, value):
    """Save or update a key in the .env file."""
    lines = []
    key_found = False

    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            pass

    # Update existing key or add new one
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped.startswith(f"# {key}="):
            new_lines.append(f"{key}={value}\n")
            key_found = True
        else:
            new_lines.append(line)

    if not key_found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"{key}={value}\n")

    try:
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"    警告: .envファイルの保存に失敗しました: {e}")


def check_ollama_installed():
    print("\n  [3/5] Ollama インストール確認...")
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            print(f"    OK: Ollama がインストールされています ({version})")
            return True
    except FileNotFoundError:
        pass
    except Exception:
        pass

    print("    Ollama がインストールされていません。")
    print()
    print("    インストール方法：")
    print("    → https://ollama.ai にアクセス")
    print("    → お使いのOSに合ったインストーラーをダウンロード")
    print("    → インストール後、このスクリプトを再実行してください")
    return False


def check_ollama_running():
    print("\n  [4/5] Ollama 起動確認...")
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode("utf-8"))
        models = [m.get("name", "") for m in data.get("models", [])]
        print(f"    OK: Ollama が起動中 ({len(models)} モデル)")
        return True, models
    except Exception:
        print("    Ollama が起動していません。")
        print()
        print("    起動方法：")
        print("    → 別のターミナルで: ollama serve")
        print("    → または Ollama アプリを起動")
        print()

        answer = input("    Ollama を起動してから Enter を押してください (q で中止): ").strip()
        if answer.lower() == 'q':
            return False, []

        # Retry
        try:
            req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "") for m in data.get("models", [])]
            print(f"    OK: Ollama が起動中 ({len(models)} モデル)")
            return True, models
        except Exception:
            print("    まだ接続できません。Ollama を起動してから再実行してください。")
            return False, []


def check_model(models):
    print(f"\n  [5/5] 推奨モデル ({RECOMMENDED_MODEL}) 確認...")

    model_base = RECOMMENDED_MODEL.split(":")[0]
    has_model = any(model_base in m for m in models)

    if has_model:
        print(f"    OK: {RECOMMENDED_MODEL} が利用可能です")
        return True

    print(f"    {RECOMMENDED_MODEL} がまだインストールされていません。")
    print()
    answer = input(f"    ダウンロードしますか？ (y/n): ").strip().lower()

    if answer != 'y':
        if models:
            print(f"\n    利用可能なモデル: {', '.join(models[:5])}")
            print(f"    既存のモデルで続行できます。")
            return True
        else:
            print(f"    モデルがありません。以下でダウンロードしてください：")
            print(f"      ollama pull {RECOMMENDED_MODEL}")
            return False

    print(f"\n    {RECOMMENDED_MODEL} をダウンロード中...")
    print(f"    (初回は数分かかります。お待ちください...)")
    print()

    try:
        process = subprocess.Popen(
            ["ollama", "pull", RECOMMENDED_MODEL],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True
        )
        for line in process.stdout:
            sys.stdout.write(f"    {line}")
            sys.stdout.flush()
        process.wait()

        if process.returncode == 0:
            print(f"\n    OK: {RECOMMENDED_MODEL} のダウンロードが完了しました！")
            return True
        else:
            print(f"\n    ダウンロードに失敗しました。手動で実行してください：")
            print(f"      ollama pull {RECOMMENDED_MODEL}")
            return False
    except Exception as e:
        print(f"\n    エラー: {e}")
        print(f"    手動で実行してください: ollama pull {RECOMMENDED_MODEL}")
        return False


def show_complete(use_gemini=False):
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║    セットアップ完了！                 ║")
    print("  ╚══════════════════════════════════════╝")
    print()
    if use_gemini:
        print(f"  AIプロバイダー: Gemini ({GEMINI_DEFAULT_MODEL})")
    else:
        print(f"  AIプロバイダー: Ollama ({RECOMMENDED_MODEL})")
    print()
    print("  起動方法：")
    print(f"    python hajime.py")
    print()
    print("  自動承認モードで起動（確認不要）：")
    print(f"    python hajime.py -y")
    print()
    print("  使い方：")
    print('    「会議メモからデータを抽出して」と入力してみましょう！')
    print()


def main():
    clear()
    print_banner()

    # Step 1: Python
    if not check_python():
        sys.exit(1)

    # Step 2: Gemini APIキー（任意）
    gemini_key = setup_gemini_key()
    use_gemini = bool(gemini_key)

    if use_gemini:
        # Geminiが使えるなら、Ollamaのチェックはスキップ
        print("\n  [3/5] Ollama インストール確認... スキップ（Gemini使用）")
        print("\n  [4/5] Ollama 起動確認... スキップ（Gemini使用）")
        print("\n  [5/5] モデル確認... Gemini 2.5 Flash Lite を使用します")
    else:
        # Step 3: Ollama installed
        if not check_ollama_installed():
            sys.exit(1)

        # Step 4: Ollama running
        running, models = check_ollama_running()
        if not running:
            sys.exit(1)

        # Step 5: Model
        check_model(models)

    # Done
    show_complete(use_gemini)


if __name__ == "__main__":
    main()
