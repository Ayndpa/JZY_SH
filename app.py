from flask import Flask
from routes.test import test_bp
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime
from utils.config_manager import load_config
from utils.update import check_member_changes

# 配置日志
def setup_logger():
    # 创建logger对象
    logger = logging.getLogger('flask_app')
    logger.setLevel(logging.DEBUG)
    
    # 创建logs目录(如果不存在)
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 按天切割日志文件
    file_handler = TimedRotatingFileHandler(
        'logs/app.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

check_member_changes()

app = Flask(__name__)
app.register_blueprint(test_bp)

# 初始化日志
logger = setup_logger()

# 加载配置
config = load_config(logger)

if __name__ == '__main__':
    logger.info('Starting Flask application...')
    logger.debug(f'Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    app.run(host='0.0.0.0', port=3001)