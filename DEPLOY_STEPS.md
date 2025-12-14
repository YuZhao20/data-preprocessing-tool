# Streamlit Cloudデプロイ手順

## ステップ1: GitHubリポジトリを作成

1. https://github.com/YuZhao20 にアクセス
2. 右上の「+」→「New repository」をクリック
3. リポジトリ情報を入力:
   - **Repository name**: `data-preprocessing-tool`（または任意の名前）
   - **Description**: "データ前処理ツール - 機械学習・統計分析用のWebアプリケーション"
   - **Public** を選択（Streamlit CloudはPublicリポジトリが必要）
   - **Add a README file** はチェックしない（既にREADME.mdがあるため）
4. 「Create repository」をクリック

## ステップ2: ローカルファイルをGitHubにプッシュ

ターミナルで以下のコマンドを実行:

```bash
cd /Users/yuzhao/data_preprocessing_project

# Gitリポジトリを初期化（まだの場合）
git init

# すべてのファイルを追加
git add .

# 初回コミット
git commit -m "Initial commit: データ前処理ツール"

# GitHubリポジトリをリモートとして追加
# YOUR_REPO_NAME を実際のリポジトリ名に置き換えてください
git remote add origin https://github.com/YuZhao20/YOUR_REPO_NAME.git

# メインブランチを設定
git branch -M main

# GitHubにプッシュ
git push -u origin main
```

**注意**: 初回プッシュ時、GitHubの認証情報（Personal Access Token）が必要な場合があります。

## ステップ3: Streamlit Cloudでデプロイ

1. **Streamlit Cloudにアクセス**
   - https://streamlit.io/cloud にアクセス
   - 「Sign in」をクリック
   - 「Continue with GitHub」を選択
   - GitHubアカウントで認証

2. **アプリをデプロイ**
   - 「New app」をクリック
   - 以下の情報を入力:
     - **Repository**: `YuZhao20/YOUR_REPO_NAME` を選択
     - **Branch**: `main` を選択
     - **Main file path**: `app.py`
     - **App URL**: 自動生成されます（例: `data-preprocessing-tool-YuZhao20.streamlit.app`）
   - 「Deploy!」をクリック

3. **デプロイ完了を待つ**
   - 数分でデプロイが完了します
   - 完了すると、アプリのURLが表示されます

## ステップ4: HPからリンク

1. **Streamlit CloudのURLを確認**
   - デプロイ完了後、表示されるURLをコピー
   - 例: `https://data-preprocessing-tool-YuZhao20.streamlit.app`

2. **HTMLファイルを更新**
   - `public_html/tools/data-preprocessing.html` を開く
   - `https://your-app-name.streamlit.app` を実際のURLに置き換え
   - 例: `https://data-preprocessing-tool-YuZhao20.streamlit.app`

3. **FTPでアップロード**
   - FTPクライアントでサーバーに接続
   - `public_html/tools/data-preprocessing.html` をアップロード

4. **メインページからリンク（オプション）**
   - `index.php` や `materials.html` などにリンクを追加:
   ```html
   <a href="tools/data-preprocessing.html">データ前処理ツール</a>
   ```

## ステップ5: 動作確認

1. HPにアクセス: `https://yu-zhao.com/tools/data-preprocessing.html`
2. リンクが正しく動作するか確認
3. Streamlitアプリが正常に表示されるか確認

## トラブルシューティング

### GitHub認証エラー
```bash
# Personal Access Tokenを作成
# GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
# 必要な権限: repo
# トークンを使用してプッシュ:
git remote set-url origin https://YOUR_TOKEN@github.com/YuZhao20/YOUR_REPO_NAME.git
```

### Streamlit Cloudでエラーが発生
- `requirements.txt` が正しく配置されているか確認
- `app.py` のパスが正しいか確認
- Streamlit Cloudのログを確認（デプロイ画面で「Manage app」→「Logs」）

### ファイルがアップロードされない
- `.gitignore` で除外されていないか確認
- 大きなファイル（>100MB）はGitHubにアップロードできません

## 今後の更新方法

コードを更新した場合:

```bash
cd /Users/yuzhao/data_preprocessing_project

# 変更をコミット
git add .
git commit -m "更新内容の説明"

# GitHubにプッシュ
git push origin main
```

Streamlit Cloudは自動的に再デプロイされます（数分かかります）。

