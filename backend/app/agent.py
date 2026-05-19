import os
import re
import logging
from functools import lru_cache
from typing import List, Dict

from openai import OpenAI
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(os.path.dirname(current_dir), '.env')
load_dotenv(env_path)

# 清除代理环境变量，避免 httpx 不支持 SOCKS 协议的问题
for _var in ['ALL_PROXY', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
    os.environ.pop(_var, None)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.getenv("EMOTION_API_KEY")
base_url = os.getenv("EMOTION_API_BASE_URL", "https://api-inference.modelscope.cn/v1")
model_id = os.getenv("EMOTION_API_MODEL", "Qwen/Qwen3-8B")

if not api_key:
    logger.warning("未检测到 EMOTION_API_KEY，情绪分析功能将无法使用！")

client = OpenAI(
    base_url=base_url,
    api_key=api_key,
    timeout=10.0,
)

VALID_EMOTIONS = ["happy", "sad", "angry", "surprised", "neutral"]

EMOTION_KEYWORDS = {
    "happy": [
        "哈哈", "开心", "高兴", "太好了", "嘻嘻", "笑死", "乐", "nice", "happy", "哈哈",
        "耶", "666", "牛", "厉害", "太棒", "爽", "完美", "赞", "好耶", "嘿嘿",
        "哈哈哈", "lol", "haha", "amazing", "great", "wonderful",
    ],
    "sad": [
        "难过", "伤心", "哭", "呜呜", "悲伤", "唉", "失望", "惨", "痛苦", "sad",
        "心碎", "遗憾", "可怜", "无奈", "心酸", "郁闷", "崩溃", "想哭",
    ],
    "angry": [
        "生气", "愤怒", "烦", "讨厌", "怒", "滚", "去死", "垃圾", "废物", "angry",
        "气死", "受不了", "忍无可忍", "无语", "操", "靠", "什么鬼", "火大",
    ],
    "surprised": [
        "天哪", "卧槽", "我去", "震惊", "不敢相信", "什么", "啊", "wow", "omg",
        "居然", "竟然", "没想到", "不会吧", "真的吗", "离谱", "惊了", "绝了",
    ],
}


def _keyword_filter(message: str) -> str | None:
    text = message.lower()
    scores = {emotion: 0 for emotion in EMOTION_KEYWORDS}

    for emotion, keywords in EMOTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                scores[emotion] += 1

    best_emotion = max(scores, key=scores.get)
    if scores[best_emotion] >= 2:
        return best_emotion
    if scores[best_emotion] == 1 and len(message) < 20:
        return best_emotion

    return None


@lru_cache(maxsize=256)
def _cached_ai_analyze(message: str) -> str:
    """缓存 AI API 调用结果，相同内容直接返回缓存。"""
    system_prompt = f"""
    你是一个即时通讯软件的情绪分析引擎。
    你的任务是根据【当前消息】，判断发送者此时此刻的情绪。

    请严格遵守以下规则：
    1. 你只能从以下标签中选择一个：{', '.join(VALID_EMOTIONS)}。
    2. 如果无法判断或情绪不明显，请返回 'neutral'。
    3. 直接输出标签单词，不要输出任何标点符号、解释或思考过程。
    """

    user_prompt = f"【当前消息】\n{message}\n\n请分析发送者的当前情绪："

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            stream=False,
            extra_body={"enable_thinking": False},
        )

        if not response.choices:
            logger.warning("API 返回空 choices，回退到 neutral")
            return "neutral"

        msg = response.choices[0].message
        result = (msg.content or getattr(msg, 'reasoning_content', None) or "").strip().lower()
        result = re.sub(r'[^\w]', '', result)

        if result in VALID_EMOTIONS:
            return result

        for emotion in VALID_EMOTIONS:
            if emotion in result:
                return emotion

        logger.warning(f"AI 返回了无效标签: {result}，回退到 neutral")
        return "neutral"

    except Exception as e:
        logger.error(f"API 调用失败: {e}")
        return "neutral"


def analyze_emotion(history_messages: List[Dict], current_message: str) -> str:
    quick_result = _keyword_filter(current_message)
    if quick_result:
        logger.info(f"关键词命中: {quick_result} | 内容: {current_message[:10]}...")
        return quick_result

    logger.info(f"调用 AI 分析 | 内容: {current_message[:10]}...")
    return _cached_ai_analyze(current_message)
