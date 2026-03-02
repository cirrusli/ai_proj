# AI 模型对比对话窗口 🦞

快速部署多模型并发提问对比工具

## 🚀 快速启动

```bash
cd /root/.openclaw/workspace/ai_proj
pip install -r requirements.txt
sudo python app/main.py
```

访问 http://localhost

## 📋 待办事项

### 高优先级
- [ ] 获取腾讯云大模型 API Key
- [ ] 获取阿里云百炼 API Key
- [ ] 实现真实 API 调用（替换 mock）

### 中优先级
- [ ] 添加更多模型支持（DeepSeek、智谱等）
- [ ] 流式输出支持
- [ ] 对话历史记录查看

### 低优先级
- [ ] 用户认证系统
- [ ] 响应统计面板
- [ ] 导出对话记录

## 📁 项目结构

```
ai_proj/
├── app/
│   └── main.py          # FastAPI 主应用
├── protos/
│   └── message.proto    # Protobuf 协议定义
├── templates/
│   └── index.html       # H5 前端
├── static/              # 静态资源
├── requirements.txt     # Python 依赖
└── README.md           # 本文件
```

## 🔑 API Key 获取

### 腾讯云大模型
1. 登录 https://cloud.tencent.com/
2. 控制台 → 人工智能 → 大模型
3. 创建 API Key

### 阿里云百炼
1. 登录 https://www.aliyun.com/
2. 控制台 → 百炼平台
3. API 管理 → 创建 Key

---

**创建时间**: 2026-03-02  
**负责人**: cirrus + 云卷 🦞
