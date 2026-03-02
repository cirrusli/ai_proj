# AI 模型对比对话窗口 🦞

多模型并发提问对比工具 - 支持腾讯云混元和阿里云百炼

[![GitHub](https://img.shields.io/badge/github-cirrusli/ai__proj-blue)](https://github.com/cirrusli/ai_proj)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## ✨ 功能特性

- 🚀 **多模型对比** - 同时调用腾讯云 + 阿里云，对比回答质量
- 🎯 **模型选择** - 支持 4 种腾讯混元 + 4 种阿里 Qwen 模型
- 🔐 **用户系统** - 登录/注册（最多 10 用户）
- 🔑 **API Key 管理** - 安全的密钥配置与存储
- 💬 **对话历史** - SQLite 持久化存储
- 🎨 **简约 UI** - 苹果风格界面设计
- 📱 **响应式** - 适配桌面和移动端

## 🚀 快速启动

### 1. 安装依赖

```bash
cd /root/.openclaw/workspace/ai_proj
pip3 install -r requirements.txt
```

### 2. 启动服务

```bash
python3 app/main.py
```

### 3. 访问页面

- 首页：http://localhost
- 登录：http://localhost/login
- 设置：http://localhost/settings

## 📋 配置指南

### 1. 注册账号

访问登录页，输入用户名 → 点击"注册"

### 2. 配置 API Key

访问 `/settings` 配置：

**腾讯云混元：**
1. 访问 https://hunyuan.cloud.tencent.com/#/app/apiKeyManage
2. 复制 API Key
3. 选择模型（Lite/标准/Pro/Turbo）

**阿里云百炼：**
1. 访问 https://bailian.console.aliyun.com/cn-beijing/?tab=model#/api-key
2. 复制 API Key
3. 选择模型（Turbo/Plus/Max/Max 长文本）

### 3. 开始对话

1. 选择要对比的模型
2. 输入问题
3. 点击"发送"
4. 查看不同模型的回答对比

## 📁 项目结构

```
ai_proj/
├── app/
│   └── main.py              # FastAPI 后端
├── protos/
│   └── message.proto        # Protobuf 协议定义
├── templates/
│   ├── index.html           # 对话页面
│   ├── login.html           # 登录页面
│   └── settings.html        # 设置页面
├── static/                  # 静态资源
├── requirements.txt         # Python 依赖
├── README.md                # 本文件
└── SECURITY.md              # 安全审计报告
```

## 🔧 技术栈

**后端：**
- FastAPI 0.109.0
- SQLite 数据库
- HTTPX 异步 HTTP 客户端

**前端：**
- 原生 HTML/CSS/JavaScript
- 苹果风格设计系统

**部署：**
- Python 3.11+
- Nginx（可选，生产环境）

## 🔐 安全性

详见 [SECURITY.md](SECURITY.md)

- ✅ API Key 不返回前端
- ✅ Cookie HttpOnly + SameSite
- ✅ SQL 参数化查询
- ✅ 错误信息脱敏
- ✅ 数据库连接管理

## 📊 数据库

```sql
-- 用户表
users (id, username, role, created_at)

-- API Key 配置
api_keys (id, user_id, provider, api_key, model_id, created_at)

-- 对话历史
messages (id, session_id, user_id, user_message, timestamp)
responses (id, session_id, user_id, model_name, content, latency_ms, timestamp)
```

## 🛠️ 开发

### 添加新模型提供商

1. 在 `app/main.py` 添加模型配置：
```python
AVAILABLE_MODELS = {
    "new_provider": [
        {"id": "model-1", "name": "模型 1", "desc": "描述"},
    ]
}
```

2. 实现 API 调用函数：
```python
async def call_new_provider_api(message, api_key, model_id):
    # 实现 API 调用
```

3. 更新设置页模板

### 部署到生产环境

```bash
# 使用 Gunicorn + Uvicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:8000
```

## 📝 更新日志

### v1.1.0 (2026-03-02)
- ✅ 安全修复：API Key 不返回前端
- ✅ Cookie 安全属性增强
- ✅ 数据库连接管理优化
- ✅ 错误信息脱敏
- ✅ 添加 SECURITY.md

### v1.0.0 (2026-03-02)
- 🎉 初始版本发布
- 支持腾讯云 + 阿里云对比
- 用户登录/注册系统
- 简约苹果风格 UI

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

**创建时间**: 2026-03-02  
**维护者**: cirrus + 云卷 🦞  
**GitHub**: https://github.com/cirrusli/ai_proj
