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
import json

app = FastAPI(title="AI Model Comparator")

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 数据库初始化
def init_db():
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    # 用户表（时区：Asia/Shanghai）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT,
            bio TEXT,
            avatar_seed TEXT,
            role TEXT DEFAULT 'user',
            created_at DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    # 检查是否需要添加新列（旧数据库升级）
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN avatar_seed TEXT")
    except sqlite3.OperationalError:
        pass  # 列已存在
    # API Key 配置表（添加模型选择）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            provider TEXT,
            api_key TEXT,
            model_id TEXT,
            created_at DATETIME DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # 对话历史表（按轮次记录，包含用户消息和所有模型的回复）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            round INTEGER,
            user_id INTEGER,
            user_message TEXT,
            model_responses TEXT,  -- JSON 格式：[{"model": "tencent", "model_id": "hunyuan-t1", "content": "...", "success": true}]
            timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
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
    history: Optional[List[dict]] = None  # 多轮对话历史 [{"role": "user/assistant", "content": "..."}]

class ModelResponse(BaseModel):
    model_name: str
    model_id: Optional[str] = None
    content: str
    success: bool
    error_message: Optional[str] = None
    latency_ms: int

class ChatResponse(BaseModel):
    session_id: str
    responses: List[ModelResponse]
    total_latency_ms: int

# API 调用实现
async def call_tencent_api(message: str, api_key: str, model_id: str, user_id: int = None, history: List[dict] = None) -> str:
    """调用腾讯云混元 API（OpenAI 兼容接口）"""
    import httpx
    import logging
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # OpenAI 兼容接口地址
    url = "https://api.hunyuan.cloud.tencent.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 默认模型
    if not model_id:
        model_id = "hunyuan-lite"
    
    # 构建消息历史（支持多轮对话）
    messages = []
    if history and len(history) > 0:
        # 添加历史对话
        for msg in history[-10:]:  # 最多保留最近 10 轮
            if msg.get("role") in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
    
    # 添加当前消息
    messages.append({"role": "user", "content": message})
    
    # OpenAI 兼容格式
    payload = {
        "model": model_id,
        "messages": messages
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # 记录完整响应（用于调试）
            logger.info(f"腾讯云响应：{data}")
            
            # OpenAI 兼容返回格式
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            
            # 错误处理
            if "error" in data:
                error_msg = data["error"].get("message", "未知错误")
                logger.error(f"腾讯云 API 错误：{error_msg}")
                raise Exception(f"腾讯云 API 错误：{error_msg}")
            
            # 未知格式，返回详细信息
            logger.error(f"未知响应格式：{data}")
            raise Exception(f"API 响应格式异常：{str(data)[:200]}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP 错误：{e.response.status_code} - {e.response.text}")
        raise Exception(f"腾讯云 API 调用失败：HTTP {e.response.status_code}")
    except Exception as e:
        logger.error(f"调用失败：{str(e)}")
        raise

async def call_aliyun_api(message: str, api_key: str, model_id: str, user_id: int = None, history: List[dict] = None) -> str:
    """调用阿里云百炼 API"""
    import httpx
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 默认模型
    if not model_id:
        model_id = "qwen-turbo"
    
    url = f"https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 构建消息历史（支持多轮对话）
    messages = []
    if history and len(history) > 0:
        for msg in history[-10:]:  # 最多保留最近 10 轮
            if msg.get("role") in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": message})
    
    payload = {
        "model": model_id,
        "input": {
            "messages": messages
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"阿里云响应：{data}")
            
            # 阿里云返回格式
            if "output" in data and "choices" in data["output"]:
                return data["output"]["choices"][0]["message"]["content"]
            
            # 错误处理
            if "code" in data:
                error_msg = data.get("message", "未知错误")
                logger.error(f"阿里云 API 错误：{data['code']} - {error_msg}")
                raise Exception(f"阿里云 API 错误：{error_msg}")
            
            logger.error(f"未知响应格式：{data}")
            raise Exception(f"API 响应格式异常：{str(data)[:200]}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP 错误：{e.response.status_code} - {e.response.text}")
        raise Exception(f"阿里云 API 调用失败：HTTP {e.response.status_code}")
    except Exception as e:
        logger.error(f"调用失败：{str(e)}")
        raise

@app.get("/")
async def root():
    return FileResponse("templates/index.html")

@app.get("/login")
async def login_page():
    return FileResponse("templates/login.html")

@app.get("/settings")
async def settings_page():
    return FileResponse("templates/settings.html")

@app.get("/profile")
async def profile_page():
    return FileResponse("templates/profile.html")

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
            max_age=86400 * 7  # 7 天有效期
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
            max_age=86400 * 7  # 7 天有效期
        )
        return response

@app.get("/api/me")
async def get_current_user(request: Request):
    if not hasattr(request.state, 'user'):
        return {"authenticated": False}
    return {"authenticated": True, "user": request.state.user}

@app.get("/api/users/{user_id}")
async def get_user_profile(user_id: int, request: Request):
    """获取用户公开资料"""
    conn = sqlite3.connect('chat_history.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, email, bio, avatar_seed, role, created_at 
            FROM users WHERE id = ?
        """, (user_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return {
            "id": row[0],
            "username": row[1],
            "email": row[2][:3] + "***" if row[2] else None,  # 脱敏
            "bio": row[3],
            "avatar_seed": row[4] or row[1],  # 默认用用户名
            "role": row[5],
            "created_at": row[6]
        }
    finally:
        conn.close()

@app.post("/api/profile")
async def update_profile(request: Request):
    """更新个人资料"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(status_code=401, detail="未登录")
    
    from json import loads
    body = await request.body()
    data = loads(body)
    
    email = data.get("email", "")
    bio = data.get("bio", "")
    
    # 验证邮箱格式
    if email and "@" not in email:
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    
    conn = sqlite3.connect('chat_history.db')
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET email = ?, bio = ? WHERE id = ?
        """, (email, bio, request.state.user['id']))
        conn.commit()
        return {"success": True}
    finally:
        conn.close()

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

# 模型配置（参考官方文档）
# 腾讯云：https://cloud.tencent.com/document/product/1729/104753
# 阿里云：https://help.aliyun.com/zh/model-studio/models
AVAILABLE_MODELS = {
    "tencent": [
        {"id": "hunyuan-lite", "name": "hunyuan-lite", "desc": "轻量级，速度快"},
        {"id": "hunyuan-standard", "name": "hunyuan-standard", "desc": "平衡性能与成本"},
        {"id": "hunyuan-standard-256k", "name": "hunyuan-standard-256k", "desc": "支持 256K 超长上下文"},
        {"id": "hunyuan-pro", "name": "hunyuan-pro", "desc": "最强性能"},
        {"id": "hunyuan-turbo", "name": "hunyuan-turbo", "desc": "高性能，适合复杂任务"},
        {"id": "hunyuan-t1-latest", "name": "hunyuan-t1-latest", "desc": "最新一代模型，性能最优"},
        {"id": "hunyuan-t1", "name": "hunyuan-t1", "desc": "深度推理模型"},
        {"id": "hunyuan-large-role-latest", "name": "hunyuan-large-role-latest", "desc": "AI 数字分身、情感陪聊"},
        {"id": "hunyuan-translation", "name": "hunyuan-translation", "desc": "33 种语言互译"},
    ],
    "aliyun": [
        # 旗舰模型
        {"id": "qwen-max", "name": "qwen-max", "desc": "最强性能，适合复杂任务"},
        {"id": "qwen-plus", "name": "qwen-plus", "desc": "效果、速度、成本均衡"},
        {"id": "qwen-flash", "name": "qwen-flash", "desc": "速度快，成本低"},
        {"id": "qwen-coder", "name": "qwen-coder", "desc": "代码专用模型"},
        # 开源版本
        {"id": "qwen3.5", "name": "qwen3.5", "desc": "最新开源版本"},
        {"id": "qwen3", "name": "qwen3", "desc": "开源版本"},
        {"id": "qwen2.5", "name": "qwen2.5", "desc": "经典开源版本"},
        # 视觉模型
        {"id": "qwen-vl-max", "name": "qwen-vl-max", "desc": "视觉理解（最强）"},
        {"id": "qwen-vl-plus", "name": "qwen-vl-plus", "desc": "视觉理解（平衡）"},
        # 语音模型
        {"id": "qwen-audio-turbo", "name": "qwen-audio-turbo", "desc": "语音理解"},
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
    if not provider:
        raise HTTPException(status_code=400, detail="provider 不能为空")
    
    if provider not in ["tencent", "aliyun"]:
        raise HTTPException(status_code=400, detail="不支持的 provider")
    
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    try:
        if api_key is None:
            # 只更新 model_id（切换模型）
            cursor.execute("UPDATE api_keys SET model_id = ? WHERE user_id = ? AND provider = ?", 
                           (model_id, request.state.user['id'], provider))
        else:
            # 验证 API Key 格式（基本检查）
            if len(api_key) < 10:
                raise HTTPException(status_code=400, detail="API Key 格式不正确")
            # 先删除旧的，再插入新的
            cursor.execute("DELETE FROM api_keys WHERE user_id = ? AND provider = ?", (request.state.user['id'], provider))
            cursor.execute("INSERT INTO api_keys (user_id, provider, api_key, model_id) VALUES (?, ?, ?, ?)", 
                           (request.state.user['id'], provider, api_key, model_id))
        conn.commit()
    finally:
        conn.close()
    
    return {"success": True}

@app.delete("/api/keys/{provider}")
async def delete_api_key(provider: str, request: Request):
    """删除指定 provider 的 API Key"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(status_code=401, detail="未登录")
    
    if provider not in ["tencent", "aliyun"]:
        raise HTTPException(status_code=400, detail="不支持的 provider")
    
    conn = sqlite3.connect('chat_history.db')
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM api_keys WHERE user_id = ? AND provider = ?", 
                       (request.state.user['id'], provider))
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
    
    # 计算当前对话轮次
    conn = sqlite3.connect('chat_history.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(round), 0) FROM chat_history WHERE session_id = ?", (session_id,))
        current_round = cursor.fetchone()[0] + 1
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
                tencent_config["model_id"],
                user_id,
                request.history
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
                aliyun_config["model_id"],
                user_id,
                request.history
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
            model_id = keys_map[model_name]["model_id"]
            results.append(ModelResponse(
                model_name=model_name,
                model_id=model_id,
                content=content,
                success=True,
                latency_ms=0  # 将在下面计算
            ))
        except Exception as e:
            model_id = keys_map[model_name]["model_id"] if model_name in keys_map else None
            results.append(ModelResponse(
                model_name=model_name,
                model_id=model_id,
                content="",
                success=False,
                error_message=str(e),
                latency_ms=0
            ))
    
    total_latency = int((time.time() - start_time) * 1000)
    
    # 保存对话历史（一轮对话，包含用户消息和所有模型回复）
    conn = sqlite3.connect('chat_history.db')
    try:
        cursor = conn.cursor()
        # 将模型响应序列化为 JSON
        model_responses_json = json.dumps([
            {
                "model": resp.model_name,
                "model_id": resp.model_id,
                "content": resp.content,
                "success": resp.success,
                "error_message": resp.error_message,
                "latency_ms": resp.latency_ms
            }
            for resp in results
        ], ensure_ascii=False)
        
        cursor.execute(
            "INSERT INTO chat_history (session_id, round, user_id, user_message, model_responses) VALUES (?, ?, ?, ?, ?)",
            (session_id, current_round, user_id, request.user_message, model_responses_json)
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
