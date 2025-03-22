import requests
from typing import Optional
from extensions import config, logger
from http_requests.send_group_msg import send_group_msg
from llm.gemini import GeminiAPI, GeminiConfig

def set_group_add_request(
    flag: str,
    sub_type: str,
    group_id: int,
    user_id: int,
    approve: bool = True,
    reason: Optional[str] = None
) -> dict:
    """
    处理加群请求/邀请
    
    Args:
        flag (str): 加群请求的flag（需从上报的数据中获得）
        sub_type (str): 请求类型（add或invite，需要和上报消息中的sub_type字段相符）
        group_id (int): 群号
        approve (bool, optional): 是否同意请求/邀请. Defaults to True.
        reason (Optional[str], optional): 拒绝理由（仅在拒绝时有效）. Defaults to None.
        
    Returns:
        dict: API响应结果
    """
    try:
        # 从配置中获取API地址
        api_url = f"{config['forward_api_url']}/set_group_add_request"
        
        # 构建请求数据
        data = {
            "flag": flag,
            "sub_type": sub_type,
            "approve": approve
        }
        
        # 仅在拒绝且提供理由时添加reason字段
        if not approve and reason:
            data["reason"] = reason
            
        # 发送POST请求
        headers = {'Authorization': 'Bearer ' + config['forward_api_token']}
        response = requests.post(api_url, json=data, headers=headers)
        
        # 检查响应状态
        response.raise_for_status()

        # @该加群群员并发送通知（使用大模型）
        if approve:
            try:
                # Initialize Gemini API
                gemini_config = GeminiConfig(api_key=config['gemini_api_key'])
                api = GeminiAPI(config=gemini_config)

                # Generate welcome message
                prompt = "生成一段欢迎加群语，内容包含：\n群公告获取整合，仔细看完所有公告，注意群规，违反立刻踢掉"
                welcome_msg = api.chat(prompt)

                # Send welcome message
                message = [
                    {"type": "at", "data": {"qq": str(user_id)}},
                    {"type": "text", "data": {"text": welcome_msg}}
                ]
                send_group_msg(group_id, message)
            except Exception as e:
                logger.error(f"Failed to send welcome message: {e}")

        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"处理加群请求失败: {str(e)}")
        return {"status": "failed", "message": str(e)}