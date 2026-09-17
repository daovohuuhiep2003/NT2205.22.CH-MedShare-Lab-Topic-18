# Synthetic datasets

Đặt generator/config/versioned seeds (không secret) tại đây khi WP2 bắt đầu. Chưa có generator hoặc dữ liệu đã tạo.

- generated/: dữ liệu synthetic được sinh — gitignored.
- oracle/: plaintext ground truth riêng cho test — gitignored.
- raw/: input chưa rà soát — gitignored; không dùng dữ liệu cá nhân thật.

Seed generator dữ liệu không dùng để sinh khóa. Observer leakage chỉ nhận projection được phép; không đọc oracle. Tiny fixtures chỉ commit sau review và không chứa khóa.
