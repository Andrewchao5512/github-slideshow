"""
ERP API 主程式
Flask 應用程式入口點
"""

from flask import Flask, jsonify, g
from flask_cors import CORS
import config
import utils

# 導入所有 API Blueprint
from api_health import api_health
from api_auth_login import api_auth_login
from api_auth_logout import api_auth_logout
from api_auth_me import api_auth_me
from api_auth_permission import api_auth_permission
from api_admin_users import api_admin_users


def create_app():
    """建立並配置 Flask 應用程式"""
    app = Flask(__name__)
    
    # 配置 CORS - 全開放允許 GitHub.io 跨域呼叫
    CORS(app, resources={
        r"/api/*": {
            "origins": config.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # 註冊 Blueprint
    app.register_blueprint(api_health, url_prefix=config.API_PREFIX)
    app.register_blueprint(api_auth_login, url_prefix=config.API_PREFIX)
    app.register_blueprint(api_auth_logout, url_prefix=config.API_PREFIX)
    app.register_blueprint(api_auth_me, url_prefix=config.API_PREFIX)
    app.register_blueprint(api_auth_permission, url_prefix=config.API_PREFIX)
    app.register_blueprint(api_admin_users, url_prefix=config.API_PREFIX)
    
    # 全局錯誤處理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': '找不到資源',
            'message': '請求的 API 端點不存在'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': '伺服器錯誤',
            'message': '內部伺服器錯誤，請稍後再試'
        }), 500
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': '方法不允許',
            'message': '此 HTTP 方法不適用於該端點'
        }), 405
    
    # 根路由
    @app.route('/')
    def index():
        return jsonify({
            'name': 'ERP API System',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'health': '/api/health',
                'login': '/api/auth/login',
                'logout': '/api/auth/logout',
                'me': '/api/auth/me',
                'permissions': '/api/auth/permissions',
                'admin_users': '/api/admin/users'
            }
        })
    
    # 資料庫關閉處理
    @app.teardown_appcontext
    def close_db(exception):
        db = g.pop('db', None)
        if db is not None:
            db.close()
    
    return app


if __name__ == '__main__':
    from flask import g
    
    # 初始化資料庫
    print("=" * 50)
    print("ERP API 系統啟動中...")
    print("=" * 50)
    
    utils.init_db()
    
    # 建立應用程式
    app = create_app()
    
    print(f"\n✓ 伺服器配置:")
    print(f"  - Host: {config.HOST}")
    print(f"  - Port: {config.PORT}")
    print(f"  - Debug: {config.DEBUG}")
    print(f"  - Database: {config.DATABASE_PATH}")
    print(f"\n✓ CORS 已啟用，允許來源：{config.CORS_ORIGINS}")
    print(f"\n✓ 預設管理員帳號:")
    print(f"  - Username: admin")
    print(f"  - Password: Admin@123456")
    print(f"\n✓ API 測試位址:")
    print(f"  - http://localhost:{config.PORT}/api/health")
    print(f"  - http://114.34.157.56:{config.PORT}/api/health")
    print("\n" + "=" * 50)
    
    # 啟動伺服器
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        threaded=True
    )
