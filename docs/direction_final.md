# Hướng đi đề xuất cho paper (05/11/2026, chờ @thuthuy và thầy duyệt)

**Cơ sở:**
- `docs/strategy_review.md` (kỳ vọng gốc, to-do gốc, các kết quả đã đo);
- `docs/p6_review.md` (chỉ lấy dữ liệu thí nghiệm của p6, không lấy lý thuyết);
- bản gốc 5 bài mới đọc qua workflow `sources` (run 42017123630, nhánh `sources-snapshots`), cùng các bài đã có (Qu et al., SWE-Skills-Bench).

## 1. Đối chiếu tính mới (câu trích từ bản gốc)

| Công trình | Đã làm (câu gốc) | Chưa làm |
| --- | --- | --- |
| On Randomness in Agentic Evals (`randomness_agentic_evals_2026`) | "single-run pass@1 estimates vary by 2.2 to 6.0 percentage points … even at temperature 0"; khuyên "estimate pass@1 from multiple independent runs" và "use statistical power analysis" | Đoạn trích theo từ khóa không có kết quả nào cho "paired", "sequential", "peek", "anytime", "skill" (bản gốc 65.903 ký tự). Họ so model và agent, không so có/không skill |
| Coding Agents Have Converged (`converged_agents_2026`) | Kiểm toán 254 bài nộp leaderboard: "Exact paired McNemar tests separate none of the 29 adjacent Verified top-thirty pairs"; "The statistical machinery itself is established, and we use it as such" | Không chạy model; không có skill; không có kiểm định tuần tự |
| Same Model, Different Harness (`same_model_harness_2026`) | So ghép cặp hai cấu hình harness: F2PF "from 28% to 49%" | Một can thiệp lớn; không có cổng nhận hay kiểm soát sai số |
| Engineering Reliable Coding Agents (`reliable_coding_agents_2026`) | Chuyên khảo tổng quan: "Measurement determines whether a difference is credible. Grading converts observations into acceptance decisions" | Danh mục thực hành; không có giao thức có bảo đảm |
| PatchDiff (`patchdiff_2025`, ICSE 2026) | "29.6% plausible patches induce different behavior than the ground truth patches"; "28.6% of behaviorally divergent patches are certainly incorrect" | **Trùng với Study Q của p6** (43,1% / 11,1%), nên **không dùng Q làm đóng góp** |
| SWE-Skills-Bench (`sskb_paper`) | "no standard procedure tests an individual skill before installation"; "we run every task once without the skill and once with it"; "use a statistical test to classify each skill"; "92 of 98 skills are Ineffective" | Mỗi nhánh chạy **một lần** cho mỗi requirement, kiểm định cỡ mẫu cố định trên 10 requirement. Không đo nhiễu A/A, không đề cập theo dõi liên tục, không có thu hồi |
| Propose, Don't Judge (Qu et al., `anytime_referee_2026`) | Referee bằng betting, "false-discovery guarantee holds at every stopping time"; admit bằng online e-BH, thu hồi bằng e-detector | Lĩnh vực tài chính; FDR; không có coding agent, scope, skill ghép |

**Khoảng trống còn lại (có bằng chứng):**
- SWE-Skills-Bench đặt đúng bài toán ("tests an individual skill before installation"). Nhưng thủ tục của họ là một lần chạy mỗi nhánh, cộng một kiểm định cỡ mẫu cố định.
- Các bài về nhiễu cho thấy một lần chạy là không đủ, nhưng không xét skill, không xét nhận skill, không xét theo dõi liên tục.
- Qu et al. có công cụ thống kê đúng, nhưng ở lĩnh vực khác.
- **Chưa ai đo, trên coding agent thật, điều gì xảy ra với việc kiểm tra skill trước khi cài khi kết quả có nhiễu và bị xem nhiều lần, rồi đưa ra và kiểm chứng một thủ tục có bảo đảm.**

## 2. Hướng đề xuất

**Tên làm việc:** *Testing a Skill Before You Install It: Noise, Peeking and Anytime-Valid Admission for Coding-Agent Skills* (kiểm tra skill trước khi cài: nhiễu, xem kết quả nhiều lần, và việc nhận skill với bảo đảm đúng ở mọi thời điểm dừng).

**Đóng góp** (không tuyên bố công cụ thống kê mới; trích Qu et al., Ville, Wang & Ramdas):

| RQ | Câu hỏi | Dữ liệu đã có | Còn thiếu |
| --- | --- | --- | --- |
| RQ1 | Nhiễu của phép so có/không skill lớn tới đâu so với các mức tăng skill đã công bố? | A/A ghép cặp trên khoảng 2.000 lần chạy; F(n); ghép cặp giảm phương sai 3,3–4,6×; 7/13 mức tăng đã công bố nằm trong nhiễu; dư địa theo loại thất bại (thăm dò) | Đăng ký và chạy lại phần dư địa; bảng số trial cần (F3) |
| RQ2 | Các cách nhận skill đang dùng có giữ được tỉ lệ nhận nhầm khi kết quả có nhiễu và bị xem nhiều lần không? | Null thật: B-X2 0,026 → 0,103. Plasmode P1: 0,075 → 0,303. GEPA, plug-in (T1, P2). Lựa chọn trên SWE-Skills-Bench (C3: 43–44% so với nền 38,5%) | Áp đúng thủ tục kiểu SWE-Skills-Bench (một lần mỗi nhánh, 10 requirement) lên nhiễu thật (miễn phí, F8) |
| RQ3 | Thủ tục anytime-valid có giữ được sai số và vẫn chứng nhận được hiệu ứng thật không, với chi phí bao nhiêu? | FWER ≤ 0,002; độ phủ 0,59 / 0,80; T4 admit ở trial 20, khớp dự đoán đăng ký 21–25; §16 (không có lợi thế khi chỉnh ngưỡng bằng đáp án, báo cáo thẳng) | Chứng minh gọn (F1) |
| RQ4 | Thu hồi skill khi hiệu ứng đổi chiều | T2: Library Drift 53%; e-SR thu hồi nhầm 35%. T2b: 100% phát hiện, độ trễ 75, 0/1000 thu hồi nhầm | — |
| Phạm vi | Khi nào **không** cần thống kê | p6 T/T2: quy tắc Ruff trên 120 dự án PyPI. Tác hại hiếm và tất định; smoke test 20 draw đạt 0/11 và 1/20, còn replay + fingerprint nhận nhầm 9/11 và 17/20 | Chỉ một đoạn hoặc một RQ phụ; báo cáo cả việc Gatekeeper thua về chi phí |

**Các điểm yếu reviewer sẽ chấm, và cách xử lý:**
1. **Một model.** SWE-Skills-Bench có 4 cấu hình agent–model, dữ liệu công khai, đã phân tích một phần (`results/sskb_analysis.json`). Dùng nó cho RQ2 (miễn phí) là bằng chứng ngoài, nhiều model. Phần nhiễu A/A vẫn chỉ có một model, nên P2 vẫn nên làm nếu có ngân sách.
2. **Trùng công cụ với Qu et al.** Nói thẳng là áp dụng; đóng góp nằm ở bài toán SE, phép đo, và các so sánh trực tiếp.
3. **Định lý.** Chỉ giữ: admission (Ville + sổ α), ghép có thứ tự định nghĩa rõ, thu hồi hai bước. Bỏ cận dịch phân phối TV nếu không dùng. Mỗi ký hiệu một nghĩa, định nghĩa "trial" một lần. Tránh đúng lỗi của p6.
4. **Không chứng nhận được skill thật.** Đây là kết quả của RQ1 (dư địa, nhiễu), không phải điểm yếu. T4 cho thấy giao thức chứng nhận đúng khi hiệu ứng có thật.

## 3. To-do (theo L38: kết quả gì, P(có kết quả dùng được), chi phí)

| # | Việc | Chi phí | P(có kết quả dùng được) | Lý do |
| --- | --- | --- | --- | --- |
| F8 | RQ2 trên thủ tục kiểu SWE-Skills-Bench: một lần chạy mỗi nhánh, 10 requirement, kiểm định cố định; áp lên plasmode nhiễu thật và lên dữ liệu SWE-Skills-Bench | 0 | ≈ 1 | Phép tính trên dữ liệu có sẵn |
| F2 | Đăng ký §18, rồi đo: dư địa, F(n), A/A trên E1 + E2; chấm lại bản vá gốc nghi chập chờn | 0 | ≈ 1 | Phép đo |
| F3 | Bảng số trial cần để chứng nhận các mức tăng đã công bố (SWE-Skills-Bench Golden, XRepoSkill, MemGovern) | 0 | ≈ 1 | Cùng cách mô phỏng đã dự đoán đúng T4 |
| F1 | Chứng minh gọn (3 mệnh đề) + 👤 người biết thống kê đọc | 0 | Cao | Kết quả chuẩn |
| F5 | Viết paper; bảng và hình sinh tự động; kiểm `refs.bib` | 0 | Cao | — |
| P2 | *(tùy chọn)* A/A trên model thứ hai, khoảng 200 lần chạy | Gemini Flash khoảng 48 USD | ≈ 1 | Phép đo, không có cổng; @thuthuy duyệt |

**Không làm:** pilot skill thật mới; bậc thang skill; Study Q; mọi lý thuyết của p6.

**Mức cạnh tranh** (định tính, không có số để tính xác suất được nhận):
- Không có P2: có dữ liệu ngoài từ 4 cấu hình của SWE-Skills-Bench, nên **cạnh tranh được nhưng ở ranh giới**.
- Có P2: **cạnh tranh được**.
- Rủi ro lớn nhất còn lại: reviewer coi đây là "áp dụng thống kê đã biết". Cách giảm: chứng minh bằng số rằng thủ tục đang được đề xuất trong tài liệu (SWE-Skills-Bench) hỏng trên nhiễu thật (F8).
