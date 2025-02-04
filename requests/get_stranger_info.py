import requests
from app import config, logger

def get_stranger_info(user_id: int, no_cache: bool = False) -> dict:
    """
    获取陌生人信息
    
    Args:
        user_id (int): QQ号
        no_cache (bool, optional): 是否不使用缓存. Defaults to False.
        
    Returns:
        dict: 包含陌生人信息的字典，包括以下字段:
            - user_id (int): QQ号
            - nickname (str): 昵称
            - sex (str): 性别 (male/female/unknown)
            - age (int): 年龄
            - qid (str): qid ID身份卡
            - level (int): 等级
            - login_days (int): 登录天数
    """
    try:
        # 从配置中获取API地址
        api_url = f"{config['forward_api_url']}/get_stranger_info"
        
        # 构建请求数据
        params = {
            "user_id": user_id,
            "no_cache": no_cache
        }
        
        # 发送GET请求
        response = requests.get(api_url, params=params)
        
        # 检查响应状态
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"获取陌生人信息失败: {str(e)}")
        return {"status": "failed", "message": str(e)}