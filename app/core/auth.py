import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

# Đọc token từ header Authorization: Bearer <token>.
# Tắt lỗi tự động để hàm bên dưới chủ động trả mã 401 khi thiếu token.
bearer = HTTPBearer(auto_error=False)


async def require_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
):
    # FastAPI gọi hàm này trước khi cho phép truy cập các API sản phẩm.
    if credentials is None:
        raise HTTPException(401, "Bearer token is required", headers={"WWW-Authenticate": "Bearer"})
    try:
        # Chuyển token sang service bài 2 để xác thực; giới hạn thời gian chờ
        # để request không bị treo khi service xác thực không phản hồi.
        async with httpx.AsyncClient(timeout=settings.auth_timeout_seconds) as client:
            response = await client.get(
                settings.auth_verify_url,
                headers={"Authorization": f"Bearer {credentials.credentials}"},
            )
    except httpx.RequestError as exc:
        # Không cho truy cập nếu không thể kết nối đến service xác thực.
        raise HTTPException(503, "Authentication service is unavailable") from exc
    if response.status_code in (401, 403):
        # Giữ mã lỗi: 401 là chưa xác thực, 403 là bị từ chối quyền truy cập.
        headers = {"WWW-Authenticate": "Bearer"} if response.status_code == 401 else None
        raise HTTPException(response.status_code, "Token is invalid or access is denied", headers=headers)
    if response.status_code != 200:
        raise HTTPException(503, "Authentication service returned an unexpected response")
    # Hợp đồng repo bài 2: app/routers/auth.py và app/schemas/auth.py
    # https://github.com/luannguyenn889/fastapi-demo
    # GET /auth trả 200 cả khi token sai; phải kiểm tra valid.
    try:
        result = response.json()
    except ValueError as exc:
        raise HTTPException(503, "Authentication service returned an invalid response") from exc
    if not isinstance(result, dict) or type(result.get("valid")) is not bool:
        raise HTTPException(503, "Authentication service returned an invalid response")
    if result["valid"] is False:
        raise HTTPException(401, "Token is invalid or expired", headers={"WWW-Authenticate": "Bearer"})
    user = result.get("user")
    if not isinstance(user, dict) or not isinstance(user.get("sub"), str) or not user["sub"].strip():
        raise HTTPException(503, "Authentication service returned an invalid user")
    return user
