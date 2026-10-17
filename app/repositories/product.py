from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductRepository:
    # Phương thức tĩnh theo mẫu: nhận session thay vì khởi tạo repository.
    @staticmethod
    def get_all(db: Session):
        return db.query(Product).order_by(Product.id).all()

    @staticmethod
    def get_by_id(db: Session, product_id: int):
        return db.query(Product).filter(Product.id == product_id).first()

    @staticmethod
    def _save(db: Session, product: Product):
        # Commit ghi dữ liệu; refresh lấy ID/thời gian do database tạo.
        try:
            db.add(product)
            db.commit()
            db.refresh(product)
        except Exception:
            db.rollback()
            raise
        return product

    @staticmethod
    def create(db: Session, product_in: ProductCreate):
        # Pydantic 2 dùng model_dump thay cho dict trong mẫu.
        return ProductRepository._save(db, Product(**product_in.model_dump()))

    @staticmethod
    def update(db: Session, db_product: Product, product_in: ProductUpdate):
        # Không ghi đè những trường người dùng không gửi.
        for key, value in product_in.model_dump(exclude_unset=True).items():
            setattr(db_product, key, value)
        return ProductRepository._save(db, db_product)

    @staticmethod
    def delete(db: Session, db_product: Product):
        try:
            db.delete(db_product)
            db.commit()
        except Exception:
            db.rollback()
            raise
        return True
