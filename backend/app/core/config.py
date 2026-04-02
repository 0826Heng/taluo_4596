from __future__ import annotations

import os
from typing import Optional


def env(key: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(key)
    if v is None or v == "":
        return default
    return v


class Settings:
    # 读服务端容器的开关
    debug: bool = (env("DEBUG", "false") or "false").lower() == "true"

    # 认证：小程序侧把 OpenID/UnionID 等标识放到请求头中
    # 你的真实接入中可以改成签名校验或 WeChat 登录回传交换 token。
    openid_header: str = env("OPENID_HEADER", "X-OpenId") or "X-OpenId"

    # API 访问频率限制（简单实现：每个 openid + path）
    rate_limit_per_minute: int = int(env("RATE_LIMIT_PER_MINUTE", "30") or "30")

    # 管理接口
    admin_secret: Optional[str] = env("ADMIN_SECRET")


settings = Settings()

