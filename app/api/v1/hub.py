# -*- coding: utf-8 -*-
"""API v1版本路由"""

from fastapi import APIRouter
from .asr import router as asr_router
from .websocket_asr import router as websocket_asr_router
from .openai_compatible import router as openai_router
from .extractor import router as extractor_router

api_router = APIRouter()

# 原有 API (阿里云兼容)
api_router.include_router(asr_router)
api_router.include_router(websocket_asr_router)

# OpenAI 兼容 API
api_router.include_router(openai_router)

# 视频提取音频 API，不使用，改为微服 Golang 版本
# api_router.include_router(extractor_router)
