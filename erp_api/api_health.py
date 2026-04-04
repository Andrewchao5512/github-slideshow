"""
健康檢查 API
用於確認伺服器運行狀態
"""

from flask import Blueprint, jsonify
from datetime import datetime

api_health = Blueprint('health', __name__)


@api_health.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return jsonify({
        'status': 'ok',
        'message': 'ERP API 服務運行中',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })


@api_health.route('/ping', methods=['GET'])
def ping():
    """簡單的 ping 測試"""
    return jsonify({'message': 'pong'})
