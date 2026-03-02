"""
数据库迁移脚本 - 添加 chat_history 表
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    # 创建新的对话历史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            round INTEGER,
            user_id INTEGER,
            user_message TEXT,
            model_responses TEXT,
            timestamp DATETIME DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 检查是否需要添加 round 列（如果表已存在）
    try:
        cursor.execute("ALTER TABLE chat_history ADD COLUMN round INTEGER")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE chat_history ADD COLUMN model_responses TEXT")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()
    print("✅ 数据库迁移完成：chat_history 表已创建")

if __name__ == "__main__":
    migrate()
