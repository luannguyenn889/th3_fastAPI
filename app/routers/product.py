from fastapi import APIRouter, Depends, HTTPException, Path, Response
from sqlalchemy.orm import Session
from app.core.auth import require_user
from app.database.session import get_db
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

# Xác thực chung cho mọi API; controller gọi repository trực tiếp theo mẫu.
router = APIRouter(prefix="/products", tags=["Products"], dependencies=[Depends(require_user)])


def find_product(db: Session, product_id: int):
    # Kiểm tra tồn tại dùng chung cho xem chi tiết, cập nhật và xóa.
    product = ProductRepository.get_by_id(db, product_id)
    if product is None:
        raise HTTPException(404, "Không tìm thấy sản phẩm")
    return product


@router.get("", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    # GET /products: lấy danh sách sản phẩm.
    return ProductRepository.get_all(db)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int = Path(gt=0), db: Session = Depends(get_db)):
    return find_product(db, product_id)


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # Body được kiểm tra trước khi tạo sản phẩm; thành công trả 201.
    return ProductRepository.create(db, product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product: ProductUpdate, product_id: int = Path(gt=0), db: Session = Depends(get_db)):
    # Theo mẫu: cho phép cập nhật từng trường.
    return ProductRepository.update(db, find_product(db, product_id), product)


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int = Path(gt=0), db: Session = Depends(get_db)):
    ProductRepository.delete(db, find_product(db, product_id))
    # Xóa thành công trả 204 không kèm body.
    return Response(status_code=204)
