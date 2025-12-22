# -*- coding: utf-8 -*-

import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, File, Query, Request, UploadFile
from fastapi.responses import JSONResponse

from ...core.config import settings
from ...core.exceptions import (
    AuthenticationException,
    DefaultServerErrorException,
    InvalidMessageException,
)
from ...core.executor import run_sync
from ...core.security import validate_token
from ...models.extractor import ExtractAudioResponse
from ...services.extractor import extract_audio_from_video
from ...utils.audio import (
    cleanup_temp_file,
)
from ...utils.common import generate_task_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["Extractor"])


@router.post(
    "/extract",
    response_model=ExtractAudioResponse,
    summary="从视频提取音频",
    description="上传视频文件并提取其音频轨道，返回音频文件访问URL",
)
async def extract_audio(
    request: Request,
    file: UploadFile = File(..., description="视频文件"),
    output_format: Optional[str] = Query(default="wav", description="输出音频格式"),
):
    task_id = generate_task_id()
    video_path = None

    logger.info(f"[{task_id}] 收到音频提取请求, output_format={output_format}")

    try:
        result, content = validate_token(request, task_id)
        if not result:
            raise AuthenticationException(content, task_id)

        file_suffix = os.path.splitext(file.filename)[1].lower()
        
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=file_suffix,
            dir=settings.TEMP_DIR
        ) as temp_file:
            video_path = temp_file.name

            total_size = 0
            chunk_size = 1024 * 1024 * 10

            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > settings.MAX_VIDEO_SIZE:
                    temp_file.close()
                    cleanup_temp_file(video_path)
                    max_size_mb = settings.MAX_VIDEO_SIZE // 1024 // 1024
                    raise InvalidMessageException(
                        f"视频文件太大，最大支持{max_size_mb}MB", task_id
                    )

                temp_file.write(chunk)

        logger.info(
            f"[{task_id}] 视频接收完成，大小: {total_size / 1024 / 1024:.2f}MB"
        )
        logger.info(f"[{task_id}] 临时文件已保存: {video_path}")

        extracted_audio_path = await run_sync(
            extract_audio_from_video, video_path, output_format
        )

        audio_filename = os.path.basename(extracted_audio_path)
        audio_url = f"/tmp/{audio_filename}"

        response_data = {
            "task_id": task_id,
            "audio_url": audio_url,
            "status": 20000000,
            "message": "SUCCESS",
        }

        return JSONResponse(content=response_data, headers={"task_id": task_id})

    except (
        AuthenticationException,
        InvalidMessageException,
        DefaultServerErrorException,
    ) as e:
        e.task_id = task_id
        logger.error(f"[{task_id}] 提取音频异常: {e.message}")
        response_data = {
            "task_id": task_id,
            "audio_url": "",
            "status": e.status_code,
            "message": e.message,
        }
        return JSONResponse(content=response_data, headers={"task_id": task_id})

    except Exception as e:
        logger.error(f"[{task_id}] 未知异常: {str(e)}")
        response_data = {
            "task_id": task_id,
            "audio_url": "",
            "status": 50000000,
            "message": f"内部服务错误: {str(e)}",
        }
        return JSONResponse(content=response_data, headers={"task_id": task_id})

    finally:
        if video_path:
            cleanup_temp_file(video_path)
