"""
ERP API 工具模組
包含：資料庫初始化、JWT 認證、密碼加密等功能
"""

import sqlite3
import hashlib
import jwt
import datetime
from functools import wraps
from flask import request, jsonify, g
import config


def get_db():
    """取得資料庫連線"""
    if 'db' not in g:
        g.db = sqlite3.connect(config.DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def init_db():
    """初始化資料庫，建立必要表格"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # 建立使用者表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user',
            permissions TEXT DEFAULT '[]',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 建立權限表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    ''')
    
    # 建立操作日誌表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource TEXT,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 建立預設管理員帳號 (如果不存在)
    # 預設帳號：admin / Admin@123456
    default_password = hash_password('Admin@123456')
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password_hash, email, role, permissions)
        VALUES (?, ?, ?, ?, ?)
    ''', ('admin', default_password, 'admin@ypascent.com.tw', 'admin', '["all"]'))
    
    # 插入預設權限
    default_permissions = [
        ('view_dashboard', '查看儀表板'),
        ('manage_users', '管理使用者'),
        ('manage_products', '管理產品'),
        ('manage_orders', '管理訂單'),
        ('view_reports', '查看報表'),
        ('all', '所有權限')
    ]
    
    for perm_name, perm_desc in default_permissions:
        cursor.execute('''
            INSERT OR IGNORE INTO permissions (name, description)
            VALUES (?, ?)
        ''', (perm_name, perm_desc))
    
    conn.commit()
    conn.close()
    print("✓ 資料庫初始化完成")


def hash_password(password):
    """使用 SHA-256 加密密碼"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, password_hash):
    """驗證密碼是否正確"""
    return hash_password(password) == password_hash


def generate_token(user_id, username, role):
    """生成 JWT Token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=config.JWT_EXPIRATION_MINUTES),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def decode_token(token):
    """解碼 JWT Token"""
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """JWT Token 驗證裝飾器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 從 Header 獲取 Token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'error': 'Token 缺失', 'message': '請提供有效的認證 Token'}), 401
        
        payload = decode_token(token)
        if payload is None:
            return jsonify({'error': 'Token 無效或已過期', 'message': '請重新登入'}), 401
        
        # 將用戶資訊存入 g 物件
        g.current_user = payload
        return f(*args, **kwargs)
    
    return decorated


def permission_required(required_permission):
    """權限驗證裝飾器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({'error': '未認證', 'message': '請先登入'}), 401
            
            user_permissions = g.current_user.get('permissions', [])
            
            # 檢查是否有 'all' 權限或指定權限
            if 'all' not in user_permissions and required_permission not in user_permissions:
                return jsonify({
                    'error': '權限不足',
                    'message': f'需要 {required_permission} 權限'
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def log_action(user_id, action, resource=None, details=None):
    """記錄操作日誌"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_logs (user_id, action, resource, details, ip_address)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, action, resource, details, request.remote_addr))
        conn.commit()
    except Exception as e:
        print(f"記錄日誌失敗：{e}")
