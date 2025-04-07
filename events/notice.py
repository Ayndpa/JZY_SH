from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from extensions import logger
from sqlite import group_record

class GroupEventType(Enum):
    INCREASE = 'group_increase'

class SubEventType(Enum):
    APPROVE = 'approve'

@dataclass
class EventData:
    notice_type: Optional[str]
    sub_type: Optional[str]
    operator_id: int
    group_id: int
    user_id: int

def _get_event_data(data: Dict[str, Any]) -> EventData:
    """Extract and validate common event data"""
    return EventData(
        notice_type=data.get('notice_type'),
        sub_type=data.get('sub_type'),
        operator_id=int(data.get('operator_id', 0)),
        group_id=int(data.get('group_id', 0)),
        user_id=int(data.get('user_id', 0))
    )

def handle_group_increase(data: Dict[str, Any]) -> bool:
    """
    Handle group increase events.
    Returns True if handled successfully, False otherwise.
    """
    try:
        event_data = _get_event_data(data)
        
        if event_data.notice_type != GroupEventType.INCREASE.value:
            logger.warning(f'Unexpected notice type: {event_data.notice_type}')
            return False

        if event_data.sub_type == SubEventType.APPROVE.value:
            logger.info(
                f'Group Join Event - [Group: {event_data.group_id}] '
                f'[User: {event_data.user_id}] [Operator: {event_data.operator_id}]'
            )
            group_record.add_record(event_data.group_id, event_data.user_id)

            # @该加群群员并发送通知（使用大模型）
            try:
                # Initialize Gemini API
                gemini_config = GeminiConfig(api_key=config['gemini_api_key'])
                api = GeminiAPI(config=gemini_config)

                # Generate welcome message
                prompt = "生成一段对一位新人的欢迎加群语，内容包含：\n群公告获取整合，仔细看完所有公告，注意群规，违反立刻踢掉"
                welcome_msg = api.chat(prompt)

                # Send welcome message
                message = [
                    {"type": "at", "data": {"qq": str(user_id)}},
                    {"type": "text", "data": {"text": welcome_msg}}
                ]
                send_group_msg(group_id, message)
            except Exception as e:
                logger.error(f"Failed to send welcome message: {e}")

            return True
        
        return False
        
    except Exception as e:
        logger.error(f'Error handling group increase event: {str(e)}', exc_info=True)
        return False