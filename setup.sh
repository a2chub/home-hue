#!/bin/bash

# エラーが発生したら停止
set -e

echo "Hue照明コントロールWebアプリケーションのセットアップを開始します..."

# Pythonがインストールされているか確認
if ! command -v python3 &> /dev/null; then
    echo "Python 3がインストールされていません。インストールしてください。"
    exit 1
fi

# 仮想環境の作成
echo "Python仮想環境を作成しています..."
python3 -m venv venv

# 仮想環境のアクティベート
echo "仮想環境をアクティベートしています..."
source venv/bin/activate

# 依存関係のインストール
echo "依存パッケージをインストールしています..."
pip install --upgrade pip
pip install -r requirements.txt

# 設定ファイルの作成
if [ ! -f .env ]; then
    echo "設定ファイルを作成しています..."
    echo "HUE_BRIDGE_IP=" > .env
    echo "設定ファイル(.env)が作成されました。Hueブリッジのアドレスを設定してください。"
fi

# 実行権限の付与
chmod +x run.sh

echo "セットアップが完了しました！"
echo "Hueブリッジのアドレスを.envファイルに設定してください。"
echo "アプリケーションを起動するには './run.sh' を実行してください。" 