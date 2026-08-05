import httpx
import json
import logging
from config import ZHIPU_API_KEY, LLM_API_URL, LLM_MODEL

logger = logging.getLogger(__name__)


async def call_llm(prompt: str, model: str = LLM_MODEL, temperature: float = 0.7) -> str:
    """调用智谱大模型（带错误处理）"""
    if not ZHIPU_API_KEY:
        return "错误：未配置ZHIPU_API_KEY"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ZHIPU_API_KEY}"
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(LLM_API_URL, headers=headers, json=body)
            
            if response.status_code != 200:
                logger.error(f"LLM API错误: {response.status_code}")
                return f"AI服务暂时不可用（错误码：{response.status_code}）"
            
            data = response.json()
            if "choices" not in data or not data["choices"]:
                return "AI服务返回数据格式异常"
            
            return data["choices"][0]["message"]["content"]
            
    except httpx.TimeoutException:
        return "AI响应超时，请稍后再试"
    except Exception as e:
        logger.error(f"LLM调用异常: {str(e)}")
        return f"AI服务出错: {str(e)}"


async def call_llm_stream(prompt: str, model: str = LLM_MODEL, temperature: float = 0.7):
    """流式调用智谱大模型"""
    if not ZHIPU_API_KEY:
        yield "错误：未配置ZHIPU_API_KEY"
        return
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ZHIPU_API_KEY}"
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "stream": True
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", LLM_API_URL, headers=headers, json=body) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    try:
                        err_data = json.loads(error_text)
                        msg = err_data.get("error", {}).get("message", str(err_data))
                    except Exception:
                        msg = error_text.decode() if isinstance(error_text, bytes) else str(error_text)
                    yield f"AI服务错误 (HTTP {response.status_code}): {msg}"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            raw = line[6:]
                            if raw.strip() == "[DONE]":
                                return
                            data = json.loads(raw)
                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
    except httpx.TimeoutException:
        yield "AI响应超时，请稍后再试"
    except Exception as e:
        yield f"流式调用出错: {str(e)}"
