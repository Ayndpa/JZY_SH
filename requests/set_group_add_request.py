import requests
from typing import Optional
from app import config, logger

def set_group_add_request(
    flag: str,
    sub_type: str,
    approve: bool = True,
    reason: Optional[str] = None
) -> dict:
    """
    处理加群请求/邀请
    
    Args:
        flag (str): 加群请求的flag（需从上报的数据中获得）
        sub_type (str): 请求类型（add或invite，需要和上报消息中的sub_type字段相符）
        approve (bool, optional): 是否同意请求/邀请. Defaults to True.
        reason (Optional[str], optional): 拒绝理由（仅在拒绝时有效）. Defaults to None.
        
    Returns:
        dict: API响应结果
    """
    try:
        # 从配置中获取API地址
        api_url = f"{config['forward_api_url']}/set_group_add_request"
        
        # 构建请求数据
        data = {
            "flag": flag,
            "sub_type": sub_type,
            "approve": approve
        }
        
        # 仅在拒绝且提供理由时添加reason字段
        if not approve and reason:
            data["reason"] = reason
            
        # 发送POST请求
        response = requests.post(api_url, json=data)
        
        # 检查响应状态
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"处理加群请求失败: {str(e)}")
        return {"status": "failed", "message": str(e)}