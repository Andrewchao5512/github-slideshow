"""
權限驗證 API
用於檢查使用者是否具有特定權限
"""

from flask import Blueprint, request, jsonify, g
from utils import token_required, get_db
import json

api_auth_permission = Blueprint('auth_permission', __name__)


@api_auth_permission.route('/auth/permission/check', methods=['POST'])
@token_required
def check_permission():
    """
    檢查使用者是否具有指定權限
    
    Request Body:
    {
        "permission": "manage_users"
    }
    
    Response:
    {
        "success": true,
        "has_permission": true,
        "permission": "manage_users"
    }
    """
    data = request.get_json()
    
    if not data or 'permission' not in data:
        return jsonify({
            'success': False,
            'error': '欄位不完整',
            'message': '請提供要檢查的權限名稱'
        }), 400
    
    required_permission = data['permission']
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
        
        user_permissions = json.loads(result['permissions']) if result['permissions'] else []
        
        # 檢查是否有 'all' 權限或指定權限
        has_permission = 'all' in user_permissions or required_permission in user_permissions
        
        return jsonify({
            'success': True,
            'has_permission': has_permission,
            'permission': required_permission,
            'user_permissions': user_permissions
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': '伺服器錯誤',
            'message': str(e)
        }), 500


@api_auth_permission.route('/auth/permissions', methods=['GET'])
@token_required
def list_permissions():
    """
    獲取系統所有可用權限列表
    
    Response:
    {
        "success": true,
        "permissions": [
            {"id": 1, "name": "view_dashboard", "description": "查看儀表板"},
            ...
        ]
    }
    """
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT id, name, description
            FROM permissions
            ORDER BY id
        ''')
        
        permissions = []
        for row in cursor.fetchall():
            permissions.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description']
            })
        
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


@api_auth_permission.route('/auth/my-permissions', methods=['GET'])
@token_required
def get_my_permissions():
    """
    獲取當前使用者的所有權限（含詳細資訊）
    
    Response:
    {
        "success": true,
        "permissions": [
            {"name": "manage_users", "granted": true},
            {"name": "manage_products", "granted": false},
            ...
        ]
    }
    """
    current_user = g.current_user
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # 獲取使用者權限
        cursor.execute('''
            SELECT permissions
            FROM users
            WHERE id = ?
        ''', (current_user['user_id'],))
        
        user_result = cursor.fetchone()
        user_permissions = json.loads(user_result['permissions']) if user_result and user_result['permissions'] else []
        
        # 獲取所有系統權限
        cursor.execute('SELECT name FROM permissions ORDER BY id')
        all_permissions = [row['name'] for row in cursor.fetchall()]
        
        # 組合結果
        permission_list = []
        for perm_name in all_permissions:
            permission_list.append({
                'name': perm_name,
                'granted': perm_name in user_permissions or 'all' in user_permissions
            })
        
        return jsonify({
            'success': True,
            'permissions': permission_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': '伺服器錯誤',
            'message': str(e)
        }), 500
