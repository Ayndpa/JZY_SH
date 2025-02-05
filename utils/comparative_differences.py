from sqlite import group_member_record as gmr
from typing import List, Dict
from extensions import config

def get_quit_members(current_members_data: Dict[int, Dict]) -> Dict[int, List[int]]:
    """
    计算退群人员
    
    Args:
        current_members_data: 键为群号,值为该群响应数据的字典
    """
    quit_members_dict = {}
    historical_records = gmr.get_latest_member_records()
    
    for group_id in config['group_ids']:
        if group_id not in historical_records:
            quit_members_dict[group_id] = []
            continue
            
        historical_members = set(historical_records[group_id])
        current_members = {member['user_id'] for member in current_members_data[group_id]['data']}
        quit_members = historical_members - current_members
        quit_members_dict[group_id] = list(quit_members)
    
    return quit_members_dict

def get_new_members(current_members_data: Dict[int, Dict]) -> Dict[int, List[int]]:
    """
    计算新入群人员
    
    Args:
        current_members_data: 键为群号,值为该群响应数据的字典
    """
    new_members_dict = {}
    historical_records = gmr.get_latest_member_records()
    
    for group_id in config['group_ids']:
        historical_members = set(historical_records.get(group_id, []))
        current_members = {member['user_id'] for member in current_members_data[group_id]['data']}
        new_members = current_members - historical_members
        new_members_dict[group_id] = list(new_members)
    
    return new_members_dict