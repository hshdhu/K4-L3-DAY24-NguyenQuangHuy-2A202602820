# CP5 — DPIA-lite

1. **Dữ liệu nào?** Ticket trong corpus và hồ sơ khách giả trong customers.json. Có CCCD, điện thoại, số tài khoản, email. Ticket dùng mức internal, hồ sơ là restricted. Token của bài cũng giả, không dùng thông tin thật.

2. **Ai dùng, để làm gì?** support_l1 được tìm và tổng hợp ticket. dpo được đọc hồ sơ liên quan cho support-reply. Quyền lấy từ principals.json, không lấy theo lời tự nhận admin trong ticket. --as dpo chỉ là mô phỏng thôi.

3. **Đi qua đâu?** Run A tìm ticket rồi che PII trước khi đưa vào LLM. Chỉ số ticket lấy từ tên file đi sang Run B. Run B kiểm policy rồi mới mở dữ liệu riêng, tra related_tickets và kiểm lại trước mỗi read_customer. Sink thử nghiệm ở http://127.0.0.1:10024/reconcile. Ledger lưu quyết định và hash tham số, không lưu nguyên hồ sơ.

4. **Chặn và cho phép gì, còn thiếu gì?** Support không đọc hồ sơ restricted. DPO vẫn đọc khách liên quan, KH-000777 chỉ xuất hiện trong text thì không bị đọc. POST restricted bị deny, bằng chứng reports/ledger.jsonl:26. Replay sau sửa cho log 0 byte; toàn bộ 33 test pass, không skip. Tuy vậy mock chưa thay cho model thật, regex có thể sót hoặc nhầm PII, quyền chưa xác thực người dùng. Hash chain một file không phát hiện được cắt đuôi nếu thiếu mốc bên ngoài. Chưa làm quy trình lưu/xóa dữ liệu hay đánh giá pháp lý đầy đủ.

Đây là bản mô tả học tập. Không phải hồ sơ đánh giá tác động pháp lý chính thức.
