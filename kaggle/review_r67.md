## R-67. §38 mục A: model viết skill khác hãng (P0 và chạy chính; chỉ hạn mức miễn phí của Kaggle)

- **Đối chiếu bản đăng ký:** `kaggle/preregistration_s38.md` được commit trước mọi lần gọi model của §38. Dữ liệu đã thấy trước khi đăng ký: phân loại 27 lần gọi của §36 (đã công bố trong paper), và nội dung các dòng lịch sử của skill cha và skill con (để định nghĩa endpoint G).
- **Nguồn (R1):** đã đọc bản gốc `train_optimize_anything.py` và `gepa/lm.py` ở commit ghim `8c7b697`, kiểm sha256. Đã thêm `gskill_proposer_call`, `gepa_lm_defaults` vào `configs/sources.json` (main, `e1240b3`). Workflow `sources` (lần 67) đã lưu đoạn trích; sha256 trùng bản đã đọc, đủ 8/8 câu cần dùng.
- **Con số (R2):**
  - 6/7/14/6 lần gọi, 32 prompt khác nhau: suy ra từ dữ liệu;
  - α = 0,025 một phía: mức đã dùng ở §25;
  - Holm, phép kiểm hoán vị chính xác: nguồn `holm`, `hemerik_goeman_2018`;
  - 3 seed: theo `plan_v2.md` đã duyệt, kèm thứ tự giảm khi thiếu tiền;
  - 8 USD/ngày, hệ số 1,5, 3 lỗi liên tiếp: vận hành (lý do ghi ở §5 của bản đăng ký);
  - 40 USD: trần đã duyệt;
  - `temperature=None`: từ nguồn.
- **Mã (R3):**
  - `a38_build.py`: chỉ đọc lưu trữ bằng `tarfile`, không giải nén ra đĩa; báo lỗi nếu khối skill cha không xuất hiện đúng một lần;
  - `a38_run_cell.py`: không in khóa hay biến môi trường; từ chối chạy khi chưa điền cấu hình từ P0, hoặc khi sha256 của dữ liệu khác;
  - `a38_analyse.py`: hàm phân tích không có giá trị mặc định cho α.
- **Test** (`kaggle/tests/test_a38.py`, 8 test, đạt):
  - bỏ dòng chỉ trong khối skill cha;
  - `extract_skills` tái tạo đúng 14/14 skill đã lưu;
  - số dòng mỗi ô và sha256 của dữ liệu;
  - p hoán vị khớp tính tay (1/35) và khớp 1/C(13,6);
  - Holm;
  - với model giả lập: notebook dừng ở trần ngày, chạy tiếp không gửi lại lần gọi đã có, và từ chối khi cấu hình chưa điền.
- **Mô phỏng (L11):** `a38_power.py`. Tỉ lệ bác bỏ dưới H0 là 0,011 ở mức 0,025; power 0,92 khi chênh lệch là 0,8 so với 0,2.
- **Chưa kiểm được:** thư viện `kaggle_benchmarks` có nhận `temperature=None` không, và có báo chi phí mỗi lần gọi không (P0 đo).

### Bổ sung: §39 (mục B)
- **Dữ liệu:** 102 prompt dựng lại bằng `build_prompt` không sửa, trên 58 lô gốc của E1. Không so được byte với bản gốc (đã mất); kiểm gián tiếp bằng tỉ lệ ký tự trên token (2,35–4,04). File không commit vì chứa quỹ đạo.
- **Ô chạy:** giống hệt ô §38 ngoài khối cấu hình (test). `SEEDS=(1,)`, không đặt nhiệt độ, như §19 C.
- **Phân tích:** dùng `parse` của §19 C. Quy tắc đếm áp lên các dòng Gemini đã lưu cho lại đúng 25, 3, 5 trên 25 của paper (test).
- **Test:** `kaggle/tests/test_b39.py`, 5 test, đạt.
