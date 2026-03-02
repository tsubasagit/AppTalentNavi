#!/usr/bin/env python3
"""AppTalentNavi ビルドスクリプト — PyInstallerでexeを生成

Usage:
    python build.py          # ビルド実行
    python build.py --clean  # dist/build をクリーンしてからビルド
"""
import os
import sys
import shutil
import subprocess

# Fix encoding for Windows Japanese console
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONUTF8', '1')
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

APP_NAME = "AppTalentNavi"
APP_VERSION = "2.0.0"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def check_pyinstaller():
    """PyInstallerがインストールされているか確認"""
    try:
        import PyInstaller
        print(f"  PyInstaller {PyInstaller.__version__} を検出")
        return True
    except ImportError:
        print("  PyInstallerがインストールされていません。")
        print("  インストール: pip install pyinstaller")
        return False


def clean():
    """ビルド成果物をクリーン"""
    for d in ["build", "dist"]:
        path = os.path.join(SCRIPT_DIR, d)
        if os.path.exists(path):
            print(f"  クリーン: {d}/")
            shutil.rmtree(path)
    spec = os.path.join(SCRIPT_DIR, f"{APP_NAME}.spec")
    if os.path.exists(spec):
        os.remove(spec)


def create_version_info():
    """Windowsバージョン情報ファイルを生成"""
    parts = APP_VERSION.split(".")
    major = int(parts[0]) if len(parts) > 0 else 2
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0

    content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, 0),
    prodvers=({major}, {minor}, {patch}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'041104b0',
          [
            StringStruct(u'CompanyName', u'AppTalentHub'),
            StringStruct(u'FileDescription', u'AppTalentNavi - AIエージェント体験 研修ツール'),
            StringStruct(u'FileVersion', u'{APP_VERSION}'),
            StringStruct(u'InternalName', u'{APP_NAME}'),
            StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
            StringStruct(u'ProductName', u'{APP_NAME}'),
            StringStruct(u'ProductVersion', u'{APP_VERSION}'),
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [0x0411, 1200])])
  ]
)
"""
    path = os.path.join(SCRIPT_DIR, "version_info.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  バージョン情報を生成: version_info.txt")
    return path


def build():
    """PyInstallerでexeをビルド"""
    print()
    print("  ╔══════════════════════════════════════╗")
    print(f"  ║  {APP_NAME} v{APP_VERSION} ビルド     ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    if not check_pyinstaller():
        return False

    # バージョン情報生成
    version_file = create_version_info()

    # アイコンファイルの確認
    icon_path = os.path.join(SCRIPT_DIR, "assets", "icon.ico")
    icon_arg = []
    if os.path.exists(icon_path):
        icon_arg = ["--icon", icon_path]
        print(f"  アイコン: assets/icon.ico")
    else:
        print("  アイコン: なし（assets/icon.ico が見つかりません）")

    # 同梱するデータファイルの構築
    sep = ";" if sys.platform == "win32" else ":"
    add_data = []

    # co-vibe.py（メインエンジン）
    co_vibe = os.path.join(SCRIPT_DIR, "co-vibe.py")
    if os.path.exists(co_vibe):
        add_data.extend(["--add-data", f"{co_vibe}{sep}."])

    # ollama_setup.py
    ollama_setup = os.path.join(SCRIPT_DIR, "ollama_setup.py")
    if os.path.exists(ollama_setup):
        add_data.extend(["--add-data", f"{ollama_setup}{sep}."])

    # data/ ディレクトリ
    data_dir = os.path.join(SCRIPT_DIR, "data")
    if os.path.isdir(data_dir):
        add_data.extend(["--add-data", f"{data_dir}{sep}data"])

    # skills/ ディレクトリ
    skills_dir = os.path.join(SCRIPT_DIR, "skills")
    if os.path.isdir(skills_dir):
        add_data.extend(["--add-data", f"{skills_dir}{sep}skills"])

    # templates/ ディレクトリ
    templates_dir = os.path.join(SCRIPT_DIR, "templates")
    if os.path.isdir(templates_dir):
        add_data.extend(["--add-data", f"{templates_dir}{sep}templates"])

    # .env.example
    env_example = os.path.join(SCRIPT_DIR, ".env.example")
    if os.path.exists(env_example):
        add_data.extend(["--add-data", f"{env_example}{sep}."])

    # PyInstallerコマンドの構築
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--console",
        "--name", APP_NAME,
        "--version-file", version_file,
    ] + icon_arg + add_data + [
        "--hidden-import=ollama_setup",
        "--noconfirm",
        os.path.join(SCRIPT_DIR, "hajime.py"),
    ]

    print()
    print("  ビルドを開始します...")
    print(f"  出力先: dist/{APP_NAME}.exe")
    print()

    try:
        result = subprocess.run(
            cmd,
            cwd=SCRIPT_DIR,
            timeout=600,  # 10分タイムアウト
        )
        if result.returncode == 0:
            exe_path = os.path.join(SCRIPT_DIR, "dist", f"{APP_NAME}.exe")
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print()
                print("  ╔══════════════════════════════════════╗")
                print("  ║  ビルド完了！                         ║")
                print("  ╚══════════════════════════════════════╝")
                print()
                print(f"  出力: dist/{APP_NAME}.exe ({size_mb:.1f} MB)")
                print()
                return True
            else:
                print("  ビルドは完了しましたが、exeファイルが見つかりません。")
                return False
        else:
            print(f"  ビルドに失敗しました（コード: {result.returncode}）")
            return False
    except subprocess.TimeoutExpired:
        print("  ビルドがタイムアウトしました（10分超過）")
        return False
    except Exception as e:
        print(f"  ビルドエラー: {e}")
        return False


def main():
    if "--clean" in sys.argv:
        clean()

    success = build()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
