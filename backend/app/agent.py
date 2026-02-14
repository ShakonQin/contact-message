import os
import logging
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(os.path.dirname(current_dir), '.env')
load_dotenv(env_path)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化客户端
api_key = os.getenv("MODELSCOPE_API_KEY")
model_id = os.getenv("MODELSCOPE_MODEL", "Qwen/Qwen3-8B")

if not api_key:
    logger.warning("未检测到 MODELSCOPE_API_KEY，AI 功能将无法使用！")

client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1',
    api_key=api_key,
)

# 定义有效的情绪标签
VALID_EMOTIONS = ["happy", "sad", "angry", "surprised", "neutral"]


def analyze_emotion(history_messages: List[Dict], current_message: str) -> str:
    """
    分析用户情绪
    :param history_messages: 历史消息列表，格式 [{'nickname': 'A', 'content': '...'}, ...]
    :param current_message: 当前用户发送的消息
    :return: 情绪标签 (happy, sad, angry, surprised, neutral)
    """

    # 构建 Prompt
    history_text = ""
    if history_messages:
        history_text = "\n".join([f"[{m['nickname']}]: {m['content']}" for m in history_messages])
    else:
        history_text = "无历史记录"

    system_prompt = f"""
    你是一个即时通讯软件的情绪分析引擎。
    你的任务是根据【历史对话】和【当前消息】，判断发送者此时此刻的情绪。

    请严格遵守以下规则：
    1. 你只能从以下标签中选择一个：{', '.join(VALID_EMOTIONS)}。
    2. 如果无法判断或情绪不明显，请返回 'neutral'。
    3. 直接输出标签单词，不要输出任何标点符号、解释或思考过程。
    """

    user_prompt = f"""
    【历史对话】
    {history_text}

    【当前消息】
    {current_message}

    请分析发送【当前消息】的人的情绪：
    """

    try:
        # 调用 API
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            stream=True,
            extra_body={
                "enable_thinking": True,
                "thinking_budget": 1024  # 限制思考长度，防止响应太慢
            }
        )

        final_answer = ""

        #解析流式响应
        for chunk in response:
            if chunk.choices:
                delta = chunk.choices[0].delta

                # Qwen/ModelScope
                if hasattr(delta, 'content') and delta.content:
                    final_answer += delta.content

        # 结果清洗与校验
        result = final_answer.strip().lower()

        # 移除可能存在的标点 (如 "happy.")
        import re
        result = re.sub(r'[^\w]', '', result)

        if result in VALID_EMOTIONS:
            logger.info(f"情绪分析结果: {result} | 内容: {current_message[:10]}...")
            return result
        else:
            # 如果 AI 返回了奇怪的东西（比如 "output: happy"），尝试补救或回退
            for emotion in VALID_EMOTIONS:
                if emotion in result:
                    return emotion
            logger.warning(f"AI 返回了无效标签: {result}，回退到 neutral")
            return "neutral"

    except Exception as e:
        logger.error(f"API 调用失败: {e}")
        return "neutral"  # 发生错误时默认冷静