# AppTalentNavi v2.0 — AIエージェント体験 研修ツール

> 自律型AIエージェントにビジネスタスクを丸投げする体験を、ゼロセットアップで。

## これは何？

ビジネスパーソンが「AIエージェントにローカル業務を任せる」体験を通じて、AI活用スキルを身につけるための研修ツールです。

- **データ抽出**: バラバラな議事録 → 構造化CSV
- **Web調査**: テーマを投げるだけ → 出典付きレポート
- **ファイル整理**: 散らばったファイル → 自動分類・リネーム

### 技術的特徴

- Pure Python、ゼロ依存（`pip install` 不要）
- シングルファイルエンジン（`co-vibe.py`）
- Gemini API（クラウド）/ Ollama（ローカル）対応
- GitHub Codespaces / Gitpod でURLクリックのみ起動

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

### B. Web調査

```
「AIエージェントの市場動向を調べて」
```

WebSearch / WebFetch を使って情報を収集し、出典URL付きのMarkdownレポートを生成します。

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

## 講師向け

研修の運営手順は [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) を参照してください。

---

## ライセンス

MIT License. Copyright (c) 2026 Yoichi Ochiai.
