# ERP API 配置文件

# 伺服器設定
HOST = '0.0.0.0'
PORT = 5508
DEBUG = False

# 資料庫設定
DATABASE_PATH = 'erp.db'

# JWT 設定
JWT_SECRET_KEY = 'your-super-secret-jwt-key-change-in-production-2024'
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_MINUTES = 60

# CORS 設定 (允許 GitHub.io 跨域)
CORS_ORIGINS = [
    'https://admin.ypascent.com.tw',
    'http://localhost:8000',  # 本地開發測試
    'http://127.0.0.1:8000',
    '*'  # 全開放，生產環境建議移除
]

# 加密設定
ENCRYPTION_KEY = 'your-encryption-key-32-chars!!'  # 必須 32 字元

# API 前綴
API_PREFIX = '/api'
