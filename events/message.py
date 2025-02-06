from typing import Dict, Any
from extensions import logger
from commands.message_parser import parse_command, process_command

def handle_message(data: Dict[str, Any]) -> None:
    """
    处理消息事件
    
    Args:
        data: 消息事件数据
    """
    try:
        message_type = data.get('message_type')
        if message_type == 'group':
            handle_group_message(data)
        else:
            logger.debug(f'未处理的消息类型: {message_type}')
    except Exception as e:
        logger.error(f'处理消息时发生错误: {str(e)}')

def handle_group_message(data: Dict[str, Any]) -> None:
    """
    处理群消息
    
    Args:
        data: 群消息数据
    """
    message = data.get('message', '')
    group_id = data.get('group_id')
    user_id = data.get('user_id')
    
    logger.debug(f'收到来自群 {group_id} 用户 {user_id} 的消息: {message}')
    
    parse_command(message, group_id, user_id)