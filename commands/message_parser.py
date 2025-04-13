import importlib
import os
import sys
from typing import Dict, Any, Tuple, Optional
import re
from extensions import logger, config

def parse_command(message: str, group_id: int, user_id: int):
    """
    解析消息中的命令和参数，并处理
    支持两种格式：
    1. @机器人QQ号 命令名称 参数1 参数2 参数3 ...
    2. 字典列表格式的消息

    Args:
        message: 原始消息字符串或字典列表
        group_id: 群组ID
        user_id: 用户ID
    """
    # Get bot QQs from config
    BOT_QQS = [str(qq) for qq in config.get('bot_accounts', [])]

    # 处理字典列表格式消息
    if isinstance(message, list):
        # 检查第一段是否@机器人
        if len(message) >= 2 and message[0].get('type') == 'at' and message[0].get('data', {}).get('qq') in BOT_QQS:
            
            # 第二段获取指令和文字参数
            command_text = message[1].get('data', {}).get('text', '').strip()
            
            # 解析命令和基本参数
            parts = command_text.split()
            if not parts:
                return
                
            command = parts[0].lower()  # 第一部分作为命令名称
            text_args = parts[1:] if len(parts) > 1 else []
            
            # 获取第三段到最后的特殊传入参数
            special_args = []
            if len(message) > 2:
                special_args = message[2:]
            
            # 组合所有参数
            args = text_args + special_args
            
            # 处理命令
            if command:
                process_command(command, args, group_id, user_id)
    
    # 处理文本格式的消息，以后可以添加
    else:
        # 文本格式的消息处理逻辑
        pass
        return

def process_command(command: str, args: Optional[list], group_id: int, user_id: int):
    """
    动态加载并处理命令
    
    Args:
        command: 命令名称
        args: 命令参数
        group_id: 群组ID
        user_id: 用户ID
    """
    try:
        # 获取当前文件所在目录的父目录路径（即项目根目录）
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 获取commands目录的绝对路径
        commands_dir = os.path.join(base_dir, 'commands')
        
        # 确保该命令文件确实存在
        command_file = os.path.join(commands_dir, f"{command}.py")
        if not os.path.exists(command_file):
            logger.error(f'命令文件不存在: {command_file}')
            return
            
        # 添加项目根目录到sys.path（而不是commands目录）
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
        
        # 打印调试信息
        logger.info(f'尝试导入模块: commands.{command}, 路径: {command_file}')
        
        # 使用完整的模块路径导入
        command_module = importlib.import_module(f'commands.{command}')
        
        # 调用模块的execute函数
        if hasattr(command_module, 'execute'):
            logger.info(f'{user_id} 在群 {group_id} 中执行命令 {command} 参数 {args}')
            command_module.execute(args, group_id, user_id)
        else:
            logger.error(f'命令 {command} 模块缺少execute函数')
            
    except ImportError as e:
        logger.error(f'未找到命令模块 {command}: {str(e)}')
    except Exception as e:
        logger.error(f'执行命令 {command} 时发生错误: {str(e)}', exc_info=True)