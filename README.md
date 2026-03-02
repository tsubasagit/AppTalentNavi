# AppTalentNavi v2.0 — AIエージェント体験 研修ツール

> 自律型AIエージェントにビジネスタスクを丸投げする体験を、ゼロセットアップで。

## これは何？

非技術者（高校生・ビジネスパーソン）が「AIエージェントの自律動作」を目の前で体験できる研修ツールです。

AIがファイルを読み取り → 分析し → 結果を書き出す **全過程** を可視化。結果だけ見せるAIツール（Claude Artifacts等）とは異なり、「AIが自律的にタスクを完遂する」過程そのものが体験価値です。

### 3つの体験シナリオ

- **データ抽出**: バラバラな議事録20件 → 構造化CSV
- **Webページ作成**: テーマを伝えるだけ → レスポンシブHTML
- **ファイル整理**: 散らばったファイル → 自動分類・リネーム

### 技術的特徴

- Pure Python、ゼロ依存（`pip install` 不要）
- シングルファイルエンジン（`co-vibe.py`）
- Gemini API（クラウド）/ Ollama（ローカル）対応
- GitHub Codespaces / Gitpod でURLクリックのみ起動
- exe化（PyInstaller）対応 → USBで配布可能
- Ollama使用時は完全オフライン動作（企業内研修向け）

---

## クイックスタート（クラウドIDE）

### GitHub Codespaces（推奨）

1. リポジトリの **Code > Codespaces > Create codespace** をクリック
2. Codespaces Secrets に `GEMINI_API_KEY` を設定
   - [Google AI Studio](https://aistudio.google.com/apikey) で無料取得
3. ターミナルで自動起動 → 「会議メモからデータを抽出して」と入力

### Gitpod

1. リポジトリURLの先頭に `gitpod.io/#` を付けてアクセス
2. 環境変数に `GEMINI_API_KEY` を設定
3. 自動起動

---

## ローカル起動

### 前提条件

- Python 3.8以上
- Gemini APIキー（推奨）または Ollama

### セットアップ

```bash
# 1. リポジトリをクローン
git clone <repo-url> && cd training-service-wip

# 2. セットアップウィザード（APIキー設定）
python setup-hajime.py

# 3. 起動
python hajime.py

# 自動承認モード（確認不要）
python hajime.py -y
```

---

## 体験シナリオ

### A. データ抽出（推奨）

`data/meetings/` に20件の営業議事録が用意されています。フォーマットはバラバラ（構造化、半構造化、自由記述、メール転送風など）。

```
「会議メモからデータを抽出して」
```

AIエージェントが全ファイルを読み取り、顧客名・クレーム内容・担当者名を抽出してCSVに整理します。

### B. Webページ作成

```
「自己紹介ページを作って」
```

AIエージェントが指定テーマに沿ったHTMLページを自動生成します。CSS・JSをインラインで含む、レスポンシブな1ファイル完結のWebページが出来上がります。

### C. ファイル整理

```
「ダウンロードフォルダを整理して」
```

Glob でファイルを探索し、拡張子や内容に基づいて自動分類・リネームします。

---

## コマンド一覧

| コマンド | 説明 |
|----------|------|
| `/scenario` | 体験シナリオ一覧 |
| `/help` | コマンドヘルプ |
| `/clear` | 会話リセット |
| `/model <名前>` | モデル切り替え |
| `/yes` / `/no` | 自動承認 ON/OFF |
| `/undo` | 最後の変更を元に戻す |
| `/save` | セッション保存 |
| `/exit` | 終了 |

---

## プロジェクト構成

```
training-service-wip/
├── hajime.py              # ランチャー（環境検出→co-vibe起動）
├── co-vibe.py             # AIエージェントエンジン（11K行）
├── setup-hajime.py        # セットアップウィザード
├── data/
│   └── meetings/          # 研修用ダミー議事録（20件）
├── skills/
│   ├── data-extraction.md # データ抽出スキル
│   ├── web-research.md    # Web調査スキル
│   └── _archive/          # v1.xスキル
├── templates/             # v1.x LPテンプレート（レガシー）
├── .devcontainer/         # GitHub Codespaces設定
├── .gitpod.yml            # Gitpod設定
└── tests/                 # テストスイート
```

---

## アーキテクチャ

```
┌─────────────────────────────────────────────┐
│  AppTalentNavi (hajime.py)                  │
│  ├─ 環境検出（Cloud IDE / ローカル）          │
│  ├─ LLM自動セットアップ（Gemini or Ollama）   │
│  ├─ 体験メニュー（3シナリオ）                 │
│  └─ 作業ディレクトリ選択                      │
├─────────────────────────────────────────────┤
│  co-vibe.py (AIエージェントエンジン)          │
│  ├─ HAJIME_MODE: 日本語UI / エラー抑制       │
│  ├─ スキル読み込み (skills/*.md)             │
│  └─ ツール自律実行 (Bash/File/Glob/Grep...)  │
├─────────────────────────────────────────────┤
│  ollama_setup.py (LLM環境管理)              │
│  ├─ 自動インストール (Windows)               │
│  ├─ サービス起動管理                          │
│  └─ モデル自動取得 + 進捗表示                 │
├─────────────────────────────────────────────┤
│  LLM Provider                               │
│  ├─ Gemini 2.5 Flash Lite (クラウド)         │
│  └─ Ollama + qwen2.5-coder:7b (ローカル)    │
└─────────────────────────────────────────────┘
```

---

## 講師向け

研修の運営手順は [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) を参照してください。

---

## ドキュメント

| ファイル | 内容 |
|---|---|
| [POSITION-PAPER.md](POSITION-PAPER.md) | 製品ポジショニング分析（Ollama/co-vibeとの比較） |
| [SERVICE_SPEC.md](SERVICE_SPEC.md) | サービス仕様書 |
| [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) | 講師ガイド（90分カリキュラム） |
| [VISION-ROADMAP.md](VISION-ROADMAP.md) | co-vibe ビジョン＆ロードマップ |

---

## ライセンス

MIT License. Copyright (c) 2026 Yoichi Ochiai.
