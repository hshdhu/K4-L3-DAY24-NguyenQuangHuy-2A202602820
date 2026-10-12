# Verification — điền trước khi nộp

## CP3a — Nhận diện và che PII

Em dùng regex trong `agent/pii.py` cho 4 loại: CCCD, điện thoại, tài khoản và email. Tài khoản có nhãn STK hoặc số tài khoản được xét trước CCCD/điện thoại, nên một số không bị báo hai loại. Email cũng xét trước để không lấy riêng dãy số trong địa chỉ email.

`start` và `end` lấy trực tiếp từ chuỗi gốc, chỉ cắt phần giá trị, không lấy nhãn STK. Hàm `redact()` thay từ cuối về đầu bằng `[REDACTED_<TYPE>]`. Làm vậy các vị trí phía trước không bị lệch.

Lệnh chạy trong `.venv`:

```powershell
python -m pytest tests/test_pii.py -v -s --basetemp=.pytest_tmp
```

Môi trường: Windows, Python 3.12.10, pytest 9.1.1. Kết quả:

```text
[pii] gold=118 pred=118 tp=118
[pii] precision=1.000 recall=1.000
2 passed, 1 warning
```

Precision và recall đều 100% trên bộ mẫu này. Recall vượt 95%, thuộc mức cao nhất của phần PII trong rubric. Có một cảnh báo pytest không ghi được cache do quyền thư mục, hai test vẫn chạy xong và pass.

Em kiểm thêm 5 trường hợp bằng `text[start:end]`: STK 12 số trùng dạng CCCD, STK trùng dạng điện thoại, điện thoại có dấu cách/gạch ngang, email chứa dãy số và dãy 17 số không hợp lệ. Các kiểm tra đều qua, phần che nhiều vùng trong cùng câu cũng đúng.

Giới hạn: regex mới nhận dạng theo hình thức, không xác minh số đó có thật hay không. Tài khoản cần đứng ngay sau nhãn STK/số tài khoản (có thể có dấu phân cách); thiếu nhãn thì có thể bỏ sót hoặc nhầm với loại khác. CCCD 12 số không có nhãn vẫn được nhận, nên một mã khác cùng dạng cũng có thể bị che nhầm. Chưa hỗ trợ số điện thoại dạng +84, CCCD có dấu cách, tên người hay các cách viết né bằng ký tự ẩn. Email chỉ xử lý dạng Latin thông dụng. Kết quả 100% ở bộ mẫu chưa nói được dữ liệu thực tế cũng đạt như vậy.

## Các phần kiểm chứng còn lại

- OS / Python / Gitleaks version:
- `python -m pytest tests/ -q`:
- `pre-commit run --all-files`:
- Ledger verify:
- Các lỗi còn lại:
