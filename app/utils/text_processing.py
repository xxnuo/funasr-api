# -*- coding: utf-8 -*-
import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)

# wetext导入 - 延迟导入以避免初始化问题
_wetext_normalizer = None


def _get_normalizer():
    """获取wetext标准化器实例（单例模式）"""
    global _wetext_normalizer
    if _wetext_normalizer is None:
        try:
            from wetext import Normalizer
            _wetext_normalizer = Normalizer(lang="zh", operator="itn")
            logger.info("WeText ITN模块初始化成功")
        except ImportError as e:
            logger.error(f"导入wetext失败: {e}")
            raise ImportError("请安装wetext库: pip install wetext")
        except Exception as e:
            logger.error(f"初始化wetext失败: {e}")
            raise
    return _wetext_normalizer


def apply_itn_to_text(text: str) -> str:
    """
    对文本应用逆文本标准化（ITN）
    使用wetext库进行高质量的中文ITN处理

    Args:
        text: 语音识别结果文本

    Returns:
        应用ITN后的文本
    """
    if not text or not text.strip():
        return text

    try:
        normalizer = _get_normalizer()
        result = normalizer.normalize(text)
        logger.debug(f"ITN处理: '{text}' -> '{result}'")
        return result
    except Exception as e:
        logger.warning(f"ITN处理失败: {text}, 错误: {str(e)}")
        return text


PUNCTUATION_PATTERN = re.compile(r'([，。！？；：,\.!?;:])')
TRAILING_PUNCTUATION = re.compile(r'[，。！？；：,\.!?;:]+$')
ASR_TAG_PATTERN = re.compile(r'<\|[^|>]+\|>')


def clean_asr_tags(text: str) -> str:
    return ASR_TAG_PATTERN.sub('', text).strip()


def split_text_by_punctuation(
    text: str,
    start_time: float,
    end_time: float,
) -> List[Tuple[str, float, float]]:
    """
    按标点符号拆分文本，并按字符比例分配时间戳

    Args:
        text: 待拆分的文本
        start_time: 整段开始时间（秒）
        end_time: 整段结束时间（秒）

    Returns:
        List of (sentence, start_time, end_time)
    """
    if not text or not text.strip():
        return []

    text = clean_asr_tags(text)
    if not text:
        return []

    total_duration = end_time - start_time
    if total_duration <= 0:
        clean_text = TRAILING_PUNCTUATION.sub('', text)
        return [(clean_text, start_time, end_time)]

    parts = PUNCTUATION_PATTERN.split(text)

    sentences: List[str] = []
    current = ""
    for part in parts:
        if not part:
            continue
        if PUNCTUATION_PATTERN.match(part):
            current += part
            if current.strip():
                sentences.append(current.strip())
            current = ""
        else:
            current += part

    if current.strip():
        sentences.append(current.strip())

    if not sentences:
        clean_text = TRAILING_PUNCTUATION.sub('', text)
        return [(clean_text, start_time, end_time)]

    if len(sentences) == 1:
        clean_text = TRAILING_PUNCTUATION.sub('', sentences[0])
        return [(clean_text, start_time, end_time)]

    total_chars = sum(len(s) for s in sentences)
    if total_chars == 0:
        clean_text = TRAILING_PUNCTUATION.sub('', text)
        return [(clean_text, start_time, end_time)]

    result: List[Tuple[str, float, float]] = []
    current_time = start_time

    for sentence in sentences:
        ratio = len(sentence) / total_chars
        duration = total_duration * ratio
        seg_end = current_time + duration
        clean_sentence = TRAILING_PUNCTUATION.sub('', sentence)
        result.append((clean_sentence, round(current_time, 3), round(seg_end, 3)))
        current_time = seg_end

    if result:
        last = result[-1]
        result[-1] = (last[0], last[1], end_time)

    return result
