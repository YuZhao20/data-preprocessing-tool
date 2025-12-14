# Xserverでのデプロイ方法（わかりやすい手順）

## 2つの選択肢

### 選択肢1: Xserver VPSを使用（推奨・簡単）
- **Xserver VPS**を契約（月額1,000円〜）
- 専用サーバーなので、Streamlitを直接実行可能
- **最も簡単で確実な方法**

### 選択肢2: Xserver共有ホスティング + 別のVPS
- **Xserver共有ホスティング**（既存のHP用）
- **別のVPS**（ConoHa VPSなど、月額500円〜）でStreamlitを実行
- XserverのHPからVPSのStreamlitにリンク

---

## 方法1: Xserver VPSでデプロイ（推奨）

### ステップ1: Xserver VPSを契約

1. **Xserverの公式サイト**にアクセス: https://www.xserver.ne.jp/
2. **VPSプラン**を選択
3. **プラン選択**:
   - メモリ: **2GB以上**（推奨: 4GB）
   - CPU: **2コア以上**
   - SSD: **50GB以上**
   - OS: **Ubuntu 22.04**を選択
4. **契約を完了**

### ステップ2: VPSの情報を確認

1. **Xserverのコントロールパネル**にログイン
2. **サーバー情報**を確認:
   - **IPアドレス**
   - **SSH接続情報**（ユーザー名、パスワード、ポート番号）

### ステップ3: SSHでVPSに接続

**Mac/Linuxの場合:**
```bash
ssh root@your-vps-ip
# パスワードを入力
```

**Windowsの場合:**
- **PuTTY**または**WSL**を使用

### ステップ4: システムのセットアップ

```bash
# システムを更新
apt update && apt upgrade -y

# 必要なパッケージをインストール
apt install -y python3 python3-pip python3-venv git curl
```

### ステップ5: アプリケーションをアップロード

#### 方法A: Gitからクローン（推奨）

```bash
# アプリケーションディレクトリを作成
mkdir -p /root/streamlit-app
cd /root/streamlit-app

# GitHubからクローン
git clone https://github.com/YuZhao20/data-preprocessing-tool.git .

# または、プライベートリポジトリの場合
# git clone https://YOUR_TOKEN@github.com/YuZhao20/data-preprocessing-tool.git .
```

#### 方法B: SCPでファイルをアップロード（ローカルから）

**Mac/Linuxの場合:**
```bash
# ローカルで実行
cd /Users/yuzhao/data_preprocessing_project
scp -r * root@your-vps-ip:/root/streamlit-app/
```

**Windowsの場合:**
- **WinSCP**などのFTPクライアントを使用

### ステップ6: 仮想環境を作成して依存パッケージをインストール

```bash
cd /root/streamlit-app

# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# pipをアップグレード
pip install --upgrade pip

# 依存パッケージをインストール
pip install -r requirements.txt
```

### ステップ7: Streamlitを起動（テスト）

```bash
# 仮想環境が有効化されていることを確認
source venv/bin/activate

# Streamlitを起動（テスト用）
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

**確認**: ブラウザで `http://your-vps-ip:8501` にアクセスして、アプリが表示されるか確認

**Ctrl+C**で停止

### ステップ8: systemdサービスとして設定（自動起動）

```bash
# サービスファイルを作成
nano /etc/systemd/system/streamlit-app.service
```

以下の内容を記述:

```ini
[Unit]
Description=Streamlit Data Preprocessing App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/streamlit-app
Environment="PATH=/root/streamlit-app/venv/bin"
ExecStart=/root/streamlit-app/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

サービスを有効化・起動:

```bash
# systemdをリロード
systemctl daemon-reload

# サービスを有効化（自動起動）
systemctl enable streamlit-app

# サービスを起動
systemctl start streamlit-app

# ステータスを確認
systemctl status streamlit-app
```

### ステップ9: Nginxでリバースプロキシ設定

```bash
# Nginxをインストール
apt install nginx -y

# 設定ファイルを作成
nano /etc/nginx/sites-available/streamlit-app
```

以下の内容を記述（`tools.yu-zhao.com`は実際のドメインに変更）:

```nginx
server {
    listen 80;
    server_name tools.yu-zhao.com;  # 実際のドメインに変更

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_buffering off;
    }
}
```

```bash
# シンボリックリンクを作成
ln -s /etc/nginx/sites-available/streamlit-app /etc/nginx/sites-enabled/

# デフォルトの設定を無効化（必要に応じて）
# rm /etc/nginx/sites-enabled/default

# 設定をテスト
nginx -t

# Nginxを再起動
systemctl reload nginx
```

### ステップ10: SSL証明書を設定（HTTPS化）

```bash
# Certbotをインストール
apt install certbot python3-certbot-nginx -y

# SSL証明書を取得
certbot --nginx -d tools.yu-zhao.com

# 自動更新を設定
certbot renew --dry-run
```

### ステップ11: ファイアウォール設定

```bash
# UFWをインストール（まだの場合）
apt install ufw -y

# 必要なポートを開放
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS

# ファイアウォールを有効化
ufw enable

# ステータスを確認
ufw status
```

### ステップ12: ドメインのDNS設定

1. **Xserverのコントロールパネル**にログイン
2. **ドメイン設定** → **DNSレコード設定**
3. **Aレコードを追加**:
   - ホスト名: `tools`（サブドメインの場合）
   - タイプ: `A`
   - 値: VPSのIPアドレス
   - TTL: `3600`
4. **設定を保存**

**注意**: DNSの反映には数時間かかる場合があります。

### 完了！

ブラウザで `https://tools.yu-zhao.com` にアクセスして、アプリが表示されることを確認してください。

---

## 方法2: Xserver共有ホスティング + 別のVPS（既存のHPがある場合）

既にXserverの共有ホスティングでHPを運営している場合、別のVPSでStreamlitを実行し、XserverのHPからリンクする方法です。

### ステップ1: 別のVPSを契約

1. **ConoHa VPS**（月額500円〜）または**DigitalOcean**（月額$5〜）を契約
2. **Ubuntu 22.04**を選択

### ステップ2〜10: 上記の「方法1」のステップ2〜10と同じ

VPSでStreamlitをデプロイします（上記の手順を参照）。

### ステップ11: Xserverでサブドメイン設定

1. **Xserverのコントロールパネル**にログイン
2. **ドメイン設定** → **サブドメイン設定**
3. **新しいサブドメインを追加**:
   - サブドメイン: `tools`
   - ドメイン: `yu-zhao.com`
   - **外部サーバーを指定**: VPSのIPアドレスを入力
4. **設定を保存**

### ステップ12: XserverのHPからリンク

1. **Xserverのファイルマネージャー**で `public_html/tools/` ディレクトリを作成
2. `data-preprocessing.html` を作成:

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=https://tools.yu-zhao.com">
    <title>データ前処理ツール</title>
</head>
<body>
    <p>リダイレクト中... <a href="https://tools.yu-zhao.com">こちらをクリック</a></p>
    <script>
        window.location.href = "https://tools.yu-zhao.com";
    </script>
</body>
</html>
```

これで、`https://yu-zhao.com/tools/data-preprocessing.html` からStreamlitアプリにアクセスできます。

---

## トラブルシューティング

### Streamlitが起動しない

```bash
# ログを確認
journalctl -u streamlit-app -f

# サービスを再起動
systemctl restart streamlit-app

# ポートが使用中か確認
netstat -tlnp | grep 8501
```

### Nginxエラー

```bash
# 設定をテスト
nginx -t

# エラーログを確認
tail -f /var/log/nginx/error.log
```

### DNS設定が反映されない

- DNSの反映には数時間かかる場合があります
- `dig tools.yu-zhao.com` でDNS設定を確認

### メモリ不足

```bash
# メモリ使用量を確認
free -h

# スワップファイルを追加（必要に応じて）
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

---

## よくある質問

### Q: Xserverの共有ホスティングで直接Streamlitを実行できますか？

A: **難しいです**。Xserverの共有ホスティングでは、バックグラウンドプロセスの実行が制限されるため、Streamlitのような常時起動アプリの実行は困難です。**Xserver VPS**または**別のVPS**を使用することを推奨します。

### Q: コストはどのくらいかかりますか？

A:
- **Xserver VPS**: 月額1,000円〜
- **別のVPS（ConoHa VPSなど）**: 月額500円〜
- **Xserver共有ホスティング**: 既に契約している場合は追加コストなし

### Q: ドメインは必要ですか？

A: **必須ではありません**が、IPアドレスでアクセスすることも可能です。ただし、SSL証明書の取得やユーザー体験の向上のため、**ドメインの使用を推奨**します。

---

## まとめ

**最も簡単な方法**: Xserver VPSを契約して、上記の手順に従ってデプロイする

**既にXserverの共有ホスティングを使用している場合**: 別のVPS（ConoHa VPSなど）でStreamlitを実行し、XserverのHPからリンクする

