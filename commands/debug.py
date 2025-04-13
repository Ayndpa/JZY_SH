from typing import Optional
from http_requests.send_group_msg import send_group_msg
from extensions import logger
from sqlite import group_record

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    命令执行入口 - 检查用户加群次数并返回调试信息
    
    Args:
        args: 命令参数 (第一个参数为要检查的QQ号)
        group_id: 群组ID
        user_id: 执行命令的用户ID
    """
    try:
        if not args or len(args) < 1:
            send_group_msg(group_id, "请提供要检查的QQ号")
            return
            
        target_qq = int(args[0])
        
        # 获取用户加群次数
        join_count = group_record.get_user_join_count(target_qq)
        
        # 获取配置中的最大加群次数
        from extensions import config
        max_joins = config.get('max_joins', 2)
        
        # 构建调试信息
        debug_info = (
            f"用户加群记录检查\n"
            f"执行人: {user_id}\n"
            f"群号: {group_id}\n"
            f"QQ号: {target_qq}\n"
            f"加群次数: {join_count}\n"
            f"最大允许次数: {max_joins}\n"
            f"状态: {'超过限制' if join_count >= max_joins else '未超过限制'}"
        )
        
        send_group_msg(group_id, debug_info)
        
    except ValueError:
        send_group_msg(group_id, "无效的QQ号，请提供正确的数字")
    except Exception as e:
        logger.error(f"检查用户加群次数失败: {e}")
        send_group_msg(group_id, f"检查失败: {str(e)}")