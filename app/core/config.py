# -*- coding: utf-8 -*-
"""
统一配置管理
ASR语音识别配置选项
"""

import os
from typing import Optional
from pathlib import Path


class Settings:
    """统一应用配置类"""

    # 应用信息
    APP_NAME: str = "FunASR-API Server"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = """基于 FunASR 的语音识别 API 服务

注意：本通用服务有两个版本，仅 FunASR 应用（地址 funasr-ai.xxx.heiyu.space）内置了全部三个模型！

ASR 通用服务（地址 asr-ai.xxx.heiyu.space）是 slim 版本，仅内置了 sensevoice-small 模型并且不支持 WebSocket 流式识别！运行其他模型或者调用流式识别会报错！

如果你需要使用其他两个模型或者使用 WebSocket 流式识别，请使用 FunASR 应用（下载地址 https://appstore.wl1.heiyu.space/#/shop/detail/cloud.lazycat.aipod.funasr）！
"""

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # 鉴权配置
    APPTOKEN: Optional[str] = None  # 从环境变量APPTOKEN读取，如果为None则鉴权可选
    APPKEY: Optional[str] = None  # 从环境变量APPKEY读取，如果为None则appkey可选

    # 设备配置
    DEVICE: str = "auto"  # auto, cpu, cuda:0, npu:0

    # 路径配置
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    TEMP_DIR: str = "temp"
    DATA_DIR: str = "data"  # 数据持久化目录
    MODELSCOPE_PATH: str = str(BASE_DIR / "models")

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = str(BASE_DIR / "logs" / "funasr-api.log")
    LOG_MAX_BYTES: int = 20 * 1024 * 1024  # 20MB
    LOG_BACKUP_COUNT: int = 50  # 保留50个备份文件

    # ASR模型配置
    DEFAULT_ASR_MODEL_ID: str = "sensevoice-small"
    FUNASR_AUTOMODEL_KWARGS = {
        "trust_remote_code": False,
        "disable_update": True,
        "disable_pbar": True,
        "disable_log": True,
        "local_files_only": True,
    }
    ASR_MODELS_CONFIG: str = str(Path(__file__).parent.parent / "services/asr/models.json")
    ASR_MODEL_MODE: str = "all"  # ASR模型加载模式: realtime, offline, all
    ASR_ENABLE_REALTIME_PUNC: bool = True  # 是否启用实时标点模型（用于中间结果展示）
    AUTO_LOAD_CUSTOM_ASR_MODELS: str = (
        ""  # 启动时自动加载的自定义ASR模型列表（逗号分隔，如: fun-asr-nano）
    )
    VAD_MODEL: str = MODELSCOPE_PATH + "/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
    VAD_MODEL_REVISION: str = "v2.0.4"
    PUNC_MODEL: str = MODELSCOPE_PATH + "/iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch"
    PUNC_MODEL_REVISION: str = "v2.0.4"
    PUNC_REALTIME_MODEL: str = (
        MODELSCOPE_PATH + "/iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727"
    )

    # 语言模型配置
    LM_MODEL: str = MODELSCOPE_PATH + "/iic/speech_ngram_lm_zh-cn-ai-wesp-fst"
    LM_MODEL_REVISION: str = "v2.0.4"
    LM_WEIGHT: float = 0.15  # 语言模型权重，建议范围 0.1-0.3
    LM_BEAM_SIZE: int = 10  # 语言模型解码 beam size
    ASR_ENABLE_LM: bool = True  # 是否启用语言模型（默认启用）

    # 流式ASR远场过滤配置
    ASR_ENABLE_NEARFIELD_FILTER: bool = True  # 是否启用远场声音过滤
    ASR_NEARFIELD_RMS_THRESHOLD: float = 0.01  # RMS能量阈值（宽松模式，适合大多数场景）
    ASR_NEARFIELD_FILTER_LOG_ENABLED: bool = True  # 是否记录过滤日志（默认启用）

    # 音频处理配置
    MAX_AUDIO_SIZE: int = 1024 * 10 * 1024 * 1024  # 10GB
    MAX_SEGMENT_SEC: float = 6.0  # 字幕分段每段最大时长（秒），根据普通对话均值估算
    MIN_SEGMENT_SEC: float = 0.8  # 字幕分段每段最小时长（秒），避免过短的片段，根据普通对话均值估算

    # 视频处理配置
    MAX_VIDEO_SIZE: int = 1024 * 50 * 1024 * 1024  # 50GB

    def __init__(self):
        """从环境变量读取配置"""
        self._load_from_env()
        self._ensure_directories()

    def _load_from_env(self):
        """从环境变量加载配置"""
        # 应用信息
        self.APP_NAME = os.getenv("APP_NAME", self.APP_NAME)
        self.APP_VERSION = os.getenv("APP_VERSION", self.APP_VERSION)
        self.APP_DESCRIPTION = os.getenv("APP_DESCRIPTION", self.APP_DESCRIPTION)

        # 服务器配置
        self.HOST = os.getenv("HOST", self.HOST)
        self.PORT = int(os.getenv("PORT", str(self.PORT)))
        self.DEBUG = os.getenv("DEBUG", str(self.DEBUG)).lower() == "true"

        # 鉴权配置
        self.APPTOKEN = os.getenv("APPTOKEN", self.APPTOKEN)
        self.APPKEY = os.getenv("APPKEY", self.APPKEY)

        # 设备配置
        self.DEVICE = os.getenv("DEVICE", self.DEVICE)

        # 路径配置
        base_dir_env = os.getenv("BASE_DIR")
        if base_dir_env:
            self.BASE_DIR = Path(base_dir_env)

        self.TEMP_DIR = os.getenv("TEMP_DIR", self.TEMP_DIR)
        self.DATA_DIR = os.getenv("DATA_DIR", self.DATA_DIR)
        self.MODELSCOPE_PATH = os.getenv("MODELSCOPE_PATH", self.MODELSCOPE_PATH)

        # 日志配置
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", self.LOG_LEVEL)
        self.LOG_FILE = os.getenv("LOG_FILE", self.LOG_FILE)
        self.LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", str(self.LOG_MAX_BYTES)))
        self.LOG_BACKUP_COUNT = int(
            os.getenv("LOG_BACKUP_COUNT", str(self.LOG_BACKUP_COUNT))
        )

        # ASR模型配置
        self.ASR_MODELS_CONFIG = os.getenv("ASR_MODELS_CONFIG", self.ASR_MODELS_CONFIG)
        self.ASR_MODEL_MODE = os.getenv("ASR_MODEL_MODE", self.ASR_MODEL_MODE)
        self.ASR_ENABLE_REALTIME_PUNC = (
            os.getenv("ASR_ENABLE_REALTIME_PUNC", str(self.ASR_ENABLE_REALTIME_PUNC)).lower() == "true"
        )
        self.AUTO_LOAD_CUSTOM_ASR_MODELS = os.getenv(
            "AUTO_LOAD_CUSTOM_ASR_MODELS", self.AUTO_LOAD_CUSTOM_ASR_MODELS
        )
        self.VAD_MODEL = os.getenv("VAD_MODEL", self.VAD_MODEL)
        self.VAD_MODEL_REVISION = os.getenv("VAD_MODEL_REVISION", self.VAD_MODEL_REVISION)
        self.PUNC_MODEL = os.getenv("PUNC_MODEL", self.PUNC_MODEL)
        self.PUNC_MODEL_REVISION = os.getenv("PUNC_MODEL_REVISION", self.PUNC_MODEL_REVISION)
        self.PUNC_REALTIME_MODEL = os.getenv("PUNC_REALTIME_MODEL", self.PUNC_REALTIME_MODEL)

        # 语言模型配置
        self.LM_MODEL = os.getenv("LM_MODEL", self.LM_MODEL)
        self.LM_MODEL_REVISION = os.getenv("LM_MODEL_REVISION", self.LM_MODEL_REVISION)
        self.ASR_ENABLE_LM = (
            os.getenv("ASR_ENABLE_LM", str(self.ASR_ENABLE_LM)).lower() == "true"
        )
        self.LM_WEIGHT = float(os.getenv("LM_WEIGHT", str(self.LM_WEIGHT)))
        self.LM_BEAM_SIZE = int(os.getenv("LM_BEAM_SIZE", str(self.LM_BEAM_SIZE)))

        # 远场过滤配置
        self.ASR_ENABLE_NEARFIELD_FILTER = (
            os.getenv("ASR_ENABLE_NEARFIELD_FILTER", str(self.ASR_ENABLE_NEARFIELD_FILTER)).lower() == "true"
        )
        self.ASR_NEARFIELD_RMS_THRESHOLD = float(
            os.getenv(
                "ASR_NEARFIELD_RMS_THRESHOLD", str(self.ASR_NEARFIELD_RMS_THRESHOLD)
            )
        )
        self.ASR_NEARFIELD_FILTER_LOG_ENABLED = (
            os.getenv("ASR_NEARFIELD_FILTER_LOG_ENABLED", str(self.ASR_NEARFIELD_FILTER_LOG_ENABLED)).lower() == "true"
        )

        # 音频处理配置
        self.MAX_AUDIO_SIZE = int(
            os.getenv("MAX_AUDIO_SIZE", str(self.MAX_AUDIO_SIZE))
        )
        self.MAX_SEGMENT_SEC = float(os.getenv("MAX_SEGMENT_SEC", str(self.MAX_SEGMENT_SEC)))
        self.MIN_SEGMENT_SEC = float(os.getenv("MIN_SEGMENT_SEC", str(self.MIN_SEGMENT_SEC)))

        # 视频处理配置
        self.MAX_VIDEO_SIZE = int(os.getenv("MAX_VIDEO_SIZE", str(self.MAX_VIDEO_SIZE)))

    def _ensure_directories(self):
        """确保必需的目录存在"""
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        os.makedirs(self.DATA_DIR, exist_ok=True)

    @property
    def models_config_path(self) -> str:
        """获取模型配置文件的完整路径"""
        return str(self.BASE_DIR / self.ASR_MODELS_CONFIG)

    @property
    def docs_url(self) -> Optional[str]:
        """获取文档URL"""
        return "/docs"

    @property
    def redoc_url(self) -> Optional[str]:
        """获取ReDoc URL"""
        return "/redoc"


# 全局配置实例
settings = Settings()
