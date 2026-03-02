# GitHub 部署指南

## 仓库结构

```
ai_proj/
├── ai_proj/          # AI 模型对比对话窗口主程序
│   ├── app/
│   ├── templates/
│   ├── protos/
│   ├── README.md
│   └── ...
├── memory/           # 会话记忆
├── skills/           # 技能文件
└── ...
```

## 推送代码

```bash
cd /root/.openclaw/workspace

# 推送
git push -u origin master
```

## 后续更新

```bash
git add .
git commit -m "更新说明"
git push
```
