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

# Patch 2: Fix encoding for Windows Japanese console
if sys.platform == 'win32':
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

# Load .env file if present (for GEMINI_API_KEY etc.)
def _load_dotenv():
    """Load .env file from the same directory as this script."""
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
    print("  AppTalentNavi — AIエージェント体験 研修ツール")
    print("  ──────────────────────────────────────────────")
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
    """Ollamaの起動確認とモデルチェック"""
    print("  Ollamaを確認中...")

    # 1. Ollama接続チェック
    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/tags",
            headers={"User-Agent": f"AppTalentNavi/{APP_VERSION}"}
        )
        ctx = None
        try:
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        except Exception:
            pass
        resp = urllib.request.urlopen(req, timeout=5, context=ctx)
        data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        print()
        print("  Ollamaに接続できません。")
        print()
        print("  以下を確認してください：")
        print("  1. Ollamaがインストールされているか")
        print("     → https://ollama.ai からダウンロード")
        print("  2. Ollamaが起動しているか")
        print("     → ターミナルで: ollama serve")
        print()
        return False

    # 2. モデルチェック
    models = [m.get("name", "") for m in data.get("models", [])]
    model_names = [m.split(":")[0] for m in models]

    has_recommended = any(RECOMMENDED_OLLAMA_MODEL.split(":")[0] in m for m in model_names)

    if not models:
        print()
        print("  Ollamaにモデルがありません。")
        print(f"  推奨モデルをダウンロードしてください：")
        print(f"    ollama pull {RECOMMENDED_OLLAMA_MODEL}")
        print()
        return False

    if has_recommended:
        print(f"  OK: {RECOMMENDED_OLLAMA_MODEL} が利用可能です")
    else:
        print(f"  注意: 推奨モデル({RECOMMENDED_OLLAMA_MODEL})が見つかりません")
        print(f"  利用可能なモデル: {', '.join(models[:5])}")
        print(f"  推奨モデルのダウンロード: ollama pull {RECOMMENDED_OLLAMA_MODEL}")
        print()
        # 利用可能なモデルがあれば続行
        if models:
            print(f"  → {models[0]} を使用して続行します")

    print()
    return True


def main():
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

    # co-vibe.py を実行
    co_vibe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "co-vibe.py")
    if not os.path.exists(co_vibe_path):
        print(f"  エラー: co-vibe.py が見つかりません: {co_vibe_path}")
        sys.exit(1)

    sys.argv[0] = co_vibe_path
    # exec in global scope so co-vibe.py's imports work correctly
    code = open(co_vibe_path, encoding='utf-8').read()
    exec(compile(code, co_vibe_path, 'exec'), globals())


if __name__ == "__main__":
    main()
