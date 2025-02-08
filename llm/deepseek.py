import requests
import json
import asyncio
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential
from extensions import logger, config
import re

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

class DeepseekAPIError(Exception):
    """自定义Deepseek API异常类"""
    pass

class DeepseekAPI:
    def __init__(self, app=None, config: Optional[DeepseekConfig] = None) -> None:
        self.config = config
        if app:
            self.init_app(app)
        elif config:
            self.setup_deepseek()
        else:
            # 如果没有提供 app 或 config，尝试从全局配置初始化
            api_key = config.get('deepseek_api_key')
            endpoint = config.get('deepseek_endpoint')
            if not (api_key and endpoint):
                logger.error("Deepseek API configuration not found in global config")
                raise DeepseekAPIError("Deepseek API configuration not found in global config")
            self.config = DeepseekConfig(api_key=api_key, endpoint=endpoint)
            self.setup_deepseek()

    def init_app(self, app) -> None:
        try:
            api_key = config.get('deepseek_api_key')
            endpoint = config.get('deepseek_endpoint')
            if not (api_key and endpoint):
                logger.error("Deepseek API configuration not found in config")
                raise DeepseekAPIError("Deepseek API configuration not found in config")
            self.config = DeepseekConfig(api_key=api_key, endpoint=endpoint)
            self.setup_deepseek()
        except Exception as e:
            logger.error(f"Failed to initialize DeepseekAPI: {str(e)}")
            raise DeepseekAPIError(f"Failed to initialize DeepseekAPI: {str(e)}")

    def setup_deepseek(self) -> None:
        if not self.config:
            raise DeepseekAPIError("DeepseekConfig not initialized")
        self.headers = {
            "api-key": self.config.api_key,
            "Content-Type": "application/json"
        }
        logger.info("Deepseek API initialized successfully")

    def _validate_response(self, response: dict) -> bool:
        """验证响应是否有效"""
        return bool(response and 'choices' in response and len(response['choices']) > 0)

    async def _process_stream(self, response_iterator) -> AsyncGenerator[str, None]:
        """处理流式响应"""
        buffer = ""
        thinking_done = False
        
        async for line in response_iterator:
            if not line:
                continue
                
            if line == b"[DONE]":
                if buffer and buffer.strip():
                    yield buffer
                break
                
            try:
                # 处理SSE格式的数据
                line = line.decode('utf-8')
                if not line.startswith('data: '):
                    continue
                    
                # 提取JSON数据部分
                json_str = line[6:].strip()  # 移除 "data: " 前缀
                if not json_str:
                    continue
                
                json_response = json.loads(json_str)
                if not isinstance(json_response, dict):
                    continue
                    
                # 验证响应结构
                delta = json_response.get('choices', [{}])[0].get('delta', {})
                content = delta.get('content', '')
                if not content:
                    continue
                
                buffer += content
                logger.debug(f"Received content: {content}")
                
                if not thinking_done and "</think>" in buffer:
                    thinking_part = buffer[:buffer.find("</think>") + 8]
                    remaining = buffer[buffer.find("</think>") + 8:]
                    buffer = remaining.lstrip()
                    thinking_done = True
                    logger.info(f"Thinking process: {thinking_part}")
                    continue
                    
                if thinking_done:
                    while any(buffer.find(end) != -1 for end in ["。", "!", "？", "!", "?", "."]):
                        for end in ["。", "!", "？", "!", "?", "."]:
                            pos = buffer.find(end)
                            if pos != -1:
                                sentence = buffer[:pos + 1].strip()
                                if sentence:
                                    yield sentence
                                buffer = buffer[pos + 1:].lstrip()
                                break

            except json.JSONDecodeError as e:
                logger.debug(f"Invalid JSON in SSE data: {line}")
                continue
            except Exception as e:
                logger.error(f"Error processing stream: {str(e)}")
                continue

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def achat(self, prompt: str, history: Optional[List[Dict[str, Any]]] = None) -> Union[str, AsyncGenerator[str, None]]:
        """异步聊天方法，支持流式输出"""
        try:
            messages = [{
                "role": "system",
                "content": "In every output, response using the following format:\n<think>\n{reasoning_content}\n</think>\n\n{content}"
            }]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": prompt})

            data = {
                "model": self.config.model_name,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "stream": self.config.stream
            }

            if not self.config.stream:
                async def make_request():
                    response = await asyncio.to_thread(
                        requests.post,
                        f"{self.config.endpoint}?api-version={self.config.api_version}",
                        headers=self.headers,
                        json=data,
                        timeout=self.config.timeout
                    )
                    response.raise_for_status()
                    return response.json()

                response_json = await make_request()
                if not self._validate_response(response_json):
                    raise DeepseekAPIError("Invalid response received")
                return response_json['choices'][0]['message']['content']
            else:
                # 创建异步迭代器来处理流式响应
                async def stream_response():
                    response = await asyncio.to_thread(
                        requests.post,
                        f"{self.config.endpoint}?api-version={self.config.api_version}",
                        headers=self.headers,
                        json=data,
                        timeout=self.config.timeout,
                        stream=True
                    )
                    response.raise_for_status()
                    
                    for line in response.iter_lines():
                        if line:  # 只yield非空行
                            yield line
                
                return self._process_stream(stream_response())
                
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            raise DeepseekAPIError(f"Chat error: {str(e)}")

    def chat(self, prompt: str, history: Optional[List[Dict[str, Any]]] = None) -> Union[str, AsyncGenerator[str, None]]:
        """同步聊天方法"""
        return asyncio.run(self.achat(prompt, history))