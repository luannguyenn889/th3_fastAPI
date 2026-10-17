# Hướng dẫn chạy và kiểm thử — Bài thực hành 3

Service quản lý sản phẩm sử dụng FastAPI, MySQL riêng và xác thực token thông qua
service bài 2. Chạy các lệnh dưới đây bằng **PowerShell**, tại thư mục dự án.

## 1. Chuẩn bị môi trường

- Python 3.11 trở lên.
- MySQL đang chạy tại `localhost:3306`.
- Tài khoản MySQL `sa`, mật khẩu `123456`, có quyền trên database `product_management`.
- Service xác thực bài 2 đang chạy và có endpoint kiểm tra Bearer token.

```powershell
Set-Location D:\th3_fastAPI
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Dự án đã có `.venv`, không cần tạo lại. Nếu chưa có môi trường này trên máy khác:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Gọi trực tiếp Python trong `.venv` nên không cần activate môi trường.

## 2. Khởi tạo MySQL

Trong MySQL Workbench, kết nối bằng tài khoản `sa`, mở file `sql/init.sql` và chạy
toàn bộ nội dung. File tạo database `product_management` và bảng `products`.

Hoặc dùng MySQL CLI nếu lệnh `mysql` đã nằm trong PATH:

```powershell
mysql -h localhost -P 3306 -u sa -p
```

Nhập mật khẩu `123456`, sau đó chạy trong **MySQL shell**:

```sql
SOURCE D:/th3_fastAPI/sql/init.sql;
USE product_management;
SHOW TABLES;
DESCRIBE products;
```

Nếu `sa` không có quyền tạo database, dùng tài khoản quản trị để chạy SQL và cấp
quyền thích hợp cho `sa`. Tài khoản `sa` phải tồn tại trong MySQL.

## 3. Cấu hình kết nối và xác thực

Kiểm tra file `.env` ở thư mục gốc:

```dotenv
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=sa
MYSQL_PASSWORD=123456
MYSQL_DATABASE=product_management
AUTH_VERIFY_URL=http://localhost:8000/auth
AUTH_TIMEOUT_SECONDS=5
```

Service bài 2: [fastapi-demo](https://github.com/luannguyenn889/fastapi-demo),
chạy cổng `8000`. Endpoint thực tế là **GET /auth** với Bearer token trong header.

- HTTP `200`, JSON `valid: true` và `user.sub` hợp lệ: cho phép truy cập.
- HTTP `200`, JSON `valid: false`: Product Service trả `401`.
- HTTP `401`/`403`: giữ mã lỗi.
- Lỗi kết nối, timeout hoặc phản hồi sai hợp đồng: trả `503`.

Khởi động lại service sau khi sửa `.env`.

## 4. Chạy service sản phẩm

Khởi động service bài 2 theo hướng dẫn của bài đó. Sau đó mở terminal riêng:

```powershell
Set-Location D:\th3_fastAPI
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Chờ thông báo `Application startup complete`.

- Trang giới thiệu: http://localhost:8001/
- Swagger UI: http://localhost:8001/docs
- OpenAPI JSON: http://localhost:8001/openapi.json

Database phải tồn tại trước khi chạy. Ứng dụng tạo bảng còn thiếu khi khởi động,
nhưng không tự thay đổi cấu trúc bảng đã tồn tại. Nhấn `Ctrl+C` để dừng service.

## 5. Lấy token và thử trên Swagger

1. Gọi `POST http://localhost:8000/login` với JSON `{"userName":"sa","password":"123456"}` hoặc tài khoản hợp lệ của bài 2.
2. Sao chép trường `access_token` từ phản hồi.
3. Mở http://localhost:8001/docs, bấm **Authorize**.
4. Nhập **chỉ giá trị token**, không thêm tiền tố `Bearer`, rồi bấm Authorize.
5. Chọn endpoint, bấm **Try it out**, nhập dữ liệu và bấm **Execute**.

Thực hiện theo thứ tự POST → GET danh sách → GET chi tiết → PUT → DELETE.
Ghi lại `id` từ POST và dùng đúng ID đó trong các bước sau.

| Method | Endpoint | Kết quả thành công |
| --- | --- | --- |
| POST | `/products` | `201`, sản phẩm mới cùng ID và thời gian |
| GET | `/products` | `200`, mảng sản phẩm |
| GET | `/products/{product_id}` | `200`, chi tiết sản phẩm |
| PUT | `/products/{product_id}` | `200`, sản phẩm sau cập nhật |
| DELETE | `/products/{product_id}` | `204`, không có body |

Body tạo sản phẩm:

```json
{
  "name": "Bàn phím cơ",
  "description": "Bàn phím dùng cổng USB",
  "price": "350000.00",
  "quantity": 10
}
```

Body cập nhật từng trường theo cách triển khai của mẫu:

```json
{
  "price": "320000.00",
  "quantity": 8
}
```

Tên và mô tả giữ nguyên vì không được gửi. Muốn xóa mô tả, gửi
`{"description": null}`. Không gửi ID hoặc thời gian trong body.

## 6. Kiểm thử bằng PowerShell

Giữ terminal chạy server mở, dùng terminal mới để chạy các bước sau.
Các biến phải được khai báo trong cùng terminal kiểm thử.

### 6.1. Khai báo token

Đăng nhập trực tiếp theo API của repo bài 2 (tài khoản phải tồn tại trong
database người dùng của bài 2, độc lập với tài khoản kết nối MySQL):

```powershell
$authBaseUrl = 'http://localhost:8000'
$loginBody = @{ userName = 'sa'; password = '123456' } | ConvertTo-Json
$login = Invoke-RestMethod -Method Post -Uri "$authBaseUrl/login" `
    -ContentType 'application/json; charset=utf-8' `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($loginBody))
$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }
$verification = Invoke-RestMethod -Method Get -Uri "$authBaseUrl/auth" -Headers $headers
$verification | ConvertTo-Json -Depth 5
```

Kết quả xác thực phải có `valid: true` và `user.sub` là tên người dùng.
Nếu `valid: false`, không dùng token đó để gọi API sản phẩm. Sau khi đăng nhập:

```powershell
$baseUrl = 'http://localhost:8001'
```

Hoặc nếu đã lấy token trên Swagger bài 2, nhập thủ công:

```powershell
$baseUrl = 'http://localhost:8001'
$token = Read-Host 'Nhập token lấy từ service bài 2'
$headers = @{ Authorization = "Bearer $token" }
```

### 6.2. POST — tạo sản phẩm

```powershell
$createBody = @{
    name = 'Bàn phím cơ'
    description = 'Bàn phím dùng cổng USB'
    price = '350000.00'
    quantity = 10
} | ConvertTo-Json

$created = Invoke-RestMethod -Method Post -Uri "$baseUrl/products" `
    -Headers $headers -ContentType 'application/json; charset=utf-8' `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($createBody))

$created | ConvertTo-Json
$productId = $created.id
```

Mong đợi HTTP `201`; có `id`, `created_at`, `updated_at`. Giá trả về dạng chuỗi
Decimal. `Invoke-RestMethod` hiển thị body; dùng Swagger để xem mã HTTP trực tiếp.

### 6.3. GET — danh sách sản phẩm

```powershell
Invoke-RestMethod -Method Get -Uri "$baseUrl/products" -Headers $headers |
    ConvertTo-Json -Depth 5
```

Mong đợi HTTP `200`; danh sách có sản phẩm vừa tạo. Nếu chưa có dữ liệu,
API trả mảng rỗng `[]`.

### 6.4. GET — chi tiết sản phẩm

```powershell
Invoke-RestMethod -Method Get -Uri "$baseUrl/products/$productId" -Headers $headers |
    ConvertTo-Json
```

Mong đợi HTTP `200`; ID và thông tin khớp với sản phẩm vừa tạo.

### 6.5. PUT — cập nhật giá và số lượng

```powershell
$updateBody = @{ price = '320000.00'; quantity = 8 } | ConvertTo-Json
Invoke-RestMethod -Method Put -Uri "$baseUrl/products/$productId" `
    -Headers $headers -ContentType 'application/json; charset=utf-8' `
    -Body ([System.Text.Encoding]::UTF8.GetBytes($updateBody)) |
    ConvertTo-Json
```

Mong đợi HTTP `200`; giá `320000.00`, số lượng `8`; tên, mô tả và ngày tạo
giữ nguyên. `updated_at` có thể trùng thời gian cũ nếu cập nhật trong cùng giây.

Có thể kiểm tra trực tiếp trong MySQL **trước khi xóa**, thay `<ID>` bằng ID thật:

```sql
SELECT * FROM product_management.products WHERE id = <ID>;
```

### 6.6. DELETE — xóa sản phẩm

```powershell
Invoke-RestMethod -Method Delete -Uri "$baseUrl/products/$productId" -Headers $headers
```

Mong đợi HTTP `204`, không có body. Gọi lại GET chi tiết với cùng ID phải trả
`404`. PowerShell sẽ báo lỗi HTTP với phản hồi này; đó là kết quả mong đợi.

## 7. Các trường hợp lỗi cần thử

Để phân biệt lỗi dữ liệu với lỗi xác thực, dùng token hợp lệ khi thử `404`/`422`.
Dùng Swagger để đọc cả mã HTTP và trường `detail` trong phản hồi.

| Tình huống | Cách thử | Kết quả |
| --- | --- | --- |
| Thiếu token | Logout trong Authorize rồi GET `/products` | `401` |
| Token sai/hết hạn | Authorize bằng token không hợp lệ | `401` khi bài 2 trả `valid: false` |
| Bị từ chối quyền | Token mà bài 2 từ chối bằng `403` | `403` |
| Không tìm thấy | GET/PUT/DELETE ID vừa xóa | `404` |
| ID không hợp lệ | GET `/products/0` hoặc `/products/abc` | `422` |
| Thiếu trường bắt buộc | POST chỉ có `{"name":"Test"}` | `422` |
| Tên rỗng | POST tên `"   "`, giá/số lượng hợp lệ | `422` |
| Giá âm | POST giá `"-1.00"` | `422` |
| Quá 2 chữ số thập phân | POST giá `"1.001"` | `422` |
| Vượt DECIMAL(10, 2) | POST giá `"100000000.00"` | `422` |
| Số lượng sai | POST quantity `-1`, `1.5` hoặc `"10"` | `422` |
| Gửi null vào trường bắt buộc | PUT `{"price":null}` | `422` |
| Gửi trường không có trong schema | PUT `{"id":999}` | `422` |
| Auth Service không chạy | Dừng bài 2 rồi GET với Bearer token | `503` |

Giá bằng `0` và số lượng bằng `0` là hợp lệ. PUT `{}` giữ nguyên dữ liệu.
Sau khi thử lỗi, gọi GET chi tiết để kiểm tra dữ liệu cũ không bị thay đổi.

## 8. Chạy bộ kiểm thử tự động

```powershell
Set-Location D:\th3_fastAPI
.\.venv\Scripts\python.exe -m pytest -q
```

Bộ kiểm thử bao gồm: CRUD, dữ liệu sai, cập nhật từng trường,
thiếu token, phản hồi xác thực và lỗi kết nối Auth Service.
Kiểm thử dùng SQLite tạm và giả lập service xác thực, không sửa dữ liệu MySQL.
Để kiểm tra tích hợp MySQL và bài 2 thực tế, thực hiện các bước thủ công ở trên.

## 9. Xử lý lỗi khởi chạy

| Lỗi | Cách xử lý |
| --- | --- |
| Không tìm thấy Python trong `.venv` | Kiểm tra Python đã cài; sửa môi trường bằng `python -m venv .venv`, rồi cài requirements |
| `ModuleNotFoundError` | Cài requirements bằng đúng Python trong `.venv` |
| `Can't connect to MySQL server` | Khởi động MySQL, kiểm tra host và cổng trong `.env` |
| `Access denied for user 'sa'` | Kiểm tra tài khoản, mật khẩu và quyền MySQL |
| `Unknown database 'product_management'` | Chạy `sql/init.sql` trước khi chạy server |
| `503` khi gọi API sản phẩm | Kiểm tra bài 2 đang chạy, URL xác thực và hợp đồng phản hồi |
| Cổng `8001` đã được sử dụng | Dừng tiến trình service cũ hoặc dùng cổng khác và sửa URL kiểm thử tương ứng |

## 10. Nội dung minh chứng cho báo cáo

Chụp kết quả Swagger của POST, GET danh sách, GET chi tiết, PUT và DELETE;
kèm GET sau xóa trả `404`, thiếu token trả `401` và dữ liệu sai trả `422`.
Chụp cấu trúc bảng `products` cùng dữ liệu sau tạo/cập nhật trong MySQL.
Nêu rõ Product Service chạy cổng `8001`, dùng database `product_management`
và gọi Auth Service bài 2 qua HTTP để xác thực.
