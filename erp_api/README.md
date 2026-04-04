# ERP API 系統

Flask RESTful API 後端系統，搭配 GitHub Pages 前端使用。

## 系統架構

```
erp_api/
├── main.py              # 主程式（入口）
├── config.py            # 配置文件
├── utils.py             # 資料庫初始化、JWT、加密
├── erp.db               # SQLite 自動生成
├── api_health.py        # 健康檢查
├── api_auth_login.py    # 登入
├── api_auth_logout.py   # 登出
├── api_auth_me.py       # 個人資訊
├── api_auth_permission.py # 權限驗證
└── api_admin_users.py   # 使用者管理
```

## 部署環境

- **前端**: GitHub Pages (admin.ypascent.com.tw)
- **後端**: Windows 本機伺服器
- **公網 IP**: 114.34.157.56:5508
- **資料庫**: SQLite (erp.db)

## 安裝步驟

### 1. 安裝 Python 依賴

```bash
pip install -r requirements.txt
```

### 2. 啟動服務

```bash
python main.py
```

### 3. 測試 API

```bash
curl http://localhost:5508/api/health
```

## 預設帳號

- **Username**: admin
- **Password**: Admin@123456

## API 端點

### 健康檢查
- `GET /api/health` - 服務狀態檢查
- `GET /api/ping` - Ping 測試

### 認證
- `POST /api/auth/login` - 使用者登入
- `POST /api/auth/logout` - 使用者登出
- `GET /api/auth/me` - 獲取當前使用者資訊
- `GET /api/auth/me/permissions` - 獲取使用者權限

### 權限
- `POST /api/auth/permission/check` - 檢查特定權限
- `GET /api/auth/permissions` - 獲取所有系統權限
- `GET /api/auth/my-permissions` - 獲取我的權限列表

### 使用者管理 (Admin)
- `GET /api/admin/users` - 使用者列表
- `GET /api/admin/users/:id` - 單一使用者詳情
- `POST /api/admin/users` - 建立使用者
- `PUT /api/admin/users/:id` - 更新使用者
- `DELETE /api/admin/users/:id` - 刪除使用者
- `POST /api/admin/users/:id/reset-password` - 重設密碼

## 網路配置

### Windows 防火牆

開放 TCP 5508 入站規則：

```powershell
netsh advfirewall firewall add rule name="ERP API" dir=in action=allow protocol=TCP localport=5508
```

### 路由器 Port Forwarding

設定 Port Forward 5508 → 區網 IP 192.168.200.147:5508

## CORS 設定

已全開放 CORS，允許 GitHub.io 跨域呼叫。

## JWT Token 使用

所有需要認證的 API 都需要在 Header 中加入：

```
Authorization: Bearer <your-jwt-token>
```

## 安全注意事項

1. 生產環境請修改 `config.py` 中的 `JWT_SECRET_KEY`
2. 建議移除 CORS 中的 `*`，僅保留必要的域名
3. 定期備份 `erp.db` 資料庫檔案
4. 使用強密碼政策
