# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field
from typing import Optional


class ExtractAudioRequest(BaseModel):
    output_format: Optional[str] = Field(
        default="wav",
        description="输出音频格式"
    )


class ExtractAudioResponse(BaseModel):
    task_id: str
    audio_url: str
    status: int
    message: str
