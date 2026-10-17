from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProductBase(BaseModel):
    # Trường chung: bỏ khoảng trắng và từ chối trường ngoài schema.
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    # Giữ Decimal để giá tương ứng chính xác với DECIMAL(10, 2) trong MySQL.
    price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    quantity: int = Field(ge=0, le=2147483647, strict=True)


class ProductCreate(ProductBase):
    # POST yêu cầu tên, giá và số lượng.
    pass


class ProductUpdate(BaseModel):
    # Theo mẫu: chỉ cập nhật những trường xuất hiện trong body PUT.
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    quantity: int | None = Field(default=None, ge=0, le=2147483647, strict=True)

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        # Bỏ trường là giữ giá trị cũ; chỉ description được phép gửi null.
        for field in ("name", "price", "quantity"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} không được là null")
        return self


class ProductResponse(ProductBase):
    # Đọc thuộc tính của model ORM và bổ sung các trường do database tạo.
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
