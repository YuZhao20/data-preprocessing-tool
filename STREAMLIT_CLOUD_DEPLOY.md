# Streamlit Cloudでのデプロイ方法

## 概要

Streamlit Cloudは、GitHubリポジトリから直接Streamlitアプリをデプロイできる無料のホスティングサービスです。

## 前提条件

1. **GitHubアカウント**を持っていること
2. **Streamlit Cloudアカウント**を持っていること（GitHubアカウントでサインイン可能）
3. **GitHubリポジトリ**にコードがプッシュされていること

## デプロイ手順

### ステップ1: GitHubリポジトリを準備

1. **GitHubにログイン**: https://github.com
2. **リポジトリを作成**（まだの場合）:
   - リポジトリ名: `data-preprocessing-tool`（または任意の名前）
   - PublicまたはPrivate（Streamlit Cloud無料版ではPublicが必要）

3. **ローカルのコードをプッシュ**:

```bash
cd /Users/yuzhao/data_preprocessing_project

# Gitリポジトリを初期化（まだの場合）
git init

# ファイルを追加
git add .

# コミット
git commit -m "Initial commit: Data preprocessing tool"

# リモートリポジトリを追加（既に追加済みの場合はスキップ）
git remote add origin https://github.com/YuZhao20/data-preprocessing-tool.git

# プッシュ
git push -u origin main
```

**注意**: GitHubの認証にはPersonal Access Token (PAT)が必要な場合があります。詳細は `GITHUB_AUTH_GUIDE.md` を参照してください。

### ステップ2: Streamlit Cloudにサインイン

1. **Streamlit Cloudにアクセス**: https://streamlit.io/cloud
2. **「Sign in」**をクリック
3. **「Continue with GitHub」**を選択
4. GitHubアカウントで認証

### ステップ3: アプリをデプロイ

1. **「New app」**をクリック
2. **設定を入力**:
   - **Repository**: `YuZhao20/data-preprocessing-tool`（実際のリポジトリ名に変更）
   - **Branch**: `main`（または `master`）
   - **Main file path**: `app.py`
   - **App URL**: 自動生成される（例: `data-preprocessing-tool-yuzhao20.streamlit.app`）

3. **「Deploy!」**をクリック

### ステップ4: デプロイの確認

1. **デプロイが完了するまで待つ**（数分かかる場合があります）
2. **アプリのURLにアクセス**して、正常に動作することを確認
3. **エラーがある場合**: Streamlit Cloudのダッシュボードでログを確認

## 自動デプロイ

Streamlit Cloudは、GitHubリポジトリに変更をプッシュすると**自動的に再デプロイ**されます。

```bash
# 変更をプッシュすると自動的に再デプロイされる
git add .
git commit -m "Update: Remove icons"
git push origin main
```

## 設定のカスタマイズ

### `.streamlit/config.toml`の設定

プロジェクトルートに `.streamlit/config.toml` を作成（既に存在する場合は確認）:

```toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### 環境変数の設定（オプション）

Streamlit Cloudのダッシュボードで環境変数を設定できます:

1. **アプリを選択**
2. **「Settings」** → **「Secrets」**
3. **環境変数を追加**（必要に応じて）

## GitHubリンクを非表示にする対策

Streamlit Cloudの無料版では、アプリページにGitHubリポジトリへのリンクが表示される可能性があります。

### 対策1: アプリ内のメニューを非表示（実装済み）

`app.py`で以下の設定をしています:

```python
st.set_page_config(
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)
```

### 対策2: CSSでGitHubリンクを非表示（実装済み）

`app.py`のCSSでGitHubリンクを非表示にしています。

### 対策3: リポジトリ名を変更（推奨）

GitHubリポジトリ名を推測しにくい名前に変更することで、リンクがあっても特定が困難になります。

1. **GitHubでリポジトリを開く**
2. **Settings** → **General** → **Repository name**
3. **新しい名前に変更**（例: `ml-utils-2024`）
4. **Rename**をクリック

詳細は `RENAME_REPO_GUIDE.md` を参照してください。

## トラブルシューティング

### デプロイエラー

**エラー**: `ModuleNotFoundError`

**解決策**: `requirements.txt`に必要なパッケージがすべて含まれているか確認

```bash
# requirements.txtを確認
cat requirements.txt
```

**エラー**: `FileNotFoundError`

**解決策**: ファイルパスが正しいか確認。Streamlit Cloudでは、リポジトリのルートディレクトリが作業ディレクトリになります。

### アプリが表示されない

1. **Streamlit Cloudのダッシュボードでログを確認**
2. **エラーメッセージを確認**
3. **`app.py`の構文エラーがないか確認**

### 日本語が文字化けする

**解決策**: ファイルのエンコーディングがUTF-8であることを確認

```bash
# ファイルのエンコーディングを確認
file -I app.py
```

## 更新方法

コードを更新する場合:

```bash
# 変更をコミット
git add .
git commit -m "Update: Description of changes"

# GitHubにプッシュ（自動的に再デプロイされる）
git push origin main
```

## 削除方法

アプリを削除する場合:

1. **Streamlit Cloudのダッシュボード**にアクセス
2. **アプリを選択**
3. **「Settings」** → **「Delete app」**
4. **確認して削除**

## まとめ

Streamlit Cloudは、GitHubリポジトリから直接デプロイできる**最も簡単な方法**です。

**メリット**:
- ✅ 無料
- ✅ 自動デプロイ
- ✅ 簡単な設定
- ✅ GitHubとの統合

**デメリット**:
- ❌ アプリページにGitHubリンクが表示される可能性（無料版）
- ❌ カスタムドメインの設定が制限される（無料版）

## 次のステップ

1. **GitHubリポジトリを準備**
2. **Streamlit Cloudにサインイン**
3. **アプリをデプロイ**
4. **動作確認**

詳細な手順は上記を参照してください。

