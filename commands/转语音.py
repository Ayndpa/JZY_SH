from typing import Optional
import requests
from http_requests.send_group_msg import send_group_msg

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    命令执行入口
    
    Args:
        args: 命令参数
        group_id: 群组ID
        user_id: 执行命令的用户ID
    """
    if not args:
        send_group_msg(group_id, [{"type": "text", "data": {"text": "请输入要转换的文本"}}])
        return

    # Join args to form the text
    text = " ".join(args)

    # API endpoint
    url = "https://tts.mzzsfy.eu.org/api/tts"
    
    # Request parameters
    params = {
        "text": text,
        "download": "true",
        "shardLength": "1000",
        "thread": "5",
        "fastDownload": "false",
        "audioType": "audio-24khz-48kbitrate-mono-mp3",
        "voiceName": "zh-CN-XiaoxiaoNeural"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            # Get the audio URL from response
            audio_url = response.url  # 直接使用重定向后的URL
            
            # Send voice message
            send_group_msg(group_id, [
                {"type": "record", "data": {
                    "file": audio_url,
                    "cache": 1,
                    "proxy": 1
                }},
                {"type": "at", "data": {"qq": str(user_id)}},
                {"type": "text", "data": {"text": "语音已生成"}}
            ])
        else:
            send_group_msg(group_id, [
                {"type": "at", "data": {"qq": str(user_id)}},
                {"type": "text", "data": {"text": "语音转换失败，请稍后重试"}}
            ])
    except Exception as e:
        send_group_msg(group_id, [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": f"发生错误：{str(e)}"}}
        ])