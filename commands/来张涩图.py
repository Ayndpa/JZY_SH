import os
from typing import Optional
import requests
from extensions import logger
from http_requests.send_group_msg import send_group_msg

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    发送随机涩图命令执行入口
    
    Args:
        args: 命令参数 [num(可选), keyword(可选)]
        group_id: 群组ID 
        user_id: 执行命令的用户ID
    """
    try:
        # 默认参数
        num = 1
        keyword = None
        
        # 解析参数
        if args:
            # Split first arg by comma or、
            parts = args[0].replace('、', ',').split(',')
            
            # Parse first part as number
            if parts[0].strip().isdigit() and 1 <= int(parts[0].strip()) <= 30:
                num = int(parts[0].strip())
                
            # Use remaining parts as keyword if any
            if len(parts) > 1:
                keyword = ','.join(parts[1:]).strip()

        # API请求URL
        api_url = "https://image.anosu.top/pixiv/direct"
        params = {
            "num": num,
            "r18": 0,  # 固定为0
        }
        
        if keyword:
            params["keyword"] = keyword

        # 发送API请求
        response = requests.get(api_url, params=params)
        
        if response.status_code == 200:
            # 发送图片消息
            send_group_msg(group_id, [
                {"type": "image", "data": {
                    "file": response.url,
                }}
            ])
        else:
            logger.error(f"API error: status_code={response.status_code}, response={response.text}")
            send_group_msg(group_id, [
                {"type": "text", "data": {"text": f"获取图片失败 (错误码: {response.status_code})"}}
            ])

    except Exception as e:
        logger.error(f"Error in 来张涩图: {e}")
        send_group_msg(group_id, [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": f" 处理过程中发生错误：{str(e)}"}}
        ])
