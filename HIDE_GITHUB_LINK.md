# GitHubリンクを非表示にする方法

## 問題

Streamlit CloudのアプリページにGitHubリポジトリへのリンクが表示されている可能性があります。

## Streamlit Cloudでの設定

### 1. アプリページの設定を確認

1. **Streamlit Cloudにログイン**: https://streamlit.io/cloud
2. **デプロイしたアプリを選択**
3. **Settings** → **General** を確認
   - 現在、GitHubリンクを非表示にする直接的なオプションはありません

### 2. Aboutセクションを編集

1. アプリページで **「...」メニュー** → **「Edit app」** または **「Settings」**
2. **About** セクションがあれば編集
   - GitHubリポジトリへのリンクを削除
   - 最小限の説明のみ残す

### 3. リポジトリ名を変更（推奨）

GitHubリポジトリ名を推測しにくい名前に変更：

```bash
# GitHubでリポジトリ名を変更
# Settings → General → Repository name
```

推奨名例：
- `ml-utils-2024`
- `data-processing-v2`
- `preprocessing-app-util`

**重要**: リポジトリ名を変更した後、Streamlit Cloudで再デプロイが必要な場合があります。

## アプリ内の対策（追加）

### カスタムCSSでGitHubリンクを非表示

`app.py`に以下を追加することで、アプリ内のGitHubリンクを非表示にできます。

