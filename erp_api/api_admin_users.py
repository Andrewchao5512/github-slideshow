"""
使用者管理 API (Admin)
提供使用者的 CRUD 操作，僅限管理員存取
"""

from flask import Blueprint, request, jsonify, g
from utils import token_required, get_db, hash_password, log_action
import json

api_admin_users = Blueprint('admin_users', __name__)


def is_admin():
    """檢查當前使用者是否為管理員"""
    if not hasattr(g, 'current_user'):
        return False
    
    current_user = g.current_user
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT role, permissions
            FROM users
            WHERE id = ?
        ''', (current_user['user_id'],))
        
        result = cursor.fetchone()
        
        if not result:
            return False
        
        # 檢查是否為 admin 角色或有 all 權限
        if result['role'] == 'admin':
            return True
        
        permissions = json.loads(result['permissions']) if result['permissions'] else []
        return 'all' in permissions or 'manage_users' in permissions
        
    except Exception:
        return False


def admin_required(f):
    """管理員權限裝飾器"""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return jsonify({
                'success': False,
                'error': '權限不足',
                'message': '此功能僅限管理員使用'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated


@api_admin_users.route('/admin/users', methods=['GET'])
@token_required
@admin_required
def list_users():
    """
    獲取所有使用者列表
    
    Query Parameters:
    - page: 頁碼 (預設 1)
    - limit: 每頁數量 (預設 20)
    - search: 搜尋關鍵字 (可選)
    
    Response:
    {
        "success": true,
        "users": [...],
        "total": 100,
        "page": 1,
        "limit": 20
    }
    """
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    search = request.args.get('search', '')
    
    offset = (page - 1) * limit
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # 計算總數
        if search:
            cursor.execute('''
                SELECT COUNT(*) as total
                FROM users
                WHERE username LIKE ? OR email LIKE ?
            ''', (f'%{search}%', f'%{search}%'))
        else:
            cursor.execute('SELECT COUNT(*) as total FROM users')
        
        total = cursor.fetchone()['total']
        
        # 查詢使用者
        if search:
            cursor.execute('''
                SELECT id, username, email, role, permissions, is_active, created_at, updated_at
                FROM users
                WHERE username LIKE ? OR email LIKE ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            ''', (f'%{search}%', f'%{search}%', limit, offset))
        else:
            cursor.execute('''
                SELECT id, username, email, role, permissions, is_active, created_at, updated_at
                FROM users
                ORDER BY id DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row['id'],
                'username': row['username'],
                'email': row['email'],
                'role': row['role'],
                'permissions': json.loads(row['permissions']) if row['permissions'] else [],
                'is_active': bool(row['is_active']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return jsonify({
            'success': True,
            'users': users,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': '伺服器錯誤',
            'message': str(e)
        }), 500


@api_admin_users.route('/admin/users/<int:user_id>', methods=['GET'])
@token_required
@admin_required
def get_user(user_id):
    """
    獲取單一使用者詳細資訊
    
    Response:
    {
        "success": true,
        "user": {...}
    }
    """
    try:
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            SELECT id, username, email, role, permissions, is_active, created_at, updated_at
            FROM users
            WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'error': '使用者不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'permissions': json.loads(user['permissions']) if user['permissions'] else [],
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


@api_admin_users.route('/admin/users', methods=['POST'])
@token_required
@admin_required
def create_user():
    """
    建立新使用者
    
    Request Body:
    {
        "username": "newuser",
        "password": "Password@123",
        "email": "user@example.com",
        "role": "user",
        "permissions": ["view_dashboard"]
    }
    
    Response:
    {
        "success": true,
        "user": {...},
        "message": "使用者建立成功"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': '無效的請求',
            'message': '請提供 JSON 格式的請求內容'
        }), 400
    
    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'error': '欄位不完整',
                'message': f'缺少必要欄位：{field}'
            }), 400
    
    username = data['username']
    password = data['password']
    email = data.get('email', '')
    role = data.get('role', 'user')
    permissions = data.get('permissions', [])
    
    # 密碼強度檢查
    if len(password) < 8:
        return jsonify({
            'success': False,
            'error': '密碼強度不足',
            'message': '密碼長度至少需要 8 個字元'
        }), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # 檢查使用者名稱是否已存在
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'error': '使用者名稱已存在',
                'message': '請使用其他使用者名稱'
            }), 409
        
        # 建立使用者
        password_hash = hash_password(password)
        permissions_json = json.dumps(permissions)
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, role, permissions)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password_hash, email, role, permissions_json))
        
        db.commit()
        
        # 獲取新建立的使用者 ID
        user_id = cursor.lastrowid
        
        # 記錄日誌
        log_action(g.current_user['user_id'], 'create_user', 'users', f'Created user: {username}')
        
        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'role': role,
                'permissions': permissions
            },
            'message': '使用者建立成功'
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': '伺服器錯誤',
            'message': str(e)
        }), 500


@api_admin_users.route('/admin/users/<int:user_id>', methods=['PUT'])
@token_required
@admin_required
def update_user(user_id):
    """
    更新使用者資訊
    
    Request Body:
    {
        "email": "newemail@example.com",
        "role": "admin",
        "permissions": ["view_dashboard", "manage_users"],
        "is_active": true
    }
    
    Response:
    {
        "success": true,
        "user": {...},
        "message": "使用者更新成功"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': '無效的請求'
        }), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # 檢查使用者是否存在
        cursor.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'error': '使用者不存在'
            }), 404
        
        # 建構更新欄位
        update_fields = []
        update_values = []
        
        if 'email' in data:
            update_fields.append('email = ?')
            update_values.append(data['email'])
        
        if 'role' in data:
            update_fields.append('role = ?')
            update_values.append(data['role'])
        
        if 'permissions' in data:
            update_fields.append('permissions = ?')
            update_values.append(json.dumps(data['permissions']))
        
        if 'is_active' in data:
            update_fields.append('is_active = ?')
            update_values.append(1 if data['is_active'] else 0)
        
        # 密碼更新（可選）
        if 'password' in data and data['password']:
            update_fields.append('password_hash = ?')
            update_values.append(hash_password(data['password']))
        
        if not update_fields:
            return jsonify({
                'success': False,
                'error': '無效的請求',
                'message': '沒有提供任何要更新的欄位'
            }), 400
        
        update_fields.append('updated_at = CURRENT_TIMESTAMP')
        update_values.append(user_id)
        
        cursor.execute(f'''
            UPDATE users
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', update_values)
        
        db.commit()
        
        # 記錄日誌
        log_action(g.current_user['user_id'], 'update_user', 'users', f'Updated user: {user["username"]}')
        
        # 獲取更新後的使用者資訊
        cursor.execute('''
            SELECT id, username, email, role, permissions, is_active, created_at, updated_at
            FROM users
            WHERE id = ?
        ''', (user_id,))
        
        updated_user = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'user': {
                'id': updated_user['id'],
                'username': updated_user['username'],
                'email': updated_user['email'],
                'role': updated_user['role'],
                'permissions': json.loads(updated_user['permissions']) if updated_user['permissions'] else [],
                'is_active': bool(updated_user['is_active']),
                'created_at': updated_user['created_at'],
                'updated_at': updated_user['updated_at']
            },
            'message': '使用者更新成功'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': '伺服器錯誤',
            'message': str(e)
        }), 500


@api_admin_users.route('/admin/users/<int:user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(user_id):
    """
    刪除使用者
    
    Response:
    {
        "success": true,
        "message": "使用者已刪除"
    }
    """
    try:
        db = get_db()
        cursor = db.cursor()
        
        # 檢查使用者是否存在
        cursor.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'error': '使用者不存在'
            }), 404
        
        # 不允許刪除自己的帳號
        if user_id == g.current_user['user_id']:
            return jsonify({
                'success': False,
                'error': '無法刪除自己的帳號',
                'message': '請使用其他管理員帳號執行此操作'
            }), 400
        
        # 刪除使用者
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        db.commit()
        
        # 記錄日誌
        log_action(g.current_user['user_id'], 'delete_user', 'users', f'Deleted user: {user["username"]}')
        
        return jsonify({
            'success': True,
            'message': '使用者已刪除'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': '伺服器錯誤',
            'message': str(e)
        }), 500


@api_admin_users.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@token_required
@admin_required
def reset_password(user_id):
    """
    重設使用者密碼
    
    Request Body:
    {
        "new_password": "NewPassword@123"
    }
    
    Response:
    {
        "success": true,
        "message": "密碼已重設"
    }
    """
    data = request.get_json()
    
    if not data or 'new_password' not in data:
        return jsonify({
            'success': False,
            'error': '欄位不完整',
            'message': '請提供新密碼'
        }), 400
    
    new_password = data['new_password']
    
    # 密碼強度檢查
    if len(new_password) < 8:
        return jsonify({
            'success': False,
            'error': '密碼強度不足',
            'message': '密碼長度至少需要 8 個字元'
        }), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        
        # 檢查使用者是否存在
        cursor.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'error': '使用者不存在'
            }), 404
        
        # 更新密碼
        password_hash = hash_password(new_password)
        cursor.execute('''
            UPDATE users
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (password_hash, user_id))
        
        db.commit()
        
        # 記錄日誌
        log_action(g.current_user['user_id'], 'reset_password', 'users', f'Reset password for: {user["username"]}')
        
        return jsonify({
            'success': True,
            'message': '密碼已重設'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': '伺服器錯誤',
            'message': str(e)
        }), 500
