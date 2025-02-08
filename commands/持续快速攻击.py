from typing import Optional, Set, Dict
from blinker import signal
from http_requests.send_group_msg import send_group_msg
from extensions import config
from http_requests.get_group_member_info import get_group_member_info

from commands.快速攻击 import execute as quick_attack_execute

# Store users being continuously attacked
# Format: {group_id: set(target_ids)}
ongoing_quick_attacks: Dict[int, Set[int]] = {}

def message_received(sender, group_id: int, user_id: int, message: str):
    """Handle received messages"""
    if group_id in ongoing_quick_attacks and user_id in ongoing_quick_attacks[group_id]:
        # If message is from attack target, execute quick attack
        quick_attack_execute([{"type": "at", "data": {"qq": str(user_id)}}], group_id, config['admin_ids'][0])

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    Continuous Quick Attack command entry point
    """
    # Check permissions
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

    # Check arguments
    if not args or len(args) < 1:
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 请指定攻击目标"}}
        ]
        send_group_msg(group_id, message)
        return

    # Extract target
    if isinstance(args[0], dict) and args[0]["type"] == "at":
        target = int(args[0]["data"]["qq"])
    else:
        raise ValueError("Invalid target format - please use @mention")

    # Add or remove continuous attack
    if group_id not in ongoing_quick_attacks:
        ongoing_quick_attacks[group_id] = set()

    message = None
    should_attack = False

    if target in ongoing_quick_attacks[group_id]:
        # Remove target if already in list
        ongoing_quick_attacks[group_id].remove(target)
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": f" 已停止持续快速攻击目标"}}
        ]
    else:
        # Add new target
        ongoing_quick_attacks[group_id].add(target)
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": f" 已开启持续快速攻击模式"}}
        ]
        should_attack = True

    # Send status message
    send_group_msg(group_id, message)
    
    # Execute first attack for new target
    if should_attack:
        quick_attack_execute(args, group_id, user_id)

# Register message signal handler
message_signal = signal('message')
message_signal.connect(message_received)