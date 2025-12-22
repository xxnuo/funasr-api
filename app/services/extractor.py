# -*- coding: utf-8 -*-

import tempfile
import logging
from pydub import AudioSegment
from ..core.config import settings
from ..core.exceptions import DefaultServerErrorException

logger = logging.getLogger(__name__)


def extract_audio_from_video(video_path: str, output_format: str = "wav") -> str:
    try:
        logger.info(f"开始提取视频音频: {video_path}")

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

    except Exception as e:
        logger.error(f"提取音频失败: {str(e)}")
        raise DefaultServerErrorException(f"视频音频提取失败: {str(e)}")
