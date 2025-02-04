import threading
from flask import Blueprint, request, jsonify
from app import config, logger
from events import onebot

onebot_bp = Blueprint('onebot', __name__)

@onebot_bp.route('/', methods=['POST'])
def handle_onebot_event():
    # 验证请求内容类型
    if request.content_type != 'application/json':
        return jsonify({
            'status': 'failed', 
            'message': '内容类型必须是 application/json'
        }), 400

    # 从请求头获取机器人ID
    self_id = request.headers.get('X-Self-ID')
    if not self_id:
        return jsonify({
            'status': 'failed', 
            'message': '缺少 X-Self-ID 请求头'
        }), 400

    # 获取JSON数据
    try:
        data = request.get_json()
        if not data:
            raise ValueError("空数据")
    except Exception as e:
        return jsonify({
            'status': 'failed', 
            'message': f'无效的JSON数据: {str(e)}'
        }), 400

    # 检查机器人ID是否已配置
    if str(self_id) not in config.get('bot_ids', []):
        logger.debug(f'机器人ID {self_id} 未配置')
        return jsonify({
            'status': 'failed', 
            'message': f'机器人ID {self_id} 未配置'
        }), 403

    # 记录接收到的事件
    logger.info(f'收到来自机器人 {self_id} 的事件: {data}')

    # 创建新线程处理事件
    threading.Thread(
        target=onebot.handle_event,
        args=(data,),
        daemon=True
    ).start()

    return '', 200