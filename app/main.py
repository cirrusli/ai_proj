"""
AI 模型对比对话窗口 - FastAPI 后端
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import time
import sqlite3
import uuid

app = FastAPI(title="AI Model Comparator")

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 数据库初始化
def init_db():
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            role TEXT DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # API Key 配置表（添加模型选择）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            provider TEXT,
            api_key TEXT,
            model_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # 消息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_id INTEGER,
            user_message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # 响应表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_id INTEGER,
            model_name TEXT,
            content TEXT,
            latency_ms INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # 插入默认管理员用户
    try:
        cursor.execute("INSERT INTO users (username, role) VALUES (?, ?)", ("cirrus", "admin"))
    except sqlite3.IntegrityError:
        pass  # 用户已存在
    conn.commit()
    conn.close()

init_db()

# 简单的会话管理
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 跳过登录、静态文件和公开 API
        public_paths = ["/login", "/api/login", "/api/register", "/static", "/api/models"]
        if request.url.path in public_paths or request.url.path.startswith("/docs"):
            return await call_next(request)
        
        session_id = request.cookies.get("session_id")
        if not session_id:
            return RedirectResponse(url="/login")
        
        # 验证会话
        conn = sqlite3.connect('chat_history.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (session_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return RedirectResponse(url="/login")
        
        request.state.user = {"id": user[0], "username": user[1], "role": user[2]}
        return await call_next(request)

app.add_middleware(AuthMiddleware)

# 请求/响应模型
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_message: str
    models: List[str] = ["tencent", "aliyun"]

class ModelResponse(BaseModel):
    model_name: str
    content: str
    success: bool
    error_message: Optional[str] = None
    latency_ms: int

class ChatResponse(BaseModel):
    session_id: str
    responses: List[ModelResponse]
    total_latency_ms: int

# API 调用实现
async def call_tencent_api(message: str, api_key: str, model_id: str) -> str:
    """调用腾讯云混元 API"""
    import httpx
    
    url = "https://hunyuan.tencentcloudapi.com"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 默认模型
    if not model_id:
        model_id = "hunyuan-lite"
    
    payload = {
        "Model": model_id,
        "Messages": [
            {"Role": "user", "Content": message}
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # 腾讯云返回格式
            if "Response" in data and "Choices" in data["Response"]:
                return data["Response"]["Choices"][0]["Message"]["Content"]
            elif "Choices" in data:
                return data["Choices"][0]["Message"]["Content"]
            else:
                return "API 响应格式异常"
    except httpx.HTTPStatusError as e:
        # 不暴露详细错误信息
        raise Exception(f"腾讯云 API 调用失败：HTTP {e.response.status_code}")
    except Exception as e:
        # 隐藏敏感信息
        raise Exception("腾讯云 API 调用失败")

async def call_aliyun_api(message: str, api_key: str, model_id: str) -> str:
    """调用阿里云百炼 API"""
    import httpx
    
    # 默认模型
    if not model_id:
        model_id = "qwen-turbo"
    
    url = f"https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model_id,
        "input": {
            "messages": [
                {"role": "user", "content": message}
            ]
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # 阿里云返回格式
            if "output" in data and "choices" in data["output"]:
                return data["output"]["choices"][0]["message"]["content"]
            else:
                return "API 响应格式异常"
    except httpx.HTTPStatusError as e:
        raise Exception(f"阿里云 API 调用失败：HTTP {e.response.status_code}")
    except Exception as e:
        raise Exception("阿里云 API 调用失败")

@app.get("/")
async def root():
    return FileResponse("templates/index.html")

@app.get("/login")
async def login_page():
    return FileResponse("templates/login.html")

@app.get("/settings")
async def settings_page():
    return FileResponse("templates/settings.html")

@app.post("/api/login")
async def api_login(request: Request):
    from json import loads
    body = await request.body()
    data = loads(body)
    username = data.get("username", "")
    action = data.get("action", "login")  # "login" or "register"
    
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    from starlette.responses import Response
    
    if action == "register":
        # 注册逻辑
        if user:
            conn.close()
            return Response(content='{"success": false, "error": "用户已存在，请直接登录"}', status_code=400)
        
        # 检查用户总数限制
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        if user_count >= 10:
            conn.close()
            return Response(content='{"success": false, "error": "注册已达上限，请联系管理员"}', status_code=400)
        
        cursor.execute("INSERT INTO users (username, role) VALUES (?, ?)", (username, "user"))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        response = Response(content='{"success": true, "registered": true}')
        response.set_cookie(
            "session_id", 
            str(user_id), 
            httponly=True,
            secure=False,  # 生产环境改为 True (HTTPS)
            samesite="lax",
            maxage=86400 * 7  # 7 天有效期
        )
        return response
    else:
        # 登录逻辑
        conn.close()
        if not user:
            return Response(content='{"success": false, "error": "用户不存在，请先注册"}', status_code=400)
        
        response = Response(content='{"success": true, "registered": false}')
        response.set_cookie(
            "session_id", 
            str(user[0]), 
            httponly=True,
            secure=False,  # 生产环境改为 True (HTTPS)
            samesite="lax",
            maxage=86400 * 7  # 7 天有效期
        )
        return response

@app.get("/api/me")
async def get_current_user(request: Request):
    if not hasattr(request.state, 'user'):
        return {"authenticated": False}
    return {"authenticated": True, "user": request.state.user}

@app.post("/api/logout")
async def api_logout():
    from starlette.responses import Response
    response = Response(content='{"success": true}')
    response.delete_cookie("session_id")
    return response

@app.get("/api/keys")
async def get_api_keys(request: Request):
    """获取 API Key 配置列表（仅返回脱敏后的信息）"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(status_code=401, detail="未登录")
    
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, provider, model_id, created_at FROM api_keys WHERE user_id = ?", (request.state.user['id'],))
    keys = []
    for row in cursor.fetchall():
        keys.append({
            "id": row[0],
            "provider": row[1],
            "model_id": row[2],
            "created_at": row[3],
            # 注意：不返回 api_key，即使是脱敏的
        })
    conn.close()
    
    return {"keys": keys}

# 模型配置
AVAILABLE_MODELS = {
    "tencent": [
        {"id": "hunyuan-lite", "name": "混元 Lite", "desc": "轻量级，速度快"},
        {"id": "hunyuan-standard", "name": "混元标准", "desc": "平衡性能与成本"},
        {"id": "hunyuan-pro", "name": "混元 Pro", "desc": "最强性能"},
        {"id": "hunyuan-turbo", "name": "混元 Turbo", "desc": "高性能，适合复杂任务"},
    ],
    "aliyun": [
        {"id": "qwen-turbo", "name": "Qwen Turbo", "desc": "速度快，成本低"},
        {"id": "qwen-plus", "name": "Qwen Plus", "desc": "平衡性能与成本"},
        {"id": "qwen-max", "name": "Qwen Max", "desc": "最强性能"},
        {"id": "qwen-max-longcontext", "name": "Qwen Max 长文本", "desc": "支持超长上下文"},
    ]
}

@app.get("/api/models")
async def get_models():
    """获取可用模型列表"""
    return {"models": AVAILABLE_MODELS}

@app.get("/api/models/{provider}")
async def get_provider_models(provider: str):
    """获取指定提供商的模型列表"""
    if provider not in AVAILABLE_MODELS:
        raise HTTPException(status_code=404, detail="不支持的提供商")
    return {"models": AVAILABLE_MODELS[provider]}

@app.post("/api/keys")
async def save_api_keys(request: Request):
    """保存 API Key 配置"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(status_code=401, detail="未登录")
    
    from json import loads
    body = await request.body()
    data = loads(body)
    provider = data.get("provider")
    api_key = data.get("api_key")
    model_id = data.get("model_id")
    
    # 验证输入
    if not provider or not api_key:
        raise HTTPException(status_code=400, detail="provider 和 api_key 不能为空")
    
    if provider not in ["tencent", "aliyun"]:
        raise HTTPException(status_code=400, detail="不支持的 provider")
    
    # 验证 API Key 格式（基本检查）
    if len(api_key) < 10:
        raise HTTPException(status_code=400, detail="API Key 格式不正确")
    
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    try:
        # 先删除旧的，再插入新的
        cursor.execute("DELETE FROM api_keys WHERE user_id = ? AND provider = ?", (request.state.user['id'], provider))
        cursor.execute("INSERT INTO api_keys (user_id, provider, api_key, model_id) VALUES (?, ?, ?, ?)", 
                       (request.state.user['id'], provider, api_key, model_id))
        conn.commit()
    finally:
        conn.close()
    
    return {"success": True}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, request_obj: Request):
    """多模型并发对话接口"""
    if not hasattr(request_obj.state, 'user'):
        raise HTTPException(status_code=401, detail="未登录")
    
    user_id = request_obj.state.user['id']
    session_id = request.session_id or str(uuid.uuid4())
    start_time = time.time()
    
    # 获取用户的 API Key 配置
    conn = sqlite3.connect('chat_history.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        # 获取 API Keys
        cursor.execute("SELECT provider, api_key, model_id FROM api_keys WHERE user_id = ?", (user_id,))
        keys_map = {}
        for row in cursor.fetchall():
            keys_map[row[0]] = {"api_key": row[1], "model_id": row[2]}
    finally:
        conn.close()
    
    # 保存用户消息
    conn = sqlite3.connect('chat_history.db')
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (session_id, user_id, user_message) VALUES (?, ?, ?)",
            (session_id, user_id, request.user_message)
        )
        conn.commit()
    finally:
        conn.close()
    
    # 并发调用多个模型
    tasks = []
    results = []
    
    if "tencent" in request.models:
        tencent_config = keys_map.get("tencent")
        if tencent_config and tencent_config["api_key"]:
            tasks.append(("tencent", call_tencent_api(
                request.user_message, 
                tencent_config["api_key"], 
                tencent_config["model_id"]
            )))
        else:
            results.append(ModelResponse(
                model_name="tencent",
                content="",
                success=False,
                error_message="未配置腾讯云 API Key",
                latency_ms=0
            ))
    
    if "aliyun" in request.models:
        aliyun_config = keys_map.get("aliyun")
        if aliyun_config and aliyun_config["api_key"]:
            tasks.append(("aliyun", call_aliyun_api(
                request.user_message, 
                aliyun_config["api_key"], 
                aliyun_config["model_id"]
            )))
        else:
            results.append(ModelResponse(
                model_name="aliyun",
                content="",
                success=False,
                error_message="未配置阿里云 API Key",
                latency_ms=0
            ))
    for model_name, task in tasks:
        try:
            content = await task
            results.append(ModelResponse(
                model_name=model_name,
                content=content,
                success=True,
                latency_ms=0  # 将在下面计算
            ))
        except Exception as e:
            results.append(ModelResponse(
                model_name=model_name,
                content="",
                success=False,
                error_message=str(e),
                latency_ms=0
            ))
    
    total_latency = int((time.time() - start_time) * 1000)
    
    # 保存模型响应
    conn = sqlite3.connect('chat_history.db')
    try:
        cursor = conn.cursor()
        for resp in results:
            cursor.execute(
                "INSERT INTO responses (session_id, user_id, model_name, content, latency_ms) VALUES (?, ?, ?, ?, ?)",
                (session_id, user_id, resp.model_name, resp.content, resp.latency_ms)
            )
        conn.commit()
    finally:
        conn.close()
    
    return ChatResponse(
        session_id=session_id,
        responses=results,
        total_latency_ms=total_latency
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
