import sqlite3
import time
import os
from typing import Literal, Optional

# 设置默认数据库路径
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "group_quit.db")

# 确保数据目录存在
os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)

def init_quit_record_table(db_path: str = DEFAULT_DB_PATH):
    """初始化退群记录表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS group_quit_record (
        qq_id INTEGER NOT NULL,
        group_id INTEGER NOT NULL,
        quit_time INTEGER NOT NULL,
        quit_type TEXT NOT NULL,
        PRIMARY KEY (qq_id, group_id, quit_time)
    )
    ''')
    
    conn.commit()
    conn.close()

def _ensure_table_exists(db_path: str = DEFAULT_DB_PATH) -> bool:
    """检查并确保表存在"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute('''
    SELECT count(*) FROM sqlite_master 
    WHERE type='table' AND name='group_quit_record'
    ''')
    
    exists = cursor.fetchone()[0] > 0
    if not exists:
        init_quit_record_table(db_path)
    
    conn.close()
    return exists

def add_quit_record(qq_id: int, group_id: int, 
                    quit_type: Literal['kick', 'leave'],
                    db_path: str = DEFAULT_DB_PATH):
    """添加退群记录"""
    _ensure_table_exists(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    current_time = int(time.time())
    cursor.execute('''
    INSERT INTO group_quit_record (qq_id, group_id, quit_time, quit_type)
    VALUES (?, ?, ?, ?)
    ''', (qq_id, group_id, current_time, quit_type))
    
    conn.commit()
    conn.close()

def get_quit_records(qq_id: Optional[int] = None, 
                     db_path: str = DEFAULT_DB_PATH) -> list:
    """查询退群记录"""
    _ensure_table_exists(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = "SELECT * FROM group_quit_record WHERE 1=1"
    params = []
    
    if qq_id is not None:
        query += " AND qq_id = ?"
        params.append(qq_id)
    
    cursor.execute(query, params)
    records = cursor.fetchall()
    
    conn.close()
    return records