# Phân tích nguyên nhân gốc của thất bại (06/11/2026)

**Yêu cầu của @thuthuy:** dò từng dòng 3 tài liệu gốc, to-do gốc và từng bước của các cách làm cũ; tìm nguyên nhân gốc và sửa.

**Đã đọc:**
- `docs/01-FSE-2027-13-paper.pdf`: toàn văn, 900 dòng văn bản sau khi bỏ số dòng.
- `docs/02-…-reading-list.pdf` và `docs/03-…-summary.pdf`: toàn văn.
- `TODO.md`: §0–§7, bản 2 ngày 01/11.
- Các bước đã làm:
  - `docs/budget_200.md`;
  - `docs/preregistration_g1_v2.md`, `_e1.md`, `_e2.md`, `_main.md` §1–§24;
  - `docs/g1_verdict.md`, `docs/pilot_postmortem.md`;
  - `docs/audit_pilot.md` A1–A86.
- Nguồn đã lưu `gskill` (nhánh `sources-snapshots`), và README của gskill ở commit đã ghim `8c7b697`.

## 1. Thất bại là gì (đo được)

| # | Hiện tượng | Số | Nguồn |
| --- | --- | --- | --- |
| F1 | Không skill thật nào được chứng nhận | G1, E1, E2 đều FAIL. E1 có hiệu ứng tới hạn khoảng 0,08; E2 khoảng 0,04 | `results/e1_final.json`, `results/e2_final.json` |
| F2 | Thiết kế chứng nhận theo (skill, scope) không kham nổi | δ = 0,109 cần 216–470 trial mỗi ô (540–1.180 USD); δ khoảng 0,03 thì 4.000 trial vẫn không đủ | `docs/pilot_postmortem.md` |
| F3 | Tác dụng lớn đã công bố không lặp lại trên agent của mình | `viper` +1,5 điểm so với +17,7 công bố (§22); Pro: hiệu số bằng 0 vì chạm trần (§23a) | §22, §23a |
| F4 | Skill dạng chương trình sửa code cũng không khả thi trên SWE-bench | Ô lớn nhất có 5 task, cần 23 (§24) | `results/edit_shape_survey.json` |

## 2. Những gì đã kiểm và **không** phải nguyên nhân gốc

- **Lỗi mã:**
  - A1–A85 đều được sửa trước khi phân tích.
  - Rà soát sau G1: 657/657 patch chấm khớp. Tính lại độc lập cho kết quả khớp.
  - A/A sạch: p = 0,82 (E1) và 0,75 (E2).
- **Công thức:**
  - Các chỗ sai của paper gốc (hệ số 2 ở Theorem 4, Theorem 7, Prop. 9) đã sửa và có test (`docs/theory/corrections.md`).
  - Trên nhiễu thật, e-process nhận nhầm ở tỉ lệ 0,002 (mức cho phép 0,025).
- **Endpoint:** đổi resolved sang loss phân bậc như paper gốc không đổi kết luận của E1 (−0,013; +0,027; −0,005).

## 3. Chuỗi "vì sao"

1. **Vì sao không chứng nhận được?** Vì số trial cần cho mỗi ô lớn hơn số task trong ô có liên quan tới skill, và hiệu ứng trên mỗi cặp nhỏ so với nhiễu (SD khoảng 0,36 mỗi cặp).
2. **Vì sao hiệu ứng nhỏ và ít task?** Vì task đích là issue tự nhiên của SWE-bench, nơi một skill chỉ liên quan tới một phần nhỏ task:
   - precision kích hoạt 0,14–0,34 (R16);
   - hình dạng của bản sửa gốc chỉ phủ được 3,6% task (§24);
   - chỉ khoảng 9% số lần chạy rơi vào đúng loại thất bại mà skill "cách chạy test" nhắm tới (§17, D-M7).

   Hiệu ứng đo được bằng khoảng (tỉ lệ task liên quan) × (hiệu ứng trên task liên quan). Đây là phép phân rã kỳ vọng theo hai nhóm; nó giả định skill không tác động lên task không liên quan.
3. **Vì sao dùng issue tự nhiên?** Vì R13 (01/11) bỏ benchmark tự dựng SkillShift-SE, và chỉ lấy task từ benchmark chuẩn. Trên thực tế, chỉ SWE-bench, Verified và Live được dùng.
4. **Vì sao điều đó trái với thiết kế của paper gốc?**
   - Ước lượng chính được định nghĩa trên P_s, phân phối các task **trong scope của skill**: *"STR(S, s) = E_{x∼P_s}[ℓ(x, π) − ℓ(x, ∅)]"*.
   - Giả định *"Within a declared scope s, target contexts used for trials are drawn i.i.d. from P_s"* (Assumption 3).
   - Đơn vị đánh giá là *"180 source-skill/target-context pairs"*, tức những cặp mà skill được áp lên đích. Vì vậy 20,6–57,9% số cặp có hại theo cách dựng (Table 1).
5. **Vì sao lọt qua?** To-do gốc đã thấy trước vấn đề này và ghi sẵn cách xử lý, nhưng không cách nào được làm:
   - §3, mục 8: *"Skill chỉ liên quan 10% task thì hiệu ứng bị pha loãng 10 lần"* → *"P_s = phân phối task mà I(x) đúng"*.
     Trong thực tế, I(x) được cài bằng regex trên issue với precision ≤ 0,34, nên P_s vẫn gần như là phân phối của mọi issue.
   - §4 và §6.1 cho phép dùng *"tập task SWE-smith đã công bố, khi thiếu task cho một scope"*. Mục này **chưa từng được dùng**.
   - Phase 2: *"gskill cho 1 repo → có SKILL.md và kết quả holdout"*. **Chưa làm.**
   - Phase 3 (R15): *"đo hiệu ứng của 3–5 skill dạng edit program"*. **Chưa làm** (A86).
   - Phase 4: *"Chạy agent trên task SWE-Gym → trajectory thành công"* để học skill. **Chưa làm**; skill được viết tay.
   - Quy tắc chọn phương án sau G1 (Bổ sung 4) chỉ tính n_có trên SWE-bench. Nó không xét tới quần thể SWE-smith mà to-do gốc cho phép.

## 4. Nguyên nhân gốc

**RC. Quần thể task dùng để đo không phải P_s.** Các skill được đo trên issue tự nhiên, nơi skill hầu như không liên quan. Thiết kế của paper gốc lại đo skill trên task trong scope của nó, và to-do gốc có sẵn đường làm điều đó bằng SWE-smith. F1, F2 và F4 đều suy ra trực tiếp từ RC.

**Bằng chứng đối chứng: tác dụng lớn có thật ở quần thể khớp scope.** gskill (nguồn `gskill`, đã lưu):
- Câu gốc: *"we learn repository-specific skills for jinja and bleve with a simple agent (Mini-SWE-Agent, gpt-5-mini), boosting its resolve rate from 55% to 82% on Jinja and from 24% to 93% on Bleve."*
- Task đánh giá là task SWE-smith **của chính repo đó**. README ở commit `8c7b697` ghi *"--train-size 200 --val-size 50 --test-size 100"*, tách từ `load_dataset("SWE-bench/SWE-smith")` theo repo.
- Đây là đúng thiết kế (skill, scope = repo) của paper gốc, với hiệu ứng 0,27–0,69.

**Đếm quần thể (`results/swesmith_census.json`, 0 USD, từ metadata đã commit):**
- SWE-smith có 59.136 task trên 222 repo.
  - 181 repo có ≥ 31 task (= n_min ở K = 3.991, §24).
  - 126 repo có ≥ 100 task; 66 repo có ≥ 300 task.
- Repo có cả task SWE-smith lẫn task tự nhiên (dùng để đo sự phụ thuộc vào scope):

  | Repo | Task SWE-smith | Task tự nhiên |
  | --- | --- | --- |
  | pandas | 2.354 | 737 (SWE-Gym) |
  | MONAI | 527 | 374 (SWE-Gym) |
  | moto | 541 | 343 (SWE-Gym) |
  | dvc | 467 | 225 (SWE-Gym) |
  | conan | 978 | 165 (Live) |

**Bằng chứng ngược, phải nêu:**
1. Trên chính task của SWE-Skills-Bench, `viper` không lặp lại trên agent của mình (§22). Dữ liệu của SSKB cũng cho tương quan giữa 4 cấu hình của họ chỉ từ −0,105 đến 0,212. Như vậy **agent và model** cũng là một yếu tố (RC2). RC giải thích vì sao **không thể** chứng nhận, nhưng **không** chứng minh skill sẽ có ích trên P_s.
2. Mức tăng của gskill chưa được tái hiện độc lập; đây là bài blog, không phải bài bình duyệt.

**Bổ sung sau rà soát lần 2 (`docs/potential_issues.md` P2):** quần thể khớp scope là **cần nhưng chưa đủ**. SWE-Skills-Bench đo trên task viết riêng cho từng skill mà 92/98 skill vẫn không hiệu quả. Tác dụng lớn đã công bố (gskill) đến từ skill **được tối ưu theo kết quả trên chính quần thể đó**. Vì vậy nguyên nhân gốc đầy đủ là: **quần thể sai, và skill không được học trên quần thể của scope.** Mức tăng của gskill cũng có thể là đặc điểm của SWE-smith (P3), và thiết kế sửa phải đo điều này.

**Yếu tố góp phần:**
- **RC2:** model yếu (Flash-Lite, tỉ lệ giải nền 0,27) làm nhiễu lớn, và nó không làm theo chỉ dẫn (§20 S5).
- **RC3:** skill viết tay dạng hướng dẫn, thay vì skill học từ trajectory như paper gốc (A86).
- **RC4:** endpoint của paper gốc (≥ 5 điểm so với B6) có power 3–5% với chính số của paper (R14). Lỗi này thuộc paper gốc và đã được sửa.

## 5. Sửa

1. **Quy tắc phòng ngừa** (L45, mục kiểm tra §4): trước mỗi thí nghiệm, phải đo được tỉ lệ task trong quần thể thuộc scope của skill. Nếu tỉ lệ này < 1, hiệu ứng thiết kế phải được nhân với tỉ lệ đó trước khi tính n.
2. **Thiết kế sửa (đề xuất, chờ @thuthuy, vì thêm thí nghiệm):** dùng lại đúng các mục chưa làm của to-do gốc.
   - **Skill:** gskill (code MIT, đã có trong to-do gốc). Skill học trên tập train SWE-smith của repo R.
   - **Scope và P_s:**
     - (a) task SWE-smith giữ lại của R: kiểm chứng nhận, tương ứng RQ1;
     - (b) task tự nhiên của cùng repo R, ví dụ pandas 737 hay MONAI 374: kiểm "skill có nên chạy ở đây không";
     - (c) task SWE-smith của repo khác: chuyển giao giữa repo, regime B của paper gốc. Cặp có hại xuất hiện tự nhiên ở đây, không phải dựng.
   - **Quyết định:** Gatekeeper theo từng ô, cùng e-process và α như §2. So với B1, B2, plug-in, B-X2 và B8 trên cùng dữ liệu.
   - **R13:** SWE-smith là benchmark đã công bố, nằm trong bảng 6.1. Task, test và nhãn chiến lược sinh lỗi đều là của họ.
3. **Các bước miễn phí tiếp theo:**
   - adapter harness SWE-smith, có test;
   - chạy thử bằng model giả lập trên 1 task thật;
   - kiểm tải image;
   - đo chi phí của gskill bằng một lần chạy có trần nhỏ. Lần đo này cần @thuthuy duyệt, vì nó thuộc một thí nghiệm mới.
