# Bản thảo EASE 2027: "A Published Skill Learner Found the Leak: Controls for Evaluating Learned Coding-Agent Skills"

Gói Overleaf này dùng để thầy đọc và góp ý. **Đây không phải bản nộp:** README này có đường dẫn tới repo, nên làm lộ danh tính tác giả. Bản nộp lên EasyChair chỉ gồm file PDF dựng từ `main.tex`.

## Mã nguồn và dữ liệu

- **Repo GitHub:** https://github.com/dinhthithuthuyduphong-bot/gatekeeper
  - Nhánh `main`: https://github.com/dinhthithuthuyduphong-bot/gatekeeper/tree/main
  - Mã nguồn của bài: https://github.com/dinhthithuthuyduphong-bot/gatekeeper/tree/main/paper
- Repo đang ở chế độ **private**. Thầy cần được mời làm collaborator mới mở được link.
- Phiên bản của gói này ứng với commit `__COMMIT__` trên nhánh `main`.

## Các file trong gói

| File | Nội dung |
| --- | --- |
| `main.tex` | Bài báo (mẫu ACM `sigconf,review,anonymous`, đúng dòng `\acmConference` của EASE 2027) |
| `numbers.tex` | Mọi con số trong bài, dưới dạng macro. File do `scripts/make_numbers.py` sinh từ `results/` của repo, **không sửa tay** |
| `refs.bib` | Tài liệu tham khảo. File do `scripts/make_bib.py` sinh từ các bản gốc đã lưu (nhánh `sources-snapshots`), **không sửa tay** |
| `main.pdf` | Bản PDF đã dựng sẵn |

## Dựng PDF trên Overleaf

1. Upload file zip thành một project mới (New Project → Upload Project).
2. Menu → Compiler: **pdfLaTeX**; Main document: **main.tex**.
3. Recompile. Overleaf tự chạy BibTeX cho `refs.bib`.

## Muốn sửa một con số hay một tài liệu tham khảo

Sửa trong repo, không sửa trong Overleaf. Con số đến từ `results/` qua `scripts/make_numbers.py`; tài liệu tham khảo đến từ `configs/sources.json` qua `scripts/make_bib.py`. Sửa tay trong Overleaf thì lần dựng sau sẽ bị ghi đè.

## Tài liệu kèm trong repo

- `docs/ease_writing_rules.md`: quy tắc viết bài theo CFP của EASE 2027, Open Science Policy của SIGSOFT và Empirical Standards; mỗi quy tắc kèm câu trích nguyên văn.
- `docs/review_log.md`: sổ review. Các mục R-97 tới R-110 ghi phản biện các bản đánh giá và những gì đã sửa.
- `docs/preregistration_main.md`: bản đăng ký trước của các thí nghiệm, kèm mọi ghi chú thực thi và sai lệch.
- `docs/plan_fallback_venues.md`: kế hoạch dự phòng nếu bài không được nhận ở EASE.

## Việc còn lại trước khi nộp (hạn tóm tắt 15/01/2027, hạn bài 22/01/2027, giờ AoE)

- Link riêng tư ẩn danh của figshare đã nằm trong mục Data Availability (R-109). Khi bài được nhận: bấm Publish trên figshare để có DOI (`docs/figshare_upload.md`).
- Để repo công khai `-gatekeeper-p6` ở chế độ private trong thời gian review.
