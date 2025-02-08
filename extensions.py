from flask import Flask
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from utils.config_manager import load_config

app = Flask(__name__)
config = None

# 创建全局 logger
_logger = logging.getLogger('flask_app')
_logger.setLevel(logging.INFO)

# 创建logs目录(如果不存在)
if not os.path.exists('logs'):
    os.makedirs('logs')

# 按天切割日志文件
file_handler = logging.handlers.RotatingFileHandler(
    'logs/app.log',
    maxBytes=10*1024*1024,  # 10MB max size
    backupCount=30,
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器
_logger.addHandler(file_handler)
_logger.addHandler(console_handler)

# 导出 logger
logger = _logger

def init_extensions():
    global config
    
    config = load_config(logger)

    if not config:
        logger.error("Failed to load configuration")
        raise RuntimeError("Configuration not loaded properly")

    logger.info("Extensions initialized successfully")
