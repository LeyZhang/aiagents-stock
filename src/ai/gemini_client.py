import openai
import json
from typing import Dict, List, Any, Optional
import config

class GeminiClient:
    """Gemini API客户端"""

    def __init__(self, model="gemini-1.5-flash"):
        self.model = model
        self.client = openai.OpenAI(
            api_key=config.GEMINI_API_KEY,
            base_url=config.GEMINI_BASE_URL
        )

    def call_api(self, messages: List[Dict[str, str]], model: Optional[str] = None,
                 temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """调用Gemini API"""
        model_to_use = model or self.model

        try:
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            message = response.choices[0].message
            result = ""

            if hasattr(message, 'reasoning_content') and message.reasoning_content:
                result += f"【推理过程】\n{message.reasoning_content}\n\n"

            if message.content:
                result += message.content

            return result if result else "API返回空响应"

        except Exception as e:
            return f"API调用失败: {str(e)}"


def get_ai_client(provider: str = None):
    """获取AI客户端，根据配置的API提供商自动选择"""
    if provider is None:
        provider = config.API_PROVIDER

    if provider == "gemini":
        return GeminiClient()
    else:
        from src.ai.deepseek_client import DeepSeekClient
        return DeepSeekClient()
