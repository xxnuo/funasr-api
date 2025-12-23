# -*- coding: utf-8 -*-
"""
OpenAI 兼容 API
实现 OpenAI Audio API 规范，兼容 OpenAI SDK 和第三方客户端
"""

import time
import logging
from typing import Optional, List
from enum import Enum

from fastapi import APIRouter, File, Form, UploadFile, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from ...core.config import settings
from ...core.executor import run_sync
from ...core.security import validate_token
from ...utils.audio import (
    save_audio_to_temp_file,
    cleanup_temp_file,
    get_audio_file_suffix,
    normalize_audio_for_asr,
    get_audio_duration,
)
from ...utils.text_processing import split_text_by_punctuation, clean_asr_tags
from ...services.asr.manager import get_model_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])


# ============= 枚举类型 =============

class ResponseFormat(str, Enum):
    JSON = "json"
    TEXT = "text"
    SRT = "srt"
    VERBOSE_JSON = "verbose_json"
    VTT = "vtt"


# ============= 响应模型 =============

class TranscriptionSegment(BaseModel):
    """转写分段"""
    id: int
    seek: int = 0
    start: float
    end: float
    text: str
    tokens: List[int] = Field(default_factory=list)
    temperature: float = 0.0
    avg_logprob: float = 0.0
    compression_ratio: float = 0.0
    no_speech_prob: float = 0.0


class TranscriptionWord(BaseModel):
    """转写词级别信息"""
    word: str
    start: float
    end: float


class TranscriptionResponse(BaseModel):
    """简单转写响应 (json 格式)"""
    text: str


class VerboseTranscriptionResponse(BaseModel):
    """详细转写响应 (verbose_json 格式)"""
    task: str = "transcribe"
    language: str
    duration: float
    text: str
    segments: List[TranscriptionSegment] = Field(default_factory=list)
    words: Optional[List[TranscriptionWord]] = None


class ModelObject(BaseModel):
    """模型对象"""
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "funasr-api"


class ModelsResponse(BaseModel):
    """模型列表响应"""
    object: str = "list"
    data: List[ModelObject]


# ============= 辅助函数 =============

def format_timestamp_srt(seconds: float) -> str:
    """格式化时间戳为 SRT 格式 (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """格式化时间戳为 VTT 格式 (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def generate_srt(segments: List[TranscriptionSegment]) -> str:
    """生成 SRT 字幕格式"""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp_srt(seg.start)
        end = format_timestamp_srt(seg.end)
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines)


def generate_vtt(segments: List[TranscriptionSegment]) -> str:
    """生成 WebVTT 字幕格式"""
    lines = ["WEBVTT", ""]
    for seg in segments:
        start = format_timestamp_vtt(seg.start)
        end = format_timestamp_vtt(seg.end)
        lines.append(f"{start} --> {end}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines)


def map_model_id(model: str) -> Optional[str]:
    """将 OpenAI 模型 ID 映射到 FunASR-API 模型 ID"""
    # whisper-* 映射到默认模型（兼容 OpenAI SDK）
    if model.lower().startswith("whisper"):
        return None  # 使用默认模型

    # 其他情况直接使用原模型 ID
    return model


# ============= API 端点 =============

@router.get(
    "/models",
    response_model=ModelsResponse,
    summary="列出可用模型",
    description="""返回当前可用的 ASR 模型列表（OpenAI `/v1/models` 兼容）。

**可用模型：**

| 模型 ID | 名称 | 说明 | 支持实时 |
|---------|------|------|----------|
| sensevoice-small | SenseVoice Small | 速度最快的语音识别，支持多语言混合、情绪识别，准确度适中（默认） | 否 |
| paraformer-large | Paraformer Large | 高精度中文语音识别，内置 VAD + 标点 + 时间戳，对其他语言支持一般，速度适中 | 是 |
| fun-asr-nano | Fun-ASR-Nano | 支持识别中文方言、唱歌等，远场高噪声识别优化，速度最慢，准确度适中，有时会有幻觉误识别 | 否 |

具体模型特点请参考官方说明：https://help.aliyun.com/zh/model-studio/recording-file-recognition

**兼容性说明：**
- `whisper-1` 等 OpenAI 模型 ID 会自动映射到默认模型
- 支持 OpenAI SDK 和第三方客户端调用
""",
)
async def list_models(request: Request):
    """列出可用模型 (OpenAI 兼容)"""
    # 可选鉴权
    result, _ = validate_token(request)
    if not result and settings.APPTOKEN:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    try:
        model_manager = get_model_manager()
        models = model_manager.list_models()

        model_objects = []
        for m in models:
            model_objects.append(ModelObject(
                id=m["id"],
                owned_by="funasr-api",
            ))

        return ModelsResponse(data=model_objects)
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/audio/transcriptions",
    summary="音频转写",
    description="""将音频文件转写为文本（完全兼容 OpenAI Audio API）。

**支持的音频格式：**
`mp3`, `mp4`, `mpeg`, `mpga`, `m4a`, `wav`, `webm`, `flac`, `ogg`, `amr`, `pcm`

**文件大小限制：**
- 最大支持 300MB（可通过 `MAX_AUDIO_SIZE` 环境变量配置）
- OpenAI 原生限制为 25MB

**输出格式：**
| 格式 | Content-Type | 说明 |
|------|-------------|------|
| `json` | application/json | 简单 JSON，仅含 text 字段（默认） |
| `text` | text/plain | 纯文本 |
| `verbose_json` | application/json | 详细 JSON，含时间戳和分段 |
| `srt` | text/plain | SRT 字幕格式 |
| `vtt` | text/vtt | WebVTT 字幕格式 |

**模型映射：**
- `whisper-1` → 使用默认模型 (sensevoice-small)
- `sensevoice-small` → 速度最快的语音识别，支持多语言混合、情绪识别，准确度适中
- `paraformer-large` → 高精度中文语音识别，内置 VAD + 标点 + 时间戳，对其他语言支持一般，速度适中
- `fun-asr-nano` → 支持识别中文方言、唱歌等，远场高噪声识别优化，速度最慢，准确度适中，有时会有幻觉误识别

**暂不支持的参数：**
`prompt`、`temperature`、`timestamp_granularities` 参数已保留但暂不生效
""",
    responses={
        200: {
            "description": "转写成功",
            "content": {
                "application/json": {
                    "example": {"text": "今天天气不错，明天可能会下雨。"}
                },
                "text/plain": {
                    "example": "今天天气不错，明天可能会下雨。"
                },
            },
        },
        400: {
            "description": "请求错误",
            "content": {
                "application/json": {
                    "example": {"detail": "File too large. Maximum size is 300MB"}
                }
            },
        },
        401: {
            "description": "认证失败",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid API key"}
                }
            },
        },
    },
)
async def create_transcription(
    request: Request,
    file: UploadFile = File(
        ...,
        description="要转写的音频文件，支持 mp3/wav/flac/ogg/m4a/amr/pcm 等格式"
    ),
    model: str = Form(
        "sensevoice-small",
        description="ASR 模型选择",
        json_schema_extra={"enum": ["sensevoice-small", "paraformer-large", "fun-asr-nano"]},
    ),
    language: Optional[str] = Form(
        None,
        description="音频语言代码（ISO-639-1），如 zh/en/ja，不填则自动检测",
        examples=["zh", "en", "ja"],
    ),
    prompt: Optional[str] = Form(None, description="提示文本（暂不支持，保留兼容）"),  # noqa: ARG001
    response_format: ResponseFormat = Form(
        ResponseFormat.JSON,
        description="输出格式",
        examples=["json", "text", "verbose_json", "srt", "vtt"],
    ),
    temperature: Optional[float] = Form(0, description="采样温度（暂不支持，保留兼容）"),  # noqa: ARG001
    timestamp_granularities: Optional[List[str]] = Form(  # noqa: ARG001
        None,
        alias="timestamp_granularities[]",
        description="时间戳粒度（暂不支持，保留兼容）"
    ),
    enable_punctuation: Optional[bool] = Form(
        True,
        description="是否启用标点预测"
    ),
    enable_itn: Optional[bool] = Form(
        True,
        description="是否启用 ITN（数字转换）"
    ),
    max_segment_sec: Optional[float] = Form(
        settings.MAX_SEGMENT_SEC,
        ge=0.1,
        le=55.0,
        description="字幕分段每段最大时长（秒）"
    ),
    min_segment_sec: Optional[float] = Form(
        settings.MIN_SEGMENT_SEC,
        ge=0.01,
        le=55.0,
        description="字幕分段每段最小时长（秒）"
    ),
):
    """音频转写 API (OpenAI Audio API 兼容)"""
    # 标记暂不支持的参数（保留以兼容 OpenAI API）
    _ = (prompt, temperature, timestamp_granularities)

    audio_path = None
    normalized_audio_path = None

    logger.info(f"[OpenAI API] 收到转写请求: model={model}, format={response_format}")

    try:
        # 可选鉴权 (支持 Bearer Token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if settings.APPTOKEN and token != settings.APPTOKEN:
                raise HTTPException(status_code=401, detail="Invalid API key")
        elif settings.APPTOKEN:
            # 如果配置了 APPTOKEN 但请求没有提供
            result, _ = validate_token(request)
            if not result:
                raise HTTPException(status_code=401, detail="Invalid authentication")

        # 读取上传的音频文件
        audio_data = await file.read()
        if not audio_data:
            raise HTTPException(status_code=400, detail="Empty audio file")

        file_size = len(audio_data)
        logger.info(f"[OpenAI API] 音频文件大小: {file_size / 1024 / 1024:.2f}MB")

        # 检查文件大小 (OpenAI 限制 25MB，这里扩展到 100MB)
        if file_size > settings.MAX_AUDIO_SIZE:
            max_mb = settings.MAX_AUDIO_SIZE // 1024 // 1024
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {max_mb}MB"
            )

        # 检测音频格式并保存临时文件
        file_suffix = get_audio_file_suffix(
            audio_address=file.filename,
            audio_data=audio_data
        )
        audio_path = save_audio_to_temp_file(audio_data, file_suffix)
        logger.info(f"[OpenAI API] 临时文件: {audio_path}")

        # 标准化音频格式
        normalized_audio_path = normalize_audio_for_asr(audio_path, target_sr=16000)

        # 获取音频时长
        audio_duration = get_audio_duration(normalized_audio_path)
        logger.info(f"[OpenAI API] 音频时长: {audio_duration:.1f}s")

        # 映射模型 ID
        mapped_model_id = map_model_id(model)

        # 获取 ASR 引擎
        model_manager = get_model_manager()
        asr_engine = model_manager.get_asr_engine(mapped_model_id)

        # 优化：非字幕格式不需要精确的时间戳分段，可以使用更大的 max_segment_sec 以减少切分，提高处理速度
        # 但保留用户通过其他参数（如 enable_punctuation, enable_itn 等）的控制
        actual_max_segment_sec = max_segment_sec
        if response_format in [ResponseFormat.JSON, ResponseFormat.TEXT]:
            # 设置一个较大的值（55秒），模型上限值
            # 这样可以避免 AudioSplitter 进行不必要的 VAD 切分和合并，直接整段（或大段）识别
            actual_max_segment_sec = 55.0
            logger.info(
                f"[OpenAI API] 非字幕格式 ({response_format})，"
                f"自动调整 max_segment_sec={actual_max_segment_sec} 以加速处理"
            )

        # 执行语音识别
        # 注：prompt 参数接收但不使用，FunASR 热词格式与 OpenAI prompt 不兼容
        asr_result = await run_sync(
            asr_engine.transcribe_long_audio,
            audio_path=normalized_audio_path,
            hotwords="",
            enable_punctuation=enable_punctuation,
            enable_itn=enable_itn,
            sample_rate=16000,
            max_segment_sec=actual_max_segment_sec,
            min_segment_sec=min_segment_sec,
        )

        logger.info(f"[OpenAI API] 识别完成: {len(asr_result.text)} 字符")

        # 构建分段信息
        segments = []
        for i, seg in enumerate(asr_result.segments):
            segments.append(TranscriptionSegment(
                id=i,
                seek=int(seg.start_time * 100),
                start=seg.start_time,
                end=seg.end_time,
                text=seg.text,
            ))

        # 检测语言 (简单实现)
        detected_language = language or "zh"
        if not language:
            # 简单的语言检测：检查是否包含中文字符
            import re
            if re.search(r'[\u4e00-\u9fff]', asr_result.text):
                detected_language = "zh"
            else:
                detected_language = "en"

        # 根据 response_format 返回不同格式
        if response_format == ResponseFormat.TEXT:
            clean_text = clean_asr_tags(asr_result.text)
            return PlainTextResponse(content=clean_text)

        elif response_format == ResponseFormat.SRT:
            subtitle_segments = []
            seg_id = 0
            for seg in asr_result.segments:
                split_results = split_text_by_punctuation(
                    seg.text, seg.start_time, seg.end_time
                )
                for text, start, end in split_results:
                    if not text.strip():
                        continue
                    subtitle_segments.append(TranscriptionSegment(
                        id=seg_id,
                        seek=int(start * 100),
                        start=start,
                        end=end,
                        text=text,
                    ))
                    seg_id += 1
            if not subtitle_segments:
                subtitle_segments = [TranscriptionSegment(
                    id=0,
                    start=0,
                    end=audio_duration,
                    text=asr_result.text,
                )]
            srt_content = generate_srt(subtitle_segments)
            return PlainTextResponse(content=srt_content, media_type="text/plain")

        elif response_format == ResponseFormat.VTT:
            subtitle_segments = []
            seg_id = 0
            for seg in asr_result.segments:
                split_results = split_text_by_punctuation(
                    seg.text, seg.start_time, seg.end_time
                )
                for text, start, end in split_results:
                    if not text.strip():
                        continue
                    subtitle_segments.append(TranscriptionSegment(
                        id=seg_id,
                        seek=int(start * 100),
                        start=start,
                        end=end,
                        text=text,
                    ))
                    seg_id += 1
            if not subtitle_segments:
                subtitle_segments = [TranscriptionSegment(
                    id=0,
                    start=0,
                    end=audio_duration,
                    text=asr_result.text,
                )]
            vtt_content = generate_vtt(subtitle_segments)
            return PlainTextResponse(content=vtt_content, media_type="text/vtt")

        elif response_format == ResponseFormat.VERBOSE_JSON:
            return JSONResponse(content=VerboseTranscriptionResponse(
                task="transcribe",
                language=detected_language,
                duration=audio_duration,
                text=asr_result.text,
                segments=[seg.model_dump() for seg in segments],
            ).model_dump())

        else:  # JSON (默认)
            return JSONResponse(content={"text": asr_result.text})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[OpenAI API] 转写失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 清理临时文件
        if audio_path:
            cleanup_temp_file(audio_path)
        if normalized_audio_path and normalized_audio_path != audio_path:
            cleanup_temp_file(normalized_audio_path)
