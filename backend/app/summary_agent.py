import os
import logging
from typing import List, Dict

from openai import OpenAI
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(os.path.dirname(current_dir), '.env')
load_dotenv(env_path)

for _var in ['ALL_PROXY', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(_var, None)

logger = logging.getLogger(__name__)

SKILLS_DIR = os.path.join(os.path.dirname(current_dir), "data", "skills")

summary_api_key = os.getenv("CHAT_AGENT_API_KEY")
summary_base_url = os.getenv("CHAT_AGENT_BASE_URL", "https://api-inference.modelscope.cn/v1")
summary_model = os.getenv("CHAT_AGENT_MODEL", "Qwen/Qwen3-8B")

if not summary_api_key:
    logger.warning("未检测到 CHAT_AGENT_API_KEY，总结 Agent 功能将无法使用！")

summary_client = OpenAI(
    base_url=summary_base_url,
    api_key=summary_api_key or "dummy",
    timeout=30.0,
)


def summarize_user(user_id: int, user_nickname: str, recent_messages: List[Dict]) -> bool:
    """
    根据最近的聊天记录，总结用户的聊天风格并写入 skill.md。
    返回是否成功。
    """
    if not summary_api_key:
        return False

    chat_lines = []
    for msg in recent_messages:
        prefix = ">>> " if msg["nickname"] == user_nickname else ""
        chat_lines.append(f"{prefix}{msg['nickname']}: {msg['content']}")

    chat_text = "\n".join(chat_lines) if chat_lines else "(无聊天记录)"

    system_prompt = """你是一个用户行为分析助手。你的任务是根据聊天记录，总结用户的聊天风格和习惯。

请输出以下内容（用中文，简洁明了）：
1. 聊天风格：说话方式、语气特点
2. 常用表达：经常使用的词语或句式
3. 兴趣爱好：从聊天中推测的兴趣点
4. 性格特点：乐观/悲观、幽默/严肃等

直接输出总结内容，不要输出标题或格式标记。总字数控制在 200 字以内。"""

    user_prompt = f"以下是用户 {user_nickname} 的最近聊天记录（以 >>> 开头的是该用户的消息）：\n\n{chat_text}\n\n请总结 {user_nickname} 的聊天习惯。"

    try:
        response = summary_client.chat.completions.create(
            model=summary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
            extra_body={"enable_thinking": False},
        )
        message = response.choices[0].message
        summary = (message.content or getattr(message, 'reasoning_content', None) or "").strip()

        # 写入 skill.md
        os.makedirs(SKILLS_DIR, exist_ok=True)
        skill_path = os.path.join(SKILLS_DIR, f"user_{user_id}.md")
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(f"# {user_nickname} 的聊天习惯档案\n\n")
            f.write(summary)
            f.write("\n")

        logger.info(f"已更新用户 {user_nickname}(id={user_id}) 的 skill.md")
        return True

    except Exception as e:
        logger.error(f"总结 Agent API 调用失败: {e}")
        return False
