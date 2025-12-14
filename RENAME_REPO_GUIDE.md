# リポジトリ名を変更してGitHubリンクを特定しにくくする方法

## 最も効果的な対策

Streamlit Cloudの無料版では、アプリページにGitHubリポジトリへのリンクが表示されることがあります。
これを完全に非表示にすることはできませんが、**リポジトリ名を変更**することで、リンクがあっても特定が困難になります。

## 手順

### ステップ1: GitHubでリポジトリ名を変更

1. **GitHubにログイン**: https://github.com
2. **リポジトリを開く**: https://github.com/YuZhao20/data-preprocessing-tool
3. **Settings** タブをクリック
4. **General** セクションまでスクロール
5. **Repository name** セクションで:
   - 現在の名前: `data-preprocessing-tool`
   - 新しい名前を入力（推奨例）:
     - `ml-utils-2024`
     - `data-tools-v2`
     - `preprocessing-app-util`
     - `ds-toolkit-2024`
6. **Rename** ボタンをクリック
7. 確認ダイアログで **I understand, rename my repository** をクリック

### ステップ2: ローカルのリモートURLを更新

ターミナルで実行:

```bash
cd /Users/yuzhao/data_preprocessing_project

# 新しいリポジトリ名を設定（実際の名前に置き換えてください）
NEW_REPO_NAME="ml-utils-2024"

# リモートURLを更新
git remote set-url origin https://github.com/YuZhao20/$NEW_REPO_NAME.git

# 確認
git remote -v
```

### ステップ3: Streamlit Cloudで再デプロイ（必要に応じて）

1. **Streamlit Cloudにアクセス**: https://streamlit.io/cloud
2. アプリを選択
3. **Settings** → **General**
4. リポジトリ名が自動的に更新されているか確認
5. 更新されていない場合は、**Delete app** して再デプロイ

または、Streamlit Cloudが自動的に新しいリポジトリ名を検出する場合もあります。

### ステップ4: リポジトリの説明を削除

1. GitHubリポジトリページで **Settings** → **General**
2. **Description** を空にするか、一般的な内容に変更:
   - ❌ "データ前処理ツール - Yu Zhao Lab"
   - ✅ "Machine Learning Utilities" または空欄

### ステップ5: リポジトリのトピックを削除

1. GitHubリポジトリページで、トピックを削除
2. 検索結果での表示を減らす

## 推奨されるリポジトリ名

推測しにくい、一般的な名前を推奨：

- `ml-utils-2024`
- `data-tools-v2`
- `preprocessing-app-util`
- `ds-toolkit-2024`
- `ml-preprocessing-tool`
- `data-processing-utils`

**避けるべき名前:**
- ❌ `data-preprocessing-tool`（現在の名前、推測しやすい）
- ❌ `yu-zhao-data-tool`（個人名が含まれる）
- ❌ `yuzhao-lab-tool`（個人情報が含まれる）

## 注意事項

- リポジトリ名を変更しても、**既存のコミット履歴は保持**されます
- **既存のクローンやフォークは影響を受けます**（新しいURLに更新が必要）
- Streamlit Cloudで再デプロイが必要な場合があります

## 確認方法

1. **GitHubで確認**: 新しいリポジトリ名でアクセスできるか
2. **Streamlit Cloudで確認**: アプリが正常に動作しているか
3. **アプリページで確認**: GitHubリンクが新しいリポジトリ名になっているか

## その他の対策

### README.mdをさらに最小化

必要に応じて、README.mdから詳細な情報を削除：

```bash
# README.mdを最小限の内容に変更
```

### リポジトリの公開設定

- **Public**: 誰でも閲覧可能（Streamlit Cloud無料版に必要）
- **Private**: 閲覧不可（Streamlit Cloud有料版が必要）

## 完全な非公開が必要な場合

Streamlit Cloudの無料版では、アプリページにGitHubリンクが表示される可能性があります。
完全な非公開が必要な場合は：

1. **Streamlit Cloud有料版**を使用（Privateリポジトリ対応）
2. **独自サーバーでデプロイ**（完全な制御が可能）

