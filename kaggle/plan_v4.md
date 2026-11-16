# Kế hoạch bản 4 (16/11/2026): mọi kịch bản để sửa điểm yếu của paper bằng Kaggle

Thay `plan_v3.md`. File theo dõi việc: `TODO.md` (cập nhật cùng lúc với file này).
**Trạng thái duyệt:** mục A, B, C đã được @thuthuy duyệt (15–16/11). Các mục mới ở bản này (C5, C7, D, E) ghi rõ mục nào cần @thuthuy quyết.

## 1. Rà soát: đã có gì, tin được tới đâu

| Mục | Kết quả | Tin được? | Hạn mức đã dùng |
| --- | --- | --- | --- |
| P0, P0b | Giá token đo chính xác cho 4 model | Có | 0,47 USD |
| **B (§39)** auditor khác hãng | Skill giả bị quy lỗi ở cả 4 auditor (10, 4, 1, 1 trên 25); cận dưới quy lỗi sai > 0 ở 1 auditor (Grok: 0,109) | **Có, xong** | 3,05 USD |
| **A (§38)** model viết skill khác hãng | Seed 1, 2 đủ (321 câu trả lời). Chưa tính endpoint | Chờ seed 3 | 13,73 USD |
| C0–C3 (§40) | Bộ chấm không-container trùng điểm Docker 224/224; agent chạy được trên Kaggle | Có, nhưng chỉ nói về **bộ chấm** | 0,01 USD |
| **C4 phiên 1** | 189 lượt Haiku | **Không.** Agent đi ra ngoài `/testbed` ở 27/189 lượt (`audit.md` K21) | 0,77 USD |
| Giai đoạn 0 (container trên Kaggle) | Hỏng 9/15 lần | Đã dừng (K14) | 0 |
| **Tổng tháng** | | | **khoảng 18,0 trên 100 USD** |

Còn lại: khoảng 82 USD hạn mức tháng; mỗi ngày 10 USD. Mục A cần thêm khoảng 7 USD.

## 2. Điểm yếu của paper, xếp theo mức nguy hiểm khi review

| # | Điểm yếu | Mức | Kaggle sửa được? | Bằng mục |
| --- | --- | --- | --- | --- |
| W1 | **Một họ model làm agent** (mọi phép nhận đo với Gemini) | Chí mạng | Chỉ khi có lớp cách ly thật | C5 → C4′ |
| W2 | Một model viết skill; cơ chế "bộ học viết chỉ dẫn rò rỉ" là một quan sát | Cao | Có | A (ngày mai) |
| W3 | Mỗi điều kiện một lượt học | Cao | Một phần, sau C | D |
| W4 | Auditor một họ model | Trung bình | **Đã xong** | B |
| W5 | Chỉ task tổng hợp; chưa có repo thật | Cao | Không | — |
| W6 | Tỉ lệ giải nền thấp | Trung bình | Kèm theo C4′ | C4′ |
| W7 | Một bộ học (gskill) | Trung bình | Không | — |
| W8 | Một repo cho phép nhận chính (Jinja; Bleve cho phần học) | Trung bình | Có thể, sau C4′ | C7 |

W5 và W7 nằm ngoài khả năng của kế hoạch này. Paper phải giữ chúng ở phần giới hạn.

## 3. Điều phiên 1 của C4 cho biết (dữ liệu thử, không dùng để kết luận)

- **Môi trường không cách ly:** agent chạy `find /`, đọc file bộ chấm để lại ở `/tmp`, vào bản clone gốc. Đây là lý do dừng.
- **Agent mạnh hơn nhiều so với agent của paper:** không skill giải 33/50 (bộ chấm S).
- **Skill được làm theo nhưng lợi ích nhỏ:** có skill, agent đọc lịch sử git ở 44/50 lượt (không skill: 14/50), nhưng chỉ giải thêm 3 task.
- **Task không mô tả vẫn khó:** 1/13 không skill, 3/13 có skill.
- **Rẻ:** 189 lượt hết 0,77 USD. Một model chạy đủ 400 lượt tốn khoảng 1,6 USD, khoảng 5 giờ.

Hệ quả cho kế hoạch: tiền không phải ràng buộc. Ràng buộc là **tính hợp lệ của môi trường** và **thời gian chạy**.

## 4. Sơ đồ quyết định

```
Ngày mai:  A seed 3 ──► A1 / A2 / A3 / A4  (mục 5)
Song song: C5 (cách ly, 0 USD) ──► đạt ──► C6 (thử 6 task) ──► C4′ (3 agent) ──► R1…R6 (mục 7)
                        │                                             └─► tốt: C7 (Pygments), D (lượt học)
                        └─ không đạt ──► dừng mục C; W1 ở lại phần giới hạn; làm E (mục 9)
Cuối:      F: đưa A, B (và C nếu hợp lệ) vào paper theo bảng câu chữ (mục 10)
```

## 5. Mục A (§38): bốn kịch bản sau seed 3

Phép kiểm chính: tỉ lệ skill có dòng lịch sử, ô có rò rỉ (6 lần gọi) so với ô không rò rỉ cùng lượt học (7 lần gọi), từng model, Holm trên 4 model.

| Kịch bản | Dấu hiệu | Ý nghĩa | Việc làm tiếp | Paper |
| --- | --- | --- | --- | --- |
| **A1 tốt** | ≥ 2 model khác hãng bác bỏ H0; ô không rò rỉ gần 0 | Cơ chế không riêng một model viết skill | Không cần chạy thêm. Thêm bảng 5 model × 4 ô | "ở các model viết skill đã thử, của 4 hãng" |
| **A2 trung tính** | Chênh lệch dương ở nhiều model nhưng không qua Holm (power thấp: 13 lần gọi) | Cùng chiều, chưa đủ bằng chứng | Báo mức chênh và khoảng tin cậy; **không** thêm seed (seed không tăng số lần gọi độc lập). Xem E1 | "cùng chiều ở k/4 model; phép kiểm chỉ đủ power cho chênh lệch ≥ 0,6" |
| **A3 chỉ Gemini** | Model mốc có chênh lệch lớn, model khác gần 0 ở cả hai ô | Cơ chế phụ thuộc model viết skill | Kiểm lại bằng endpoint G; đọc tay 18 skill của ô có rò rỉ để chắc endpoint không bỏ sót cách diễn đạt khác | Thu hẹp: "với model viết skill của gskill"; ghi số của 4 model khác |
| **A4 ngoài dự kiến** | Model viết dòng lịch sử cả khi không có rò rỉ (ô `noleak` hoặc `clean` cao) | Chỉ dẫn là thói quen của model | Tách theo endpoint G; kiểm ô `clean` (14 lần gọi, môi trường một commit) | Viết lại phần cơ chế ở §36; phát hiện chính (mất tác dụng khi bịt rò rỉ) không đổi |
| A5 hạ tầng | Phiên 3 không xong (hạn mức, lỗi) | — | Chạy thêm một phiên; không phân tích khi chưa đủ | — |

## 6. Mục C5: lớp cách ly (0 USD; cổng mới, bắt buộc trước mọi lượt agent)

**Docker cho mỗi task những gì, và hiện thiếu gì:**

| Docker cho | Hiện tại | Cần |
| --- | --- | --- |
| Hệ thống file riêng: không thấy task khác, bản clone gốc, mirror, mã chấm, file task | Dùng chung cả máy | Che `/var/lib/lshim`, `/kaggle`, `/benchmarks`, thư mục cache |
| `/tmp`, `/root` riêng | Dùng chung giữa các task | Riêng cho từng task |
| `/opt/mirror.git` riêng (nhánh một commit xóa nó) | Dùng chung, phải chép lại | Riêng cho từng task |
| Tiến trình chết khi container bị xóa | Tiến trình nền sống tiếp | Dừng mọi tiến trình của task khi task xong |
| Mạng | Có | Giữ như Docker |

**Ba cách, thử theo thứ tự; dừng ở cách đầu tiên đạt:**

| Cách | Cần gì | Ưu | Rủi ro |
| --- | --- | --- | --- |
| S1. `unshare` (mount namespace) + gắn thư mục riêng, bằng quyền root | Kaggle cho phép lệnh `mount` trong namespace mới | Gốc của Linux, nhanh, giống Docker nhất | Notebook có thể không có quyền này |
| S2. `proot` (gắn thư mục ở mức người dùng) | Tải được một file chạy; `ptrace` được phép | Đã chạy được trên notebook thường (K0a, chế độ P1) | Chậm hơn; chưa thử trên notebook Benchmarks |
| S3. Chạy lệnh của agent bằng người dùng thường, thư mục nhạy cảm đặt quyền chỉ root đọc, `/tmp` dọn giữa các task | Không cần gì thêm | Luôn làm được | Yếu nhất: `/tmp` vẫn chung trong lúc một task chạy; agent không còn là root như trong Docker (sai lệch) |

**Cập nhật 16/11 (sau ô thăm dò):** notebook Benchmarks không cho S1 (không có `CAP_SYS_ADMIN`) và không có sẵn `proot`. Nó có `CAP_SYS_CHROOT` và `CAP_MKNOD`. **Cách được chọn là S4:** tải hệ thống file của image gốc, mỗi task chạy trong `chroot` của một bản sao riêng (`scripts/chroot_shim.py`; chi tiết ở `preregistration_s40.md` ghi chú 40-4). S4 mạnh hơn S2 và S3: agent thấy đúng file của image thật và không thấy gì của máy chủ. Sáu phép thử của cổng được viết lại cho S4 ở ghi chú 40-4.

**Cổng C5 đạt khi (đo bằng máy, đặt trước; bản ban đầu):**
1. **Chim mồi:** đặt file đánh dấu ở mọi nơi cần che (bản clone gốc, mirror, `/kaggle/working`, `/tmp` của task trước, `/root` của task trước). Từ trong môi trường của task, `find / ` không thấy file nào: **0 / số file đặt**.
2. **Tiến trình:** một tiến trình nền do task tạo không còn sống sau khi task kết thúc: 0 còn sống.
3. **Ghi chéo:** task A ghi vào `/testbed`, `/tmp`; task B không thấy: 0 file.
4. **Môi trường lệnh:** `which python`, `pwd -P`, `git log`, biến môi trường giống image (như ghi chú 40-1).
5. **C1 chạy lại qua lớp cách ly:** 224/224 trùng, gốc 20/20, "không vá" 0/20.
6. Chạy được trên notebook Benchmarks (ô thử 0 USD).

**Kịch bản của C5:**

| Kết quả | Việc |
| --- | --- |
| S1 hoặc S2 đạt cả 6 điều | Sang C6 |
| Chỉ S3 đạt | **Cần @thuthuy quyết:** S3 là một sai lệch thật (agent không phải root, `/tmp` chung trong lúc chạy). Lời khuyên: chỉ dùng nếu bộ theo dõi sau khi chạy cho 0 lượt đụng đường dẫn ngoài; nếu không thì dừng |
| Không cách nào đạt | Dừng mục C. W1 ở lại phần giới hạn. Chuyển sang E |

## 7. Mục C6 và C4′: agent khác hãng, chạy lại từ đầu

- **C6 (trần 0,5 USD):** 6 task với Haiku, gồm **3 task không mô tả** (loại task đã làm lộ lỗi ở phiên 1) và 3 task có mô tả, ở nhánh `lf_none`. Đạt khi bộ theo dõi cho 0 lượt đụng đường dẫn ngoài *thành công* (lệnh có thể được thử, nhưng không thấy gì) và không lỗi hạ tầng.
- **C4′:** thiết kế của mục 6 bản đăng ký §40 giữ nguyên (3 agent, 4 nhánh, 100 task, quy tắc §25). 189 lượt của phiên 1 không dùng lại. Ước tính: 1,6 USD và 5 giờ mỗi model.

**Kịch bản kết quả cho mỗi agent** (e-process, θ = 0, α = 0,025):

| Mã | Môi trường gốc | Một commit | Ý nghĩa | Việc làm tiếp |
| --- | --- | --- | --- | --- |
| **R1 tốt** | nhận | không nhận | Lặp lại phát hiện chính với agent khác hãng | C7 (repo thứ hai), rồi D |
| **R2 trung tính** | không nhận | không nhận | Skill không giúp agent này | Xem R2a–R2c dưới đây |
| **R3 ngoài dự kiến** | nhận | nhận | Skill giúp cả khi không có rò rỉ | Phân tích nội dung: phần nào của skill giúp (so với skill đã bỏ dòng lịch sử, §29). Paper thu hẹp "mất tác dụng" về agent gốc |
| **R4 ngoài dự kiến** | không nhận | nhận | Không có giải thích sẵn | Kiểm lỗi trước (thứ tự nhánh, rò rỉ ngoài); báo nguyên trạng |
| **R5 có hại** | mức tăng âm rõ ở một môi trường | — | Skill làm agent này kém đi | Chạy e-process theo chiều hại (đúng mục đích ban đầu của Gatekeeper). Đây là một ca phát hiện skill có hại trên agent thật |
| **R6 trần** | tỉ lệ giải nền quá cao, không còn chỗ để tăng | — | Không đo được | Phân tích riêng 34 task không mô tả (đặt trước); thêm agent yếu hơn |

**R2 chia nhỏ (dựa trên điều phiên 1 gợi ý: agent mạnh, lợi ích nhỏ):**

| Mã | Dấu hiệu | Diễn giải | Việc |
| --- | --- | --- | --- |
| R2a | Nhánh không skill tự thấy "Bug Patch" ở nhiều lượt | Agent mạnh **tự khai thác rò rỉ**, không cần skill. Rò rỉ vẫn là vấn đề của benchmark | So `none` với `lf_none`: mức giảm khi bịt rò rỉ là thước đo rò rỉ không phụ thuộc skill. Đây là kết quả mạnh cho paper |
| R2b | Agent làm theo skill (đọc lịch sử) nhưng không giải thêm | Thấy commit rò rỉ chưa đủ để sửa đúng | Đếm lượt thấy "Bug Patch" mà vẫn trượt; báo như giới hạn của việc "khai thác" |
| R2c | Agent không làm theo skill | Skill không chuyển sang agent khác | Báo tỉ lệ làm theo; kết luận về tính chuyển giao của skill |

**Mẫu hình giữa ba agent:**

| Mẫu hình | Paper nói được |
| --- | --- |
| Cả ba R1 | "Phát hiện lặp lại ở 4 họ agent" (mạnh nhất) |
| Agent yếu R1, agent mạnh R2a | "Lợi ích của skill giảm khi agent mạnh lên; agent mạnh tự khai thác rò rỉ" (quan hệ liều lượng–đáp ứng; vẫn mạnh) |
| Cả ba R2 | "Skill học từ agent Gemini không chuyển sang agent khác"; phát hiện chính được giới hạn về agent gốc, nhưng phép đo rò rỉ `none` so với `lf_none` vẫn dùng được |
| Trái chiều | Báo từng agent; không gộp |

## 8. Mục mở rộng, chỉ khi C4′ hợp lệ

| Mục | Điều kiện mở | Việc | Sửa điểm yếu | Ước tính |
| --- | --- | --- | --- | --- |
| **C7** repo thứ hai | Ít nhất một agent cho R1 hoặc R2a | Lặp C1 và C4′ trên Pygments (Python thuần; paper đã có kết quả Gemini) | W8 | 0 USD cho cổng; khoảng 2 USD mỗi agent |
| **C8** seed thứ hai | Kết quả sát ngưỡng | Chạy lại agent đó với seed khác | Độ ổn định | 1,6 USD mỗi agent |
| **C9** agent hạng giữa | Cả ba agent nhỏ cho R6 hoặc R2 | Thêm một model hạng giữa của một hãng, sau khi đo giá | W1, W6 | Chưa biết; đo trước, trần 0,3 USD |
| **D** lượt học thứ hai | C4′ hợp lệ và phiên Kaggle chịu được nhiều giờ | Chạy lại lượt học gskill (Jinja, môi trường gốc và một commit) với agent khác hãng | W3 | Chưa đo; cần cổng riêng và @thuthuy chốt trần |

C7, C8, C9, D đều là thêm thí nghiệm: **cần @thuthuy duyệt từng mục** khi tới lúc.

## 9. Mục E: việc thuần văn bản, không phụ thuộc cách ly (dự phòng và bổ sung)

| Mục | Khi nào làm | Việc | Giá trị |
| --- | --- | --- | --- |
| E1 | A ra A2 hoặc A3 | Đọc tay và dùng 2 model khác hãng phân loại 18 skill của ô có rò rỉ: có chỉ dẫn đọc lịch sử không. Đo độ đồng thuận với quy tắc máy | Bảo vệ endpoint của A trước phản biện "quy tắc chuỗi ký tự bỏ sót" |
| E2 | Mục C dừng | Cho model khác hãng đọc quỹ đạo đã lưu của paper, hỏi agent có dùng commit chèn lỗi không; so với bộ theo dõi bằng quy tắc (34/34; 0/398) | Bảo vệ bộ theo dõi rò rỉ |
| E3 | Luôn làm được | Dùng 189 lượt của phiên 1 như **bằng chứng định tính** trong phần giới hạn: agent mạnh tìm mọi nguồn thông tin trên máy | Trung thực; cho thấy vì sao cách ly quan trọng. Không dùng làm số đo |

## 10. Câu chữ trong paper theo kịch bản (mục F)

| Phần | Nếu tốt nhất (A1, R1 ở ≥ 2 agent) | Nếu trung tính (A2, R2) | Nếu ngoài dự kiến |
| --- | --- | --- | --- |
| Tóm tắt | thêm "replicated with agents and skill writers of other vendors" | giữ nguyên; thêm một câu về phạm vi | giữ nguyên |
| Kết quả chính | bảng agent × môi trường | báo mức tăng, ghi rõ không qua ngưỡng | báo nguyên trạng, thu hẹp kết luận |
| Cơ chế (§36) | "ở 4 hãng" | "cùng chiều, chưa đủ power" | viết lại nếu A4 |
| Auditor (phụ lục) | 7 auditor của 4 hãng, đã có | như bên | như bên |
| Giới hạn | bỏ "một họ agent", "một họ auditor"; giữ W5, W7 | giữ "một họ agent cho phép nhận"; thêm kết quả đo | thêm các kết quả trái chiều |

Mọi thay đổi vào paper và hai file báo cáo cần @thuthuy đồng ý. `kaggle/` chỉ chuyển về `main` khi mọi mục đã chạy xong và đã kiểm.

## 11. Thứ tự việc và ai làm

| Bước | Ai | Việc | Tiền |
| --- | --- | --- | --- |
| 1 | @thuthuy | Chạy phiên 3 của A (notebook mục A, một ô) | khoảng 7 USD |
| 2 | Claude | Phân tích A; xác định A1–A4 | 0 |
| 3 | Claude | Viết và thử S1, S2, S3 tại máy của phiên; viết ô thử C5 | 0 |
| 4 | @thuthuy | Chạy ô C5 trên notebook Benchmarks | 0 |
| 5 | Claude, @thuthuy | C6 (6 task) | ≤ 0,5 USD |
| 6 | @thuthuy | C4′: ba agent, mỗi ngày một phiên | khoảng 5 USD |
| 7 | Claude | Phân tích theo R1–R6; đề xuất C7, C8, C9, D | 0 |
| 8 | Claude | Mục F sau khi @thuthuy đồng ý | 0 |

## 12. Cần @thuthuy quyết (đủ ba điều theo quy tắc)

**Q1. Có tiếp tục mục C bằng lớp cách ly (C5) không?**
- Vì sao thuộc quyền @thuthuy: đây là thay đổi thiết kế của một thí nghiệm đã duyệt, và có thể kết thúc bằng việc bỏ thí nghiệm đó.
- Ảnh hưởng: W1 là điểm yếu chí mạng duy nhất Kaggle còn có thể chạm tới. Bỏ C thì paper giữ nguyên "một họ agent". Làm C5 tốn 0 USD và khoảng một ngày công; C4′ tốn khoảng 5 USD hạn mức.
- Lời khuyên: **làm C5.** Tôi sẽ bắt đầu ngay phần 0 USD tại máy của phiên, vì nó nằm trong mục C đã duyệt và không tốn hạn mức. Dừng ngay nếu cổng không đạt.

**Q2. Nếu chỉ cách S3 đạt, có chấp nhận sai lệch đó không?** (Chỉ cần trả lời khi tới lúc.)

**Q3. Các mục mở rộng C7, C8, C9, D:** duyệt khi có kết quả C4′.
