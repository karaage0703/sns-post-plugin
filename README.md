# Claude Code プラグイン雛形

このリポジトリは Claude Code プラグインのスターターテンプレートです。

## 特徴
- **/hello** コマンドで日本語挨拶
- GitHub経由で簡単にインストール・共有可能

---

## 🚀 インストール

### 1. マーケットプレイスを追加
```
/plugin marketplace add https://github.com/karaage0703/claude-plugin-template
```

### 2. プラグインをインストール
```
/plugin install hello-plugin@karaage0703/claude-plugin-template
```

### 3. Claude Code を再起動

### 4. テスト
```
/hello
```
→ 「こんにちは！」と返れば成功です 🎉

---

## 📝 カスタマイズ

このテンプレートをフォークして、独自のプラグインを作成できます：

1. このリポジトリをフォーク
2. `commands/` フォルダに新しいコマンドを追加
3. `.claude-plugin/plugin.json` を編集
4. チームメンバーにリポジトリURLを共有

---

## 📁 ファイル構成

```
claude-plugin-template/
├── .claude-plugin/
│   ├── plugin.json          # プラグイン設定
│   └── marketplace.json     # マーケットプレイス設定
├── commands/
│   └── hello.md             # /hello コマンド定義
├── README.md
└── LICENSE
```

---

## 📄 ライセンス

MIT License
