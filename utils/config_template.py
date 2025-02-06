DEFAULT_CONFIG = {
    "bot_accounts": [3028251597],    # QQ机器人账号列表
    "group_ids": [904171229],        # QQ群号列表
    "admin_ids": [3079498044],
    "gemini_api_key": "AIzaSyCjnvdnSQkBCP2aeo5PfK2V7yU0muGHFr4",            # Gemini API密钥
    "admin_group_id": 686038298,         # 管理员通知群号
    "forward_api_url": "http://127.0.0.1:5700",  # 机器人正向HTTP API地址,
    "enable_level_check": True,  # 是否开启等级检查
    "min_join_level": 15,  # 最低加群等级
    "audits_ai_system_prompt": "提示词",  # AI助手提示语,
    "max_leave_count": 1,
    "max_kick_count": 2,
    "deepseek_attack_prompt": "In every output, response using the following format:\n<think>\n{reasoning_content}\n</think>\n\n{content}\n\n结合对方的信息和聊天记录，尽可能粗暴地辱骂对方，注意言辞不要太高级，尽可能通俗易懂。",  # Deepseek攻击提示
    "deepseek_api_key": "8kk2WPujeFEdISduExh0cy0hYVdeN96bNwZVq6semShLzwgRJqFxJQQJ99BBACMsfrFXJ3w3AAAAACOGWhhM",
    "deepseek_endpoint": "https://ayndpadeepseek.services.ai.azure.com/models/chat/completions"
}