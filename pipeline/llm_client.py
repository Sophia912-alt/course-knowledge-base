"""
llm_client.py — OpenAI 兼容 API 调用（带重试）
"""

import time
import json
import requests
from typing import Optional

from . import config


class LLMClient:
    """轻量 OpenAI 兼容 API 客户端"""

    def __init__(self, model: Optional[str] = None):
        self.api_key = config.OPENAI_API_KEY
        self.base_url = config.OPENAI_BASE_URL.rstrip("/")
        self.model = model or config.OPENAI_MODEL
        self.max_retries = config.LLM_MAX_RETRIES
        self.timeout = config.LLM_TIMEOUT

    def chat(self, system: str, user: str,
             temperature: float = 0.3, max_tokens: int = 4096) -> str:
        """
        调用 LLM 并返回文本回复。
        具备指数退避重试机制。
        """
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY 未设置。请设置环境变量后再运行 LLM 步骤。"
            )

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]

            except requests.exceptions.RequestException as e:
                last_err = e
                if attempt < self.max_retries:
                    wait = 2 ** attempt  # 2, 4, 8 秒退避
                    print(f"    ⚠ LLM 调用失败 (第{attempt}次), {wait}s 后重试: {e}")
                    time.sleep(wait)
                else:
                    raise RuntimeError(
                        f"LLM 调用在 {self.max_retries} 次重试后仍失败: {last_err}"
                    )
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                raise RuntimeError(f"LLM 响应解析失败: {e}")

        raise RuntimeError(f"LLM 调用最终失败: {last_err}")

    def chat_json(self, system: str, user: str,
                  temperature: float = 0.3, max_tokens: int = 4096) -> dict:
        """调用 LLM 并解析 JSON 响应"""
        system_with_instruction = (
            system
            + "\n\n你必须只返回合法的 JSON 对象，不要包含 markdown 代码块或额外文字。"
        )
        raw = self.chat(system_with_instruction, user, temperature, max_tokens)
        # 清理可能的 markdown 包裹
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()
        return json.loads(raw)
