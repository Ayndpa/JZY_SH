import sqlite3
import os
from typing import List, Dict

# 设置默认数据库路径
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "group_member.db")

# 确保数据目录存在
os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)

def init_member_record_table(db_path: str = DEFAULT_DB_PATH):
    """初始化群成员记录表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS group_member_record (
        group_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        PRIMARY KEY (group_id, user_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def _ensure_table_exists(db_path: str = DEFAULT_DB_PATH) -> bool:
    """检查并确保表存在"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT count(*) FROM sqlite_master 
    WHERE type='table' AND name='group_member_record'
    ''')
    
    exists = cursor.fetchone()[0] > 0
    if not exists:
        init_member_record_table(db_path)
    
    conn.close()
    return exists

def add_single_member_record(group_id: int, user_id: int, db_path: str = DEFAULT_DB_PATH):
    """添加单一群成员记录
    
    Args:
        group_id: 群号
        user_id: QQ号
        db_path: 数据库路径
    """
    _ensure_table_exists(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO group_member_record (group_id, user_id)
    VALUES (?, ?)
    ''', (group_id, user_id))
    
    conn.commit()
    conn.close()

def add_member_record(group_id: int, member_list: List[Dict], 
                     db_path: str = DEFAULT_DB_PATH):
    """添加群成员记录"""
    _ensure_table_exists(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for member in member_list:
        cursor.execute('''
        INSERT OR REPLACE INTO group_member_record (group_id, user_id)
        VALUES (?, ?)
        ''', (group_id, member.get('user_id')))
    
    conn.commit()
    conn.close()

def get_latest_member_records(db_path: str = DEFAULT_DB_PATH) -> Dict[int, list]:
    """获取所有群的最新成员记录
    从数据库中获取所有群组的最新成员记录信息。返回一个字典,key为群组ID,value为该群组的成员ID列表。
        db_path (str, optional): SQLite数据库文件路径. 默认为 DEFAULT_DB_PATH.
        Dict[int, list]: 包含所有群组最新成员记录的字典
            - value (list[int]): 群组成员ID列表,每个元素为成员的用户ID
    """
    _ensure_table_exists(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT group_id, user_id
    FROM group_member_record
    ''')
    
    results = {}
    for row in cursor.fetchall():
        group_id, user_id = row
        if group_id not in results:
            results[group_id] = []
        results[group_id].append(user_id)
    
    conn.close()
    return results

def clear_member_records(db_path: str = DEFAULT_DB_PATH):
    """清空群成员记录表
    
    Args:
        db_path: 数据库路径
    """
    _ensure_table_exists(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM group_member_record')
    
    conn.commit()
    conn.close()

def is_member_in_group(user_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """检查指定用户是否在任何一个群中
    
    Args:
        user_id: QQ号
        db_path: 数据库路径
        
    Returns:
        bool: 用户是否在任何群中
    """
    _ensure_table_exists(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 1 FROM group_member_record 
    WHERE user_id = ?
    ''', (user_id,))
    
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def delete_member_record(group_id: int, user_id: int, db_path: str = DEFAULT_DB_PATH):
    """删除指定用户的群成员记录
    
    Args:
        group_id: 群号
        user_id: QQ号
        db_path: 数据库路径
    """
    _ensure_table_exists(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    DELETE FROM group_member_record 
    WHERE group_id = ? AND user_id = ?
    ''', (group_id, user_id))
    
    conn.commit()
    conn.close()