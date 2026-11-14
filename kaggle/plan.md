# Kế hoạch dùng Kaggle để sửa điểm yếu của paper (0 USD tiền mặt)

Đề xuất ngày 14/11/2026; @thuthuy duyệt **giai đoạn 0** cùng ngày ("làm trước bước 0đ là giai đoạn 0"). Các giai đoạn 1–3 **chưa được duyệt**: sẽ quyết sau khi có số đo của giai đoạn 0.

## 1. Tài nguyên Kaggle dùng được cho paper

| Tài nguyên | Dùng cho | Mức chắc chắn |
| --- | --- | --- |
| Hạn mức gọi model (AI quota) | Gọi model khác hãng (Claude) và Gemini mà không cần khóa riêng | **Đã xác nhận ở trang Settings của tài khoản (14/11): 10 USD/ngày, 100 USD/tháng.** Chỉ gọi được trong notebook Benchmarks |
| Máy CPU, khoảng 30 GB RAM, 70 GB đĩa, phiên tối đa 12 giờ | Chạy agent và chấm bài | Khá chắc |
| 30 giờ GPU mỗi tuần | Model mã mở làm agent, trọng số cố định | Khá chắc; tốc độ phải đo |

Khóa học, cuộc thi, huy chương: không giúp gì cho paper.

## 2. Nút thắt

- Task SWE-smith chạy trong Docker image; notebook Kaggle không có Docker daemon (cần K0a xác nhận). Giải pháp: chạy image bằng udocker, mã chấm của SWE-smith giữ nguyên (`scripts/udocker_shim.py`).
- Thư viện gọi model của Kaggle (`kaggle_benchmarks`) chỉ được mô tả cho notebook Kaggle; bản chạy ngoài ghi "for internal team only". Agent vì thế phải chạy **bên trong** Kaggle.
- Môi trường chạy khác Docker gốc là một sai lệch phải ghi trong paper, kể cả khi điểm chấm khớp hoàn toàn.

## 3. Giai đoạn 0: cổng khả thi (đã duyệt; `preregistration_s37.md`)

| Bước | Kiểm gì | Đạt khi | Trạng thái |
| --- | --- | --- | --- |
| K0a | Image Jinja chạy được không cần Docker daemon | Chạy được test của 1 task | Đạt ở máy của phiên làm việc; **chưa chạy trên Kaggle** |
| K0b | Chấm lại 117 bản vá Jinja đã lưu, bản vá gốc và "không vá" của 20 task | 100% trùng điểm; gốc 20/20; không vá 0/20; 0 lỗi | Đạt ở máy của phiên làm việc (117/117, 20/20, 0/20, 0 lỗi); **chưa chạy trên Kaggle** |
| K0c | Hạn mức thật, danh sách model, chi phí một hội thoại ngắn | Có số đo | Chưa chạy |
| K0d | Hội thoại nhiều lượt có giữ lịch sử; đặt được nhiệt độ hoặc seed | Nối được với mini-swe-agent mà không sửa agent | Chưa chạy |
| K0e | Điều khoản dùng hạn mức cho nghiên cứu | Không cấm | @thuthuy đọc và chép nguyên văn |

Nếu K0a hoặc K0b không đạt **trên Kaggle**, hướng này dừng; không dùng một bộ chấm khác.

## 4. Giai đoạn 1–3 (chưa duyệt; chi phí suy từ số đo trên Vertex, phải đo lại ở K0c)

| # | Thí nghiệm | Điểm yếu được sửa | Ước tính hạn mức |
| --- | --- | --- | --- |
| 1 | Đối chứng một commit cho Gemini Flash trên 34 task không mô tả | Câu hỏi còn hở của §34: rò rỉ có làm tăng điểm agent mạnh không | ≈ 5 USD |
| 2 | Model khác hãng trên 34 task, bốn nhánh (có/không skill × gốc/một commit) | Một họ model | ≈ 10–20 USD |
| 3 | Model khác hãng trên 100 task, bốn nhánh | Một họ model; tỉ lệ giải nền thấp | ≈ 30–60 USD |
| 4 | Thêm 2 lượt học Jinja (có rò rỉ, bịt rò rỉ) | Mỗi điều kiện một lượt học; log nửa đầu đã mất | ≈ 11–12 USD mỗi lượt |
| 5 | Lượt học trên 2 repo mới chọn theo quy tắc (tỉ lệ task không mô tả cao và thấp) | "Một trường hợp hay quy luật" (kế hoạch S2 của `docs/plan_astar.md`) | ≈ 11–12 USD mỗi lượt |
| 6 | Model mã mở trên GPU làm agent thứ ba, 34 task | Model đổi theo ngày; tái lập (trọng số cố định) | 0 hạn mức; cần đo tốc độ |

- Thứ tự: 1 → 2 → 4 → 3 → 5. Tháng đầu làm 1, 2, 4 và một phần 3 trong 100 USD hạn mức; tháng thứ hai làm 3 và 5.
- Trần 10 USD/ngày: một lượt học chia hai ngày; lưu log sau mỗi nửa (L59).
- Mỗi thí nghiệm có bản đăng ký trước riêng, review và chạy thử miễn phí trước khi gọi model.
- Chạy agent trong Kaggle cần thêm một lớp thay thế cho harness của gskill (`SWEHarness`, gọi Docker SDK trực tiếp); làm sau khi giai đoạn 0 đạt.

## 5. Không sửa được bằng hướng này

- Repo thật (issue thật): image của SWE-bench-Live nặng vài GB mỗi task; chỉ thử sau K0a.
- Chỉ một bộ học (gskill); phần lý thuyết ít mới.
- Độ lặp lại nếu K0d cho thấy không đặt được seed.

Ước lượng (không phải số đo): nếu 1–5 thành công, điểm A\* của paper từ 3,2 lên khoảng 3,8–4,0.

## 6. Cần @thuthuy

1. Tài khoản Kaggle đã xác minh số điện thoại; chạy `notebooks/kaggle_stage0.ipynb` theo `run_stage0.md`; gửi lại ba file kết quả và ba ghi chú (hạn mức ngày/tháng, hạn mức bị trừ sau ô 5, câu điều khoản).
2. Quyết các giai đoạn 1–3 sau khi có số đo K0c.
