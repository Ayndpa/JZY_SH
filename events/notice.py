from typing import Dict, Any, Optional
from enum import Enum
from extensions import logger
from sqlite.group_member_record import add_single_member_record, delete_member_record
from sqlite.group_quit_record import add_quit_record

class GroupEventType(Enum):
    DECREASE = 'group_decrease'
    INCREASE = 'group_increase'

class SubEventType(Enum):
    LEAVE = 'leave'
    KICK = 'kick'
    KICK_ME = 'kick_me'
    APPROVE = 'approve'
    INVITE = 'invite'

def _get_event_data(data: Dict[str, Any]) -> tuple[Optional[str], Optional[str], int, int, int]:
    """Extract common event data"""
    return (
        data.get('notice_type'),
        data.get('sub_type'),
        data.get('operator_id', 0),
        data.get('group_id', 0),
        data.get('user_id', 0)
    )

def handle_group_decrease(data: Dict[str, Any]) -> None:
    try:
        notice_type, sub_type, operator_id, group_id, user_id = _get_event_data(data)
        
        if notice_type != GroupEventType.DECREASE.value:
            return

        log_messages = {
            SubEventType.LEAVE.value: f'User {user_id} left group {group_id}',
            SubEventType.KICK.value: f'User {user_id} was kicked from group {group_id} by {operator_id}',
            SubEventType.KICK_ME.value: f'Bot was kicked from group {group_id} by {operator_id}'
        }

        if sub_type in log_messages:
            logger.info(log_messages[sub_type]) if sub_type != SubEventType.KICK_ME.value else logger.warning(log_messages[sub_type])
        else:
            logger.debug(f'Unknown group_decrease sub_type: {sub_type}')

        if sub_type in [SubEventType.LEAVE.value, SubEventType.KICK.value]:
            quit_type = 'leave' if sub_type == SubEventType.LEAVE.value else 'kick'
            add_quit_record(user_id, group_id, quit_type)
            delete_member_record(group_id, user_id)
    except Exception as e:
        logger.error(f'Error handling group decrease event: {str(e)}')

def handle_group_increase(data: Dict[str, Any]) -> None:
    try:
        notice_type, sub_type, operator_id, group_id, user_id = _get_event_data(data)
        
        if notice_type != GroupEventType.INCREASE.value:
            return

        log_messages = {
            SubEventType.APPROVE.value: f'User {user_id} joined group {group_id} (approved)',
            SubEventType.INVITE.value: f'User {user_id} was invited to group {group_id} by {operator_id}'
        }

        if sub_type in log_messages:
            logger.info(log_messages[sub_type])
        else:
            logger.debug(f'Unknown group_increase sub_type: {sub_type}')

        add_single_member_record(group_id, user_id)
    except Exception as e:
        logger.error(f'Error handling group increase event: {str(e)}')