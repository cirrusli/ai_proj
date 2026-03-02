"""
数据库迁移脚本 - 优化表结构
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    print("📊 当前数据统计...")
    
    # 检查冗余表
    cursor.execute("SELECT COUNT(*) FROM messages")
    msg_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM responses")
    resp_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM chat_history")
    history_count = cursor.fetchone()[0]
    
    print(f"  messages 表：{msg_count} 条")
    print(f"  responses 表：{resp_count} 条")
    print(f"  chat_history 表：{history_count} 条")
    
    # 删除冗余表（数据已在 chat_history 中）
    if msg_count == 0 and resp_count == 0:
        print("\n✅ 删除冗余表...")
        cursor.execute("DROP TABLE IF EXISTS messages")
        cursor.execute("DROP TABLE IF EXISTS responses")
        print("  已删除 messages 表")
        print("  已删除 responses 表")
    
    # 添加索引优化查询
    print("\n📈 添加索引优化查询...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_user ON chat_history(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_session ON chat_history(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history(timestamp)")
    print("  已添加 user_id 索引")
    print("  已添加 session_id 索引")
    print("  已添加 timestamp 索引")
    
    # 添加模型使用统计视图
    print("\n📊 创建统计视图...")
    cursor.execute("DROP VIEW IF EXISTS user_model_stats")
    cursor.execute("""
        CREATE VIEW user_model_stats AS
        SELECT 
            u.id as user_id,
            u.username,
            COUNT(DISTINCT ch.session_id) as total_sessions,
            COUNT(ch.id) as total_rounds,
            COUNT(ch.id) as total_messages,
            MIN(ch.timestamp) as first_message_at,
            MAX(ch.timestamp) as last_message_at
        FROM users u
        LEFT JOIN chat_history ch ON u.id = ch.user_id
        GROUP BY u.id, u.username
    """)
    print("  已创建 user_model_stats 视图")
    
    # 模型使用详情视图
    cursor.execute("DROP VIEW IF EXISTS model_usage_stats")
    cursor.execute("""
        CREATE VIEW model_usage_stats AS
        SELECT 
            ch.user_id,
            json_extract(json_each.value, '$.model') as model_name,
            json_extract(json_each.value, '$.model_id') as model_id,
            COUNT(*) as usage_count,
            AVG(json_extract(json_each.value, '$.latency_ms')) as avg_latency_ms
        FROM chat_history ch, json_each(ch.model_responses)
        GROUP BY ch.user_id, json_extract(json_each.value, '$.model'), json_extract(json_each.value, '$.model_id')
    """)
    print("  已创建 model_usage_stats 视图")
    
    conn.commit()
    conn.close()
    
    print("\n✅ 迁移完成！")

if __name__ == "__main__":
    migrate()
