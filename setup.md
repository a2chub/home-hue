# Hue照明コントロールWebアプリケーション セットアップ手順

このドキュメントでは、Hue照明コントロールWebアプリケーションのセットアップ方法について詳しく説明します。

## 前提条件

- Ubuntu 24.10 (Proxmox VM内)
- Python 3.10以上
- インターネット接続
- Philips Hueブリッジがローカルネットワークに接続されていること

## 手動セットアップ手順

### 1. リポジトリのクローン/ファイルの配置

```bash
# 適当なディレクトリにファイルを配置してください
mkdir -p ~/hue_controller
cd ~/hue_controller
# 必要なファイルをコピーまたはダウンロードしてください
```

### 2. Python仮想環境のセットアップ

```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境のアクティベート
source venv/bin/activate

# 依存パッケージのインストール
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Hueブリッジの設定

1. Hueブリッジのローカルネットワークアドレスを確認します。
   - Hueアプリの設定から確認できます
   - または、[Hue Bridge Discovery](https://discovery.meethue.com/)を使用して確認できます

2. `.env`ファイルを作成し、ブリッジのIPアドレスを設定します：

```bash
echo "HUE_BRIDGE_IP=192.168.x.x" > .env  # 実際のIPアドレスに置き換えてください
```

### 4. アプリケーションの実行

```bash
# 実行権限を付与
chmod +x run.sh

# アプリケーションの起動
./run.sh
```

ブラウザで `http://localhost:5000` にアクセスしてアプリケーションを使用できます。

## 自動セットアップ手順

より簡単にセットアップするには、以下のコマンドを実行してください：

```bash
# 実行権限を付与
chmod +x setup.sh

# セットアップスクリプトの実行
./setup.sh
```

セットアップスクリプトは以下の処理を自動的に行います：
- Python仮想環境の作成
- 依存パッケージのインストール
- 設定ファイルのテンプレート作成

セットアップ後、`.env`ファイルを編集してHueブリッジのIPアドレスを設定してください。

## トラブルシューティング

### Hueブリッジに接続できない場合

1. ブリッジのIPアドレスが正しいか確認してください
2. 初回接続時は、ブリッジの物理ボタンを押す必要があります
3. アプリケーションを再起動してください

### 依存パッケージのインストールに失敗する場合

```bash
# 仮想環境が有効になっていることを確認
source venv/bin/activate

# pipを最新バージョンに更新
pip install --upgrade pip

# 依存パッケージを個別にインストール
pip install Flask==2.3.3
pip install phue==1.1
# 他の依存パッケージも同様に
``` 