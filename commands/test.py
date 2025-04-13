
from typing import Optional
from random import randint
from http_requests.send_group_msg import send_group_msg

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    命令执行入口
    
    Args:
        args: 命令参数
        group_id: 群组ID
        user_id: 执行命令的用户ID
    """
    # 在这里实现具体的命令逻辑
    # Generate random 8-digit number
    random_num = randint(10000000, 99999999)

    # Create message array with @user and random number
    message = [
        {
            "type": "at",
            "data": {
            "qq": str(user_id)
            }
        },
        {
            "type": "text", 
            "data": {
            "text": f" {random_num}"
            }
        }
    ]

    # Send the message
    send_group_msg(group_id, message)