from typing import Optional, Set, Dict
from blinker import signal
from http_requests.send_group_msg import send_group_msg
from extensions import config, logger
from llm.deepseek import DeepseekAPI, DeepseekConfig
from http_requests.get_group_member_info import get_group_member_info
from commands.攻击 import execute as attack_execute

# 存储正在被持续攻击的用户
# 格式: {group_id: set(target_ids)}
ongoing_attacks: Dict[int, Set[int]] = {}

def message_received(sender, group_id: int, user_id: int, message: str):
    """处理收到的消息"""
    if group_id in ongoing_attacks and user_id in ongoing_attacks[group_id]:
        # 如果是被攻击目标的消息，执行攻击
        attack_execute([{"type": "at", "data": {"qq": str(user_id)}}], group_id, config['admin_ids'][0])

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    持续攻击命令执行入口
    """
    # 权限检查
    user_info = get_group_member_info(group_id, user_id, no_cache=True)
    if user_info.get("status") == "failed" or (
        user_id not in config['admin_ids'] and 
        user_info.get("data", {}).get("role") not in ["owner", "admin"]
    ):
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 您没有使用此命令的权限"}}
        ]
        send_group_msg(group_id, message)
        return

    # 检查参数
    if not args or len(args) < 1:
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 请指定攻击目标"}}
        ]
        send_group_msg(group_id, message)
        return

    # 提取目标
    if isinstance(args[0], dict) and args[0]["type"] == "at":
        target = int(args[0]["data"]["qq"])
    else:
        raise ValueError("Invalid target format - please use @mention")

    # 添加或移除持续攻击
    if group_id not in ongoing_attacks:
        ongoing_attacks[group_id] = set()

    if target in ongoing_attacks[group_id]:
        # 如果目标已在列表中，则移除
        ongoing_attacks[group_id].remove(target)
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": f" 已停止持续攻击目标"}}
        ]
    else:
        # 添加新目标
        ongoing_attacks[group_id].add(target)
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": f" 已开启持续攻击模式"}}
        ]
        # 执行首次攻击
        attack_execute(args, group_id, user_id)

    send_group_msg(group_id, message)

# 注册消息信号处理器
message_signal = signal('message')
message_signal.connect(message_received)