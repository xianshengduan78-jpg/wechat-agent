import json
import time

import httpx

from config.settings import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, DEEPSEEK_TIMEOUT, DEEPSEEK_MAX_RETRIES


class DeepSeekClient:
    """DeepSeek API 封装（兼容 OpenAI 格式，直接用 httpx）。"""

    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.base_url = DEEPSEEK_BASE_URL
        self.model = DEEPSEEK_MODEL
        self.timeout = DEEPSEEK_TIMEOUT
        self.max_retries = DEEPSEEK_MAX_RETRIES

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(self, messages, temperature=0.7, json_mode=False):
        """普通调用。返回 response.choices[0].message.content (str)。"""
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        last_exc = None
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(
                        f"{self.base_url}/chat/completions",
                        headers=self._headers(),
                        json=body,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    if json_mode:
                        return json.loads(content)
                    return content
            except (httpx.TimeoutException, httpx.RequestError, json.JSONDecodeError,
                    KeyError, httpx.HTTPStatusError) as e:
                last_exc = e
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt
                    time.sleep(wait)
                continue

        raise RuntimeError(f"DeepSeek API 调用失败（重试 {self.max_retries} 次后）: {last_exc}")

    def chat_json(self, messages, temperature=0.7):
        """JSON mode 调用。返回解析后的 dict。"""
        return self.chat(messages, temperature=temperature, json_mode=True)
