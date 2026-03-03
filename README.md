# AI 模型对比对话窗口 🦞

多模型并发提问对比工具 - 支持腾讯云混元和阿里云百炼

[![GitHub](https://img.shields.io/badge/github-cirrusli/ai__proj-blue)](https://github.com/cirrusli/ai_proj)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## ✨ 功能特性

- 🚀 **多模型对比** - 同时调用腾讯云 + 阿里云，对比回答质量
- 🎯 **丰富模型** - 支持 9 种腾讯混元 + 10 种阿里 Qwen 模型
- 🔐 **用户系统** - 登录/注册（最多 10 用户，无密码认证）
- 🔑 **API Key 管理** - 安全的密钥配置与存储（前端不暴露）
- 💬 **对话历史** - SQLite 持久化存储，支持多轮对话上下文
- 🎨 **简约 UI** - 苹果风格界面设计，悬浮输入框
- 📱 **响应式** - 适配桌面和移动端
- 👤 **个人主页** - GitHub 风格头像、个性签名、真实统计
- 📊 **会话管理** - 新建/切换/编辑标题/历史列表
- ⚡ **流式输出** - SSE 实时打字机效果，真正并发
- 📝 **Markdown** - 支持代码/表格/列表渲染
- 📈 **数据统计** - 模型使用次数/延迟/会话数/消息数
- 📁 **文件下载** - 安全白名单机制，支持中文文件名，移动端适配

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
1. 访问 [API Key 管理](https://console.cloud.tencent.com/hunyuan/start)
2. 复制 API Key
3. 选择模型（Lite/标准/Pro/Turbo/T1 等）

**阿里云百炼：**
1. 访问 [API Key 管理](https://bailian.console.aliyun.com/cn-beijing/?tab=model#/api-key)
2. 复制 API Key
3. 选择模型（Turbo/Plus/Max/Max 长文本）

### 3. 开始对话

1. 选择要对比的模型
2. 输入问题
3. 点击"发送"（或按 Enter）
4. 查看不同模型的回答对比

## 📁 文件下载

访问 `/files` 页面可下载预设的工作区文件。

**安全特性：**
- 🔒 白名单机制 - 只允许下载配置的文件
- 🛡️ 路径验证 - 双重检查，防止路径遍历攻击
- 🔐 只读访问 - 无上传/修改/删除功能
- 📱 移动端适配 - 汉堡菜单，响应式布局
- 🌐 中文支持 - RFC 5987 编码，完美支持中文文件名

**配置方式：**
编辑 `app/files.json`（热加载，无需重启）：

```json
{
  "files": {
    "文件名.xlsx": {
      "path": "/root/.openclaw/workspace/eco_proj/文件名.xlsx",
      "desc": "文件描述",
      "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
  }
}
```

⚠️ **注意**：`files.json` 包含真实路径，已加入 `.gitignore`，不要提交到仓库。

## 📊 可用模型

### 腾讯云混元（9 种）

| 模型 | 描述 | 适用场景 |
|------|------|----------|
| hunyuan-lite | 轻量级，速度快 | 简单问答、快速响应 |
| hunyuan-standard | 平衡性能与成本 | 日常使用 |
| hunyuan-standard-256k | 支持 256K 超长上下文 | 长文档理解、书籍分析 |
| hunyuan-pro | 最强性能 | 复杂任务、高质量要求 |
| hunyuan-turbo | 高性能，适合复杂任务 | 专业场景 |
| hunyuan-t1-latest | 最新一代模型 | 性能最优 |
| hunyuan-t1 | 深度推理模型 | 数学、科学、逻辑推理 |
| hunyuan-large-role-latest | AI 角色扮演 | 情感陪聊、数字分身 |
| hunyuan-translation | 33 种语言互译 | 多语言翻译 |

📖 **官方文档**：[腾讯混元大模型](https://cloud.tencent.com/document/product/1729)
- [产品概述](https://cloud.tencent.com/document/product/1729/104753)
- [API 调用示例](https://cloud.tencent.com/document/product/1729/111007)
- [API Key 管理](https://cloud.tencent.com/document/product/1729/111008)

### 阿里云通义千问（10 种）

| 模型 | 描述 | 适用场景 |
|------|------|----------|
| qwen-flash | 极速响应，低成本 | 简单问答 |
| qwen-coder | 代码专用模型 | 编程/调试 |
| qwen3.5 | 最新版本 | 通用场景 |
| qwen3 | 经典版本 | 日常使用 |
| qwen-plus | 平衡性能与成本 | 日常使用 |
| qwen-max | 最强性能 | 复杂任务 |
| qwen-max-longcontext | 支持超长上下文 | 长文档分析 |
| qwen-turbo | 速度快，成本低 | 高频调用 |
| qwen-long | 长文本处理 | 文档理解 |
| qwen-vl-max | 视觉语言模型 | 图像理解 |

📖 **官方文档**：[阿里云百炼](https://help.aliyun.com/product/42154.html)

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
│   ├── settings.html        # 设置页面
│   ├── profile.html         # 个人主页
│   └── files.html           # 文件下载页面
├── app/
│   ├── main.py              # FastAPI 后端
│   └── file_config.py       # 文件下载配置（热加载）
├── static/                  # 静态资源
├── tests/                   # 单元测试
├── k8s/                     # Kubernetes 部署配置
├── requirements.txt         # Python 依赖
├── Dockerfile               # Docker 镜像
├── docker-compose.yml       # Docker Compose 配置
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
- GitHub 风格马赛克头像生成

**部署：**
- Python 3.11+
- Docker & Docker Compose
- Kubernetes
- Nginx（反向代理）

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
users (id, username, email, bio, avatar_seed, role, created_at)

-- API Key 配置
api_keys (id, user_id, provider, api_key, model_id, created_at)

-- 对话历史（按轮次记录，包含所有模型响应）
chat_history (id, session_id, round, user_id, user_message, model_responses JSON, timestamp)

-- 会话标题
session_titles (session_id PK, user_id, title, created_at)
```

**索引优化：**
- `idx_chat_history_user` - 按用户查询
- `idx_chat_history_session` - 按会话查询
- `idx_chat_history_timestamp` - 按时间查询

**统计视图：**
- `user_model_stats` - 用户统计（会话数/轮数/消息数）
- `model_usage_stats` - 模型使用统计（次数/平均延迟）

## 💡 使用技巧

### 会话管理

**Q: 新建会话后如何找到之前的对话？**

A: 有三种方式：

1. **会话列表** - 点击页面顶部的会话列表区域，显示所有历史会话
2. **会话标题** - 点击 ✏️ 图标编辑会话标题，方便识别（如"Python 问题"、"论文写作"）
3. **时间排序** - 会话列表按最后更新时间排序，最近的在最上面

**Q: 如何切换会话？**

A: 点击会话列表中的任意会话即可切换，对话历史会自动加载。

**Q: 如何新建会话？**

A: 点击页面右上角的"+ 新对话"按钮。

### 模型对比

- 同时勾选腾讯云 + 阿里云，对比同一问题的不同回答
- 在设置页可以随时切换模型，无需重新输入 API Key
- 每个模型响应显示延迟时间（ms），帮助选择最优模型

### 长回复阅读

- 超过 100 字的回复会自动折叠（6em 高度）
- 点击右下角"展开"按钮查看完整内容
- 再次点击可收起

## 🧪 测试

### 运行测试

```bash
# 安装测试依赖
pip3 install -r tests/requirements-test.txt

# 运行所有测试
pytest

# 运行特定测试类
pytest tests/test_main.py::TestAuth -v

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 测试覆盖

- ✅ 认证系统（登录/注册/限制）
- ✅ API Key 管理（保存/查询/安全）
- ✅ 对话功能（权限验证）
- ✅ 模型列表 API
- ✅ 安全性（SQL 注入/Cookie）

**测试结果**：13/13 通过 ✅

## 🐳 Docker 部署

### Docker Compose（推荐）

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f ai-comparator

# 停止服务
docker-compose down

# 重启服务
docker-compose restart
```

访问：http://localhost

### 单独 Docker

```bash
# 构建镜像
docker build -t ai-comparator .

# 运行容器
docker run -d -p 8000:8000 \
  -v ai_data:/app \
  --name ai-comparator \
  ai-comparator
```

### Kubernetes 部署

```bash
# 创建资源
kubectl apply -f k8s/deployment.yaml

# 查看状态
kubectl get pods -l app=ai-comparator

# 查看日志
kubectl logs -l app=ai-comparator

# 扩缩容
kubectl scale deployment ai-comparator --replicas=3
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

### v1.2.0 (2026-03-02)
- ✅ 添加腾讯云混元完整模型列表（9 个）
- ✅ 个人主页功能（头像、签名、邮箱）
- ✅ 下拉菜单导航（移动端优化）
- ✅ 输入框优化（嵌入式发送按钮）
- ✅ 使用腾讯云 OpenAI 兼容接口
- ✅ 更新官方文档链接

### v1.1.0 (2026-03-02)
- ✅ 安全修复：API Key 不返回前端
- ✅ Cookie 安全属性增强
- ✅ 数据库连接管理优化
- ✅ 错误信息脱敏
- ✅ 添加 SECURITY.md
- ✅ 添加单元测试（13 个）
- ✅ Docker & K8s 部署支持

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
