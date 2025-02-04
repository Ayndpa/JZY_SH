from enum import Enum
from typing import Dict, Any, Optional
from app import config, logger
from .notice import handle_group_decrease, handle_group_increase
from .request import handle_group_request

class PostType(Enum):
    NOTICE = "notice"
    REQUEST = "request"
    MESSAGE = "message"

class NoticeType(Enum):
    GROUP_DECREASE = "group_decrease"
    GROUP_INCREASE = "group_increase"

def validate_group(group_id: Optional[int]) -> bool:
    """验证群组ID是否合法"""
    return bool(group_id and str(group_id) in config.get('groups', {}))

def handle_event(data: Dict[str, Any]) -> None:
    """
    处理OneBot事件
    
    Args:
        data: 从POST请求接收的JSON数据
    """
    try:
        group_id = data.get('group_id')
        if not validate_group(group_id):
            logger.debug(f'收到未授权群组的事件: {group_id}')
            return

        post_type = data.get('post_type')
        if not post_type:
            logger.warning('收到无效事件类型')
            return

        if post_type == PostType.NOTICE.value:
            handle_notice_event(data)
        elif post_type == PostType.REQUEST.value:
            handle_request_event(data)
        else:
            logger.debug(f'未处理的事件类型: {post_type}')

    except Exception as e:
        logger.error(f'处理事件时发生错误: {str(e)}')

def handle_notice_event(data: Dict[str, Any]) -> None:
    """处理通知类型事件"""
    notice_type = data.get('notice_type')
    if notice_type == NoticeType.GROUP_DECREASE.value:
        handle_group_decrease(data)
    elif notice_type == NoticeType.GROUP_INCREASE.value:
        handle_group_increase(data)

def handle_request_event(data: Dict[str, Any]) -> None:
    """处理请求类型事件"""
    request_type = data.get('request_type')
    if request_type == 'group':
        handle_group_request(data)