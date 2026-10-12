# CP4 — Token giả trong lịch sử

Em dùng Gitleaks 8.30.1. Máy ban đầu chưa có scanner nên tải bản Windows từ release chính thức, đặt trong .venv/Scripts để hook dùng được. Không đưa binary vào bài nộp.

Chạy `gitleaks git --config .gitleaks.toml --redact .`: quét 11 commit, có 1 finding, exit 1. Đúng token giả của bài. Chạy thêm --verbose để xem vị trí, vẫn che giá trị token.

Finding ở `lab-fake-secret.txt:1`, commit `1bdd849922156c868a5ee9293d68f5b72e242d2c` (viết ngắn là `1bdd849`). Rule `lab24-synthetic-token`. Token LAB24-DEMO này vô hiệu, chỉ dùng cho bài tập.

Chạy `gitleaks dir --config .gitleaks.toml --redact .`: không có finding, exit 0. Lần quét đầu cũng sạch, không gặp false positive trong .venv nên không chỉnh allowlist hay tắt rule.

Đã tạo requirements.lock bằng piptools compile --generate-hashes, pin phiên bản và SHA-256 cho từng dependency. Lệnh pip install --require-hashes chạy thành công. Có cài lại với --force-reinstall để kiểm hash khi tải gói, vì lần đầu các gói đã có sẵn.

Hook dùng repo https://github.com/gitleaks/gitleaks, rev v8.30.1, id gitleaks-system và pass_filenames: false. pre-commit install thành công, pre-commit run --all-files báo Passed. Hook kiểm thay đổi chuẩn bị commit; không thay cho việc quét toàn bộ lịch sử ở trên.

Nếu là secret thật thì phải thu hồi/rotate tại dịch vụ cấp token trước, xem log có bị dùng sai không rồi xử lý các bản sao trong lịch sử, clone, CI hoặc artifact. Xóa file ở commit mới không làm token cũ mất hiệu lực. Pin dependency cũng không giải quyết được token đã lộ.
