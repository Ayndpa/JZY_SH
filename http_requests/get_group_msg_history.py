import requests
from typing import Optional
from extensions import logger, config

def get_group_msg_history(
    group_id: int,
    message_seq: int = 0,
    count: int = 20,
    reverse_order: bool = False
) -> dict:
    """
    获取群消息历史记录
    
    Args:
        group_id (int): 群号
        message_seq (int): 消息序号. Defaults to 0.
        count (int, optional): 获取数量. Defaults to 20.
        reverse_order (bool, optional): 是否倒序. Defaults to False.
        
    Returns:
        dict: API响应结果，包含状态、返回码、数据等信息
    """
    try:
        # 从配置中获取API地址
        api_url = f"{config['forward_api_url']}/get_group_msg_history"
        
        # 构建请求数据
        data = {
            "group_id": group_id,
            "message_seq": message_seq,
            "count": count,
            "reverseOrder": reverse_order
        }
        
        # 发送POST请求
        headers = {'Authorization': 'Bearer ' + config['forward_api_token']}
        response = requests.post(api_url, json=data, headers=headers)
        
        # 检查响应状态
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"获取群消息历史记录失败: {str(e)}")
        return {
            "status": "failed",
            "retcode": -1,
            "data": None,
            "message": str(e),
            "wording": "获取群消息历史记录失败",
            "echo": ""
        }
    
def get_user_messages_in_group(
    group_id: int,
    user_id: int,
    message_seq: int = 0,
    target_count: int = 20,
    max_search: int = 100
) -> list:
    """
    获取群聊中指定用户的消息记录
    
    Args:
        group_id (int): 群号
        user_id (int): 用户QQ号
        message_seq (int): 起始消息序号. Defaults to 0.
        target_count (int, optional): 需要获取的目标消息数量. Defaults to 20.
        max_search (int, optional): 最大搜索消息数量. Defaults to 100.
        
    Returns:
        list: 指定用户的消息列表
    """
    user_messages = []
    current_seq = message_seq
    
    while len(user_messages) < target_count:
        response = get_group_msg_history(group_id, current_seq)
        
        if response.get("status") != "ok" or not response.get("data", {}).get("messages"):
            break
            
        messages = response["data"]["messages"]
        for msg in messages:
            if msg.get("sender", {}).get("user_id") == user_id:
                user_messages.append(msg)
                if len(user_messages) >= target_count:
                    break
                    
        if len(messages) < 20 or len(user_messages) >= max_search:
            break
            
        current_seq = messages[-1].get("message_seq", 0)
        
    return user_messages[:target_count]