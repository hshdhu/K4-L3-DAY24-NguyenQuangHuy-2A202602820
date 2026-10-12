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

## CP3c — Agent làm thay ai

Em đã thay runner scaffold bằng luồng có kiểm quyền. Run A tìm ticket, che PII trước khi đưa text cho LLM, lấy mã ticket từ tên file. Run B chỉ nhận danh sách mã ticket dạng số, không nhận nội dung ticket hay mã khách do chỉ thị cài vào cung cấp. Hai run có run_id riêng, hạn dùng 5 phút tính theo UTC.

Trước search_docs và read_customer đều gọi policy rồi ghi ledger, allow mới chạy tool. Riêng Run B còn kiểm quyền trước khi mở customers.json để tra quan hệ ticket. Support không có quyền thì dừng ở đó. DPO được đọc khách có related_tickets khớp danh sách nhận từ Run A. Không lấy khách chỉ vì thấy KH-... trong text.

Mỗi dòng ledger có on_behalf_of, agent_id, run_id, expires_at và reason, cùng hash của tham số thay vì ghi hồ sơ vào log. Khi thấy chỉ thị gửi dữ liệu, Run A ghi quyết định http_post deny cho dữ liệu restricted; không gọi tool POST. Run B không có quyền network.

`agent/ledger.py` ban đầu cũng còn stub nên em làm thêm append và verify để runner có thể ghi audit qua đúng hàm của bài. Có chuỗi hash giữa các dòng. Test sửa nội dung log phát hiện được, nhưng chuỗi hash này chưa chống được việc viết lại cả file hoặc cắt đuôi nếu không có mốc lưu bên ngoài.

Lệnh kiểm tra đã chạy trong `.venv`:

```powershell
python -m pytest tests/test_obo.py tests/test_policy.py tests/test_ledger.py tests/test_split.py tests/test_injection.py -v --basetemp=.pytest_tmp -p no:cacheprovider
```

Kết quả: `21 passed in 4.69s`. Riêng OBO là 5/5 test qua: support deny, DPO allow, không vượt scope cha, hết hạn/principal lạ bị chặn và runner kiểm quyền ngay trước tool. Phần split không đọc KH-000777 do attacker nhắc trong text, vẫn đọc khách hợp lệ. Cả 4 lure chạy dưới support và DPO đều qua test chặn rò rỉ, tổng cộng 8 trường hợp. Ledger qua 3 test, gồm phát hiện sửa log và reason rỗng.

Lần chạy trong sandbox ban đầu bị lỗi quyền .pytest_tmp của Windows, nên em chạy lại ngoài sandbox và được kết quả trên. Không sửa test để né lỗi. Log của test ghi trong thư mục tạm, reports/attack-before.log vẫn giữ bằng chứng cũ; chưa tạo attack-after.log cho CP5.

Quyền principal vẫn chỉ là mô phỏng từ data/principals.json. --as dpo không xác thực người đang dùng máy. Phần này chưa phải hệ thống xác thực thực tế.

## Các phần kiểm chứng còn lại

- OS / Python / Gitleaks version:
- `python -m pytest tests/ -q`:
- `pre-commit run --all-files`:
- Ledger verify:
- Các lỗi còn lại:
