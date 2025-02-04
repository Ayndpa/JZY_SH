import json
import os
from .config_template import DEFAULT_CONFIG

def load_config(logger):
    """
    加载配置文件，如果不存在则创建默认配置
    """
    config_path = 'config.json'
    if not os.path.exists(config_path):
        # 使用模板创建默认配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        logger.info('Created default config file')
        return DEFAULT_CONFIG
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info('Config loaded successfully')
        return config
    except Exception as e:
        logger.error(f'Failed to load config: {str(e)}')
        return None
