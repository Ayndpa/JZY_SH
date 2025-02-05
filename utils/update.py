from sqlite.group_member_record import add_member_record, clear_member_records
from http_requests.get_group_member_list import get_group_member_list
from extensions import config, logger
from utils.comparative_differences import get_quit_members
from sqlite.group_quit_record import add_quit_record

def check_member_changes():
    """检查群成员变动"""
    # 获取所有群的当前成员列表
    current_members_data = {}
    logger.debug(f'Config: {config}')
    for group_id in config['group_ids']:
        current_members_data[group_id] = get_group_member_list(group_id)
    
    # 计算退群
    logger.debug(f'Current members data: {current_members_data}')
    quit_members = get_quit_members(current_members_data)

    # 记录退群者信息
    for group_id, members in quit_members.items():
        for member in members:
            add_quit_record(member['user_id'], group_id, 'leave')

    # 重新构建group_member记录
    clear_member_records()
    logger.debug('Rebuilding group_member_record...')   
    for group_id, group_data in current_members_data.items():
        if group_data['status'] == 'ok' and 'data' in group_data:
            add_member_record(group_id, group_data['data'])