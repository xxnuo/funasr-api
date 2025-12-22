# -*- coding: utf-8 -*-

import tempfile
import logging
import os
import subprocess
from pydub import AudioSegment
from ..core.config import settings
from ..core.exceptions import DefaultServerErrorException

logger = logging.getLogger(__name__)


def extract_audio_from_video(video_path: str, output_format: str = "wav") -> str:
    try:
        logger.info(f"开始提取视频音频: {video_path}")

        file_size = os.path.getsize(video_path)
        file_size_gb = file_size / (1024 ** 3)

        if file_size_gb > 4:
            logger.info(f"文件大小 {file_size_gb:.2f}GB 超过4GB，使用ffmpeg直接处理")

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f".{output_format}",
                dir=settings.TEMP_DIR
            ) as temp_file:
                output_path = temp_file.name

            cmd = [
                'ffmpeg', '-y', '-i', video_path,
                '-vn', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"ffmpeg处理失败: {result.stderr}")
                raise DefaultServerErrorException("视频音频提取失败: ffmpeg error")
        else:
            video = AudioSegment.from_file(video_path)

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f".{output_format}",
                dir=settings.TEMP_DIR
            ) as temp_file:
                output_path = temp_file.name

            video.export(output_path, format=output_format)

        logger.info(f"音频提取完成: {output_path}")
        return output_path

    except DefaultServerErrorException:
        raise
    except Exception as e:
        logger.error(f"提取音频失败: {str(e)}")
        raise DefaultServerErrorException(f"视频音频提取失败: {str(e)}")
