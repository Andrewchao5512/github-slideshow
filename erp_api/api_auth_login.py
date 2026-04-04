"""
登入 API
處理使用者登入請求，生成 JWT Token
"""

from flask import Blueprint, request, jsonify
from utils import get_db, verify_password, generate_token, hash_password

api_auth_login = Blueprint('auth_login', __name__)


@api_auth_login.route('/auth/login', methods=['POST'])
def login():
    """
    使用者登入端點
    
    Request Body:
    {
        "username": "使用者名稱",
        "password": "密碼"
    }
    
    Response:
    {
        "success": true,
        "token": "JWT Token",
        "user": {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "permissions": ["all"]
        }
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': '無效的請求',
            'message': '請提供 JSON 格式的請求內容'
        }), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({
            'success': False,
            'error': '欄位不完整',
            'message': '請提供使用者名稱和密碼'
        }), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # 查詢使用者
        cursor.execute('''
            SELECT id, username, password_hash, email, role, permissions, is_active
            FROM users
            WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'error': '登入失敗',
                'message': '使用者名稱或密碼錯誤'
            }), 401
        
        # 檢查帳號是否被停用
        if not user['is_active']:
            return jsonify({
                'success': False,
                'error': '帳號已停用',
                'message': '請聯絡管理員'
            }), 403
        
        # 驗證密碼
        if not verify_password(password, user['password_hash']):
            return jsonify({
                'success': False,
                'error': '登入失敗',
                'message': '使用者名稱或密碼錯誤'
            }), 401
        
        # 解析權限 (SQLite 儲存為 JSON 字串)
        import json
        permissions = json.loads(user['permissions']) if user['permissions'] else []
        
        # 生成 Token
        token = generate_token(
            user_id=user['id'],
            username=user['username'],
            role=user['role']
        )
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'permissions': permissions
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': '伺服器錯誤',
            'message': str(e)
        }), 500
