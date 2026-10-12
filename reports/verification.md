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

## CP3d — Tách luồng và chặn injection

Em kiểm lại runner theo yêu cầu bước này. Phần split đã làm cùng CP3c nên không cần sửa thêm code. Run A chỉ gọi search_docs, lấy số ticket từ tên file, ví dụ ticket-007.md thành 7. Nội dung ticket được che PII trước khi đưa cho LLM tóm tắt. Không lấy mã khách từ lời attacker để chuyển sang Run B.

Run B chỉ nhận danh sách số ticket cùng thông tin quyền của lần chạy, không có text ticket. Sau khi policy allow mới mở dữ liệu riêng để tra related_tickets, rồi kiểm policy lần nữa trước mỗi read_customer. Vì vậy KH-000777 xuất hiện trong text cũng không đủ để agent đọc hồ sơ này. Còn khách thật sự gắn với ticket vẫn đọc được nếu principal có quyền.

Khi phát hiện chỉ thị gửi, runner kiểm riêng http_post với restricted và egress=True. Tham số lượt kiểm chỉ có URL sink localhost, không mang hồ sơ. Policy deny thì ghi ledger với reason, không gọi tools.http_post.

Hai lệnh đã chạy trong .venv:

```powershell
python -m pytest tests/test_split.py -v --basetemp=.pytest_tmp -p no:cacheprovider
python -m pytest tests/test_injection.py -v --basetemp=.pytest_tmp -p no:cacheprovider
```

Kết quả split: `1 passed in 2.64s`. Test theo dõi read_customer, xác nhận KH-000777 chưa từng được đọc và vẫn có khách hợp lệ được đọc. Đây là chặn ngay từ việc chọn hồ sơ, không chỉ giữ dữ liệu lại sau khi đã đọc nhầm.

Kết quả injection: `8 passed in 3.65s`, không có SKIP. Đủ 4 lure chạy với cả support_l1 và dpo, không có PII tới sink. Support bị chặn quyền đọc hồ sơ; DPO vẫn được đọc hồ sơ liên quan, còn lượt gửi restricted bị policy chặn. Không chặn tất cả để lấy test pass.

Test chạy ngoài sandbox do lỗi quyền thư mục tạm Windows đã gặp trước đó, tắt cache pytest. Log test nằm trong thư mục tạm. Chưa chạy CLI tạo ledger thật hay attack-after.log ở bước này; bằng chứng attack-before.log vẫn giữ nguyên.

## CP3e — Kiểm ledger

Ledger đã viết cùng CP3c, lần này em chạy kiểm lại và tạo log thật. append thêm prev_hash rồi tính SHA-256 từ dòng chưa có hash, dùng json.dumps với sort_keys=True. verify kiểm reason, liên kết dòng trước và hash từng dòng. Runner ghi cả allow/deny, tham số chỉ lưu args_hash, không lưu hồ sơ khách.

Lệnh test:

```powershell
python -m pytest tests/test_ledger.py -v --basetemp=.pytest_tmp -p no:cacheprovider
```

Kết quả `3 passed in 0.04s`. Chạy ngoài sandbox vì lỗi quyền thư mục tạm Windows đã gặp trước đó.

Sau đó chạy CLI thật qua runner mới:

```powershell
python -m agent.loop --mock --as dpo "Tổng hợp các ticket còn mở tuần này"
python -c "from agent.ledger import verify; from pathlib import Path; print(verify(Path('reports/ledger.jsonl')))"
```

Agent tổng hợp 45 file ticket. verify trả `True`, ledger hiện có 24 dòng. Dòng `reports/ledger.jsonl:2` có tool=http_post, decision=deny, on_behalf_of=dpo. Reason là `Restricted data cannot be used in a run with egress enabled`. Có lý do rõ, không gửi POST.

Em sao chép ledger rồi thêm một ký tự X vào reason ở dòng 13, giữ nguyên hash. verify bản sửa trả `False`. Bản gốc vẫn `True`; bản thử đã xóa, không sửa bằng chứng thật.

Chạy thêm thì số dòng sẽ tăng. Hash chain này phát hiện sửa dòng khi chưa tính lại hash, nhưng không tự phát hiện xóa dòng cuối hay viết lại cả chuỗi. Muốn kiểm kiểu đó cần mốc tin cậy bên ngoài file.

## CP4 — Supply chain và token giả

Gitleaks 8.30.1, pre-commit 4.6.2, Python vẫn 3.12.10. Ban đầu chưa có gitleaks trong PATH nên tải release chính thức, đặt vào .venv/Scripts. Kích hoạt .venv thì dùng được lệnh gitleaks.

Các lệnh đã chạy (dùng Python của .venv):

```powershell
gitleaks version
gitleaks git --config .gitleaks.toml --redact .
gitleaks dir --config .gitleaks.toml --redact .
python -m piptools compile --generate-hashes -o requirements.lock requirements.txt
python -m pip install --require-hashes -r requirements.lock
python -m pip install --require-hashes --force-reinstall -r requirements.lock
pre-commit install
pre-commit run --all-files
python -m pytest tests/test_supply_chain.py -v --basetemp=.pytest_tmp -p no:cacheprovider
```

Quét lịch sử: 11 commit, 1 finding, exit 1. Token giả ở commit 1bdd849, file lab-fake-secret.txt dòng 1, rule lab24-synthetic-token. Quét file hiện tại: sạch, exit 0. Không cần chỉnh .gitleaks.toml. Chi tiết ghi ở reports/secrets-incident.md.

Lock tạo thành công, cài với hash thành công. Cài lại thêm để kiểm hash gói thật sự, không chỉ báo đã có sẵn. Hook pin v8.30.1, gitleaks-system, pass_filenames=false; đã install, run --all-files báo Passed. Test supply chain `3 passed in 0.03s`. Test chạy ngoài sandbox vì quyền thư mục tạm Windows.

## CP5 — Chạy lại sau sửa

Reset sink trước test, rồi chạy:

```powershell
python sink/sink.py --reset
python -m pytest tests/ -q --basetemp=.pytest_tmp -p no:cacheprovider
```

Kết quả `33 passed in 4.80s`, 0 fail, 0 skip. Chạy ngoài sandbox để tránh lỗi quyền thư mục tạm Windows. Sau test em reset sink lần nữa, bật server localhost trong nền rồi chạy CLI, đúng luồng runner mới:

```powershell
python -m agent.loop --mock --as dpo "Tổng hợp các ticket còn mở tuần này"
Copy-Item -LiteralPath reports/sink.log -Destination reports/attack-after.log
(Get-Item reports/attack-after.log).Length
```

Agent tổng hợp 45 file ticket. attack-after.log có 0 byte. Sink đang nghe trong lúc replay, đã tắt sau khi lấy log. Không dùng log tự reset của pytest làm bằng chứng này.

Kiểm cuối: python -m agent.check_lure corpus/ticket-90*.md báo 4/4 lure sẵn sàng; pre-commit run --all-files báo Passed. git diff --check sạch sau khi bỏ một dòng trắng dư cuối báo cáo lure.

attack-before.log vẫn có 4 dòng POST với KH-000999 giả. Ledger sau replay có 48 dòng, verify trả True, mọi dòng có reason. Dòng 26 ghi http_post deny, on_behalf_of=dpo, reason là Restricted data cannot be used in a run with egress enabled. Dòng 2 là lượt deny cũ từ CP3e, không xóa đi.

Đã bổ sung kết quả sau sửa cho 4 lure trong injection-corpus.md. Log rỗng là replay chung cả corpus; kết quả riêng từng lure dựa trên 8 test injection. compliance-mapping.md có link nguồn chính thức và số dòng thật; điều khoản pháp luật cụ thể chưa xác minh từ toàn văn nên ghi rõ. dpia-lite.md chỉ mô tả học tập.

## Các phần kiểm chứng còn lại

- OS / Python / Gitleaks version: Windows / 3.12.10 / 8.30.1.
- `python -m pytest tests/ -q`: 33 passed, 0 fail, 0 skip ở CP5.
- `pre-commit run --all-files`: Passed ở CP4.
- Ledger verify: `True` ở CP5, 48 dòng; bản sao sửa dòng 13 ở CP3e trả `False`.
- Các lỗi còn lại: không có test fail. NOT_VERIFIED: điều khoản pháp luật cụ thể và mức tuân thủ hệ thống thật; bài chỉ có mock và dữ liệu giả.
