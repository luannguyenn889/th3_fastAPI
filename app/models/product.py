from sqlalchemy import Column, Integer, String, Text, Numeric, TIMESTAMP
from sqlalchemy.sql import func
from app.database.session import Base

class Product(Base):
    """
    ORM class đại diện cho bảng 'products' trong MySQL.
    Dùng để tương tác trực tiếp với cơ sở dữ liệu (Thêm, Sửa, Xóa, Truy vấn qua SQLAlchemy Session).
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
