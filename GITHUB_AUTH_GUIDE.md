# GitHub認証ガイド

## 問題: パスワード認証エラー

GitHubは2021年8月以降、パスワード認証を廃止しました。
Personal Access Token (PAT) または SSH認証を使用する必要があります。

## 方法1: Personal Access Token (PAT) を使用（推奨）

### ステップ1: Personal Access Tokenを作成

1. GitHubにログイン: https://github.com
2. 右上のプロフィール画像をクリック → **Settings**
3. 左サイドバーの一番下 → **Developer settings**
4. **Personal access tokens** → **Tokens (classic)**
5. **Generate new token** → **Generate new token (classic)**
6. 以下を設定:
   - **Note**: `Streamlit App Deployment`（任意の名前）
   - **Expiration**: 90 days または No expiration（お好みで）
   - **Select scopes**: `repo` にチェック（すべての権限が選択されます）
7. **Generate token** をクリック
8. **トークンをコピー**（この画面でしか表示されません！）

### ステップ2: リモートURLを更新

ターミナルで実行:

```bash
cd /Users/yuzhao/data_preprocessing_project

# 既存のリモートを削除
git remote remove origin

# Personal Access Tokenを使用してリモートを追加
# YOUR_TOKEN を実際のトークンに置き換えてください
git remote add origin https://YOUR_TOKEN@github.com/YuZhao20/data-preprocessing-tool.git

# プッシュ
git push -u origin main
```

**注意**: トークンは機密情報なので、他人に見せないでください。

### ステップ3: より安全な方法（推奨）

トークンを直接URLに含めない方法:

```bash
# リモートURLを通常の形式に設定
git remote set-url origin https://github.com/YuZhao20/data-preprocessing-tool.git

# プッシュ時にトークンを入力
git push -u origin main
# Username: YuZhao20
# Password: YOUR_PERSONAL_ACCESS_TOKEN（パスワードではなくトークンを入力）
```

## 方法2: SSH認証を使用

### ステップ1: SSH鍵を生成（まだ持っていない場合）

```bash
# SSH鍵を確認
ls -la ~/.ssh

# 鍵がない場合、生成
ssh-keygen -t ed25519 -C "your_email@example.com"
# Enterキーを3回押す（パスフレーズなしの場合）

# 公開鍵を表示
cat ~/.ssh/id_ed25519.pub
```

### ステップ2: GitHubにSSH鍵を登録

1. 上記で表示された公開鍵をコピー
2. GitHub → Settings → SSH and GPG keys
3. **New SSH key** をクリック
4. 鍵を貼り付けて保存

### ステップ3: リモートURLをSSH形式に変更

```bash
cd /Users/yuzhao/data_preprocessing_project

# リモートURLをSSH形式に変更
git remote set-url origin git@github.com:YuZhao20/data-preprocessing-tool.git

# 接続テスト
ssh -T git@github.com
# "Hi YuZhao20! You've successfully authenticated..." と表示されればOK

# プッシュ
git push -u origin main
```

## 方法3: GitHub CLIを使用（最も簡単）

### インストール

```bash
# Homebrewでインストール
brew install gh

# GitHubにログイン
gh auth login
# → GitHub.com を選択
# → HTTPS を選択
# → Login with a web browser を選択
# → ブラウザで認証
```

### 使用

```bash
cd /Users/yuzhao/data_preprocessing_project

# プッシュ（認証は自動）
git push -u origin main
```

## トラブルシューティング

### リモートが既に存在する場合

```bash
# 既存のリモートを確認
git remote -v

# 削除して再追加
git remote remove origin
git remote add origin https://github.com/YuZhao20/data-preprocessing-tool.git
```

### コミットがない場合

```bash
# 変更があるか確認
git status

# 変更をコミット
git add .
git commit -m "Initial commit: データ前処理ツール"
```

### トークンが無効になった場合

1. GitHub → Settings → Developer settings → Personal access tokens
2. 古いトークンを削除
3. 新しいトークンを作成
4. リモートURLを更新

## 推奨: 認証情報を安全に保存

### macOS Keychainを使用

```bash
# 認証情報をKeychainに保存
git config --global credential.helper osxkeychain

# 次回から自動的に認証されます
```

### Git Credential Managerを使用

```bash
# インストール
brew install git-credential-manager

# 設定
git config --global credential.credentialStore osxkeychain
```

