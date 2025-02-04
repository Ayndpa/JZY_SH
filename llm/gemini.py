import google.generativeai as genai
from typing import List, Dict, Any, Optional, Union
import asyncio
import json
from tenacity import retry, stop_after_attempt, wait_exponential
from dataclasses import dataclass

@dataclass
class GeminiConfig:
    api_key: str
    model_name: str = "gemini-2.0-flash-exp"
    max_retries: int = 3
    timeout: int = 30

class GeminiAPIError(Exception):
    """自定义Gemini API异常类"""
    pass

class GeminiAPI:
    def __init__(self, app=None, config: Optional[GeminiConfig] = None) -> None:
        self.config = config
        self.model = None
        if app:
            self.init_app(app)

    def init_app(self, app) -> None:
        api_key = app.config.get('gemini_api_key')
        if not api_key:
            raise GeminiAPIError("gemini_api_key not found in app config")
        self.config = GeminiConfig(api_key=api_key)
        self.setup_gemini()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def setup_gemini(self) -> None:
        try:
            genai.configure(api_key=self.config.api_key)
            self.model = genai.GenerativeModel(model_name=self.config.model_name)
        except Exception as e:
            raise GeminiAPIError(f"Failed to initialize Gemini API: {str(e)}")

    def _validate_response(self, response: str) -> bool:
        """验证响应是否有效"""
        return bool(response and len(response.strip()) > 0)

    async def achat(self, prompt: str, history: Optional[List[Dict[str, Any]]] = None,
                   system_prompt: str = "") -> str:
        """异步聊天方法"""
        if not self.model:
            raise GeminiAPIError("Gemini model not initialized")
        
        try:
            model = genai.GenerativeModel(
                model_name=self.config.model_name,
                system_instruction=system_prompt if system_prompt else None
            )
            chat = model.start_chat(history=history or [])
            response = await asyncio.to_thread(chat.send_message, prompt)
            
            if not self._validate_response(response.text):
                raise GeminiAPIError("Invalid response received")
                
            return response.text
        except Exception as e:
            raise GeminiAPIError(f"Chat error: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def chat(self, prompt: str, history: Optional[List[Dict[str, Any]]] = None,
            system_prompt: str = "") -> str:
        """同步聊天方法"""
        return asyncio.run(self.achat(prompt, history, system_prompt))

    async def achat_json(self, prompt: str, schema: Dict[str, Any],
                        history: Optional[List[Dict[str, Any]]] = None,
                        system_prompt: str = "") -> Dict[str, Any]:
        """异步JSON响应聊天方法"""
        if not self.model:
            raise GeminiAPIError("Gemini model not initialized")

        try:
            generation_config = {
                "response_schema": schema,
                "response_mime_type": "application/json"
            }
            model = genai.GenerativeModel(
                model_name=self.config.model_name,
                generation_config=generation_config,
                system_instruction=system_prompt if system_prompt else None
            )
            chat = model.start_chat(history=history or [])
            response = await asyncio.to_thread(chat.send_message, prompt)
            
            # 验证JSON响应
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                raise GeminiAPIError("Invalid JSON response")
                
        except Exception as e:
            raise GeminiAPIError(f"JSON chat error: {str(e)}")

    def chat_json(self, prompt: str, schema: Dict[str, Any],
                 history: Optional[List[Dict[str, Any]]] = None,
                 system_prompt: str = "") -> Dict[str, Any]:
        """同步JSON响应聊天方法"""
        return asyncio.run(self.achat_json(prompt, schema, history, system_prompt))

def main():
    api = GeminiAPI()
    
    prompt = "Tell me a short joke"
    api.setup_gemini("AIzaSyCjnvdnSQkBCP2aeo5PfK2V7yU0muGHFr4")
    response = api.chat(prompt)
    print("Prompt:", prompt)
    print("Response:", response)

if __name__ == "__main__":
    main()