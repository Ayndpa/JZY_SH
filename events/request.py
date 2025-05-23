from typing import Dict, Any, Optional, TypedDict, Tuple
from functools import wraps
from extensions import logger, config
from http_requests.send_group_msg import send_group_msg
from http_requests.set_group_add_request import set_group_add_request
from http_requests.get_stranger_info import get_stranger_info
from enum import Enum
from http_requests.get_group_member_info import get_group_member_info
from audits.join_audit import JoinRequestAuditor
from sqlite import group_record

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

class LevelCheckResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"

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
        _notify_admin(request_data, NotifyReason.EMPTY_COMMENT)
        return

    level_check = check_level_requirements(request_data['user_id'])
    if level_check == LevelCheckResult.FAIL:
        _reject_request(request_data, "等级过低")
        return
    elif level_check == LevelCheckResult.ERROR:
        _notify_admin(request_data, NotifyReason.LEVEL_CHECK_FAILED)
        return
    
    if check_other_groups(request_data['user_id']):
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
        group_ids = config.get('group_ids', [])
        for group_id in group_ids:
            response = get_group_member_info(group_id, user_id)
            if response.get('status') == 'ok' and response.get('retcode') == 0:
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking group membership: {e}")
        return False
    
class RejectReason(Enum):
    JOIN_LIMIT = "加群次数过多"  # 新增加群次数限制的原因

def check_quit_history(user_id: int) -> Tuple[bool, Optional[str]]:
    join_count = group_record.get_user_join_count(user_id)
    
    if join_count >= config.get('max_joins', 2):
        return False, RejectReason.JOIN_LIMIT.value
        
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

class NotifyReason(Enum):
    EMPTY_COMMENT = "加群留言为空"
    LEVEL_CHECK_FAILED = "无法获取等级信息"
    CUSTOM_REASON = "自定义原因"

def _notify_admin(data: RequestData, reason_type: NotifyReason, custom_msg: str = "") -> None:
    admin_group = config.get('admin_group_id')
    
    base_info = (
        f"需要人工审核\n"
        f"原因: {reason_type.value}\n"
        f"群号: {data['group_id']}\n"
        f"用户: {data['user_id']}"
    )
    
    if custom_msg:
        base_info += f"\n附加信息: {custom_msg}"
        
    if reason_type == NotifyReason.EMPTY_COMMENT:
        base_info += "\n说明: 用户未填写加群申请信息"
    elif reason_type == NotifyReason.LEVEL_CHECK_FAILED:
        base_info += "\n说明: 无法通过 API 获取用户等级信息"
    
    send_group_msg(admin_group, base_info)
    logger.info(f"Admin notification sent: {base_info}")

def _reject_request(data: RequestData, reason: str) -> None:
    set_group_add_request(data['flag'], data['sub_type'], group_id=data['group_id'], user_id=data['user_id'], approve=False, reason=reason)
    logger.info(
        f"Rejected join request | Group: {data['group_id']} | "
        f"User: {data['user_id']} | Reason: {reason}"
    )

@handle_error
def check_level_requirements(user_id: int) -> LevelCheckResult:
    if not config.get('enable_level_check', False):
        return LevelCheckResult.PASS
        
    min_level = config.get('min_join_level', 0)
    user_info = get_stranger_info(user_id)
    
    user_data = user_info.get('data', {})
    level = user_data.get('qqLevel', 0)
    
    if not level:
        return LevelCheckResult.ERROR

    return LevelCheckResult.PASS if level >= min_level else LevelCheckResult.FAIL

@handle_error
def process_request(data: RequestData) -> None:
    auditor = JoinRequestAuditor()
    result = auditor.audit(data['comment'])
    
    if result.agreed:
        set_group_add_request(data['flag'], data['sub_type'], group_id=data['group_id'], user_id=data['user_id'], approve=True)
        logger.info(
            f"Approved join request | Group: {data['group_id']} | "
            f"User: {data['user_id']}"
        )
    else:
        _reject_request(data, result.reason)