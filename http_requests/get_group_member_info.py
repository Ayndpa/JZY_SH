import requests
from typing import Union
from extensions import logger, config

def get_group_member_info(group_id: int, user_id: int, no_cache: bool = False) -> dict:
    """
    获取群成员信息
    
    Args:
        group_id (int): 群号
        user_id (int): QQ号
        no_cache (bool, optional): 是否不使用缓存. Defaults to False.
        
    Returns:
        dict: API响应结果
            {
                "status": str,   # 请求状态
                "retcode": int,  # 响应码
                "data": object,  # 响应数据
                   {
                       "group_id": int,      # 群号
                       "user_id": int,       # QQ号
                       "nickname": str,      # QQ昵称
                       "card": str,          # 群名片
                       "sex": str,           # 性别
                       "age": int,           # 年龄
                       "area": str,          # 地区
                       "level": str,         # 成员等级
                       "qq_level": int,      # QQ等级
                       "join_time": int,     # 加群时间戳
                       "last_sent_time": int,# 最后发言时间戳
                       "title_expire_time": int,  # 专属头衔过期时间戳
                       "unfriendly": bool,   # 是否不良记录成员 
                       "card_changeable": bool,   # 是否允许修改群名片
                       "is_robot": bool,     # 是否机器人
                       "shut_up_timestamp": int,  # 禁言到期时间戳
                       "role": str,          # 角色(owner/admin/member)
                       "title": str          # 专属头衔
                   },
                "message": str,  # 提示信息
                "wording": str,  # 提示信息(人性化)
                "echo": str      # 回显
            }
    """
    try:
        # 从配置中获取API地址
        api_url = f"{config['forward_api_url']}/get_group_member_info"
        
        # 构建请求数据
        data = {
            "group_id": group_id,
            "user_id": user_id,
            "no_cache": no_cache
        }
        
        # 发送POST请求
        response = requests.post(api_url, json=data)
        
        # 检查响应状态
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"获取群成员信息失败: {str(e)}")
        return {"status": "failed", "message": str(e)}