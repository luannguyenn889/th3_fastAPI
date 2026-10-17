from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Đọc cấu hình từ biến môi trường hoặc file .env; bỏ qua khóa không sử dụng.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Thông tin kết nối database riêng của service quản lý sản phẩm.
    mysql_host: str = "localhost"
    mysql_port: int = Field(default=3306, ge=1, le=65535)
    mysql_user: str = "sa"
    mysql_password: str = "123456"
    mysql_database: str = "product_management"
    # GET /auth của service fastapi-demo (bài thực hành 2).
    auth_verify_url: str = "http://localhost:8000/auth"
    auth_timeout_seconds: float = Field(default=5, gt=0)


# Tạo cấu hình dùng chung khi ứng dụng được import.
settings = Settings()
