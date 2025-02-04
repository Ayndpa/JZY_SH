DEFAULT_CONFIG = {
    "bot_accounts": [3028251597],    # QQ机器人账号列表
    "group_ids": [987654321],        # QQ群号列表
    "gemini_api_key": "AIzaSyCjnvdnSQkBCP2aeo5PfK2V7yU0muGHFr4",            # Gemini API密钥
    "admin_group_id": 123456789,         # 管理员通知群号
    "forward_api_url": "http://127.0.0.1:5700",  # 机器人正向HTTP API地址,
    "enable_level_check": True,  # 是否开启等级检查
    "min_join_level": 5,  # 最低加群等级
    "audits_ai_system_prompt": "你是鸡子鱼群的审核，你要做的是审核加群信息是否符合要求。\n要求为：必须包含鸡子鱼整合、",  # AI助手提示语
}