# Tủ Sách Gia Đình

Hệ thống đọc truyện thư thái, phông chữ lớn, giao diện tối ưu cho người lớn tuổi đọc trên điện thoại và máy tính.

---

## Các bộ truyện đã được tích hợp sẵn

1. Đầu Xuân Tươi Sáng (Tác giả: Cô Nương Đừng Khóc) - Trọn bộ 149 chương.
2. Chỉ Là Tiểu Thiếp - Nguyệt Minh Châu (Tác giả: Nguyệt Minh Châu) - Trọn bộ 88 chương (đầy đủ tên mục và phụ đề từng chương).
3. Bạn Học Số 7 - Nam Tri Bắc (Tác giả: Nam Tri Bắc) - Trọn bộ 95 chương.

---

## Cấu trúc thư mục

- index.html: Giao diện Tủ truyện, trang giới thiệu và trình đọc chương.
- style.css: Phong cách giao diện hỗ trợ 4 chế độ màu (Sáng, Nâu Sepia, Tối, Đen OLED) và tùy biến hiển thị.
- app.js: Điều hướng đa truyện qua URL hash, ghi nhớ chương đọc riêng cho từng bộ truyện trong LocalStorage.
- scrape_story.py: Công cụ cào thêm bất kỳ truyện nào từ nguồn về thư viện chỉ với một lệnh.
- assets/: Thư mục chứa ảnh bìa các bộ truyện.
- data/library.json: Danh mục tổng hợp tất cả các bộ truyện trong thư viện.
- data/stories/: Thư mục chứa nội dung từng bộ truyện cùng danh sách chương và chi tiết tên mục.

---

## Cách cào thêm truyện mới vào thư viện

Chạy lệnh sau với slug của bộ truyện:

```bash
python3 scrape_story.py <slug_truyen>
```

Ví dụ:

```bash
python3 scrape_story.py khong-can-loan-an-va-1
```

Script sẽ tự động tải ảnh bìa, trích xuất đầy đủ tên mục và phụ đề của từng chương, làm sạch watermark quảng cáo, chuẩn hóa bảng mã tiếng Việt và tự động cập nhật vào Tủ truyện `data/library.json`.

---

## Hướng dẫn chạy thử nghiệm nội bộ

Khởi chạy máy chủ cục bộ:

```bash
python3 -m http.server 8099
```

Sau đó mở trình duyệt và truy cập:

```
http://localhost:8099
```

---

## Hướng dẫn đưa lên GitHub Pages

```bash
cd /Users/elite/.gemini/antigravity-ide/scratch/dau-xuan-tuoi-sang-web
git init
git add .
git commit -m "Kho truyen doc tinh khong quang cao"
git branch -M main
git remote add origin https://github.com/Ten_Tai_Khoan/kho-truyen.git
git push -u origin main
```

Sau đó vào Settings của kho lưu trữ trên GitHub, chọn Pages, chọn Branch `main` và thư mục `/ (root)` để kích hoạt trang web.
