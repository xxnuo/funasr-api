from fastapi import APIRouter, Path
from typing import List, Dict

# 创建路由器
compatible_router = APIRouter(tags=["Compatible"], prefix="/api/ps")


@compatible_router.get(
    "",
    summary="该接口为兼容旧版服务的接口，无实际作用，请勿使用！",
    description="该接口为兼容旧版服务的接口，无实际作用，请勿使用！",
    response_model=Dict[str, List[str]],
    response_description="返回可用模型列表",
)
def compatible_get_ps():
    """
    该接口为兼容旧版服务的接口，无实际作用，请勿使用！

    该接口为兼容旧版服务的接口，无实际作用，请勿使用！
    """
    return {
        "models": ["sensevoice-small", "whisper-1", "Systran/faster-whisper-large-v2"]
    }


@compatible_router.post(
    "/{model_id}",
    summary="该接口为兼容旧版服务的接口，无实际作用，请勿使用！",
    description="该接口为兼容旧版服务的接口，无实际作用，请勿使用！",
    response_model=Dict[str, str],
    response_description="操作是否成功",
)
def compatible_post_ps_model_id(model_id: str = Path(..., description="模型ID")):
    """
    该接口为兼容旧版服务的接口，无实际作用，请勿使用！

    本接口兼容历史API，激活指定模型，无实际作用。
    """
    return {"status": "ok"}


@compatible_router.delete(
    "/{model_id}",
    summary="该接口为兼容旧版服务的接口，无实际作用，请勿使用！",
    description="该接口为兼容旧版服务的接口，无实际作用，请勿使用！",
    response_model=Dict[str, str],
    response_description="操作是否成功",
)
def compatible_delete_ps_model_id(model_id: str = Path(..., description="模型ID")):
    """
    该接口为兼容旧版服务的接口，无实际作用，请勿使用！

    该接口为兼容旧版服务的接口，无实际作用，请勿使用！
    """
    return {"status": "ok"}
