from typing import Optional
from http_requests.send_group_msg import send_group_msg
from extensions import config
from http_requests.get_group_member_info import get_group_member_info
from sqlite.group_record import clear_user_records, get_user_join_count

# filepath: d:\AuroraProjects\Python\JZY_SH\commands\清空次数.py

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    清空加群次数命令执行入口
    
    Args:
        args: 命令参数 (预期包含要清空记录的QQ号)
        group_id: 群组ID
        user_id: 执行命令的用户ID
    """
    # Get user's info and check if they are admin
    user_info = get_group_member_info(group_id, user_id, no_cache=True)
    if user_info.get("status") == "failed":
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 无法获取您的权限信息"}}
        ]
        send_group_msg(group_id, message)
        return

    # 统一检查用户权限
    user_role = user_info.get("data", {}).get("role")
    if user_id not in config['admin_ids'] and user_role not in ["owner", "admin"]:
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 您没有使用此命令的权限"}}
        ]
        send_group_msg(group_id, message)
        return

    # 检查是否提供了QQ号
    if not args or len(args) < 1:
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 请提供要清空加群次数的QQ号"}}
        ]
        send_group_msg(group_id, message)
        return

    # 获取目标QQ号
    try:
        target_qq = int(args[0])
    except ValueError:
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " QQ号必须是数字"}}
        ]
        send_group_msg(group_id, message)
        return

    # 获取当前加群次数
    current_count = get_user_join_count(target_qq)
    
    # 清空加群记录
    deleted_count = clear_user_records(target_qq)
    
    # 发送操作结果
    message = [
        {"type": "at", "data": {"qq": str(user_id)}},
        {"type": "text", "data": {"text": f" 已清空QQ {target_qq} 的加群记录，共删除 {deleted_count} 条记录（原加群次数: {current_count}）"}}
    ]
    send_group_msg(group_id, message)