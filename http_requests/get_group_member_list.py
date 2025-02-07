import requests
from typing import List
from extensions import config, logger

def get_group_member_list(group_id: int) -> List[dict]:
    """
    获取群成员列表
    
    Args:
        group_id (int): 群号
        
    Returns:
        List[dict]: 群成员列表
        
        Returns dictionary with fields:
        - group_id (int): Group number
        - user_id (int): QQ number  
        - nickname (str): Nickname
        - card (str): Group card/note
        - sex (str): Gender (male/female/unknown)
        - age (int): Age
        - area (str): Location
        - join_time (int): Join timestamp 
        - last_sent_time (int): Last message timestamp
        - level (str): Member level
        - role (str): Role (owner/admin/member)
        - unfriendly (bool): If member has bad record
        - title (str): Special title
        - title_expire_time (int): Title expiration timestamp 
        - card_changeable (bool): If card can be modified
    """
    try:
        api_url = f"{config['forward_api_url']}/get_group_member_list"
        
        params = {
            "group_id": group_id,
            "no_cache": True
        }
        
        headers = {
            "Authorization": f"Bearer {config['forward_api_token']}"
        }
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"获取群成员列表失败: {str(e)}")
        return {"status": "failed", "message": str(e)}