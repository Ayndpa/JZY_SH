import asyncio
from typing import Optional
from http_requests.send_group_msg import send_group_msg
from extensions import config, logger
from llm.deepseek import DeepseekAPI, DeepseekConfig
from http_requests.get_group_member_info import get_group_member_info
from http_requests.get_group_msg_history import get_user_messages_in_group
import random

async def process_attack(api, prompt, group_id, target):
    """处理攻击响应"""
    response_gen = await api.achat(prompt)
    async for sentence in response_gen:
        # Randomly decide @ position (0: no @, 1: start, 2: end) with bias towards no @
        at_position = random.choices([0, 1, 2], weights=[0.7, 0.15, 0.15])[0]
        
        if at_position == 0:
            follow_message = [
            {"type": "text", "data": {"text": sentence}}
            ]
        elif at_position == 1:
            follow_message = [
            {"type": "at", "data": {"qq": target}},
            {"type": "text", "data": {"text": sentence}}
            ]
        else:  # at_position == 2
            follow_message = [
            {"type": "text", "data": {"text": sentence}},
            {"type": "at", "data": {"qq": target}}
            ]

        send_group_msg(group_id, follow_message)
        # 添加短暂延迟，避免消息发送过快
        await asyncio.sleep(0.5)

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    攻击命令执行入口
    
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
            {
                "type": "at",
                "data": {
                    "qq": str(user_id)
                }
            },
            {
                "type": "text",
                "data": {
                    "text": " 请指定攻击目标"
                }
            }
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
            {
                "type": "at", 
                "data": {"qq": str(user_id)}
            },
            {
                "type": "text",
                "data": {"text": " 无法获取目标信息"}
            }
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
                "text": f"{user_info.get('data', {}).get('card') or user_info.get('data', {}).get('nickname') or user_id} 对 {target_name} 发起了攻击！"
            }
        }
    ]
    send_group_msg(group_id, message)

    # 修改DeepseekAPI初始化，启用流式输出
    deepseek_config = DeepseekConfig(
        api_key=config['deepseek_api_key'],
        endpoint=config['deepseek_endpoint'],
        stream=True  # 启用流式输出
    )
    api = DeepseekAPI(config=deepseek_config)

    prompt = config.get("deepseek_attack_prompt", "In every output, response using the following format:\n<think>\n{reasoning_content}\n</think>\n\n{content}\n\n结合对方的信息和聊天记录，尽可能粗暴地辱骂对方，注意言辞不要太高级，尽可能通俗易懂。")
    # Include target user info in prompt
    prompt = prompt + f"\n```目标用户信息（注意，只做参考，重点攻击最近发言）：{target_data}```"

    # Get target's recent messages
    recent_msgs = get_user_messages_in_group(group_id, int(target), target_count=20, max_search=100)
    msg_history = "\n\n```最近的发言："
    for msg in recent_msgs:
        if "message" in msg:
            msg_history += f"\n{msg['message']}"
    msg_history += "\n```"
    prompt = prompt + msg_history
    # Add additional note from arg[1] if provided
    if len(args) > 1:
        prompt = prompt + f"\n\n注意：{args[1]}"

    # 替换原有的直接调用为异步处理
    asyncio.run(process_attack(api, prompt, group_id, target))