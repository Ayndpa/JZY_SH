import logging
import requests
import json
import asyncio
from typing import List, Dict, Any, Optional, Union, AsyncGenerator, Callable
from dataclasses import dataclass, field
from tenacity import retry, stop_after_attempt, wait_exponential, before_log, after_log
from extensions import logger, config

@dataclass
class DeepseekConfig:
    api_key: str
    endpoint: str
    api_version: str = "2024-05-01-preview"
    model_name: str = "DeepSeek-R1"
    max_tokens: int = 4000
    temperature: float = 0.6
    max_retries: int = 3
    timeout: int = 180
    stream: bool = False
    # 添加新的配置选项
    retry_callback: Optional[Callable] = field(default=None)
    sentence_endings: tuple = field(default=("。", "!", "？", "!", "?", "."))

class DeepseekAPIError(Exception):
    """自定义Deepseek API异常类，包含详细的错误信息"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response

class DeepseekAPI:
    def __init__(self, app=None, config: Optional[DeepseekConfig] = None) -> None:
        """初始化DeepseekAPI实例"""
        self.config = None
        self.headers = None
        if app:
            self.init_app(app)
        elif config:
            self.setup_deepseek(config)
        else:
            self._init_from_global_config()

    def _init_from_global_config(self) -> None:
        """从全局配置初始化"""
        api_key = config.get('deepseek_api_key')
        endpoint = config.get('deepseek_endpoint')
        if not (api_key and endpoint):
            raise DeepseekAPIError("Deepseek API configuration not found in global config")
        self.setup_deepseek(DeepseekConfig(api_key=api_key, endpoint=endpoint))

    def init_app(self, app) -> None:
        """使用Flask应用初始化API"""
        try:
            api_key = config.get('deepseek_api_key')
            endpoint = config.get('deepseek_endpoint')
            if not (api_key and endpoint):
                raise DeepseekAPIError("Deepseek API configuration not found in config")
            self.setup_deepseek(DeepseekConfig(api_key=api_key, endpoint=endpoint))
        except Exception as e:
            logger.error(f"Failed to initialize DeepseekAPI: {str(e)}")
            raise

    def setup_deepseek(self, config: DeepseekConfig) -> None:
        """设置Deepseek配置"""
        self.config = config
        self.headers = {
            "api-key": self.config.api_key,
            "Content-Type": "application/json"
        }
        logger.info("Deepseek API initialized successfully")

    async def _process_stream(self, response_iterator) -> AsyncGenerator[str, None]:
        """优化的流式响应处理"""
        buffer = ""
        thinking_done = False
        last_sentence = ""
        
        try:
            async def process_lines():
                for line in response_iterator:
                    yield line
                    await asyncio.sleep(0)  # 让出控制权给事件循环
                    
            async for line in process_lines():
                if not line:
                    continue
                    
                line_str = line.decode('utf-8').strip()
                
                if line_str == "data: [DONE]":
                    remaining = buffer.strip()
                    if remaining and remaining != last_sentence:
                        yield remaining
                    break
                
                if not line_str.startswith('data: '):
                    continue
                
                try:
                    json_response = json.loads(line_str[6:])
                    content = json_response.get('choices', [{}])[0].get('delta', {}).get('content', '')
                    
                    if not content:
                        continue
                    
                    buffer += content
                    
                    # 处理思考过程
                    if not thinking_done and "</think>" in buffer:
                        thinking_part, buffer = self._extract_thinking(buffer)
                        thinking_done = True
                        continue
                    
                    # 处理完整句子
                    if thinking_done:
                        while any(end in buffer for end in self.config.sentence_endings):
                            sentence, buffer = self._extract_sentence(buffer)
                            if sentence and sentence != last_sentence:
                                last_sentence = sentence
                                yield sentence
                                await asyncio.sleep(0)  # 让出控制权
                                
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            logger.error(f"Stream processing error: {str(e)}")
            raise DeepseekAPIError(f"Stream processing error: {str(e)}")

    def _extract_thinking(self, buffer: str) -> tuple[str, str]:
        """提取思考过程"""
        split_pos = buffer.find("</think>") + 8
        thinking = buffer[:split_pos]
        remaining = buffer[split_pos:].lstrip()
        logger.debug(f"Extracted thinking: {thinking}")
        return thinking, remaining

    def _extract_sentence(self, buffer: str) -> tuple[str, str]:
        """提取完整句子"""
        for end in self.config.sentence_endings:
            pos = buffer.find(end)
            if pos != -1:
                sentence = buffer[:pos + len(end)].strip()
                remaining = buffer[pos + len(end):].lstrip()
                return sentence, remaining
        return "", buffer

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before=before_log(logger, logging.DEBUG),
        after=after_log(logger, logging.DEBUG)
    )
    async def _make_request(self, data: Dict[str, Any], stream: bool = False) -> Union[requests.Response, str]:
        """处理API请求"""
        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{self.config.endpoint}?api-version={self.config.api_version}",
                headers=self.headers,
                json=data,
                timeout=self.config.timeout,
                stream=stream
            )
            response.raise_for_status()
            return response if stream else response.json()
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise

    async def achat(
        self,
        prompt: str,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> Union[str, AsyncGenerator[str, None]]:
        """异步聊天方法，支持流式输出"""
        if not self.config:
            raise DeepseekAPIError("DeepseekAPI not properly initialized")

        messages = self._prepare_messages(prompt, history)
        data = self._prepare_request_data(messages)

        try:
            if not self.config.stream:
                response_json = await self._make_request(data)
                if not response_json.get('choices'):
                    raise DeepseekAPIError("Invalid response format")
                return response_json['choices'][0]['message']['content']
            else:
                response = await self._make_request(data, stream=True)
                return self._process_stream(response.iter_lines())
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise DeepseekAPIError(f"Chat error: {str(e)}")

    def _prepare_messages(self, prompt: str, history: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """准备消息列表"""
        messages = [{
            "role": "system",
            "content": "In every output, response using the following format:\n<think>\n{reasoning_content}\n</think>\n\n{content}"
        }]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return messages

    def _prepare_request_data(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """准备请求数据"""
        return {
            "model": self.config.model_name,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": self.config.stream
        }

    async def _handle_regular_chat(self, data: Dict[str, Any]) -> str:
        """处理普通聊天请求"""
        response = await asyncio.to_thread(
            requests.post,
            f"{self.config.endpoint}?api-version={self.config.api_version}",
            headers=self.headers,
            json=data,
            timeout=self.config.timeout
        )
        response.raise_for_status()
        response_json = response.json()
        
        if not response_json.get('choices'):
            raise DeepseekAPIError("Invalid response format", response.status_code, response_json)
            
        return response_json['choices'][0]['message']['content']

    async def _handle_stream_chat(self, data: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """处理流式聊天请求"""
        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{self.config.endpoint}?api-version={self.config.api_version}",
                headers=self.headers,
                json=data,
                timeout=self.config.timeout,
                stream=True
            )
            response.raise_for_status()
            
            async for chunk in self._process_stream(response.iter_lines()):
                yield chunk
                
        except Exception as e:
            logger.error(f"Stream chat error: {str(e)}")
            raise DeepseekAPIError(f"Stream chat error: {str(e)}")

    def chat(self, prompt: str, history: Optional[List[Dict[str, Any]]] = None) -> Union[str, AsyncGenerator[str, None]]:
        """同步聊天方法的包装器"""
        return asyncio.run(self.achat(prompt, history))