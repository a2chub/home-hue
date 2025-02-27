#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from phue import Bridge  # Philips Hue APIライブラリ
from dotenv import load_dotenv  # 環境変数読み込みライブラリ
import logging
import requests
import socket
import time

# ロギングの設定 - アプリケーションの動作ログを記録するための設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  # このモジュール用のロガーを取得

# .envファイルから環境変数を読み込み
load_dotenv()

# Flaskアプリケーションの初期化
app = Flask(__name__)

# Hueブリッジの設定
bridge_ip = os.getenv('HUE_BRIDGE_IP')  # 環境変数からブリッジのIPアドレスを取得
bridge = None  # ブリッジオブジェクトの初期化

def discover_bridge():
    """
    Hueブリッジを自動検出する関数
    
    Returns:
        str or None: 検出されたブリッジのIPアドレス、検出できなかった場合はNone
    """
    try:
        # Philips Hueの公式ディスカバリーAPIを使用してブリッジを検出
        response = requests.get('https://discovery.meethue.com/')
        bridges = response.json()
        if bridges:
            # 最初に見つかったブリッジのIPアドレスを返す
            return bridges[0]['internalipaddress']
    except Exception as e:
        # エラーが発生した場合はログに記録
        logger.error(f"ブリッジ検出エラー: {e}")
    return None

def connect_to_bridge():
    """
    Hueブリッジに接続する関数
    
    Returns:
        bool: 接続成功の場合はTrue、失敗の場合はFalse
    """
    global bridge, bridge_ip  # グローバル変数を使用
    
    # 環境変数からIPアドレスが設定されている場合
    if bridge_ip:
        try:
            # ブリッジオブジェクトを作成して接続
            bridge = Bridge(bridge_ip)
            # 初回接続時はブリッジの物理ボタンを押す必要がある
            bridge.connect()
            logger.info(f"ブリッジ {bridge_ip} に接続しました")
            return True
        except Exception as e:
            # 接続エラーをログに記録
            logger.error(f"ブリッジ接続エラー: {e}")
    
    # IPアドレスが設定されていないか、接続に失敗した場合は自動検出を試みる
    discovered_ip = discover_bridge()
    if discovered_ip:
        try:
            # 検出したIPアドレスでブリッジに接続
            bridge_ip = discovered_ip
            bridge = Bridge(bridge_ip)
            # 初回接続時はブリッジの物理ボタンを押す必要がある
            bridge.connect()
            logger.info(f"ブリッジ {bridge_ip} に接続しました")
            # 検出したIPアドレスを.envファイルに保存して次回以降の接続を簡略化
            with open('.env', 'w') as f:
                f.write(f"HUE_BRIDGE_IP={bridge_ip}\n")
            return True
        except Exception as e:
            # 接続エラーをログに記録
            logger.error(f"ブリッジ接続エラー: {e}")
    
    return False

@app.route('/')
def index():
    """
    メインページを表示するルート
    
    Returns:
        HTML: メインページのレンダリング結果
    """
    global bridge
    
    # ブリッジに接続されていない場合は接続を試みる
    if bridge is None:
        if not connect_to_bridge():
            # 接続失敗時はセットアップページを表示
            return render_template('setup.html', error="Hueブリッジに接続できませんでした。")
    
    try:
        # 照明の情報を取得
        lights = bridge.get_light_objects('id')  # 照明オブジェクトをID順に取得
        light_data = []  # 照明データを格納するリスト
        
        # 各照明の詳細情報を取得してリストに追加
        for light_id, light in lights.items():
            light_info = bridge.get_light(light_id)  # 照明の詳細情報を取得
            light_data.append({
                'id': light_id,  # 照明のID
                'name': light_info['name'],  # 照明の名前
                'on': light_info['state']['on'],  # オン/オフ状態
                'brightness': light_info['state'].get('bri', 0),  # 明るさ（0-254）
                'reachable': light_info['state']['reachable'],  # 接続状態
                'type': light_info['type'],  # 照明のタイプ
                'has_color': 'hue' in light_info['state'] and 'sat' in light_info['state']  # カラー対応かどうか
            })
        
        # ルーム（グループ）情報を取得
        rooms = {}
        try:
            groups = bridge.get_group()  # すべてのグループを取得
            for group_id, group_info in groups.items():
                # タイプが'Room'のグループのみを取得（ゾーンやその他のグループは除外）
                if group_info.get('type') == 'Room':
                    rooms[group_id] = group_info
        except Exception as e:
            # ルーム情報取得エラーをログに記録（致命的ではないので警告レベル）
            logger.warning(f"ルーム情報取得エラー: {e}")
        
        # テンプレートをレンダリングして返す
        return render_template('index.html', lights=light_data, rooms=rooms, bridge_ip=bridge_ip)
    except Exception as e:
        # 照明情報取得エラーをログに記録
        logger.error(f"照明情報取得エラー: {e}")
        return render_template('setup.html', error=f"エラーが発生しました: {e}")

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """
    セットアップページを表示・処理するルート
    
    Returns:
        HTML: セットアップページのレンダリング結果またはリダイレクト
    """
    global bridge, bridge_ip
    
    # POSTリクエスト（フォーム送信）の場合
    if request.method == 'POST':
        new_bridge_ip = request.form.get('bridge_ip')  # フォームからIPアドレスを取得
        if new_bridge_ip:
            bridge_ip = new_bridge_ip  # 新しいIPアドレスを設定
            # 新しいIPアドレスを.envファイルに保存
            with open('.env', 'w') as f:
                f.write(f"HUE_BRIDGE_IP={bridge_ip}\n")
            
            # 新しいIPアドレスでブリッジに接続を試みる
            if connect_to_bridge():
                # 接続成功時はメインページにリダイレクト
                return redirect(url_for('index'))
    
    # 自動検出を試みる（GETリクエストまたはPOSTで接続失敗時）
    discovered_ip = discover_bridge()
    
    # セットアップページを表示
    return render_template('setup.html', discovered_ip=discovered_ip, current_ip=bridge_ip)

@app.route('/api/lights', methods=['GET'])
def get_lights():
    """
    照明の情報をJSON形式で返すAPI
    
    Returns:
        JSON: 照明情報のJSONデータ
    """
    global bridge
    
    # ブリッジに接続されていない場合は接続を試みる
    if bridge is None:
        if not connect_to_bridge():
            # 接続失敗時はエラーを返す
            return jsonify({'error': 'ブリッジに接続できません'}), 500
    
    try:
        # 照明の情報を取得
        lights = bridge.get_light_objects('id')
        light_data = {}  # 照明データを格納する辞書
        
        # 各照明の詳細情報を取得して辞書に追加
        for light_id, light in lights.items():
            light_info = bridge.get_light(light_id)
            light_data[light_id] = {
                'name': light_info['name'],  # 照明の名前
                'on': light_info['state']['on'],  # オン/オフ状態
                'brightness': light_info['state'].get('bri', 0),  # 明るさ（0-254）
                'reachable': light_info['state']['reachable'],  # 接続状態
                'type': light_info['type'],  # 照明のタイプ
                'has_color': 'hue' in light_info['state'] and 'sat' in light_info['state']  # カラー対応かどうか
            }
        
        # JSON形式で照明情報を返す
        return jsonify(light_data)
    except Exception as e:
        # エラーをログに記録してJSONでエラーメッセージを返す
        logger.error(f"API照明情報取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/lights/<int:light_id>', methods=['PUT'])
def update_light(light_id):
    """
    照明の状態を更新するAPI
    
    Args:
        light_id (int): 更新する照明のID
        
    Returns:
        JSON: 更新結果のJSONデータ
    """
    global bridge
    
    # ブリッジに接続されていない場合は接続を試みる
    if bridge is None:
        if not connect_to_bridge():
            # 接続失敗時はエラーを返す
            return jsonify({'error': 'ブリッジに接続できません'}), 500
    
    try:
        # リクエストボディからJSONデータを取得
        data = request.json
        command = {}  # Hueブリッジに送信するコマンド
        
        # オン/オフ状態
        if 'on' in data:
            command['on'] = data['on']
        
        # 明るさ（1-254の範囲に制限）
        if 'brightness' in data:
            command['bri'] = max(1, min(254, int(data['brightness'])))
        
        # 色相（0-65535の範囲に制限）
        if 'hue' in data:
            command['hue'] = max(0, min(65535, int(data['hue'])))
        
        # 彩度（0-254の範囲に制限）
        if 'saturation' in data:
            command['sat'] = max(0, min(254, int(data['saturation'])))
        
        # 色温度（153-500の範囲に制限）
        if 'color_temp' in data:
            command['ct'] = max(153, min(500, int(data['color_temp'])))
        
        # コマンドをブリッジに送信
        bridge.set_light(light_id, command)
        
        # 成功結果を返す
        return jsonify({'success': True, 'light_id': light_id, 'command': command})
    except Exception as e:
        # エラーをログに記録してJSONでエラーメッセージを返す
        logger.error(f"照明更新エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups', methods=['GET'])
def get_groups():
    """
    グループ（ルーム）の情報をJSON形式で返すAPI
    
    Returns:
        JSON: グループ情報のJSONデータ
    """
    global bridge
    
    # ブリッジに接続されていない場合は接続を試みる
    if bridge is None:
        if not connect_to_bridge():
            # 接続失敗時はエラーを返す
            return jsonify({'error': 'ブリッジに接続できません'}), 500
    
    try:
        # グループ情報を取得してJSON形式で返す
        groups = bridge.get_group()
        return jsonify(groups)
    except Exception as e:
        # エラーをログに記録してJSONでエラーメッセージを返す
        logger.error(f"グループ情報取得エラー: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<int:group_id>', methods=['PUT'])
def update_group(group_id):
    """
    グループ（ルーム）の状態を更新するAPI
    
    Args:
        group_id (int): 更新するグループのID
        
    Returns:
        JSON: 更新結果のJSONデータ
    """
    global bridge
    
    # ブリッジに接続されていない場合は接続を試みる
    if bridge is None:
        if not connect_to_bridge():
            # 接続失敗時はエラーを返す
            return jsonify({'error': 'ブリッジに接続できません'}), 500
    
    try:
        # リクエストボディからJSONデータを取得
        data = request.json
        command = {}  # Hueブリッジに送信するコマンド
        
        # オン/オフ状態
        if 'on' in data:
            command['on'] = data['on']
        
        # 明るさ（1-254の範囲に制限）
        if 'brightness' in data:
            command['bri'] = max(1, min(254, int(data['brightness'])))
        
        # 色相（0-65535の範囲に制限）
        if 'hue' in data:
            command['hue'] = max(0, min(65535, int(data['hue'])))
        
        # 彩度（0-254の範囲に制限）
        if 'saturation' in data:
            command['sat'] = max(0, min(254, int(data['saturation'])))
        
        # 色温度（153-500の範囲に制限）
        if 'color_temp' in data:
            command['ct'] = max(153, min(500, int(data['color_temp'])))
        
        # コマンドをブリッジに送信
        bridge.set_group(group_id, command)
        
        # 成功結果を返す
        return jsonify({'success': True, 'group_id': group_id, 'command': command})
    except Exception as e:
        # エラーをログに記録してJSONでエラーメッセージを返す
        logger.error(f"グループ更新エラー: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # アプリケーション起動時にブリッジへの接続を試みる
    connect_to_bridge()
    
    # 開発サーバーの起動（本番環境ではWSGIサーバーを使用することを推奨）
    app.run(host='0.0.0.0', port=5000, debug=True) 