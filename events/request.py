from typing import Dict, Any, Optional, TypedDict
from functools import wraps
from extensions import logger, config
from http_requests.send_group_msg import send_group_msg
from http_requests.set_group_add_request import set_group_add_request
from llm.audit import AuditService
from http_requests.get_stranger_info import get_stranger_info
from sqlite.group_member_record import get_latest_member_records
from sqlite.group_quit_record import get_quit_records
from enum import Enum

class RequestData(TypedDict):
    sub_type: str
    group_id: int
    user_id: int
    comment: str
    flag: str

def handle_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
    return wrapper

@handle_error
def handle_group_request(data: Dict[str, Any]) -> None:
    request_data = RequestData(
        sub_type=data.get('sub_type', ''),
        group_id=data.get('group_id', 0),
        user_id=data.get('user_id', 0),
        comment=data.get('comment', ''),
        flag=data.get('flag', '')
    )

    if not all([request_data['group_id'], request_data['user_id']]):
        logger.error("Invalid request data: missing required fields")
        return

    _log_request(request_data)
    
    if request_data['sub_type'] != 'add':
        return

    if not request_data['comment']:
        _notify_admin(request_data)
        return

    if not check_level_requirements(request_data['user_id']):
        _reject_request(request_data, "等级过低")
        return
    
    if not check_other_groups(request_data['user_id']):
        _reject_request(request_data, "已在其他群")
        return
    
    passed, reason = check_quit_history(request_data['user_id'])
    if not passed:
        _reject_request(request_data, reason)
        return

    process_request(request_data)

@handle_error
def check_other_groups(user_id: int) -> bool:
    """Check if user is in other groups"""
    try:
        group_records = get_latest_member_records()
        for members in group_records.values():
            if user_id in members:
                return False
        return True
    except Exception as e:
        logger.error(f"Error checking group history: {e}")
        return True
    
class RejectReason(Enum):
    KICK_LIMIT = "被踢次数过多"
    LEAVE_LIMIT = "主动退群次数过多"

@handle_error
def check_quit_history(user_id: int) -> tuple[bool, Optional[str]]:
    """Check if user has previously quit the group"""
    
    quit_records = get_quit_records(user_id)
    if not quit_records:
        return True, None
        
    # Check for kicks vs voluntary leaves
    for record in quit_records:
        quit_type = record[3]  # quit_type is the 4th column
        if quit_type == 'kick':
            kick_count = sum(1 for r in quit_records if r[3] == 'kick')
            if kick_count >= config.get('max_kick_count', 2):
                return False, RejectReason.KICK_LIMIT.value
        else:  # voluntary leave
            leave_count = sum(1 for r in quit_records if r[3] == 'leave')
            if leave_count >= config.get('max_leave_count', 1):
                return False, RejectReason.LEAVE_LIMIT.value
    return True, None

def _log_request(data: RequestData) -> None:
    if data['sub_type'] == 'add':
        logger.info(
            f"Join request | Group: {data['group_id']} | "
            f"User: {data['user_id']} | Comment: {data['comment']}"
        )
    elif data['sub_type'] == 'invite':
        logger.info(
            f"Invite request | Group: {data['group_id']} | "
            f"User: {data['user_id']}"
        )

def _notify_admin(data: RequestData) -> None:
    admin_group = config.get('admin_group_id')
    msg = (
        f"加群留言为空，需要人工审核\n"
        f"群号: {data['group_id']}\n"
        f"用户: {data['user_id']}"
    )
    send_group_msg(admin_group, msg)

def _reject_request(data: RequestData, reason: str) -> None:
    set_group_add_request(data['flag'], data['sub_type'], approve=False, reason=reason)
    logger.info(
        f"Rejected join request | Group: {data['group_id']} | "
        f"User: {data['user_id']} | Reason: {reason}"
    )

@handle_error
def check_level_requirements(user_id: int) -> bool:
    if not config.get('enable_level_check', False):
        return True
        
    min_level = config.get('min_join_level', 0)
    user_info = get_stranger_info(user_id)
    
    logger.debug(f"User info: {user_info}")

    return user_info.get('data', {}).get('qqLevel', 0) >= min_level

@handle_error
def process_request(data: RequestData) -> None:
    audit_svc = AuditService()
    result = audit_svc.audit_join_request(data['comment'])
    
    if result.get("agreed", False):
        set_group_add_request(data['flag'], data['sub_type'], approve=True)
        logger.info(
            f"Approved join request | Group: {data['group_id']} | "
            f"User: {data['user_id']}"
        )
    else:
        reason = result.get("reason", "未通过审核")
        _reject_request(data, reason)