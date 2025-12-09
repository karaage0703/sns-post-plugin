# SNS Post Plugin

Zenn、Qiita、はてなブログの記事を取得し、SNS推薦投稿を生成するためのMCPサーバーです。

## 特徴

- **Zenn記事取得**: ユーザーの人気記事を確率的に選択（個人/企業アカウント対応）
- **Qiita記事取得**: Qiita API v2を使用した記事取得といいね数による重み付け選択
- **はてなブログ記事取得**: アーカイブから記事を収集し、はてなブックマーク数で重み付け選択
- **キャッシュ機能**: はてなブログの記事データをキャッシュして高速化
- **Claude Code/Claude Desktop連携**: MCPプロトコルでシームレスに統合

---

## 🚀 インストール

### 前提条件

- Python 3.12以上
- [uv](https://github.com/astral-sh/uv)パッケージマネージャー

### 1. リポジトリをクローン

```bash
git clone https://github.com/karaage0703/sns-post-plugin.git
cd sns-post-plugin
```

### 2. 依存関係をインストール

```bash
uv sync
```

### 3. Claude Code にプラグインをインストール

```bash
# プラグインマーケットプレイスを追加（初回のみ）
/plugin marketplace add https://github.com/karaage0703/sns-post-plugin

# プラグインをインストール
/plugin install sns-post-plugin@karaage0703/sns-post-plugin
```

MCPサーバーは `.claude-plugin/plugin.json` に設定されているため、プラグインインストール時に自動的に有効化されます。

### 4. Claude Code を再起動

---

## 📖 使い方

### Zenn記事を取得

```
Zennのkaraage0703の記事を1つ取得してください
```

MCPサーバーが以下のツールを提供します:

- **fetch_zenn_articles**: Zennの記事を取得
  - `username`: Zennのユーザー名（必須）
  - `is_company`: 企業アカウントの場合はtrue（デフォルト: false）
  - `limit`: 取得する記事数（デフォルト: 1）
  - `random_seed`: ランダムシード（省略可）

### Qiita記事を取得

```
Qiitaのkaraage0703の記事を1つ取得してください
```

- **fetch_qiita_articles**: Qiitaの記事を取得
  - `username`: Qiitaのユーザー名（必須）
  - `limit`: 取得する記事数（デフォルト: 1）
  - `random_seed`: ランダムシード（省略可）

### はてなブログ記事を取得

```
https://karaage.hatenadiary.jp/ のはてなブログ記事を1つ取得してください
```

- **fetch_hatena_articles**: はてなブログの記事を取得
  - `blog_url`: はてなブログのURL（必須）
  - `start_year`: 記事収集の開始年（デフォルト: 2014）
  - `use_cache`: キャッシュを使用するか（デフォルト: true）

**注意**: 初回実行時は全記事を収集するため時間がかかります。2回目以降はキャッシュを使用します。

---

## 🎯 スラッシュコマンド

プラグインには、記事取得から投稿文生成までを自動化するスラッシュコマンドが用意されています。

### `/sns-post-plugin:zenn`

Zenn記事の取得とX（Twitter）向け推薦投稿文の生成を行います。

```
/sns-post-plugin:zenn
```

- ZennのURLを対話的に確認（デフォルト: https://zenn.dev/karaage0703）
- 個人アカウント・企業アカウント（`/p/`）を自動判定
- 記事内容に応じた投稿文パターンを自動選択
- `YYYYMMDD_<タイトル>.md` として保存

### `/sns-post-plugin:qiita`

Qiita記事の取得とX（Twitter）向け推薦投稿文の生成を行います。

```
/sns-post-plugin:qiita
```

- QiitaのURLを対話的に確認（デフォルト: https://qiita.com/karaage0703）
- いいね数による重み付けで記事を選択
- 記事内容に応じた投稿文パターンを自動選択
- `YYYYMMDD_qiita_<記事ID>.md` として保存

### `/sns-post-plugin:hatena`

はてなブログ記事の取得とX（Twitter）向け推薦投稿文の生成を行います。

```
/sns-post-plugin:hatena
```

- ブログURLを対話的に確認（デフォルト: https://karaage.hatenadiary.jp）
- 収集開始年を対話的に確認（デフォルト: 昨年から）
- はてなブックマーク数による重み付けで記事を選択
- `YYYYMMDD_hatena_<記事ID>.md` として保存
- 初回は記事収集に30秒〜1分程度かかります（2回目以降はキャッシュ使用）

---

## 📁 プロジェクト構成

```
sns-post-plugin/
├── src/
│   └── sns_post_plugin/
│       ├── __init__.py
│       ├── server.py           # MCPサーバーメインエントリーポイント
│       ├── zenn_fetcher.py     # Zenn記事取得機能
│       ├── qiita_fetcher.py    # Qiita記事取得機能
│       └── hatena_fetcher.py   # はてなブログ記事取得機能
├── commands/
│   ├── zenn.md                 # Zenn推薦生成コマンド
│   ├── qiita.md                # Qiita推薦生成コマンド
│   └── hatena.md               # はてなブログ推薦生成コマンド
├── pyproject.toml              # uv設定ファイル
├── mcp-config.json             # MCP設定例
├── zenn-recommendation.md      # Zenn推薦投稿ルール
├── karaage_hatena_recommendation.md  # はてな推薦投稿ルール
└── README.md
```

---

## 🔧 開発

### MCP Inspector でテスト

MCPサーバーをインタラクティブにテストできます：

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/sns-post-plugin run sns-post-plugin
```

ブラウザが開き、`fetch_zenn_articles`、`fetch_qiita_articles`、`fetch_hatena_articles` ツールをテストできます。

---

## 📝 記事推薦投稿の生成

取得した記事情報をもとに、以下のルールファイルに従って投稿文を生成できます:

- `zenn-recommendation.md`: Zenn記事推薦投稿のフォーマットとガイドライン
- `karaage_hatena_recommendation.md`: はてなブログ記事推薦投稿のフォーマットとガイドライン

---

## ⚠️ トラブルシューティング

### MCPサーバーが起動しない

```bash
# 依存関係の再インストール
uv sync --force

# Pythonバージョン確認（3.12以上必要）
python --version
```

### 記事が取得できない

- **Zenn**: ユーザー名のスペルを確認
- **Qiita**: ユーザー名のスペルを確認、API制限（60req/h）に注意
- **はてなブログ**: URLが正しいか確認（`https://` で始まる完全なURL）
- ネットワーク接続を確認

### キャッシュをクリア（はてなブログ）

```bash
rm -rf ~/.cache/sns-post-plugin/
```

---

## 📄 ライセンス

MIT License
