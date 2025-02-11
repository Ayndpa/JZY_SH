from enum import Enum
from typing import Dict, Any, Optional
from .notice import handle_group_increase
from .request import handle_group_request
from .message import handle_message
from extensions import config, logger

class PostType(Enum):
    NOTICE = "notice"
    REQUEST = "request"
    MESSAGE = "message"

class NoticeType(Enum):
    GROUP_INCREASE = "group_increase"

def validate_group(group_id: Optional[int]) -> bool:
    """验证群组ID是否合法"""
    return bool(group_id in config.get('group_ids', {}) or group_id == config.get('admin_group_id'))

def handle_event(data: Dict[str, Any]) -> None:
    """
    处理OneBot事件
    
    Args:
        data: 从POST请求接收的JSON数据
    """
    try:
        group_id = data.get('group_id')
        
        if not validate_group(group_id):
            logger.debug(f'机器人不在群组 {group_id} 中')
            return
        
        post_type = data.get('post_type')
        if not post_type:
            logger.debug('收到无效事件类型')
            return

        if post_type == PostType.NOTICE.value:
            handle_notice_event(data)
        elif post_type == PostType.REQUEST.value:
            handle_request_event(data)
        elif post_type == PostType.MESSAGE.value:
            handle_message(data)
        else:
            logger.debug(f'未处理的事件类型: {post_type}')

    except Exception as e:
        logger.error(f'处理事件时发生错误: {str(e)}')

def handle_notice_event(data: Dict[str, Any]) -> None:
    """处理通知类型事件"""
    notice_type = data.get('notice_type')
    if notice_type == NoticeType.GROUP_INCREASE.value:
        handle_group_increase(data)

def handle_request_event(data: Dict[str, Any]) -> None:
    """处理请求类型事件"""
    request_type = data.get('request_type')
    if request_type == 'group':
        handle_group_request(data)