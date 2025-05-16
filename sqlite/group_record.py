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
        # Check if table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='group_records'")
        if not cursor.fetchone():
            cursor.execute('''
            CREATE TABLE group_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                qq INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                join_time TIMESTAMP NOT NULL
            )
            ''')
            # Create an index for faster queries
            cursor.execute("CREATE INDEX idx_qq_group ON group_records(qq, group_id)")
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

@ensure_db_initialized
def clear_user_records(qq: int) -> int:
    """清空用户的所有加群记录，返回被删除的记录数"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM group_records WHERE qq = ?", (qq,))
        deleted_count = cursor.rowcount
        conn.commit()
        return deleted_count
    finally:
        conn.close()