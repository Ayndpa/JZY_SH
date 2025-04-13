import time
from typing import Optional, Dict, List
from http_requests.send_group_msg import send_group_msg
from extensions import logger, config
from http_requests.get_group_member_info import get_group_member_info
from http_requests.get_group_member_list import get_group_member_list
from http_requests.set_group_kick import set_group_kick  # 修改导入语句
from utils.reboot_qq import reboot_qq

class PendingKicks:
    _instance = None
    _pending_kicks: Dict[str, List[int]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def add(self, group_id: int, user_id: int, members: List[int]):
        key = f"{group_id}_{user_id}"
        self._pending_kicks[key] = members

    def get(self, group_id: int, user_id: int) -> List[int]:
        key = f"{group_id}_{user_id}"
        return self._pending_kicks.get(key, [])

    def remove(self, group_id: int, user_id: int):
        key = f"{group_id}_{user_id}"
        self._pending_kicks.pop(key, None)

pending_kicks = PendingKicks()

def calculate_member_weight(member: dict) -> float:
    """
    计算成员权重，用于决定清理优先级
    权重越高越可能被清理
    """
    last_sent_time = member.get("last_sent_time", 0)
    level = member.get("level", "0")
    
    try:
        level_num = int(level)
    except (ValueError, TypeError):
        level_num = 0
        
    # 计算距离现在的天数
    import time
    days_inactive = (time.time() - last_sent_time) / (24 * 3600)
    
    # 权重计算：未发言天数 / (等级 + 1)
    # 等级越高，权重越低；未发言时间越长，权重越高
    return days_inactive / (level_num + 1)

def execute(args: Optional[list], group_id: int, user_id: int):
    """
    清理群成员命令执行入口
    
    Args:
        args: 命令参数 (可选，第一个参数可以是数量或"确认清理")
        group_id: 群组ID
        user_id: 执行命令的用户ID
    """
    # 检查用户权限
    user_info = get_group_member_info(group_id, user_id, no_cache=True)
    if user_info.get("status") == "failed":
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 无法获取您的权限信息"}}
        ]
        send_group_msg(group_id, message)
        return

    # 只允许群主和管理员使用
    user_role = user_info.get("data", {}).get("role")
    if user_id not in config['admin_ids'] and user_role not in ["owner", "admin"]:
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 您没有使用此命令的权限"}}
        ]
        send_group_msg(group_id, message)
        return

    # 处理确认清理的情况
    if args and args[0] == "确认清理":
        to_kick = pending_kicks.get(group_id, user_id)
        if not to_kick:
            message = [
                {"type": "at", "data": {"qq": str(user_id)}},
                {"type": "text", "data": {"text": " 没有待处理的清理操作"}}
            ]
            send_group_msg(group_id, message)
            return

        # 执行踢人操作
        success = 0
        failed = 0
        for target_id in to_kick:
            try:
                # 正确调用set_group_kick函数
                result = set_group_kick(group_id, target_id)
                if result.get("status") == "ok":
                    success += 1
                else:
                    logger.error(f"Failed to kick member {target_id}: {result.get('message', 'Unknown error')}")
                    failed += 1
                # 添加限速，每两个成员之间暂停0.5秒
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Failed to kick member {target_id}: {e}")
                failed += 1

        # 清理临时存储
        pending_kicks.remove(group_id, user_id)

        # 发送结果消息
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": f" 清理完成。成功: {success}, 失败: {failed}\nQQ将在3秒内重启"}}
        ]
        send_group_msg(group_id, message)

        # 重启QQ
        time.sleep(3)
        reboot_qq()

        return

    # 设置默认清理数量
    target_count = 10
    if args and len(args) > 0:
        try:
            target_count = int(args[0])
        except ValueError:
            message = [
                {"type": "at", "data": {"qq": str(user_id)}},
                {"type": "text", "data": {"text": " 请输入有效的数字"}}
            ]
            send_group_msg(group_id, message)
            return

    # 获取群成员列表
    members_response = get_group_member_list(group_id)
    if members_response.get("status") == "failed":
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 获取群成员列表失败"}}
        ]
        send_group_msg(group_id, message)
        return

    # 修改排序逻辑，使用权重排序
    members = sorted(
        members_response.get("data", []),
        key=lambda x: calculate_member_weight(x),
        reverse=True  # 权重高的排在前面
    )

    # 筛选要清理的成员（排除管理员和群主）
    to_kick = []
    for member in members:
        if (member.get("role") not in ["owner", "admin"] and 
            len(to_kick) < target_count):
            to_kick.append(member)

    if not to_kick:
        message = [
            {"type": "at", "data": {"qq": str(user_id)}},
            {"type": "text", "data": {"text": " 没有可清理的成员"}}
        ]
        send_group_msg(group_id, message)
        return

    # 修改确认消息，显示等级信息
    confirm_text = f"即将清理以下 {len(to_kick)} 名成员：\n"
    for member in to_kick:
        name = member.get("card") or member.get("nickname") or str(member.get("user_id"))
        level = member.get("level", "未知")
        last_sent = time.strftime("%Y-%m-%d", time.localtime(member.get("last_sent_time", 0)))
        confirm_text += f"{name} (QQ:{member.get('user_id')}) 等级:{level} 最后发言:{last_sent}\n"
    confirm_text += "\n请回复'确认清理'执行操作"

    message = [
        {"type": "at", "data": {"qq": str(user_id)}},
        {"type": "text", "data": {"text": confirm_text}}
    ]
    send_group_msg(group_id, message)

    # 存储待清理列表供确认时使用
    pending_kicks.add(group_id, user_id, [member.get("user_id") for member in to_kick])