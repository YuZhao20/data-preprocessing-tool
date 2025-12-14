# クイックスタート: GitHubにプッシュ

## 現在の状態

✅ Gitリポジトリは初期化済み  
✅ コミット済み（"Initial commit: データ前処理ツール"）  
✅ リモートリポジトリは設定済み  
❌ 認証が必要（Personal Access Token）

## 解決方法: Personal Access Tokenを作成

### ステップ1: GitHubでトークンを作成

1. **GitHubにログイン**: https://github.com
2. **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
3. **Generate new token** → **Generate new token (classic)**
4. 設定:
   - **Note**: `Streamlit Deployment`（任意）
   - **Expiration**: お好みで（90 days推奨）
   - **Select scopes**: `repo` にチェック
5. **Generate token** をクリック
6. **トークンをコピー**（この画面でしか表示されません！）

### ステップ2: プッシュ

#### 方法A: スクリプトを使用（簡単）

```bash
cd /Users/yuzhao/data_preprocessing_project
./PUSH_TO_GITHUB.sh
# トークンを入力
```

#### 方法B: 手動で実行

```bash
cd /Users/yuzhao/data_preprocessing_project

# トークンを環境変数に設定（セキュリティのため）
# YOUR_TOKEN を実際のトークンに置き換え
export GITHUB_TOKEN="YOUR_TOKEN"

# リモートURLを更新
git remote set-url origin https://${GITHUB_TOKEN}@github.com/YuZhao20/data-preprocessing-tool.git

# プッシュ
git push -u origin main
```

#### 方法C: 対話的に入力（推奨・安全）

```bash
cd /Users/yuzhao/data_preprocessing_project

# リモートURLを通常の形式に設定
git remote set-url origin https://github.com/YuZhao20/data-preprocessing-tool.git

# プッシュ（認証情報を対話的に入力）
git push -u origin main
# Username: YuZhao20
# Password: YOUR_PERSONAL_ACCESS_TOKEN（パスワードではなくトークンを入力！）
```

**重要**: Password欄には**パスワードではなく、Personal Access Token**を入力してください。

### ステップ3: 認証情報を保存（次回から自動）

```bash
# macOS Keychainに保存
git config --global credential.helper osxkeychain

# 次回から自動的に認証されます
```

## プッシュ成功後

1. **GitHubで確認**: https://github.com/YuZhao20/data-preprocessing-tool
2. **Streamlit Cloudでデプロイ**: https://streamlit.io/cloud
3. **HPからリンク**: `public_html/tools/data-preprocessing.html` を更新

## トラブルシューティング

### トークンが無効
- トークンの有効期限を確認
- 新しいトークンを作成

### 権限エラー
- トークンに `repo` スコープが含まれているか確認

### リモートエラー
```bash
# リモートを確認
git remote -v

# 再設定
git remote remove origin
git remote add origin https://github.com/YuZhao20/data-preprocessing-tool.git
```

