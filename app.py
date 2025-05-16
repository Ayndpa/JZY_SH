from extensions import app, logger, init_extensions
from datetime import datetime
import os

# 初始化扩展
init_extensions()

# 注册蓝图
from routes.test import test_bp
from routes.onebot import onebot_bp
app.register_blueprint(test_bp)
app.register_blueprint(onebot_bp)

def init_app():
    os.environ["HTTP_PROXY"] = "http://127.0.0.1:7897"
    os.environ["HTTP_PROXYS"] = "http://127.0.0.1:7897"

    from utils.update import do_check
    do_check()
    logger.info('Starting Flask application...')

if __name__ == '__main__':
    init_app()
    app.run(host='0.0.0.0', port=3001)