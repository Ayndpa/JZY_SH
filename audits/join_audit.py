from dataclasses import dataclass
from typing import Dict

@dataclass
class AuditResult:
    agreed: bool
    reason: str = ""

class JoinRequestAuditor:
    def __init__(self):
        self.keywords = ['季梓虞', '鸡子鱼']
    
    def audit(self, comment: str) -> AuditResult:
        """
        审核加群申请信息
        :param comment: 加群申请信息
        :return: AuditResult 包含审核结果和原因
        """
        if not comment:
            return AuditResult(agreed=False, reason="加群信息不能为空")

        # 检查是否包含关键词
        for keyword in self.keywords:
            if keyword in comment:
                return AuditResult(
                    agreed=True
                )
        
        return AuditResult(
            agreed=False,
            reason="答案不正确"
        )
