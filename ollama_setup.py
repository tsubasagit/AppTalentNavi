#!/usr/bin/env python3
"""Ollama自動セットアップ — AppTalentNavi v2.0

Ollamaのインストール確認・自動インストール・起動・モデルダウンロードを
Pure Python (stdlib のみ) で行うモジュール。

Usage:
    from ollama_setup import ensure_ollama_ready
    if ensure_ollama_ready("qwen2.5-coder:7b"):
        print("準備完了！")
"""
import os
import sys
import json
import time
import shutil
import subprocess
import urllib.request
import urllib.error
import tempfile
import threading

# Windows UTF-8
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_DOWNLOAD_URL = "https://ollama.com/download/OllamaSetup.exe"


def _print_status(msg, end="\n"):
    """ステータスメッセージを表示"""
    print(f"  {msg}", end=end, flush=True)


def _print_progress_bar(current, total, width=30):
    """プログレスバーを表示"""
    if total <= 0:
        return
    pct = min(current / total, 1.0)
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    if total >= 1024 * 1024 * 1024:
        cur_str = f"{current / (1024**3):.1f}GB"
        tot_str = f"{total / (1024**3):.1f}GB"
    elif total >= 1024 * 1024:
        cur_str = f"{current / (1024**2):.0f}MB"
        tot_str = f"{total / (1024**2):.0f}MB"
    else:
        cur_str = f"{current / 1024:.0f}KB"
        tot_str = f"{total / 1024:.0f}KB"
    print(f"\r  [{bar}] {pct*100:.0f}% ({cur_str}/{tot_str})", end="", flush=True)


def is_ollama_installed():
    """Ollamaがインストールされているか確認

    Returns:
        str or None: 見つかったollamaコマンドのパス。見つからなければNone
    """
    # 1. PATH上にollamaコマンドがあるか
    cmd = shutil.which("ollama")
    if cmd:
        return cmd
    # 2. Windows: デフォルトインストール先を確認
    if sys.platform == "win32":
        default_paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"),
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Ollama", "ollama.exe"),
        ]
        for p in default_paths:
            if p and os.path.isfile(p):
                return p
    # 3. ollama --version で確認
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return "ollama"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def download_ollama_installer(dest_dir=None):
    """Ollamaインストーラーをダウンロードしてパスを返す"""
    if dest_dir is None:
        dest_dir = tempfile.gettempdir()
    dest_path = os.path.join(dest_dir, "OllamaSetup.exe")

    _print_status("インストーラーをダウンロード中...")

    try:
        ctx = None
        try:
            import ssl
            ctx = ssl.create_default_context()
        except Exception:
            pass

        req = urllib.request.Request(
            OLLAMA_DOWNLOAD_URL,
            headers={"User-Agent": "AppTalentNavi/2.0"}
        )
        resp = urllib.request.urlopen(req, timeout=60, context=ctx)
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1024 * 256  # 256KB chunks

        with open(dest_path, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    _print_progress_bar(downloaded, total)

        if total > 0:
            print()  # newline after progress bar
        _print_status("ダウンロード完了！")
        return dest_path

    except Exception as e:
        _print_status(f"ダウンロードに失敗しました: {e}")
        return None


def install_ollama(installer_path):
    """Ollamaをサイレントインストール"""
    if not os.path.isfile(installer_path):
        _print_status("インストーラーが見つかりません。")
        return False

    _print_status("AIエンジン（Ollama）をインストールしています...")
    _print_status("（管理者権限が必要な場合、確認ダイアログが表示されます）")

    try:
        # /VERYSILENT: 完全サイレント（Inno Setupベース）、/NORESTART: 再起動しない
        result = subprocess.run(
            [installer_path, "/VERYSILENT", "/NORESTART"],
            capture_output=True, text=True, timeout=300  # 5分タイムアウト
        )
        if result.returncode == 0:
            _print_status("インストールが完了しました！")
            # PATH更新を反映するために少し待つ（レジストリ反映待ち）
            time.sleep(3)
            return True
        else:
            _print_status(f"インストールに失敗しました（コード: {result.returncode}）")
            if result.stderr:
                _print_status(f"  詳細: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        _print_status("インストールがタイムアウトしました。手動でインストールしてください。")
        _print_status("  → https://ollama.com からダウンロード")
        return False
    except OSError as e:
        _print_status(f"インストーラーの実行に失敗しました: {e}")
        return False


def is_ollama_running():
    """Ollamaサーバーが起動中か確認"""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags")
        resp = urllib.request.urlopen(req, timeout=3)
        resp.read()
        return True
    except Exception:
        return False


def start_ollama_service():
    """Ollamaサービスをバックグラウンドで起動"""
    _print_status("AIエンジンを起動中...")

    # Windows: ollama serve をバックグラウンドで起動
    try:
        ollama_cmd = shutil.which("ollama")
        if not ollama_cmd and sys.platform == "win32":
            # デフォルトパスを試す
            default = os.path.join(
                os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"
            )
            if os.path.isfile(default):
                ollama_cmd = default

        if not ollama_cmd:
            _print_status("ollamaコマンドが見つかりません。")
            return False

        # バックグラウンドで起動 (Windows: CREATE_NO_WINDOW)
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        subprocess.Popen(
            [ollama_cmd, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **kwargs
        )

        # サーバーが起動するまで待機
        for i in range(30):  # 最大30秒
            time.sleep(1)
            if is_ollama_running():
                _print_status("AIエンジンが起動しました！")
                return True

        _print_status("AIエンジンの起動がタイムアウトしました。")
        return False

    except Exception as e:
        _print_status(f"AIエンジンの起動に失敗しました: {e}")
        return False


def get_installed_models():
    """インストール済みモデルの一覧を取得"""
    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/tags",
            headers={"User-Agent": "AppTalentNavi/2.0"}
        )
        resp = urllib.request.urlopen(req, timeout=5)
        data = json.loads(resp.read().decode("utf-8"))
        return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []


def pull_model(model_name):
    """モデルをダウンロード（進捗表示付き）"""
    _print_status(f"AIモデル ({model_name}) をダウンロード中...")
    _print_status("（初回は数分〜十数分かかります）")

    try:
        # /api/pull エンドポイントを使用（ストリーミングレスポンス）
        req_data = json.dumps({"name": model_name, "stream": True}).encode("utf-8")
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/pull",
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "AppTalentNavi/2.0",
            },
            method="POST",
        )

        resp = urllib.request.urlopen(req, timeout=1800)  # 30分タイムアウト
        last_status = ""

        for line in resp:
            line = line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            status = data.get("status", "")
            total = data.get("total", 0)
            completed = data.get("completed", 0)

            if total > 0 and completed > 0:
                _print_progress_bar(completed, total)
            elif status and status != last_status:
                if last_status and "pulling" in last_status.lower():
                    print()  # newline after progress bar
                _print_status(status)
                last_status = status

            if data.get("error"):
                print()
                _print_status(f"エラー: {data['error']}")
                return False

        print()  # newline after last progress bar
        _print_status(f"{model_name} のダウンロードが完了しました！")
        return True

    except urllib.error.URLError as e:
        _print_status(f"ダウンロードに失敗しました: {e}")
        _print_status("Ollamaが起動しているか確認してください。")
        return False
    except Exception as e:
        _print_status(f"エラーが発生しました: {e}")
        return False


def ensure_ollama_ready(model_name):
    """Ollamaのインストール・起動・モデルDLをすべて自動で行う

    Args:
        model_name: 使用するモデル名（例: "qwen2.5-coder:7b"）

    Returns:
        bool: 準備が完了したらTrue
    """
    print()
    _print_status("━━ AIエンジン セットアップ ━━━━━━━━━━━━━━")
    print()

    # Step 1: Ollamaインストール確認
    _print_status("AIエンジンを確認中...")

    if not is_ollama_installed():
        _print_status("AIエンジン（Ollama）が見つかりません。")

        if sys.platform != "win32":
            _print_status("自動インストールはWindows版のみ対応しています。")
            _print_status("以下からインストールしてください：")
            _print_status("  → https://ollama.com")
            return False

        _print_status("自動インストールを開始します...")
        print()

        installer = download_ollama_installer()
        if not installer:
            return False

        if not install_ollama(installer):
            return False

        # インストーラーを削除
        try:
            os.remove(installer)
        except OSError:
            pass

        print()

        # インストール後の確認（PATHがプロセスに反映されない場合があるため直接パスもチェック）
        ollama_path = is_ollama_installed()
        if not ollama_path:
            _print_status("インストール後の確認に失敗しました。")
            _print_status("PCを再起動してから再度お試しください。")
            return False
    else:
        _print_status("AIエンジン: OK")

    # Step 2: Ollama起動確認
    if not is_ollama_running():
        if not start_ollama_service():
            _print_status("")
            _print_status("AIエンジンを起動できませんでした。")
            _print_status("以下を試してください：")
            _print_status("  1. PCを再起動する")
            _print_status("  2. Ollamaアプリを手動で起動する")
            return False
    else:
        _print_status("AIエンジン起動: OK")

    # Step 3: モデル確認・ダウンロード
    models = get_installed_models()
    model_base = model_name.split(":")[0]
    has_model = any(model_base in m for m in models)

    if not has_model:
        print()
        if not pull_model(model_name):
            _print_status("")
            _print_status("モデルのダウンロードに失敗しました。")
            _print_status("ネットワーク接続を確認してください。")
            return False
    else:
        _print_status(f"AIモデル ({model_name}): OK")

    print()
    _print_status("✓ 準備が完了しました！")
    print()
    return True


if __name__ == "__main__":
    # テスト用: 直接実行するとセットアップを実行
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5-coder:7b"
    success = ensure_ollama_ready(model)
    sys.exit(0 if success else 1)
