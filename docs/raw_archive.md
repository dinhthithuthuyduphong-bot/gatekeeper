# Lưu trữ dữ liệu gốc (nhánh `raw-archive`)

## Vì sao
Các con số dùng để phân tích nằm trong file kết quả `results/pilot/*.json` trên `main`. Bằng chứng gốc gồm:
- trajectory của agent;
- bản vá agent nộp;
- đề bài đúng như agent nhận (đã chèn skill);
- log test của harness.

Các file này được sinh trên container của phiên làm việc, và mất khi container bị thu hồi (`docs/audit_pilot.md` A52). Chúng cần để:
- kiểm lại về sau (ví dụ A37 và A28 đã phải dùng chúng);
- tái lập kết quả;
- trả lời reviewer.

## Ở đâu và cấu trúc
- **Nhánh `raw-archive`** của repo này, tách khỏi `main` (không làm nặng `main`).
- `archive/<giai đoạn>/<lô>.tar.gz`: một file cho mỗi lô, nén **tất định** (cùng nội dung thì cùng byte, cùng SHA-256). Mỗi file gồm:
  - `runs/<lô>/**`: trajectory, bản vá, đề bài đã chèn skill, cấu hình agent;
  - `logs/run_evaluation/<lô>-<nhánh>[-…]/**`: bản vá được chấm, `eval.sh`, output test, `report.json`;
  - file báo cáo của harness `<model>.<lô>-<nhánh>[-…].json`.
- `archive/MANIFEST.json`, ghi cho mỗi lô:
  - SHA-256 và kích thước file nén;
  - số file, số trajectory;
  - file kết quả tương ứng, trạng thái của nó (`valid`, `invalid` = giữ làm bằng chứng nhưng loại khỏi mọi phân tích, `no result file` = bị dừng trước khi ghi), và SHA-256 của nó lúc lưu trữ.

## Kiểm tra lại (bất cứ lúc nào, ở bất kỳ máy nào có repo)
```bash
python scripts/verify_archive.py
```
Script này đối chiếu:
1. SHA-256 của từng file nén với manifest;
2. số trajectory trong file nén với số lần chạy agent trong file kết quả trên `main`;
3. file kết quả hiện tại với SHA-256 lúc lưu trữ (nếu file bị sửa sau đó thì được báo).

Script trả mã thoát 1 nếu (1) hoặc (2) lệch.

Lấy bằng chứng của một lô để đọc:
```bash
git fetch origin raw-archive
git show origin/raw-archive:archive/g1-e1-s41/g1-e1-s41-p05.tar.gz | tar -xz -C /tmp/lo
```

## Khi nào được lưu
- Sau mỗi giai đoạn của E1 và sau mỗi lô của E2: các script chạy gọi `python scripts/archive_raw.py` và in `[archive] ok` hoặc `[archive] FAILED`.
- Khi mở mỗi phiên: hook khởi động phiên báo số lô chưa được lưu.
- Lô đang chạy (còn tiến trình `run_pilot.py` mang tên lô đó) chưa được lưu. Lô bị dừng giữa chừng vẫn được lưu.

## An toàn
- **Repo công khai.** Lô nào có skill chứa nội dung của bên thứ ba **không có giấy phép** (XRepoSkill ở E2) thì **không** đưa nội dung lên. Manifest chỉ ghi `withheld` cùng SHA-256. Nội dung đó cần một nơi lưu riêng tư (đề xuất cho @thuthuy khi E2 chạy).
- Trước khi ghi, mọi file được quét tìm khóa bí mật (dấu hiệu PEM có gạch ngang; trường `private_key` của file khóa). Thấy thì dừng, không ghi gì.
- Nhánh được ghi bằng lệnh git cấp thấp (index riêng, không checkout), nên không đụng thư mục làm việc của thí nghiệm đang chạy. Vì git hook không chạy với cách ghi này, các kiểm tra trên đóng vai cổng chặn.
- Mỗi file nén phải dưới 95 MB (giới hạn file của GitHub là 100 MB).

## Hiện trạng (03/11/2026)
- 119 lô, 1.052 trajectory, 61,5 MB nén (từ khoảng 660 MB).
- Trạng thái: 107 hợp lệ, 11 bị loại, 1 bản chạy thử bị dừng.
- `verify_archive.py`: 0 chỗ lệch.
