# AppTalentNavi v2.0 — CLI 動作確認・バグ報告

研修目的「CLIを使えるようにする」に基づき、コマンドごとの動作確認結果と修正内容をまとめました。

---

## 確認したコマンド一覧

| コマンド | 仕様上の入口 | 確認結果 |
|----------|--------------|----------|
| `python hajime.py` | 対話起動 | 要API・対話あり（想定どおり） |
| `python hajime.py -y` | 自動承認で起動 | 要API・ガイド後に起動（想定どおり） |
| `python hajime.py -p "..."` | ワンショット | 要API・ガイドスキップ可（想定どおり） |
| `python hajime.py --help` | ヘルプ表示 | **要修正→対応済** |
| `python hajime.py --version` | バージョン表示 | **要修正→対応済** |
| `python hajime.py --list-sessions` | セッション一覧 | **要修正→対応済** |
| `python hajime.py --resume` | 前回セッション再開 | 要API・作業フォルダ・ガイドあり（要望なら --skip-guide と併用でスキップ可） |
| `python hajime.py --skip-guide` | ガイド・作業フォルダをスキップ | **要修正→対応済**（2回目でガイドが出る不具合を修正） |
| `python setup-hajime.py` | セットアップ | 対話式（引数なし・想定どおり） |
| `python co-vibe.py --help` | （co-vibe 直接） | 正常 |
| `python co-vibe.py --list-sessions` | （co-vibe 直接） | 正常 |

---

## 修正したバグ

### 1. 【重大】`python hajime.py --help` / `--version` / `--list-sessions` で対話が止まらずエラー相当になる

**事象**  
仕様では「`python hajime.py` がメインのCLI入口」だが、`--help` / `--version` / `--list-sessions` を付けても、hajime.py が先に以下を実行してしまう。

1. ヘッダー表示  
2. Gemini / Ollama の接続チェック（未設定なら exit(1)）  
3. 作業フォルダ選択の入力待ち（「番号を入力 [1-5]」でブロック）  

このため「ヘルプだけ見たい」「セッション一覧だけ出したい」ができず、研修で「コマンドでエラーが出ないか」を確認する目的に合わない。

**原因**  
hajime.py が「CLI専用オプション」を解釈せず、常に API チェック → 作業フォルダ → ガイドの順で実行していた。

**対応**  
- `_is_cli_only_request()` を追加し、`-h` / `--help` / `--version` / `--list-sessions` のいずれかが付いているときは、API チェック・作業フォルダ・ガイドを一切行わず、そのまま co-vibe を実行するようにした。  
- 上記のオプションは co-vibe 側で処理されるため、`python hajime.py --help` 等で対話なしにヘルプ・バージョン・セッション一覧が表示される。

**確認コマンド（いずれも対話なしで終了）**

```powershell
python hajime.py --help
python hajime.py --version
python hajime.py --list-sessions
```

---

### 2. 【軽微】`--skip-guide` を付けても 2 回目にガイドメニューが出る

**事象**  
`python hajime.py --skip-guide --resume` などで、作業フォルダ選択はスキップされるが、その後に「体験メニュー」が表示される。

**原因**  
`_should_skip_guide()` 内で `sys.argv` から `--skip-guide` を **削除** していたため、  
「作業フォルダをスキップするか」の判定では `True` になるが、  
「ガイドメニューをスキップするか」の 2 回目の判定時には既に `--skip-guide` が無く `False` となり、ガイドが表示されていた。

**対応**  
- `_should_skip_guide()` では `sys.argv` を変更せず、`--skip-guide` の有無を参照するだけにした。  
- co-vibe に渡す直前に、hajime 専用オプション `--skip-guide` を `sys.argv` から除去するようにした（co-vibe の argparse が未知オプションでエラーにならないようにするため）。

---

## 研修用に推奨する確認手順

1. **ヘルプ・バージョン・セッション一覧（対話なしで成功することの確認）**

   ```powershell
   python hajime.py --help
   python hajime.py --version
   python hajime.py --list-sessions
   ```

2. **セットアップ**

   ```powershell
   python setup-hajime.py
   ```

3. **通常起動・自動承認・ワンショット**

   ```powershell
   python hajime.py
   python hajime.py -y
   python hajime.py --skip-guide -p "会議メモからデータを抽出して"
   ```

4. **対話中のスラッシュコマンド（SERVICE_SPEC 記載）**

   - `/scenario` — 体験シナリオ一覧  
   - `/help` — コマンド一覧  

   いずれも co-vibe 側で実装済み。対話起動後に入力して動作確認可能。

---

## 未対応・既知の点

- **`/resume`**  
  対話ループ内のスラッシュコマンドとしては未実装。  
  セッション再開は `python hajime.py --resume`（または `--session-id ID`）で行う（IMPROVEMENTS.md 記載の通り）。
- **`python hajime.py --resume` 時のガイド**  
  `--resume` 単体では作業フォルダ・ガイドはスキップされない。  
  ガイドを出したくない場合は `python hajime.py --skip-guide --resume` とする。

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2026-03-02 | 初版。CLI確認結果、バグ2件の修正内容と研修用確認手順を記載。 |
