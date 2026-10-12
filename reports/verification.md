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

## CP3b — Cổng quyết định cho tool

Em đã viết `check()` trong `agent/policy.py`. Đầu tiên kiểm loại dữ liệu, chỉ nhận public/internal/restricted. Restricted mà run bật egress thì chặn luôn. DPO cũng vậy.

Các lời gọi còn lại phải có principal trong `data/principals.json`, đúng mục đích và tool được phép. Tool phải nằm trong scope của agent, nếu có ủy quyền thì phải nằm thêm trong scope của agent cha. Hạn dùng cần có múi giờ UTC và chưa hết hạn. Cả allow lẫn deny đều trả lý do, không để trống.

Lệnh đã chạy trong `.venv`:

```powershell
python -m pytest tests/test_policy.py -v --basetemp=.pytest_tmp -p no:cacheprovider
```

Kết quả: `4 passed in 0.02s`. Hai test restricted + egress đều deny, gồm cả trường hợp DPO có đủ quyền. Tìm ticket internal hợp lệ được allow, public + egress cũng được allow khi đủ các điều kiện còn lại. Không phải chặn hết. Em tắt phần cache của pytest để tránh lỗi quyền thư mục đã gặp ở CP3a.

Em kiểm thêm 12 trường hợp trực tiếp: DPO hợp lệ, loại dữ liệu lạ, support đọc hồ sơ, principal lạ, sai mục đích, thiếu scope agent, thiếu scope cha, ủy quyền hợp lệ, hết hạn, thiếu hạn, hạn không có múi giờ và hạn khác UTC. Đều ra đúng allow/deny dự kiến, có reason.

Phần này mới là hàm quyết định. Runner vẫn scaffold, chưa đặt cổng trước tool thật hay ghi ledger; việc đó làm tiếp ở CP3c. Principal trong JSON cũng chỉ là quyền giả lập của bài, chưa xác thực người dùng thật.

## Các phần kiểm chứng còn lại

- OS / Python / Gitleaks version:
- `python -m pytest tests/ -q`:
- `pre-commit run --all-files`:
- Ledger verify:
- Các lỗi còn lại:
