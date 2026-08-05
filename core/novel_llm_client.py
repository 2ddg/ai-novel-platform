"""小说写作专用 LLM 客户端 - 支持腾讯混元 / 智谱"""
import httpx
import json
import logging
import hashlib
import hmac
import time as time_module
from typing import Optional

from config import ZHIPU_API_KEY, LLM_MODEL, LLM_API_URL

logger = logging.getLogger(__name__)

HUNYUAN_API_KEY = None
HUNYUAN_API_URL = "https://hunyuan.tencentcloudapi.com"
HUNYUAN_MODEL = "hunyuan-large"


def _load_hunyuan_key():
    global HUNYUAN_API_KEY
    if HUNYUAN_API_KEY is None:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        HUNYUAN_API_KEY = os.getenv("HUNYUAN_API_KEY", "")
    return HUNYUAN_API_KEY


async def call_novel_llm(
    prompt: str,
    temperature: float = 0.8,
    max_tokens: int = 2500,
    system_prompt: Optional[str] = None,
) -> str:
    """调用 LLM（优先腾讯混元，失败回退智谱）"""
    result = await _call_hunyuan(prompt, temperature, max_tokens, system_prompt)
    if result is not None:
        return result
    return await _call_zhipu(prompt, temperature, max_tokens, system_prompt)


async def call_novel_llm_stream(
    prompt: str,
    temperature: float = 0.8,
    max_tokens: int = 2500,
    system_prompt: Optional[str] = None,
):
    """流式调用 LLM（优先腾讯混元，失败回退智谱）"""
    api_key = _load_hunyuan_key()
    if api_key:
        has_yielded = False
        async for chunk in _call_hunyuan_stream(prompt, temperature, max_tokens, system_prompt):
            has_yielded = True
            yield chunk
        if has_yielded:
            return
    async for chunk in _call_zhipu_stream(prompt, temperature, max_tokens, system_prompt):
        yield chunk


async def _call_hunyuan(
    prompt: str,
    temperature: float,
    max_tokens: int,
    system_prompt: Optional[str],
) -> Optional[str]:
    """调用腾讯混元 API（非流式）"""
    api_key = _load_hunyuan_key()
    if not api_key:
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": HUNYUAN_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                HUNYUAN_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=body,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.warning(f"混元 API 返回 {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        logger.warning(f"混元 API 调用失败: {e}")
        return None


async def _call_hunyuan_stream(
    prompt: str,
    temperature: float,
    max_tokens: int,
    system_prompt: Optional[str],
):
    """流式调用腾讯混元 API"""
    api_key = _load_hunyuan_key()
    if not api_key:
        return

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": HUNYUAN_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                HUNYUAN_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=body,
            ) as response:
                if response.status_code != 200:
                    logger.warning(f"混元流式 API 返回 {response.status_code}")
                    return
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        raw = line[6:]
                        if raw.strip() == "[DONE]":
                            return
                        try:
                            data = json.loads(raw)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        logger.error(f"混元流式调用异常: {e}")
        yield f"AI服务出错: {str(e)}"


async def _call_zhipu(
    prompt: str,
    temperature: float,
    max_tokens: int,
    system_prompt: Optional[str],
) -> str:
    """调用智谱 API（非流式，作为回退）"""
    if not ZHIPU_API_KEY:
        return "错误：未配置任何 LLM API Key"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                LLM_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ZHIPU_API_KEY}",
                },
                json=body,
            )
            if response.status_code != 200:
                return f"AI服务暂时不可用（错误码：{response.status_code}）"
            data = response.json()
            if "choices" not in data or not data["choices"]:
                return "AI服务返回数据格式异常"
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI服务出错: {str(e)}"


async def _call_zhipu_stream(
    prompt: str,
    temperature: float,
    max_tokens: int,
    system_prompt: Optional[str],
):
    """流式调用智谱 API（作为回退）"""
    if not ZHIPU_API_KEY:
        yield "错误：未配置任何 LLM API Key"
        return

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                LLM_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {ZHIPU_API_KEY}",
                },
                json=body,
            ) as response:
                if response.status_code != 200:
                    yield f"AI服务错误 (HTTP {response.status_code})"
                    return
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        raw = line[6:]
                        if raw.strip() == "[DONE]":
                            return
                        try:
                            data = json.loads(raw)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        yield f"流式调用出错: {str(e)}"
