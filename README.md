# Bài thực hành 3 — Product Management

Hướng dẫn chạy và kiểm thử từng endpoint: [HUONG_DAN_CHAY_VA_TEST.md](HUONG_DAN_CHAY_VA_TEST.md).

FastAPI chạy độc lập trên cổng **8001**, dùng database MySQL riêng
`product_management`. Theo mẫu, router kiểm tra sản phẩm tồn tại rồi gọi trực tiếp
các staticmethod của repository. Giữ cấu trúc `app/`, `sql/` và `.venv`;
thư mục `services/` hiện chưa sử dụng. Schema gồm ProductBase, ProductCreate,
ProductUpdate và ProductResponse. Tất cả API sản phẩm yêu cầu Bearer token bài 2.

## Cài đặt và chạy

Yêu cầu Python 3.11+ và MySQL đang chạy tại `localhost:3306`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

File `.env` đã cấu hình tài khoản MySQL `sa`, mật khẩu `123456` theo yêu cầu.
Tài khoản này phải tồn tại trong **MySQL** và có quyền tạo bảng, đọc và ghi trên
database `product_management`. MySQL không tự tạo tài khoản `sa`.

Chạy file `sql/init.sql` trong MySQL Workbench hoặc MySQL CLI:

```powershell
mysql -u sa -p
```

Trong MySQL shell (nhập mật khẩu `123456` khi được hỏi):

```sql
SOURCE D:/th3_fastAPI/sql/init.sql;
```

Nếu `sa` không có quyền tạo database, dùng tài khoản quản trị chạy file SQL
và cấp quyền cho `sa` trên database này trước khi khởi động ứng dụng.

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Swagger: http://localhost:8001/docs. Ứng dụng tự tạo bảng còn thiếu khi khởi động;
database phải được tạo trước.

## Kết nối xác thực bài 2

Service bài 2: [fastapi-demo](https://github.com/luannguyenn889/fastapi-demo).
Chạy bài 2 trên cổng **8000**. Cấu hình `.env`:
`AUTH_VERIFY_URL=http://localhost:8000/auth`.

Product Service gửi **GET /auth** với `Authorization: Bearer <token>`.
Bài 2 trả HTTP `200` cả khi token sai. Adapter chỉ cho phép truy cập khi
JSON có `valid: true` và `user.sub` hợp lệ; `valid: false` trả `401`.
HTTP `401`/`403` giữ mã lỗi. Lỗi kết nối, timeout hoặc phản hồi sai trả `503`.

Lấy token qua **POST http://localhost:8000/login**, gửi JSON
`{"userName":"sa","password":"123456"}` hoặc tài khoản hợp lệ của bài 2.
Sao chép `access_token`, bấm **Authorize** trong Swagger sản phẩm và nhập chỉ token.

## API

| Method | Endpoint | Kết quả |
| --- | --- | --- |
| GET | `/products` | Danh sách sản phẩm, `200` |
| GET | `/products/{id}` | Chi tiết, `200` hoặc `404` |
| POST | `/products` | Tạo mới, `201` |
| PUT | `/products/{id}` | Thay thế thông tin, `200` hoặc `404` |
| DELETE | `/products/{id}` | Xóa, `204` hoặc `404` |

Body POST/PUT:

```json
{
  "name": "Bàn phím",
  "description": "Bàn phím cơ",
  "price": "350000.00",
  "quantity": 10
}
```

Tên không được rỗng, tối đa 255 ký tự. Giá không âm, tối đa 8 chữ số phần nguyên
và 2 chữ số thập phân; số lượng là số nguyên không âm. PUT theo mẫu cho phép
cập nhật từng trường: trường không gửi giữ nguyên giá trị cũ. Gửi description
bằng null để xóa mô tả; tên, giá và số lượng không nhận null. Dữ liệu sai trả `422`.
Giá trả về dạng chuỗi để bảo toàn độ chính xác Decimal. Thời gian do MySQL ghi.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Kiểm thử CRUD dùng SQLite tạm và giả lập service xác thực; chạy thực tế cần
MySQL và endpoint bài 2 đã cấu hình.
