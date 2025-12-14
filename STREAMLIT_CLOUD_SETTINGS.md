# Streamlit CloudでGitHubリンクを非表示にする方法

## 問題

Streamlit CloudのアプリページにGitHubリポジトリへのリンクが表示されている。

## 確認すべき場所

### 1. Streamlit Cloudのアプリページ

アプリのURL（例: `https://your-app.streamlit.app`）にアクセスして確認：

- **右上のメニュー（☰）**: GitHubリンクが表示されていないか
- **フッター**: GitHubリンクが表示されていないか
- **Aboutセクション**: GitHubリポジトリへのリンクが表示されていないか

### 2. Streamlit Cloudのダッシュボード

1. https://streamlit.io/cloud にログイン
2. アプリを選択
3. **Settings** → **General** を確認
4. **About** セクションを編集（可能な場合）

## 対策

### 対策1: リポジトリ名を変更（最も効果的）

GitHubリポジトリ名を推測しにくい名前に変更：

1. **GitHubでリポジトリを開く**: https://github.com/YuZhao20/data-preprocessing-tool
2. **Settings** → **General** → **Repository name**
3. 新しい名前に変更（例: `ml-utils-2024`）
4. **Rename** をクリック

**注意**: リポジトリ名を変更した後、Streamlit Cloudで再デプロイが必要な場合があります。

### 対策2: リポジトリの説明を削除

1. GitHubリポジトリページで **Settings** → **General**
2. **Description** を空にするか、一般的な内容に変更

### 対策3: リポジトリのトピックを削除

1. GitHubリポジトリページで、トピックを削除
2. 検索結果での表示を減らす

### 対策4: アプリ内のCSSで非表示（実装済み）

`app.py`にCSSを追加して、アプリ内のGitHubリンクを非表示にしました。

### 対策5: Streamlit Cloudの設定

現在、Streamlit Cloudの無料版では、アプリページからGitHubリンクを完全に非表示にする直接的なオプションは**ありません**。

## 完全な解決策

### オプション1: リポジトリをPrivateにする（有料版のみ）

- Streamlit Cloudの有料版が必要
- Privateリポジトリを使用可能
- アプリページからGitHubリンクが表示されない

### オプション2: 独自サーバーでデプロイ

- VPSや専用サーバーでStreamlitを実行
- 完全な制御が可能
- GitHubリンクを完全に非表示にできる

### オプション3: リポジトリを分離

- **公開用リポジトリ**: 最小限の情報のみ
- **開発用リポジトリ**: 詳細な情報を含む（Private）

## 推奨される対策

1. ✅ **リポジトリ名を変更**（推測しにくい名前に）
2. ✅ **リポジトリの説明を削除**
3. ✅ **アプリ内のCSSで非表示**（実装済み）
4. ✅ **メニューを非表示**（実装済み）

これらを組み合わせることで、GitHubリポジトリが特定されにくくなります。

## 制限事項

- Streamlit Cloudの無料版では、アプリページにGitHubリポジトリへのリンクが表示される場合があります
- これはStreamlit Cloudの仕様であり、完全に非表示にするには有料版または独自サーバーが必要です
- ただし、リポジトリ名を変更することで、リンクがあっても特定が困難になります

