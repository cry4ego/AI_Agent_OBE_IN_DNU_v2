"""
LLM Helper - Factory function tạo LLM instance theo cấu hình agent
Hỗ trợ Groq (primary), Gemini (Google), Claude (Anthropic) và Local (Qwen)
"""

import sys
import os
import asyncio
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import get_logger
from config import (
    USE_LOCAL_MODEL,
    LOCAL_MODEL_NAME,
    GROQ_API_KEY, GROQ_MODEL,
    GOOGLE_API_KEY, GEMINI_MODEL,
    ANTHROPIC_API_KEY, CLAUDE_MODEL,
    MODEL_PARAMS,
)

logger = get_logger("utils.llm_helper")

# ------------------------------------------------------------
# Local model wrapper
# ------------------------------------------------------------
if USE_LOCAL_MODEL:
    from utils.local_llm import generate_response


def _call_local(messages: list, temperature: float = 0.0, max_tokens: int = 8192) -> str:
    """Gọi model local (Qwen) với danh sách messages."""
    # Chuyển đổi từ LangChain message objects sang dict nếu cần
    if hasattr(messages[0], 'content'):
        messages = [{"role": "system" if m.type == "system" else "user", "content": m.content} for m in messages]
    return generate_response(messages, max_new_tokens=max_tokens, temperature=temperature)


async def _call_local_async(messages: list, temperature: float = 0.0, max_tokens: int = 8192) -> str:
    """Async wrapper cho local model."""
    return await asyncio.to_thread(_call_local, messages, temperature, max_tokens)


# ------------------------------------------------------------
# Factory: trả về LLM instance (dùng cho LangChain nếu cần)
# ------------------------------------------------------------
def get_llm(agent_name: str):
    """Tạo LLM instance phù hợp cho agent.

    Nếu USE_LOCAL_MODEL = True, trả về một wrapper tương thích LangChain
    để các agent dùng .invoke()/.ainvoke() không bị lỗi.
    """
    if USE_LOCAL_MODEL:
        logger.info(f"[{agent_name}] Sử dụng LOCAL model: {LOCAL_MODEL_NAME}")
        # Trả về đối tượng giả lập để tương thích với LangChain
        class LocalChatModel:
            def invoke(self, messages, **kwargs):
                return _invoke_local(messages, **kwargs)
            async def ainvoke(self, messages, **kwargs):
                return _invoke_local_async(messages, **kwargs)
        return LocalChatModel()

    # Groq là primary
    if GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            logger.info(f"[{agent_name}] Sử dụng Groq: {GROQ_MODEL}")
            return ChatGroq(
                model=GROQ_MODEL,
                api_key=GROQ_API_KEY,
                temperature=MODEL_PARAMS["temperature"],
            )
        except ImportError:
            logger.warning("langchain_groq chưa được cài đặt, fallback về Gemini")
        except Exception as e:
            logger.warning(f"Lỗi khởi tạo Groq: {e}, fallback về Gemini")

    # Fallback về Gemini
    if GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            logger.info(f"[{agent_name}] Sử dụng Gemini: {GEMINI_MODEL}")
            return ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=MODEL_PARAMS["temperature"],
            )
        except Exception as e:
            logger.warning(f"Lỗi khởi tạo Gemini: {e}, fallback về Claude")

    # Fallback về Claude
    if ANTHROPIC_API_KEY:
        try:
            from langchain_anthropic import ChatAnthropic
            logger.info(f"[{agent_name}] Sử dụng Claude: {CLAUDE_MODEL}")
            return ChatAnthropic(
                model=CLAUDE_MODEL,
                api_key=ANTHROPIC_API_KEY,
                temperature=MODEL_PARAMS["temperature"],
                max_tokens=MODEL_PARAMS["max_tokens"],
            )
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Claude: {e}")

    raise ValueError(
        "Cần ít nhất một API Key hợp lệ hoặc bật USE_LOCAL_MODEL"
    )


# ------------------------------------------------------------
# Synchronous & Asynchronous calls
# ------------------------------------------------------------
def call_llm_json(agent_name: str, system_prompt: str, user_prompt: str) -> str:
    """Gọi LLM và trả về response dạng string (raw)."""
    if USE_LOCAL_MODEL:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return _call_local(messages, temperature=MODEL_PARAMS["temperature"],
                           max_tokens=MODEL_PARAMS["max_tokens"])

    # Dùng LangChain khi chạy API
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm(agent_name)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = llm.invoke(messages)
    return response.content


async def call_llm_json_async(agent_name: str, system_prompt: str, user_prompt: str,
                              timeout: int = 300) -> str:
    """Async version của call_llm_json với timeout và retry cho local model."""
    if USE_LOCAL_MODEL:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            try:
                raw = await asyncio.wait_for(
                    _call_local_async(messages, temperature=MODEL_PARAMS["temperature"],
                                     max_tokens=MODEL_PARAMS["max_tokens"]),
                    timeout=timeout
                )
                # Kiểm tra nhanh xem có thể parse được JSON không
                test = extract_json_from_response(raw)
                if test and test.strip().startswith('{'):
                    if attempt > 1:
                        logger.info(f"[{agent_name}] Lần {attempt}: Đã nhận được JSON hợp lệ.")
                    return raw
                if attempt < max_attempts:
                    logger.warning(f"[{agent_name}] Lần {attempt}: phản hồi không chứa JSON hợp lệ, thử lại...")
                    # Thêm hướng dẫn rõ ràng hơn cho lần thử tiếp theo
                    messages.append({"role": "user", "content": (
                        "Phản hồi trước của bạn không phải là JSON hợp lệ. "
                        "Hãy chỉ trả về MỘT đối tượng JSON duy nhất, không giải thích gì thêm. "
                        "Đảm bảo tất cả các chuỗi đều được đặt trong dấu ngoặc kép."
                    )})
            except asyncio.TimeoutError:
                raise TimeoutError(f"AI không phản hồi sau {timeout} giây.")
        # Sau 2 lần thử, trả về raw (để caller tự xử lý)
        return raw

    # Code gọi API cũ
    from langchain_core.messages import HumanMessage, SystemMessage

    llm = get_llm(agent_name)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        response = await asyncio.wait_for(llm.ainvoke(messages), timeout=timeout)
        return response.content
    except asyncio.TimeoutError:
        logger.error(f"[{agent_name}] LLM timeout sau {timeout}s")
        raise TimeoutError(
            f"AI không phản hồi sau {timeout} giây. "
            "Vui lòng thử lại sau hoặc kiểm tra kết nối mạng."
        )
    except Exception as e:
        err_str = str(e).lower()
        if "429" in str(e) or "rate limit" in err_str or "rate_limit" in err_str:
            logger.warning(f"[{agent_name}] Rate limit: {e}")
            raise RuntimeError(
                "API đã đạt giới hạn yêu cầu (rate limit). "
                "Vui lòng đợi vài giây rồi thử lại."
            )
        if "401" in str(e) or "unauthorized" in err_str or "api key" in err_str:
            logger.error(f"[{agent_name}] Auth error: {e}")
            raise RuntimeError(
                "API Key không hợp lệ hoặc đã hết hạn. "
                "Vui lòng kiểm tra lại cấu hình."
            )
        if "503" in str(e) or "service unavailable" in err_str or "overloaded" in err_str:
            logger.warning(f"[{agent_name}] Service unavailable: {e}")
            raise RuntimeError(
                "Dịch vụ AI tạm thời không khả dụng (503). "
                "Vui lòng thử lại sau ít phút."
            )
        logger.error(f"[{agent_name}] LLM error: {e}")
        raise


# Hàm phụ cho local model wrapper (dùng trong get_llm)
def _invoke_local(messages, **kwargs):
    """LangChain compatible invoke."""
    return type('obj', (object,), {'content': _call_local(messages, **kwargs)})()

async def _invoke_local_async(messages, **kwargs):
    """LangChain compatible ainvoke."""
    content = await _call_local_async(messages, **kwargs)
    return type('obj', (object,), {'content': content})()


# ------------------------------------------------------------
# Helper trích xuất JSON (giữ nguyên)
# ------------------------------------------------------------
def extract_json_from_response(text: str) -> str:
    """Trích xuất JSON từ response LLM (loại bỏ markdown code blocks nếu có)."""
    if not text:
        return ""
    # Tìm JSON trong code block markdown
    pattern = r"```(?:json)?\s*([\s\S]*?)```"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()

    # Tìm JSON object trực tiếp
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return text.strip()