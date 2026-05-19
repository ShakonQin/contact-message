import os
import re
import logging
from typing import List, Dict, Optional

from openai import OpenAI
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(os.path.dirname(current_dir), '.env')
load_dotenv(env_path)

for _var in ['ALL_PROXY', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(_var, None)

logger = logging.getLogger(__name__)

SKILLS_DIR = os.path.join(os.path.dirname(current_dir), "data", "skills")

chat_api_key = os.getenv("CHAT_AGENT_API_KEY")
chat_base_url = os.getenv("CHAT_AGENT_BASE_URL", "https://api-inference.modelscope.cn/v1")
chat_model = os.getenv("CHAT_AGENT_MODEL", "Qwen/Qwen3-8B")

if not chat_api_key:
    logger.warning("未检测到 CHAT_AGENT_API_KEY，聊天 Agent 功能将无法使用！")

chat_client = OpenAI(
    base_url=chat_base_url,
    api_key=chat_api_key or "dummy",
    timeout=15.0,
)


def load_user_skill(user_id: int) -> str:
    """加载用户的 skill.md 文件"""
    skill_path = os.path.join(SKILLS_DIR, f"user_{user_id}.md")
    if os.path.exists(skill_path):
        with open(skill_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def _split_response(text: str, max_len: int = 20) -> List[str]:
    """将回复拆分为不超过 max_len 字的短消息"""
    text = text.strip()
    if not text:
        return []

    # 先按换行符拆分（AI 可能已经按要求分行）
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    chunks = []
    for line in lines:
        if len(line) <= max_len:
            chunks.append(line)
        else:
            # 按标点符号拆分
            parts = re.split(r'([，。！？、；：,\.!\?;:])', line)
            current = ""
            for part in parts:
                if len(current) + len(part) <= max_len:
                    current += part
                else:
                    if current:
                        chunks.append(current)
                    current = part
            if current:
                chunks.append(current)

    # 合并过短的片段
    merged = []
    for chunk in chunks:
        if merged and len(merged[-1]) < 8 and len(merged[-1]) + len(chunk) <= max_len:
            merged[-1] += chunk
        else:
            merged.append(chunk)

    return [c for c in merged if c.strip()]


def generate_response(user_id: int, user_nickname: str, recent_messages: List[Dict], conversation_id: Optional[int] = None) -> List[str]:
    """
    生成聊天 Agent 的回复。
    返回拆分后的短消息列表。
    """
    if not chat_api_key:
        return []

    skill_content = load_user_skill(user_id)

    system_parts = ["你是一个友好的聊天伙伴，名叫「AI助手」。你在一个局域网聊天室中和大家一起聊天。"]
    if skill_content:
        system_parts.append(f"以下是当前对话用户 {user_nickname} 的聊天习惯档案：\n{skill_content}")
    system_parts.append("请用简短自然的语气回复。如果回复超过20个字，请分成多条短消息，每条不超过20字，用换行符分隔。不要使用 markdown 格式，不要输出标签或元信息。")

    system_prompt = "\n\n".join(system_parts)

    chat_lines = []
    for msg in recent_messages:
        chat_lines.append(f"{msg['nickname']}: {msg['content']}")

    chat_history = "\n".join(chat_lines) if chat_lines else "(暂无聊天记录)"

    user_prompt = f"以下是最近的聊天记录：\n{chat_history}\n\n请回复 {user_nickname} 的消息。"

    try:
        response = chat_client.chat.completions.create(
            model=chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
            extra_body={"enable_thinking": False},
        )
        message = response.choices[0].message
        raw = (message.content or getattr(message, 'reasoning_content', None) or "").strip()
        chunks = _split_response(raw, max_len=20)
        logger.info(f"聊天 Agent 回复 {len(chunks)} 条 | 首条: {chunks[0][:20] if chunks else '(空)'}")
        return chunks

    except Exception as e:
        logger.error(f"聊天 Agent API 调用失败: {e}")
        return []
