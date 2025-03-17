from typing import Optional
from extensions import logger, config
from http_requests.send_group_msg import send_group_msg
from http_requests.get_group_member_info import get_group_member_info
from sqlite import group_record
from datetime import datetime
from http_requests.set_group_kick import set_group_kick

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    永久踢出命令执行入口
    
    Args:
        args: 命令参数 (需要被踢出用户的QQ号)
        group_id: 群组ID
        user_id: 执行命令的用户ID
    """
    # 检查是否有权限执行此命令
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

    # 检查参数
    if not args or len(args) != 1:
        send_group_msg(group_id, "用法: 永久踢出 @用户")
        return

    try:
        # 解析目标用户ID
        target_id = int(args[0]['data']['qq']) if isinstance(args[0], dict) else int(args[0].strip())
        
        # 获取最大允许加群次数
        max_joins = config.get('max_joins', 2)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 写入多次加群记录以超过限制
        for _ in range(max_joins + 1):
            group_record.add_record(target_id, group_id, current_time)

        # 踢出用户
        kick_result = set_group_kick(group_id, target_id)
        if kick_result.get("status") == "ok":
            send_group_msg(group_id, f"已将用户 {target_id} 踢出并加入永久黑名单")
        else:
            send_group_msg(group_id, f"已将用户 {target_id} 加入永久黑名单，但踢出失败")
            
        logger.info(f"User {target_id} has been permanently banned from joining by admin {user_id}")

    except ValueError:
        send_group_msg(group_id, "无效的用户ID")
    except Exception as e:
        logger.error(f"Error in permanent ban command: {str(e)}")
        send_group_msg(group_id, "执行命令时发生错误")