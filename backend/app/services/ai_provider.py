"""
AI Provider abstraction layer - supports multiple AI backends
"""
import json
import base64
import io
from abc import ABC, abstractmethod
from typing import List
from PIL import Image
import google.generativeai as genai
from openai import OpenAI
from app.config import settings


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    def generate_text(self, prompt: str, temperature: float = 0, max_tokens: int = 2000) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    def generate_with_image(self, prompt: str, image: Image.Image, temperature: float = 0, max_tokens: int = 4000) -> str:
        """Generate text from prompt + image (for OCR)"""
        pass


class GeminiProvider(AIProvider):
    """Google Gemini AI Provider"""

    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.text_model = genai.GenerativeModel('gemini-2.5-flash-lite')
        self.vision_model = genai.GenerativeModel('gemini-2.5-flash-lite')

    def generate_text(self, prompt: str, temperature: float = 0, max_tokens: int = 2000) -> str:
        response = self.text_model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        return response.text.strip()

    def generate_with_image(self, prompt: str, image: Image.Image, temperature: float = 0, max_tokens: int = 4000) -> str:
        response = self.vision_model.generate_content(
            [prompt, image],
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )
        return response.text.strip()


class OpenRouterProvider(AIProvider):
    """OpenRouter AI Provider (supports multiple free models)"""

    def __init__(self, model: str = "google/gemini-2.0-flash-exp:free"):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        self.model = model

    def generate_text(self, prompt: str, temperature: float = 0, max_tokens: int = 2000) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    def generate_with_image(self, prompt: str, image: Image.Image, temperature: float = 0, max_tokens: int = 4000) -> str:
        # Convert PIL Image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()


def get_ai_provider() -> AIProvider:
    """Factory function to get the configured AI provider"""
    provider = settings.ai_provider.lower()

    if provider == "gemini":
        return GeminiProvider()
    elif provider == "openrouter":
        return OpenRouterProvider()
    else:
        raise ValueError(f"Unknown AI provider: {provider}")
