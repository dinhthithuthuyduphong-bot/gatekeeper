# §37. Giai đoạn 0 của hướng Kaggle (bản đăng ký trước)

> Chuyển từ `docs/preregistration_main.md` §37 trên `main` (commit đăng ký `17c6634`, 14/11/2026) theo yêu cầu của @thuthuy: mọi thứ của hướng Kaggle nằm ở thư mục này trên nhánh mặc định cho tới khi chạy ổn. Nội dung giữ nguyên, chỉ đổi đường dẫn file.


**Lý do:** @thuthuy 14/11: "làm trước bước 0đ là giai đoạn 0". Kaggle cho hạn mức gọi model miễn phí và máy CPU, nhưng notebook Kaggle không có Docker daemon (chưa xác nhận; K0a đo). Task SWE-smith chạy trong Docker image. Muốn dùng Kaggle thì phải chạy image bằng công cụ không cần daemon, và phải **chứng minh** điểm chấm không đổi.

**Đã thấy trước khi đăng ký** (chạy thử ở máy của phiên làm việc, không phải Kaggle): udocker 1.2.11 kéo và chạy được image Jinja; 4 bản vá của `s33_ship_skill.json` được chấm qua lớp thay thế và cả 4 trùng với điểm đã ghi (3 giải được, 1 không).

**Can thiệp (định nghĩa can thiệp):**
- Mã chấm của SWE-smith (`run_evaluation`, `run_patch_in_container`, `get_eval_report`; bản 0.0.9) dùng **nguyên văn**.
- Chỉ thay hai chỗ: đối tượng `docker.from_env()` và lệnh kéo image, bằng `kaggle/scripts/udocker_shim.py` (udocker, image kéo nguyên từ Docker Hub).
- Khác biệt so với Docker, ghi trước:
  - mỗi image giải nén một lần; mỗi "container" nhận một bản sao mới của `/testbed`, phần còn lại của hệ thống file dùng chung, nên chạy **tuần tự**;
  - không áp giới hạn bộ nhớ 10 GB;
  - lệnh chạy qua chế độ thực thi mặc định của udocker.

**Các cổng:**
- **K0a (môi trường):** ghi có Docker daemon hay không; udocker giải nén và chạy được image. Đạt khi chạy được test của ít nhất 1 task.
- **K0b (điểm chấm không đổi):** chấm lại một lần mọi bản vá khác rỗng của `f1_probe.json` và `f1_skill_probe.json` (Jinja, môi trường gốc, seed 41; đây là các bản vá đã được chấm lại 448 lần dưới Docker với 0 lần lệch, P26). Thêm bản vá gốc và "không vá" cho 20 task test đầu theo thứ tự của gskill.
  - **Đạt** khi: 100% bản vá trùng điểm đã ghi; bản vá gốc giải được 20/20; "không vá" giải được 0/20; không lượt nào ở trạng thái khác `completed`.
  - **Không đạt** (dù chỉ một bản vá lệch): hướng Kaggle dừng ở đây cho tới khi tìm ra nguyên nhân. Không dùng bộ chấm lệch để ra kết quả.
  - Lượt lỗi hạ tầng được chạy lại và không tính là điểm (L1, A105).
- **K0c (hạn mức và giá):** trong notebook Kaggle: hạn mức ngày và tháng hiển thị, danh sách model, và chi phí (do Kaggle báo) của một hội thoại ngắn. Chỉ ghi số đo; không có ngưỡng.
- **K0d (giao diện gọi model):** hội thoại nhiều lượt có giữ lịch sử không; có đặt được nhiệt độ hoặc seed không.
- **K0e (điều khoản):** @thuthuy đọc điều khoản dùng hạn mức trên trang Kaggle; ghi nguyên văn câu liên quan.

**Thứ tự chạy:** K0b chạy hai lần: ở máy của phiên làm việc (kiểm lớp thay thế), rồi trong notebook Kaggle (kiểm môi trường Kaggle). Chỉ kết quả trong Kaggle mới mở cổng cho các bước sau.

**Chưa đăng ký ở đây:** chạy agent trong Kaggle (cần một lớp thay thế tương tự cho harness của gskill) và mọi thí nghiệm mới. Chúng có mục riêng sau khi cổng này đạt và @thuthuy quyết.

### §37: kết quả K0b ở máy của phiên làm việc (14/11/2026; `kaggle/results/k0b_local.jsonl`; chưa phải Kaggle)
- **Môi trường (K0a):** không có Docker daemon; udocker 1.2.11; 4 CPU.
- **Điểm chấm:** 117/117 bản vá khác rỗng của `f1_probe.json` và `f1_skill_probe.json` trùng điểm đã ghi dưới Docker (68 giải được, 49 không). Bản vá gốc 20/20; "không vá" 0/20. 157 lượt chấm, 0 lượt khác `completed`; trung vị 5,8 giây mỗi lượt.
- **Đối chiếu điều kiện đạt:** đạt đủ bốn điều kiện, ở máy này.
- **Ghi chú thực thi 37-1:** bản đăng ký ghi "các bản vá đã được chấm lại 448 lần". Con số 448 là của bốn file (224 bản vá × 2 lần, P26); hai file dùng ở K0b có 117 bản vá khác rỗng.
- **Chưa kết luận gì về Kaggle:** cổng chỉ mở khi `kaggle/notebooks/kaggle_stage0.ipynb` cho cùng kết quả trong Kaggle.
