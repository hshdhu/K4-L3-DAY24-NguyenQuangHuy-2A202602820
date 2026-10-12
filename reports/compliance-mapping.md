# CP5 — Đối chiếu control

Bảng này đối chiếu bài lab với các chủ đề, không phải chứng nhận tuân thủ. Em kiểm được nguồn chính thức bên dưới. Điều khoản pháp luật cụ thể chưa xác minh từ toàn văn nên không ghi số điều.

| Nguồn / chủ đề | Control đã làm | Bằng chứng file:dòng thật | Giới hạn |
|---|---|---|---|
| [Luật 91/2025/QH15 — Bảo vệ dữ liệu cá nhân](https://congbao.chinhphu.vn/van-ban/luat-so-91-2025-qh15-45578.htm) | Che PII trước tóm tắt, chặn gửi restricted | agent/pii.py:69; agent/runner.py:91; agent/policy.py:63 | Điều khoản cụ thể chưa xác minh. Chỉ dùng dữ liệu giả, chưa đánh giá căn cứ xử lý hay quyền chủ thể dữ liệu. |
| [NĐ 356/2025/NĐ-CP — hướng dẫn bảo vệ dữ liệu cá nhân](https://congbao.chinhphu.vn/van-ban/nghi-dinh-so-356-2025-nd-cp-468371/61065.htm) | Kiểm quyền đọc hồ sơ và ghi quyết định vào audit | agent/runner.py:131; agent/runner.py:120; reports/ledger.jsonl:26 | Điều khoản cụ thể chưa xác minh. Ledger một file chưa thay cho quy trình quản trị hay hồ sơ pháp lý. |
| [Luật AI 134/2025/QH15](https://congbao.chinhphu.vn/van-ban/luat-so-134-2025-qh15-468694.htm) | Tách luồng, ghi lý do quyết định để kiểm lại | agent/runner.py:102; agent/runner.py:109 | Điều khoản cụ thể chưa xác minh. Mock không chứng minh hệ thống AI thực tế an toàn hoặc đáp ứng luật. |
| [OWASP ASI01 — Agent Goal Hijack](https://genai-security-project.github.io/crosswalk/) | Chỉ chuyển số ticket từ tên file, không chuyển chỉ thị attacker sang Run B; chặn POST | agent/runner.py:102; agent/runner.py:131; reports/ledger.jsonl:26 | Kiểm trên 4 lure của lab, chưa bao phủ mọi cách injection hay model thật. |
| [OWASP ASI03 — Identity and Privilege Abuse](https://genai-security-project.github.io/crosswalk/) | Giao quyền principal với scope agent/cha, kiểm mục đích và TTL | agent/policy.py:60; agent/runner.py:109 | --as chỉ chọn principal giả lập, chưa xác thực người dùng. |
| [OWASP ASI04 — Agentic Supply Chain Vulnerabilities](https://genai-security-project.github.io/crosswalk/) | Pin hook, lock có hash, quét secret cả lịch sử | .pre-commit-config.yaml:3; requirements.lock:213; reports/secrets-incident.md:5 | Hash và pin chưa bảo đảm gói không có mã độc. Quét secret không phải quét mọi lỗ hổng dependency. |

Bằng chứng replay: reports/attack-before.log có 4 POST giả, reports/attack-after.log là file rỗng 0 byte nên không có dòng để trích. Ledger dòng 26 ghi deny, reason có nội dung, on_behalf_of=dpo.
