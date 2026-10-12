# CP1 — Đọc code baseline

1. **Mỗi lần chạy baseline đã có agent_id/run_id và danh tính người dùng để kiểm quyền chưa?**

   Chưa: `_naive_loop()` chỉ nhận `message` và `llm`, không tạo `agent_id` hay `run_id` để xác định từng lần chạy (`agent/loop.py:27`). Dù `run_once()` có tham số `principal_id` mặc định là `support_l1` (`agent/loop.py:58`), khi chuyển sang baseline thì chỉ truyền `message` và `llm`, nên danh tính người dùng không được đưa vào luồng này để kiểm quyền (`agent/loop.py:74`).

2. **Trước http_post, có policy nào kiểm mục đích, quyền và loại dữ liệu không? Ai thực sự quyết định gửi?**

   Không có cổng kiểm mục đích, quyền hay loại dữ liệu trước hai lệnh `read_customer()` và `http_post()` (`agent/loop.py:39`, `agent/loop.py:44`); `http_post()` chỉ kiểm URL thuộc HTTP tại `127.0.0.1:10024`, rồi gửi body được truyền vào (`agent/tools.py:76–84`). Ticket là dữ liệu nhưng baseline xử lý chỉ thị bên trong như lệnh: nó tìm ticket, ghép nội dung rồi đưa vào `find_injection()` (`agent/loop.py:31–34`). Chính kết quả từ `llm.find_injection()` cung cấp mã khách và URL, còn nhánh `if` trong baseline quyết định đọc hồ sơ và gửi khi thu được dữ liệu, chứ không có policy phê duyệt (`agent/loop.py:35–44`).

3. **Dòng nào tạo body POST, và file nào ghi lại việc sink đã nhận body đó?**

   Body POST được tạo ngay tại `agent/loop.py:44` bằng `{"records": collected}`, trong đó `collected` chứa các hồ sơ lấy từ `read_customer()` ở `agent/loop.py:39`; body này được gửi dưới dạng JSON tại `agent/tools.py:84`. Sink ghi dữ liệu nhận được vào `reports/sink.log` (`sink/sink.py:37`), mỗi POST là một dòng JSON gồm `path` và `body` (`sink/sink.py:45–47`). Ở CP2, bản sao `reports/attack-before.log` sẽ giữ bằng chứng trước khi sửa; CP1 này mới đọc code nên chưa khẳng định đã có POST thực tế.
