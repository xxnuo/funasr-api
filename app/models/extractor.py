# -*- coding: utf-8 -*-

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class OutputFormat(str, Enum):
    """输出音频格式"""

    PCM = "pcm"
    WAV = "wav"
    OPUS = "opus"
    SPEEX = "speex"
    AMR = "amr"
    MP3 = "mp3"
    AAC = "aac"
    M4A = "m4a"
    FLAC = "flac"
    OGG = "ogg"


class ExtractAudioRequest(BaseModel):
    output_format: Optional[OutputFormat] = Field(
        default=OutputFormat.WAV, description="输出音频格式"
    )


class ExtractAudioResponse(BaseModel):
    """提取音频响应"""

    task_id: str = Field(..., description="任务ID")
    audio_url: str = Field(..., description="音频URL")
    status: int = Field(..., description="状态码")
    message: str = Field(..., description="响应消息")
