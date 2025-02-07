import requests
from typing import Union
from extensions import logger, config

def send_group_msg(group_id: int, message: Union[str, dict], auto_escape: bool = False) -> dict:
    """
    发送群消息
    
    Args:
        group_id (int): 群号
        message (Union[str, dict]): 要发送的消息内容
        auto_escape (bool, optional): 消息内容是否作为纯文本发送. Defaults to False.
        
    Returns:
        dict: API响应结果
    """
    try:
        # 从配置中获取API地址
        api_url = f"{config['forward_api_url']}/send_group_msg"
        
        # 构建请求数据
        data = {
            "group_id": group_id,
            "message": message,
            "auto_escape": auto_escape
        }
        
        # 发送POST请求
        headers = {'Authorization': 'Bearer ' + config['forward_api_token']}
        response = requests.post(api_url, json=data, headers=headers)
        
        # 检查响应状态
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"发送群消息失败: {str(e)}")
        return {"status": "failed", "message": str(e)}