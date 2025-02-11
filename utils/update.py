from http_requests.get_group_member_list import get_group_member_list
from extensions import config, logger
from http_requests.get_group_system_msg import get_group_system_msg
from events.request import handle_group_request

def process_join_requests():
    """处理待处理的加群请求"""
    logger.info('Processing join requests...')
    
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
    process_join_requests()
    logger.info("Check completed")