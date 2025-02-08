import requests
from extensions import logger, config

def set_group_kick(group_id: int, user_id: int, reject_add_request: bool = False) -> dict:
    """
    踢出群成员
    
    Args:
        group_id (int): 群号
        user_id (int): 要踢出的 QQ 号
        reject_add_request (bool, optional): 拒绝此人的加群请求. Defaults to False.
        
    Returns:
        dict: API响应结果
    """
    try:
        # 从配置中获取API地址
        api_url = f"{config['forward_api_url']}/set_group_kick"
        
        # 构建请求数据
        data = {
            "group_id": group_id,
            "user_id": user_id,
            "reject_add_request": reject_add_request
        }
        
        # 发送POST请求
        headers = {'Authorization': 'Bearer ' + config['forward_api_token']}
        response = requests.post(api_url, json=data, headers=headers)
        
        # 检查响应状态
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"踢出群成员失败: {str(e)}")
        return {"status": "failed", "message": str(e)}