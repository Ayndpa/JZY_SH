import requests
from typing import List, Dict, Union
from extensions import logger, config

def send_group_forward_msg(
    group_id: int,
    messages: List[Dict],
    news: List[Dict] = None,
    prompt: str = "",
    summary: str = "",
    source: str = ""
) -> dict:
    """
    发送群合并转发消息
    
    Args:
        group_id (int): 群号
        messages (List[Dict]): 要发送的消息列表
        news (List[Dict], optional): 新闻内容列表. Defaults to None.
        prompt (str, optional): 外显文本. Defaults to "".
        summary (str, optional): 底部文本. Defaults to "".
        source (str, optional): 来源文本. Defaults to "".
    
    Returns:
        dict: API响应结果
    """
    try:
        # 从配置中获取API地址
        api_url = f"{config['forward_api_url']}/send_group_forward_msg"
        
        # 构建请求数据
        data = {
            "group_id": group_id,
            "messages": messages,
        }
        
        # 添加可选参数
        if news:
            data["news"] = news
        if prompt:
            data["prompt"] = prompt
        if summary:
            data["summary"] = summary
        if source:
            data["source"] = source
            
        # 发送POST请求
        headers = {'Authorization': 'Bearer ' + config['forward_api_token']}
        response = requests.post(api_url, json=data, headers=headers)
        
        # 检查响应状态
        response.raise_for_status()
        return response.json()
        
    except requests.RequestException as e:
        logger.error(f"发送群合并转发消息失败: {str(e)}")
        return {"status": "failed", "message": str(e)}