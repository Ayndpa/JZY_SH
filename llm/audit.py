from typing import Dict
from .gemini import GeminiAPI, GeminiConfig
from .pool import sync_execute_request, execute_request
from extensions import config, logger
from functools import lru_cache
import json

class AuditService:
    def __init__(self):
        try:
            api_key = config.get('gemini_api_key')
            if not api_key:
                raise ValueError("Gemini API key not found in config")
                
            gemini_config = GeminiConfig(api_key=api_key)
            self.gemini_api = GeminiAPI(config=gemini_config)
            
        except Exception as e:
            logger.error(f"Failed to initialize AuditService: {str(e)}")
            raise
        
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

    @staticmethod
    def _get_cache_key(message: str, schema: dict, system_prompt: str) -> str:
        """生成可哈希的缓存键"""
        cache_data = {
            'message': message,
            'schema': json.dumps(schema, sort_keys=True),
            'system_prompt': system_prompt
        }
        return json.dumps(cache_data, sort_keys=True)

    @lru_cache(maxsize=100)
    def _cached_audit_impl(self, cache_key: str) -> Dict:
        """实际的缓存实现"""
        cache_data = json.loads(cache_key)
        return sync_execute_request(
            self.gemini_api.chat_json,
            cache_data['message'],
            json.loads(cache_data['schema']),
            system_prompt=cache_data['system_prompt']
        )

    def _cached_audit(self, message: str) -> Dict:
        """缓存相同的审核请求"""
        cache_key = self._get_cache_key(
            message,
            self.schema,
            config['audits_ai_system_prompt']
        )
        return self._cached_audit_impl(cache_key)

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
