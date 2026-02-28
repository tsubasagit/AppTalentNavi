#!/usr/bin/env python3
"""AppTalentNavi — LP作成トレーニングCLIツール
Ollama（ローカルLLM）を使って、対話しながらランディングページを作成するツール。
プログラミング初心者向け研修用。

Usage:
    python hajime.py                    # 対話モード
    python hajime.py -p "カフェのLPを作って"  # ワンショット
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

APP_VERSION = "1.0.0"
APP_NAME = "AppTalentNavi"
RECOMMENDED_MODEL = "qwen2.5-coder:7b"
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


def print_header():
    """シンプルなヘッダーを表示"""
    print()
    print("  AppTalentNavi — LP作成トレーニングツール")
    print("  ────────────────────────────────────────")
    print()


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

    has_recommended = any(RECOMMENDED_MODEL.split(":")[0] in m for m in model_names)

    if not models:
        print()
        print("  Ollamaにモデルがありません。")
        print(f"  推奨モデルをダウンロードしてください：")
        print(f"    ollama pull {RECOMMENDED_MODEL}")
        print()
        return False

    if has_recommended:
        print(f"  OK: {RECOMMENDED_MODEL} が利用可能です")
    else:
        print(f"  注意: 推奨モデル({RECOMMENDED_MODEL})が見つかりません")
        print(f"  利用可能なモデル: {', '.join(models[:5])}")
        print(f"  推奨モデルのダウンロード: ollama pull {RECOMMENDED_MODEL}")
        print()
        # 利用可能なモデルがあれば続行
        if models:
            print(f"  → {models[0]} を使用して続行します")

    print()
    return True


def main():
    print_header()

    # Ollamaチェック
    if not check_ollama():
        sys.exit(1)

    # === 環境変数で AppTalentNavi モードを設定 ===
    os.environ["HAJIME_MODE"] = "1"
    os.environ["HAJIME_VERSION"] = APP_VERSION
    os.environ["HAJIME_APP_NAME"] = APP_NAME
    os.environ["OLLAMA_BASE_URL"] = OLLAMA_BASE_URL
    os.environ["CO_VIBE_STRATEGY"] = "auto"
    os.environ["CO_VIBE_MODEL"] = os.environ.get("CO_VIBE_MODEL", RECOMMENDED_MODEL)
    os.environ["HAJIME_AUTO_OPEN_HTML"] = "1"

    # co-vibe.py を実行
    co_vibe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "co-vibe.py")
    if not os.path.exists(co_vibe_path):
        print(f"  エラー: co-vibe.py が見つかりません: {co_vibe_path}")
        sys.exit(1)

    sys.argv[0] = co_vibe_path
    exec(open(co_vibe_path, encoding='utf-8').read())


if __name__ == "__main__":
    main()
