#!/usr/bin/env python3
"""AppTalentNavi セットアップ
Ollamaのインストール・起動確認と推奨モデルのダウンロードを行います。
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
RECOMMENDED_MODEL = "qwen2.5-coder:7b"
OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║    AppTalentNavi セットアップ         ║")
    print("  ╚══════════════════════════════════════╝")
    print()


def check_python():
    print("  [1/4] Python バージョン確認...")
    ver = sys.version_info
    if ver >= (3, 8):
        print(f"    OK: Python {ver.major}.{ver.minor}.{ver.micro}")
        return True
    else:
        print(f"    NG: Python {ver.major}.{ver.minor} (3.8以上が必要です)")
        return False


def check_ollama_installed():
    print("\n  [2/4] Ollama インストール確認...")
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
    print("\n  [3/4] Ollama 起動確認...")
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
    print(f"\n  [4/4] 推奨モデル ({RECOMMENDED_MODEL}) 確認...")

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


def show_complete():
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║    セットアップ完了！                 ║")
    print("  ╚══════════════════════════════════════╝")
    print()
    print("  起動方法：")
    print(f"    python hajime.py")
    print()
    print("  自動承認モードで起動（確認不要）：")
    print(f"    python hajime.py -y")
    print()
    print("  使い方：")
    print('    「カフェのLPを作って」と入力してみましょう！')
    print()


def main():
    clear()
    print_banner()

    # Step 1: Python
    if not check_python():
        sys.exit(1)

    # Step 2: Ollama installed
    if not check_ollama_installed():
        sys.exit(1)

    # Step 3: Ollama running
    running, models = check_ollama_running()
    if not running:
        sys.exit(1)

    # Step 4: Model
    check_model(models)

    # Done
    show_complete()


if __name__ == "__main__":
    main()
