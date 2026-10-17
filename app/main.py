from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.session import Base, engine
from app.routers.product import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khi khởi động: tạo bảng còn thiếu theo metadata của các model.
    # Database MySQL phải tồn tại trước; create_all không sửa bảng đã tồn tại.
    Base.metadata.create_all(bind=engine)
    yield
    # Khi ứng dụng dừng: đóng các kết nối còn nằm trong pool.
    engine.dispose()


# Khởi tạo ứng dụng và đăng ký router CRUD; Swagger được cung cấp tại /docs.
app = FastAPI(title="Product Management Service", version="1.0.0", lifespan=lifespan)
app.include_router(router)


@app.get("/", tags=["Service"])
def index():
    # Endpoint giới thiệu service, không yêu cầu đăng nhập.
    return {"service": "Product Management", "docs": "/docs"}
