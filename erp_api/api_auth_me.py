"""
個人資訊 API
獲取當前登入使用者的資訊
"""

from flask import Blueprint, jsonify, g
from utils import token_required, get_db
import json

api_auth_me = Blueprint('auth_me', __name__)


@api_auth_me.route('/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """
    獲取當前登入使用者資訊
    
    Response:
    {
        "success": true,
        "user": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
            "permissions": ["all"],
            "is_active": true,
            "created_at": "2024-01-01T00:00:00"
        }
    }
    """
    current_user = g.current_user
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # 從資料庫獲取完整使用者資訊
        cursor.execute('''
            SELECT id, username, email, role, permissions, is_active, created_at, updated_at
            FROM users
            WHERE id = ?
        ''', (current_user['user_id'],))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'error': '使用者不存在',
                'message': '請重新登入'
            }), 404
        
        # 解析權限
        permissions = json.loads(user['permissions']) if user['permissions'] else []
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'permissions': permissions,
                'is_active': bool(user['is_active']),
                'created_at': user['created_at'],
                'updated_at': user['updated_at']
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': '伺服器錯誤',
            'message': str(e)
        }), 500


@api_auth_me.route('/auth/me/permissions', methods=['GET'])
@token_required
def get_user_permissions():
    """
    獲取當前使用者的權限列表
    
    Response:
    {
        "success": true,
        "permissions": ["all", "manage_users", ...]
    }
    """
    current_user = g.current_user
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT permissions
            FROM users
            WHERE id = ?
        ''', (current_user['user_id'],))
        
        result = cursor.fetchone()
        
        if not result:
            return jsonify({
                'success': False,
                'error': '使用者不存在'
            }), 404
        
        permissions = json.loads(result['permissions']) if result['permissions'] else []
        
        return jsonify({
            'success': True,
            'permissions': permissions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': '伺服器錯誤',
            'message': str(e)
        }), 500
