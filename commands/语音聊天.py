import os
import uuid
from typing import Optional
import requests
from extensions import config, logger
from http_requests.send_group_msg import send_group_msg
from llm.gemini import GeminiAPI, GeminiConfig

# filepath: /d:/AuroraProjects/Python/JZY_SH/commands/语音聊天.py

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    语音聊天命令执行入口
    
    Args:
        args: 命令参数
        group_id: 群组ID
        user_id: 执行命令的用户ID
    """
    if not args:
        send_group_msg(group_id, [{"type": "text", "data": {"text": "请输入要聊天的内容"}}])
        return

    # Join args to form the chat message
    chat_text = " ".join(args)
    temp_file = None

    try:
        # 使用Gemini API生成回复
        gemini_config = GeminiConfig(api_key=config['gemini_api_key'])
        api = GeminiAPI(config=gemini_config)
        response = api.chat(chat_text)

        # 转换为语音
        tts_url = "https://tts.mzzsfy.eu.org/api/tts"
        tts_params = {
            "text": response,
            "download": "true",
            "voiceName": "zh-TW-YunJheNeural",
            "pitch": 20
        }

        tts_response = requests.get(tts_url, params=tts_params)
        if tts_response.status_code == 200:
            # 创建临时文件
            temp_dir = "temp"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                
            temp_file = os.path.join(temp_dir, f"{uuid.uuid4()}.mp3")
            
            # 保存语音文件
            with open(temp_file, "wb") as f:
                f.write(tts_response.content)

            # 发送语音消息
            send_group_msg(group_id, [
                {"type": "record", "data": {
                    "file": f"file:///{os.path.abspath(temp_file)}",
                }}
            ])
        else:
            # 如果语音转换失败，只发送文字
            send_group_msg(group_id, [
                {"type": "text", "data": {"text": response}}
            ])

    except Exception as e:
        logger.error(f"Error in 语音聊天: {e}")
        send_group_msg(group_id, [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": f" 处理过程中发生错误：{str(e)}"}}
        ])
    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception as e:
                logger.error(f"Error deleting temp file: {e}")