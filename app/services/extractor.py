# -*- coding: utf-8 -*-
import logging
import os
import subprocess
import tempfile

from ..core.config import settings
from ..core.exceptions import DefaultServerErrorException

logger = logging.getLogger(__name__)


def extract_audio_from_video(video_path: str, output_format: str = "wav") -> str:
    output_path = None
    try:
        logger.info(f"开始提取视频音频: {video_path}")

        if not os.path.exists(video_path):
            raise DefaultServerErrorException(f"视频文件不存在: {video_path}")

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{output_format}",
            dir=settings.TEMP_DIR
        ) as temp_file:
            output_path = temp_file.name

        format_configs = {
            "pcm": ["-acodec", "pcm_s16le", "-f", "s16le"],
            "wav": ["-acodec", "pcm_s16le"],
            "opus": ["-acodec", "libopus", "-b:a", "64k"],
            "speex": ["-acodec", "libspeex"],
            "amr": ["-acodec", "libopencore_amrnb", "-ar", "8000"],
            "mp3": ["-acodec", "libmp3lame", "-b:a", "128k"],
            "aac": ["-acodec", "aac", "-b:a", "128k"],
            "m4a": ["-acodec", "aac", "-b:a", "128k"],
            "flac": ["-acodec", "flac"],
            "ogg": ["-acodec", "libvorbis", "-b:a", "128k"],
        }

        codec_args = format_configs.get(output_format, ["-acodec", "pcm_s16le"])

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vn",
            *codec_args,
            "-ar", "16000",
            "-ac", "1",
            "-y",
            output_path
        ]

        logger.info(f"执行 FFmpeg 命令: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=6000 * 2,  # 2 hours
            check=False
        )

        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            logger.error(f"FFmpeg 执行失败: {error_msg}")

            if output_path and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception as cleanup_err:
                    logger.warning(f"清理临时文件失败: {cleanup_err}")

            if "Invalid data found" in error_msg or "does not contain any stream" in error_msg:
                raise DefaultServerErrorException("视频文件格式无效或不包含音频流")
            elif "No such file or directory" in error_msg:
                raise DefaultServerErrorException("FFmpeg 未安装或视频文件路径无效")
            else:
                raise DefaultServerErrorException(f"音频提取失败: {error_msg[:200]}")

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            if output_path and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            raise DefaultServerErrorException("音频提取失败: 输出文件为空")

        logger.info(f"音频提取完成: {output_path}")
        return output_path

    except DefaultServerErrorException:
        raise
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg 执行超时")
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception:
                pass
        raise DefaultServerErrorException("音频提取超时,请检查视频文件大小")
    except Exception as e:
        logger.error(f"提取音频失败: {str(e)}")
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except Exception:
                pass
        raise DefaultServerErrorException(f"视频音频提取失败: {str(e)}")
