from typing import Dict
from .gemini import GeminiAPI
from .pool import sync_execute_request, execute_request
from app import config, logger
from functools import lru_cache

class AuditService:
    def __init__(self):
        self.gemini_api = GeminiAPI()
        if 'gemini_api_key' in config:
            self.gemini_api.setup_gemini(config['gemini_api_key'])
        
        # Schema for the audit response
        self.schema = {
            "type": "object",
            "properties": {
                "agreed": {
                    "type": "boolean"
                },
                "reason": {
                    "type": "string"
                }
            },
            "required": ["agreed"]
        }

    @lru_cache(maxsize=100)
    def _cached_audit(self, message: str) -> Dict:
        """缓存相同的审核请求"""
        return sync_execute_request(
            self.gemini_api.chat_json,
            message, 
            self.schema, 
            system_prompt=config['audits_ai_system_prompt']
        )

    def audit_join_request(self, message: str) -> Dict:
        """
        带缓存的审核请求处理
        """
        try:
            return self._cached_audit(message)
        except Exception as e:
            logger.error(f"Error during join request audit: {e}")
            raise

    async def audit_join_request_async(self, message: str) -> Dict:
        """
        异步审核请求处理
        """
        try:
            return await execute_request(
                self.gemini_api.chat_json,
                message, 
                self.schema, 
                system_prompt=config['audits_ai_system_prompt']
            )
        except Exception as e:
            logger.error(f"Error during async join request audit: {e}")
            raise
