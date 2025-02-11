import sqlite3
from datetime import datetime
from typing import List
import os
from functools import wraps

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "group_record.db")

def ensure_db_initialized(func):
    """确保数据库已初始化的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_records (
                qq INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                join_time TIMESTAMP NOT NULL,
                PRIMARY KEY (qq, group_id)
            )
        ''')
        conn.commit()
        conn.close()
        return func(*args, **kwargs)
    return wrapper

@ensure_db_initialized
def add_record(qq: int, group_id: int, join_time: datetime = None):
    """添加一条加群记录"""
    if join_time is None:
        join_time = datetime.now()
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR REPLACE INTO group_records (qq, group_id, join_time) VALUES (?, ?, ?)",
            (qq, group_id, join_time)
        )
        conn.commit()
    finally:
        conn.close()

@ensure_db_initialized
def get_user_join_count(qq: int) -> int:
    """获取用户加群次数"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM group_records WHERE qq = ?", (qq,))
        return cursor.fetchone()[0]
    finally:
        conn.close()