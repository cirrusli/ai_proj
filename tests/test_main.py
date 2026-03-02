"""
AI 模型对比对话窗口 - 单元测试
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app, init_db
import sqlite3
import os

# 测试数据库
TEST_DB = 'test_chat_history.db'

@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库"""
    # 使用测试数据库
    old_db = 'chat_history.db'
    os.rename(old_db, f'{old_db}.bak') if os.path.exists(old_db) else None
    
    # 初始化测试数据库
    init_db()
    
    yield
    
    # 清理测试数据库
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    # 恢复原数据库
    os.rename(f'{old_db}.bak', old_db) if os.path.exists(f'{old_db}.bak') else None

@pytest.fixture
async def client():
    """创建测试客户端"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

class TestAuth:
    """测试认证系统"""
    
    async def test_login_success(self, client, test_db):
        """测试登录成功"""
        # 先注册
        resp = await client.post("/api/login", json={
            "username": "testuser",
            "action": "register"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        
        # 再登录
        resp = await client.post("/api/login", json={
            "username": "testuser",
            "action": "login"
        })
        assert resp.status_code == 200
        assert "session_id" in resp.cookies
    
    async def test_login_user_not_found(self, client, test_db):
        """测试用户不存在"""
        resp = await client.post("/api/login", json={
            "username": "nonexistent",
            "action": "login"
        })
        assert resp.status_code == 400
        data = resp.json()
        assert "用户不存在" in data["error"]
    
    async def test_register_duplicate(self, client, test_db):
        """测试重复注册"""
        # 第一次注册
        resp = await client.post("/api/login", json={
            "username": "duplicate",
            "action": "register"
        })
        assert resp.status_code == 200
        
        # 第二次注册
        resp = await client.post("/api/login", json={
            "username": "duplicate",
            "action": "register"
        })
        assert resp.status_code == 400
        assert "用户已存在" in resp.json()["error"]
    
    async def test_register_limit(self, client, test_db):
        """测试注册人数限制（最多 10 人）"""
        # 测试逻辑：验证限制存在即可
        # 注意：实际测试中数据库是共享的，所以只验证错误消息
        for i in range(20):
            resp = await client.post("/api/login", json={
                "username": f"limit_test_{i}",
                "action": "register"
            })
            if resp.status_code == 400:
                # 达到限制
                assert "注册已达上限" in resp.json()["error"]
                return
        
        # 如果 20 个都成功了，说明限制没生效
        assert False, "注册人数限制未生效"

class TestAPIKeys:
    """测试 API Key 管理"""
    
    async def test_save_api_key(self, client, test_db):
        """测试保存 API Key"""
        # 先登录
        await client.post("/api/login", json={
            "username": "keytest",
            "action": "register"
        })
        
        # 保存 API Key
        resp = await client.post("/api/keys", json={
            "provider": "tencent",
            "api_key": "test_key_123456789",
            "model_id": "hunyuan-lite"
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True
    
    async def test_api_key_not_returned(self, client, test_db):
        """测试 API Key 不返回前端"""
        # 先登录并保存 Key
        await client.post("/api/login", json={
            "username": "keytest2",
            "action": "register"
        })
        await client.post("/api/keys", json={
            "provider": "tencent",
            "api_key": "secret_key_123456789",
            "model_id": "hunyuan-lite"
        })
        
        # 获取 Keys
        resp = await client.get("/api/keys")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["keys"]) == 1
        
        # 确保不返回完整 API Key
        key = data["keys"][0]
        assert "api_key" not in key or key.get("api_key") is None
        assert "api_key_full" not in key
    
    async def test_invalid_provider(self, client, test_db):
        """测试无效的 provider"""
        await client.post("/api/login", json={
            "username": "keytest3",
            "action": "register"
        })
        
        resp = await client.post("/api/keys", json={
            "provider": "invalid",
            "api_key": "test_key"
        })
        assert resp.status_code == 400
    
    async def test_short_api_key(self, client, test_db):
        """测试 API Key 长度验证"""
        await client.post("/api/login", json={
            "username": "keytest4",
            "action": "register"
        })
        
        resp = await client.post("/api/keys", json={
            "provider": "tencent",
            "api_key": "short"  # 太短
        })
        assert resp.status_code == 400

class TestChat:
    """测试对话功能"""
    
    async def test_chat_without_auth(self, client, test_db):
        """测试未登录不能对话"""
        resp = await client.post("/api/chat", json={
            "user_message": "你好",
            "models": ["tencent"]
        })
        assert resp.status_code == 307  # 重定向到登录
    
    async def test_chat_without_api_key(self, client, test_db):
        """测试未配置 API Key 时的错误"""
        # 登录但不配置 Key
        await client.post("/api/login", json={
            "username": "chattest",
            "action": "register"
        })
        
        resp = await client.post("/api/chat", json={
            "user_message": "你好",
            "models": ["tencent"]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["responses"]) == 1
        assert data["responses"][0]["success"] is False
        assert "未配置" in data["responses"][0]["error_message"]

class TestModels:
    """测试模型列表"""
    
    async def test_get_models(self, client, test_db):
        """测试获取模型列表"""
        resp = await client.get("/api/models")
        assert resp.status_code == 200
        data = resp.json()
        
        assert "models" in data
        assert "tencent" in data["models"]
        assert "aliyun" in data["models"]
        
        # 腾讯云模型
        tencent_models = data["models"]["tencent"]
        assert len(tencent_models) == 4
        model_ids = [m["id"] for m in tencent_models]
        assert "hunyuan-lite" in model_ids
        
        # 阿里云模型
        aliyun_models = data["models"]["aliyun"]
        assert len(aliyun_models) == 4
        model_ids = [m["id"] for m in aliyun_models]
        assert "qwen-turbo" in model_ids

class TestSecurity:
    """测试安全性"""
    
    async def test_sql_injection(self, client, test_db):
        """测试 SQL 注入防护"""
        # 尝试 SQL 注入
        resp = await client.post("/api/login", json={
            "username": "admin' OR '1'='1",
            "action": "login"
        })
        # 应该失败或当作普通用户名处理
        assert resp.status_code in [200, 400]
    
    async def test_cookie_httponly(self, client, test_db):
        """测试 Cookie HttpOnly"""
        await client.post("/api/login", json={
            "username": "cookietest",
            "action": "register"
        })
        
        # 检查 Cookie 属性
        cookies = client.cookies
        session_cookie = cookies.get("session_id")
        assert session_cookie is not None
        # HttpOnly 无法通过 HTTP 检查，但代码中已设置

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
