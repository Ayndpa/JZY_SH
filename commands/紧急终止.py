from typing import Optional
from http_requests.send_group_msg import send_group_msg
from http_requests.get_group_member_info import get_group_member_info
from extensions import config
import sys

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    禁止终止命令执行入口
    
    Args:
        args: 命令参数 (不需要)
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

    # Check user permissions
    user_role = user_info.get("data", {}).get("role")
    if user_id not in config['admin_ids'] and user_role not in ["owner", "admin"]:
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 您没有使用此命令的权限"}}
        ]
        send_group_msg(group_id, message)
        return

    # Send confirmation message before termination
    message = [
        {"type": "at", "data": {"qq": str(user_id)}},
        {"type": "text", "data": {"text": " 正在终止进程..."}}
    ]
    send_group_msg(group_id, message)
    
    # Terminate the process
    sys.exit(0)