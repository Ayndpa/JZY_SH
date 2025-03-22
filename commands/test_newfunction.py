from typing import Optional
from http_requests.send_group_msg import send_group_msg
from llm.gemini import GeminiAPI, GeminiConfig
from extensions import config, logger

# filepath: d:\AuroraProjects\Python\JZY_SH\commands\test_newfunction.py

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    命令执行入口 - 发送AI生成的欢迎消息
    
    Args:
        args: 命令参数
        group_id: 群组ID
        user_id: 执行命令的用户ID
    """
    try:
        # Initialize Gemini API
        gemini_config = GeminiConfig(api_key=config['gemini_api_key'])
        api = GeminiAPI(config=gemini_config)

        # Generate welcome message
        prompt = "生成一段欢迎加群语，内容包含：\n群公告获取整合，仔细看完所有公告，注意群规，违反立刻踢掉"
        welcome_msg = api.chat(prompt)

        # Create and send message
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": welcome_msg}}
        ]
        send_group_msg(group_id, message)
        
    except Exception as e:
        logger.error(f"Failed to send welcome message: {e}")