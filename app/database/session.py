from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    # Lớp cha của các model; metadata lưu mô tả bảng để tạo bảng trong database.
    pass


# Tạo URL bằng đối tượng để xử lý đúng cả mật khẩu có ký tự đặc biệt.
# PyMySQL là driver kết nối MySQL; utf8mb4 hỗ trợ tiếng Việt và emoji.
database_url = URL.create(
    "mysql+pymysql",
    username=settings.mysql_user,
    password=settings.mysql_password,
    host=settings.mysql_host,
    port=settings.mysql_port,
    database=settings.mysql_database,
    query={"charset": "utf8mb4"},
)
# Kiểm tra kết nối trước khi lấy từ pool, tránh dùng kết nối đã bị MySQL đóng.
engine = create_engine(database_url, pool_pre_ping=True)
# Mỗi session là một đơn vị làm việc với database.
# Chỉ ghi khi chủ động commit; giữ dữ liệu đối tượng sau khi commit.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    # Cấp session cho mỗi request qua Depends; tự đóng sau khi request kết thúc,
    # kể cả khi xảy ra lỗi. Việc commit/rollback do repository xử lý.
    with SessionLocal() as session:
        yield session
