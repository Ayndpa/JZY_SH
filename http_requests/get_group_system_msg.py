import requests
from typing import Dict
from extensions import logger, config

def get_group_system_msg(group_id: int) -> Dict:
    """
    获取群系统消息
    
    Args:
        group_id (int): 群号
        
    Returns:
        dict: API响应结果
    """
    try:
        # 从配置中获取API地址
        api_url = f"{config['forward_api_url']}/get_group_system_msg"
        
        # 构建请求数据
        data = {
            "group_id": group_id
        }
        
        # 发送GET请求
        response = requests.get(api_url, params=data)
        
        # 检查响应状态
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"获取群系统消息失败: {str(e)}")
        return {"status": "failed", "message": str(e)}