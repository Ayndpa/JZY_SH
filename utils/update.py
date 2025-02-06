from sqlite.group_member_record import add_member_record, clear_member_records
from http_requests.get_group_member_list import get_group_member_list
from extensions import config, logger
from utils.comparative_differences import get_quit_members
from sqlite.group_quit_record import add_quit_record
from http_requests.get_group_system_msg import get_group_system_msg
from events.request import handle_group_request

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
            add_quit_record(member, group_id, 'leave')

    # 重新构建group_member记录
    clear_member_records()
    logger.debug('Rebuilding group_member_record...')   
    for group_id, group_data in current_members_data.items():
        if group_data['status'] == 'ok' and 'data' in group_data:
            add_member_record(group_id, group_data['data'])

def process_join_requests():
    """处理待处理的加群请求"""
    logger.debug('Processing join requests...')
    
    # 获取所有群的系统消息
    for group_id in config['group_ids']:
        try:
            response = get_group_system_msg(group_id)
            if response.get('status') != 'ok' or 'data' not in response:
                continue
                
            # 处理未处理的加群请求
            join_requests = response['data'].get('join_requests', [])
            for request in join_requests:
                if not request.get('checked'):
                    request_data = {
                        'sub_type': 'add',
                        'group_id': request['group_id'],
                        'user_id': request['invitor_uin'],
                        'comment': request.get('message', ''),
                        'flag': str(request['request_id'])
                    }
                    handle_group_request(request_data)
                    
        except Exception as e:
            logger.error(f'Error processing join requests for group {group_id}: {e}')

def do_check():
    """执行检查"""
    check_member_changes()
    process_join_requests()
    logger.info("Check completed")