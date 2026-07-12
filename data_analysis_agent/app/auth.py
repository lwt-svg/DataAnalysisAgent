# JWT验证

import jwt
from typing import Optional
from .config import JWT_SECRET_KEY, JWT_ALGORITHM


def verify_jwt_token(token: str) -> Optional[dict]:
    """验证JWT token并返回payload

    说明：数据分析Agent是B端内部工具，token仅用于识别用户身份，
    不强制验证过期时间（用户已通过Django登录），避免长期使用时token过期导致身份丢失。
    仍验证签名有效性，防止伪造token。
    """
    try:
        if token and token.startswith("Bearer "):
            token = token[7:]
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={'verify_exp': False}  # 不验证过期时间，仅验证签名
        )
        return payload
    except jwt.InvalidSignatureError as e:
        print(f"无效的token签名: {e}")
        return None
    except Exception as e:
        print(f"token验证错误: {e}")
        return None


def get_user_email_from_token(token: Optional[str]) -> Optional[str]:
    """从token中获取用户email"""
    if not token:
        return None
    payload = verify_jwt_token(token)
    if not payload:
        return None
    return payload.get("username")
