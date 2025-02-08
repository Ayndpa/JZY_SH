from typing import Optional, List, Dict
from http_requests.send_group_msg import send_group_msg
from http_requests.send_group_forward_msg import send_group_forward_msg
from http_requests.get_group_member_list import get_group_member_list
from http_requests.get_group_member_info import get_group_member_info
from extensions import config

def chunk_members(members: dict, chunk_size: int = 50) -> List[Dict]:
    """将成员信息分片"""
    result = []
    current_chunk = []
    count = 0
    
    for uid, groups in members.items():
        current_chunk.append((uid, groups))
        count += 1
        
        if count >= chunk_size:
            result.append(dict(current_chunk))
            current_chunk = []
            count = 0
            
    if current_chunk:
        result.append(dict(current_chunk))
        
    return result

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    计算同时在多个群的成员
    
    Args:
        args: 命令参数，可选的第一个参数为最少群数
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

    # 解析最少群数参数
    min_groups = None
    if args and len(args) > 0:
        try:
            min_groups = int(args)
            if min_groups < 2:
                message = [
                    {"type": "at", "data": {"qq": str(user_id)}},
                    {"type": "text", "data": {"text": " 最少群数必须大于等于2"}}
                ]
                send_group_msg(group_id, message)
                return
        except ValueError:
            message = [
                {"type": "at", "data": {"qq": str(user_id)}},
                {"type": "text", "data": {"text": " 参数格式错误，请输入有效的数字"}}
            ]
            send_group_msg(group_id, message)
            return
    else:
        min_groups = 2

    # 获取配置中的所有群
    group_ids = config['group_ids']
    
    # 存储每个群的成员
    members_by_group = {}
    # 存储用户出现在哪些群
    user_groups = {}
    
    # 获取所有群的成员列表
    for gid in group_ids:
        response = get_group_member_list(gid)
        if isinstance(response, dict) and 'data' in response:
            members = response['data']
        else:
            members = response
        members_by_group[gid] = members
        
        # 记录每个用户在哪些群出现
        for member in members:
            if isinstance(member, dict):
                user_id = member.get('user_id')
                if user_id:
                    if user_id not in user_groups:
                        user_groups[user_id] = []
                    user_groups[user_id].append(gid)
    
    # 找出在多个群的用户
    if min_groups:
        multi_group_users = {uid: groups for uid, groups in user_groups.items() if len(groups) >= min_groups}
    else:
        multi_group_users = {uid: groups for uid, groups in user_groups.items() if len(groups) > 1}
    
    # 生成消息
    if not multi_group_users:
        min_groups_text = f"至少{min_groups}个" if min_groups else "多个"
        message = [{"type": "text", "data": {"text": f"没有找到同时在{min_groups_text}群的成员"}}]
        send_group_msg(group_id, message)
        return

    # 准备转发消息
    messages = []
    min_groups_text = f"至少{min_groups}个" if min_groups else "多个"
    
    # 添加总览消息
    overview = f"在{min_groups_text}群的成员统计结果（共 {len(multi_group_users)} 人）"
    messages.append({
        "type": "node",
        "data": {
            "name": "群成员统计",
            "uin": str(config.get('bot_id', '0')),
            "content": [{"type": "text", "data": {"text": overview}}]
        }
    })

    # 将用户列表分片处理
    user_items = list(multi_group_users.items())
    for i in range(0, len(user_items), 50):
        chunk = user_items[i:i+50]
        chunk_text = f"第 {i//50 + 1} 页 (用户 {i+1} - {min(i+50, len(user_items))})\n"
        
        # 处理这一批的用户
        for uid, groups in chunk:
            first_group = groups[0]
            user_info = next((m for m in members_by_group[first_group] if isinstance(m, dict) and m.get('user_id') == uid), None)
            nickname = user_info.get('card') or user_info.get('nickname') or str(uid) if user_info else str(uid)
            chunk_text += f"用户 {nickname} ({uid}) 在群: {', '.join(map(str, groups))}\n"
        
        # 添加这一批用户的消息节点
        messages.append({
            "type": "node",
            "data": {
                "name": "群成员统计",
                "uin": str(config.get('bot_id', '0')),
                "content": [{"type": "text", "data": {"text": chunk_text}}]
            }
        })

    # 发送完整的转发消息
    send_group_forward_msg(
        group_id=group_id,
        messages=messages,
        prompt=f"群成员统计结果",
        summary=f"共 {len(multi_group_users)} 人，点击查看详细信息"
    )