# Hướng dẫn từng bước cho các việc có phí (C10, C6, C1/C4′, C2)

Lập 17/11/2026, theo yêu cầu của @thuthuy: "hướng dẫn chi tiết từng bước của phần có phí". Danh sách việc ở `docs/todo_ease_revision.md`. Hạn đóng băng thí nghiệm: **01/12/2026**.

**Cách đọc:** mỗi mục ghi bốn thứ:
- **ai duyệt gì:** đúng một câu trả lời @thuthuy cần gửi;
- **phần miễn phí:** những gì phải làm trước;
- **lệnh chạy:** chính xác nút bấm hay ô notebook;
- **sau khi chạy:** những gì phải kiểm.

Ai làm bước nào: "**@thuthuy**" là việc chỉ @thuthuy làm được (tiền, tài khoản Kaggle, nút bấm trên trang web). Còn lại là việc Claude làm trong một phiên làm việc.

## 0. Quy tắc chung (mọi mục)

1. **Không chi khi chưa có câu duyệt.** Câu duyệt của @thuthuy được chép nguyên văn vào `CLAUDE.md`, mục ngân sách, kèm ngày.
2. **Thứ tự bắt buộc:**
   1. bản đăng ký được commit;
   2. review theo `docs/research_rules.md` §4, ghi vào `docs/review_log.md`;
   3. `python scripts/preflight.py --ci` đạt;
   4. chạy thử miễn phí trên ít nhất một task thật;
   5. chỉ sau đó mới chạy có phí.
3. **Trần tính từ số đã chi thật** (`spent_usd` trong file kết quả), không từ số dự kiến (L8, L63).
4. **Sau mỗi lần chạy:**
   - kiểm `infra_failures`, `endpoint_mismatch`, `patch_apply_failed`, `stopped` trong file kết quả;
   - chạy `python scripts/archive_raw.py` rồi `python scripts/verify_archive.py`;
   - commit, push, đọc kết luận CI.
5. **Không chạy lại một lượt lỗi do agent gây ra** (L1). Chỉ chạy bù lượt lỗi hạ tầng, theo quy tắc đã đăng ký.

**Hai chữ "C6" khác nhau.**
- **C6 ở mục 2** của file này là việc trên Vertex (agent Flash, môi trường một commit).
- **"Ô C6" trong `kaggle/TODO.md`** (N3) là phép thử 6 task qua lớp cách ly trên Kaggle, ở mục 3 của file này.

## 1. C10: can thiệp lịch sử git có kiểm soát (Vertex, tiền thật)

**Câu hỏi:** trong mức tăng của skill ở môi trường gốc, phần nào do thông điệp "Bug Patch", phần nào do diff của commit đó?

**Thiết kế:** 2 × 2 (thông điệp × diff), xem `docs/todo_ease_revision.md` mục 7. Bốn biến thể lịch sử, tạo bằng `scripts/history_variants.py`:

| Biến thể | Lịch sử agent thấy | Thông điệp "Bug Patch" | Diff của lỗi |
| --- | --- | --- | --- |
| A | T0 → T1 → T2, dựng lại đúng từng bit (mã băm `HEAD` bằng bản gốc) | có | có |
| B | T0 → T1 → T2, thông điệp của commit giữa thay bằng một câu trung tính | không | có |
| C | T1 → T1 → T2: commit "Bug Patch" rỗng | có | không |
| D | T1 → T2 | không | không |

- Commit "Remove F2P Tests" (T1 → T2) giống hệt nhau ở cả bốn biến thể. Kiểm toán §41 cho thấy agent nghiên cứu không dùng kênh này (0 lượt).
- Bốn biến thể có cùng bước dọn dẹp: bỏ remote, mirror, reflog, đối tượng không còn tham chiếu. Vì vậy các ô chỉ khác nhau ở yếu tố của thiết kế.
- Ô A **mới** được chạy cùng lúc với B, C, D. Không dùng lại số của §33.

**Đã làm (miễn phí, 17/11):**
- `scripts/history_variants.py` và `tests/test_history_variants.py`: 9 test, gồm cả HEAD tách rời; A ra đúng mã băm gốc.
- Tùy chọn `--history-variant` và `--neutral-message` trong `scripts/f1_probe.py`.
- Plan `swesmith-c10` trong `.github/workflows/pilot.yml`:
  - tám nhánh (4 biến thể × có/không skill) chạy cùng lúc;
  - giá trị đã đăng ký đọc từ `configs/c10.json`;
  - chạy thử dùng `tests/fixtures/c10_dryrun.json`.

**Chi phí (A135: con số 7,5 USD cũ sai).** Tính từ số đã chi của bốn nhánh trên task không mô tả:

| Nguồn | Tổng 4 nhánh | Số task | USD mỗi task (4 nhánh) |
| --- | --- | --- | --- |
| §33, 34 task test không mô tả (`cost_usd` từng lượt, `results/s33_*.json`) | 1,513 | 34 | 0,0445 |
| §35, 36 task mới không mô tả (`spent_usd`, `results/s35_*.json`) | 1,393 | 36 | 0,0387 |

- **34 task:**
  - dự kiến 2 × 34 × 0,0445 = **3,03 USD**;
  - trần = dự kiến + một cost_limit (0,30) cho mỗi nhánh = 3,03 + 8 × 0,30 = **5,43 USD**.
- **70 task:**
  - dự kiến 2 × (1,513 + 1,393) = **5,81 USD**;
  - trần = 5,81 + 16 × 0,30 = **10,61 USD**, vì mỗi nhánh chạy hai phần: 34 task test và 36 task mới.
- **Giới hạn của ước tính:** B và C chưa từng chạy. Nếu agent ở B hay C lục lịch sử lâu hơn, chi phí mỗi lượt có thể cao hơn. Trần của từng nhánh chặn việc này: nhánh dừng khi số đã chi cộng cost_limit vượt trần.

**Bước 1. @thuthuy duyệt** (thuộc quyền @thuthuy: ngân sách mới, thêm thí nghiệm). Một câu, chọn một trong hai:
- "Duyệt C10 34 task, trần 5,43 USD": power thấp hơn, và tập task được chú ý vì đã thấy hiệu ứng ở đó.
- **"Duyệt C10 70 task, trần 10,61 USD" (lời khuyên).** Lý do: 36 task thêm được chọn bằng quy tắc trước khi có kết quả (§35), nên tránh được lời bắt bẻ "chọn tập sau khi thấy dữ liệu". Ở phép so tương tự của §40 (ghi chú 40-5), power tăng từ 0,63 lên 1,00 khi đi từ 34 lên 70 task.

**Bước 2. Bản đăng ký `docs/preregistration_main.md` §43 (Claude, miễn phí).** Phải chốt trước khi chạy:
1. **Phép so chính, chỉ một:** đề xuất (B − D) trên Z gộp theo task, bằng phép kiểm cuối pool (λ = 0,5, θ = 0, ngưỡng 40), tức "diff không kèm thông điệp có đủ tạo mức tăng không".
   - Phép kiểm tương tác (A − B − C + D) được đăng ký là phép phụ.
   - Đọc kết quả theo bảng đặt trước, như ghi chú 40-5 mục 5.
2. **Câu trung tính của B,** kèm quy tắc chọn:
   - không chứa từ chỉ lỗi, sửa, test hay tên file;
   - lấy từ lịch sử thật của repo jinja (một thông điệp có sẵn, chọn bằng quy tắc nêu trước, ví dụ commit gần nhất trước mã gốc của task mà thông điệp thỏa các điều trên).
   - Ghi câu đó vào `configs/c10.json` (`neutral_message`). Mã từ chối câu rỗng hoặc chứa "Bug".
3. **Trần từng nhánh:** `caps_test34` (và `caps_extra36` nếu 70 task), tám khóa `A_none` … `D_skill`. Mỗi trần = số dự kiến của nhánh + 0,30. Số dự kiến của nhánh lấy từ nhánh tương ứng của §33/§35: có skill hay không, gốc hay một commit. Script trong workflow kiểm tổng các trần ≤ `budget_usd`.
4. **Mô phỏng power** cho phép so chính trong `scripts/verify_methods.py`, dưới hai kịch bản:
   - B giống A;
   - B giống D.
5. Quy tắc chạy bù hạ tầng (L57) và theo dõi cả hai kênh rò rỉ bằng `scripts/history_audit.py` cho từng nhánh.

**Bước 3. Review (Claude):** ghi R-# vào `docs/review_log.md`, chạy preflight, commit, push.

**Bước 4. Chạy thử miễn phí (Claude bấm, 0 USD).** GitHub → Actions → "Pilot (paid, Vertex AI)" → Run workflow, với `ref` = main:
- `plan` = `swesmith-c10`, `repo` = `jinja`, `arm` = `c10test34`, `dryrun` = `true`, `budget_usd` = `15`;
- các ô khác để mặc định.

Model giả lập trả lời ngay "nộp bài", nên không có lệnh gọi model nào. Sau khi chạy, kiểm:
- tám file `results/c10dry_*_test34.json` trên `pilot-snapshots`, mỗi file 1 lượt;
- `history_check` của mỗi lượt bằng đúng chuỗi của `expected_check`:
  - A: `commits=3 … bug_msg=1 … t0_present=1`;
  - B: `bug_msg=0`, `t0_present=1`;
  - C: `bug_msg=1`, `t0_present=0`;
  - D: `commits=2`, `bug_msg=0`, `t0_present=0`;
- `spent_usd` = 0 ở cả tám file.

Một lần chạy thử với `arm` = `c10all70` kiểm thêm phần 36 task.

**Bước 5. Chạy có phí (Claude bấm, sau bước 1–4).** Như bước 4, nhưng:
- `dryrun` = `false`;
- `arm` = `c10test34` hoặc `c10all70`, theo câu duyệt;
- `budget_usd` = trần đã duyệt.

Tám nhánh chạy cùng lúc trên một máy. Nếu job vượt giới hạn 355 phút: lượt đã xong vẫn được lưu, và lượt sau dùng `--skip-done`. Cách chạy tiếp như vậy phải được ghi trong bản đăng ký trước khi chạy.

**Bước 6. Sau khi chạy:**
- quy tắc chung ở mục 0;
- `history_check` của **mọi** lượt đúng chuỗi mong đợi; lượt nào sai thì là lỗi hạ tầng;
- `scripts/history_audit.py` cho từng nhánh;
- phân tích đúng như §43; thêm macro vào `scripts/make_numbers.py`; sửa paper.

## 2. C6: agent Flash trong môi trường một commit (Vertex, tiền thật; dự phòng)

**Khi nào:** chỉ khi C1/C4′ (mục 3) không chạy được trước 01/12. Đây là quyết định của @thuthuy (Q5).

**Chi phí:** §34 (cùng agent, môi trường gốc, 34 task, hai nhánh) đã chi **5,20 USD** (`spent_usd` của bốn file `results/s34_*_{pilot,rest}.json`).
- Dự kiến khoảng 5,2 USD.
- Trần = 5,20 + 2 × 0,34 = **5,88 USD**. 0,34 là cost_limit đã đăng ký ở ghi chú 34-2.
- Chi phí trong môi trường một commit có thể khác: ở §33, nhánh không skill một commit tốn hơn bản gốc 0,0246 USD trên 34 task.

**Bước 1. @thuthuy duyệt:** "Duyệt C6, trần 5,88 USD".

**Bước 2. Phần miễn phí (Claude):**
- thêm tùy chọn `--leak-free` cho plan `swesmith-s34` (một biến workflow, giống §35 nhánh `lf_*`), kèm test;
- bản đăng ký §44: phép so chính là hiệu giữa môi trường gốc (§34, đã có) và một commit. **Hai nhánh mới chạy ngày khác §34**, nên phải ghi rõ đây là phép so khác lượt chạy (T1 trộn tác dụng với khác biệt giữa hai lượt; `docs/method_end_of_pool.md` mục 6). Lựa chọn mạnh hơn: chạy lại cả bốn nhánh cùng lúc, chi phí gấp đôi, khoảng 11 USD (cần duyệt riêng).
- chạy thử miễn phí (`dryrun` = `true`).

**Bước 3. Chạy:** Actions → Pilot → `plan` = `swesmith-s34`, `arm` = `pilot`, rồi `arm` = `rest`, như §34. `cost_limit` = 0,34; `budget_usd` = trần đã duyệt.

**Bước 4. Sau khi chạy:** như mục 0, cộng `history_audit.py` cho cả hai kênh. Agent Flash đã dùng kênh test bị xóa ở 29/34 lượt không skill trong §34.

## 3. C1 / C4′: ba agent khác hãng trên Kaggle (hạn mức AI Kaggle, 0 USD tiền thật)

**Trạng thái** (`kaggle/TODO.md`, chỉ có trên nhánh mặc định `claude/gatekeeper-13-research-nxytoh`):
- cổng C5 đạt tại máy của phiên;
- ô C5 trên Kaggle chưa chạy (T2);
- ô C6 (N3) và ô C4′ (N4) chưa viết (D2, D3 của phiên Kaggle).

**Bước 1. @thuthuy trả lời T5:** "A" hoặc "B" (ghi chú 40-5 trong `kaggle/preregistration_s40.md`).
- **A:** 100 task; phép thử chính trên 34 task không mô tả; power 0,63.
- **B (lời khuyên):** thêm 36 task của §35; phép thử chính trên 70 task không mô tả; power 1,00. Tốn khoảng 36% thời gian và hạn mức hơn A. Không dùng tiền thật.

**Bước 2. @thuthuy chạy ô C5 (0 USD, khoảng 10 phút):**
1. Mở https://www.kaggle.com/benchmarks/tasks/new để tạo notebook.
2. Dán **cả** file `kaggle/notebooks/c5_cell.py` vào **một** ô, rồi chạy. Ô tải image task (1,4 GB).
3. Trong khung Output, tải `/kaggle/working/c5.json` và `c5.log`, gửi cho Claude.

**Bước 3. @thuthuy chép câu điều khoản của Kaggle về việc dùng hạn mức AI (T3)** và gửi nguyên văn. Cần trước C4′.

**Bước 4. Claude:**
- đọc `c5.json`: cả 6 phép thử phải đạt;
- nối `c3_agent.py` và `c4_driver.py` với lớp `chroot`, chạy thử miễn phí (D2);
- viết ô C6 và ô C4′ (D3), commit lên nhánh mặc định, báo @thuthuy.

**Bước 5. @thuthuy chạy ô C6** (6 task, 3 không mô tả, trần 0,5 USD hạn mức), theo hướng dẫn kèm ô. Gửi kết quả.

**Bước 6. @thuthuy chạy ô C4′** (ba agent, bốn nhánh, 100 hoặc 136 task theo T5), theo hướng dẫn kèm ô.
- **Không chạy lại `c4_cell.py` cũ** (T4: phiên 1 không hợp lệ, K21).
- Ghi mức "Daily AI Models" trên trang Quotas trước và sau khi chạy.

**Bước 7. Claude phân tích** theo ghi chú 40-5:
- phép thử chính: hiệu giữa hai môi trường, phép kiểm cuối pool, ngưỡng 3/α = 120 cho ba agent;
- `history_audit.py` cho từng nhánh.

## 4. C2: §38 phiên 3 trên Kaggle (khoảng 7 USD hạn mức, 0 USD tiền thật)

Theo `kaggle/run_s38_s39.md` và T1 của `kaggle/TODO.md`.

**Bước 1. @thuthuy:**
1. Mở notebook mục A.
2. Notebook chỉ còn một ô: dán cả file `kaggle/notebooks/a38_run_cell.py`.
3. Add Input → dataset `gatekeeper-a38-results` (kết quả seed 1 và 2).

**Bước 2. Ghi mức "Daily AI Models" trên trang Quotas**, rồi chạy bằng Save Version → Save & Run All (Commit).
- Dòng đầu log phải là `jobs 480, done 321`. Nếu khác thì dừng và gửi log.
- Ô tự dừng khi chạm 7,0 USD trong ngày, hoặc 40 USD cộng dồn.

**Bước 3. Khi xong:** tải các file `a38_results_*.jsonl` mới trong Output, gửi cho Claude.

**Bước 4. Claude:**
- phân tích theo `kaggle/preregistration_s38.md` (`kaggle/scripts/a38_analyse.py`);
- báo tỉ lệ theo từng model; ghi rõ các đầu ra không phải các lượt học độc lập (C2 của todo).

## 5. Thứ tự khuyên dùng trước 01/12

1. **Ngay:** @thuthuy trả lời T5 và Q4 (C10), chạy ô C5. Ba việc này không phụ thuộc nhau.
2. Claude làm bước 2–4 của C10 (khoảng một phiên) và D2–D3 của Kaggle.
3. C10 chạy có phí. C6/C4′ trên Kaggle chạy song song vì dùng hạn mức khác.
4. C2 bất kỳ lúc nào; mỗi ngày Kaggle chỉ cho một lượt khoảng 7 USD hạn mức.
5. C6 trên Vertex (mục 2) chỉ khi đến khoảng 25/11 mà C4′ vẫn chưa chạy được.
