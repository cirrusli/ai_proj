"""
安全文件下载配置 - 白名单机制（热加载版本）
每次请求时读取 JSON 配置文件，修改后无需重启服务
"""
import os
import json
from pathlib import Path

# 配置文件路径
CONFIG_FILE = Path(__file__).parent / "files.json"

def load_config() -> dict:
    """
    从 JSON 文件加载配置（每次调用都会重新读取）
    返回格式：{文件名：{path, desc, type}}
    """
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("files", {})
    except Exception as e:
        print(f"⚠️ 加载文件配置失败：{e}")
        return {}

def validate_file_path(filename: str) -> str | None:
    """
    验证文件是否在白名单中
    返回真实路径，如果不在白名单则返回 None
    """
    allowed_files = load_config()
    
    if filename not in allowed_files:
        return None
    
    file_info = allowed_files[filename]
    real_path = file_info.get("path")
    
    if not real_path:
        return None
    
    # 双重验证：文件必须存在且是文件
    if not os.path.isfile(real_path):
        return None
    
    # 安全验证：路径必须在 workspace 内
    if not real_path.startswith("/root/.openclaw/workspace/"):
        return None
    
    return real_path

def get_file_list():
    """
    获取文件列表（用于前端展示）
    每次调用都会重新读取配置文件
    """
    allowed_files = load_config()
    result = []
    
    for name, info in allowed_files.items():
        try:
            size = os.path.getsize(info["path"])
            size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / 1024 / 1024:.1f} MB"
        except:
            size_str = "未知"
        
        result.append({
            "name": name,
            "desc": info.get("desc", ""),
            "size": size_str,
            "type": info.get("type", "application/octet-stream")
        })
    
    return result

def add_file(filename: str, path: str, desc: str, file_type: str = None) -> bool:
    """
    添加文件到白名单（需要手动保存 JSON 文件）
    返回是否成功添加
    """
    # 验证路径安全
    if not path.startswith("/root/.openclaw/workspace/"):
        return False
    
    if not os.path.isfile(path):
        return False
    
    if file_type is None:
        file_type = "application/octet-stream"
    
    allowed_files = load_config()
    allowed_files[filename] = {
        "path": path,
        "desc": desc,
        "type": file_type
    }
    
    # 保存回 JSON 文件
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "description": "文件下载白名单配置 - 修改后无需重启服务",
                "files": allowed_files
            }, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False
