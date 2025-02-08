import requests
from typing import Union
from extensions import logger, config

def set_group_ban(group_id: int, user_id: int, duration: int = 1800) -> dict:
    """
    设置群成员禁言
    
    Args:
        group_id (int): 群号
        user_id (int): 要禁言的 QQ 号
        duration (int, optional): 禁言时长，单位为秒，0 表示解除禁言. Defaults to 1800 (30分钟).
        
    Returns:
        dict: API响应结果
    """
    try:
        # 从配置中获取API地址
        api_url = f"{config['forward_api_url']}/set_group_ban"
        
        # 构建请求数据
        data = {
            "group_id": group_id,
            "user_id": user_id,
            "duration": duration
        }
        
        # 发送POST请求
        headers = {'Authorization': 'Bearer ' + config['forward_api_token']}
        response = requests.post(api_url, json=data, headers=headers)
        
        # 检查响应状态
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"设置群禁言失败: {str(e)}")
        return {"status": "failed", "message": str(e)}