"""
登出 API
處理使用者登出請求 (JWT 為無狀態，主要用於前端清除 Token)
"""

from flask import Blueprint, request, jsonify
from utils import token_required

api_auth_logout = Blueprint('auth_logout', __name__)


@api_auth_logout.route('/auth/logout', methods=['POST'])
@token_required
def logout():
    """
    使用者登出端點
    
    注意：由於 JWT 是無狀態的，此端點主要用於：
    1. 前端清除儲存的 Token
    2. 記錄登出日誌 (可選)
    
    Response:
    {
        "success": true,
        "message": "已成功登出"
    }
    """
    # 在無狀態 JWT 架構下，登出主要由前端處理
    # 如需實現黑名單機制，可將 token 加入 Redis 或資料庫黑名單
    
    return jsonify({
        'success': True,
        'message': '已成功登出',
        'note': '請前端清除儲存的 Token'
    })


@api_auth_logout.route('/auth/logout-all', methods=['POST'])
@token_required
def logout_all():
    """
    從所有裝置登出
    
    這需要實現 Token 黑名單機制，目前僅返回提示
    """
    return jsonify({
        'success': True,
        'message': '此功能需要實現 Token 黑名單機制',
        'note': '建議使用 Redis 或資料庫儲存已撤銷的 Token'
    })
