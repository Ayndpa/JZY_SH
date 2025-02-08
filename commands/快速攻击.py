from typing import Optional
from http_requests.send_group_msg import send_group_msg
from extensions import config, logger
from llm.gemini import GeminiAPI, GeminiConfig
from http_requests.get_group_member_info import get_group_member_info
from http_requests.get_group_msg_history import get_user_messages_in_group

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    快速攻击命令执行入口
    
    Args:
        args: 命令参数 (预期包含攻击目标)
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

    # 检查是否提供了攻击目标
    if not args or len(args) < 1:
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 请指定攻击目标"}}
        ]
        send_group_msg(group_id, message)
        return

    # Extract target from message/args
    if isinstance(args[0], dict) and "type" in args[0] and args[0]["type"] == "at":
        target = args[0]["data"]["qq"]
    else:
        raise ValueError("Invalid target format - please use @mention")

    # Get target member info
    target_info = get_group_member_info(group_id, int(target), no_cache=True)
    if target_info.get("status") == "failed":
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 无法获取目标信息"}}
        ]
        send_group_msg(group_id, message)
        return

    target_data = target_info.get("data", {})
    target_name = target_data.get("card") or target_data.get("nickname") or target

    # 发送攻击结果消息
    message = [
        {
            "type": "text",
            "data": {
                "text": f"{user_info.get('data', {}).get('card') or user_info.get('data', {}).get('nickname') or user_id} 对 {target_name} 发起了快速攻击！"
            }
        }
    ]
    send_group_msg(group_id, message)

    # 调用GeminiAPI生成攻击描述
    try:
        gemini_config = GeminiConfig(api_key=config['gemini_api_key'])
        api = GeminiAPI(config=gemini_config)

        prompt = config.get("gemini_attack_prompt", "生成一段针对性的攻击内容，要求言辞尖锐但不过分，结合目标的信息。")
        
        # Include target user info and recent messages in prompt
        prompt = prompt + f"\n\n目标用户信息：{target_data}"
        
        # Get target's recent messages
        recent_msgs = get_user_messages_in_group(group_id, int(target), target_count=10, max_search=50)
        msg_history = "\n\n目标最近的发言："
        for msg in recent_msgs:
            if "message" in msg:
                msg_history += f"\n{msg['message']}"
        prompt = prompt + msg_history

        # Add additional note from arg[1] if provided
        if len(args) > 1:
            prompt = prompt + f"\n\n注意：{args[1]}"

        attack_desc = api.chat(prompt)

        # 发送攻击描述
        follow_message = [
            {"type": "at", "data": {"qq": target}},
            {"type": "text", "data": {"text": attack_desc}}
        ]
        send_group_msg(group_id, follow_message)

    except Exception as e:
        logger.error(f"Error generating attack with Gemini: {e}")
        error_message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 生成攻击内容时发生错误"}}
        ]
        send_group_msg(group_id, error_message)