# Hướng đi hoàn chỉnh (bản 3, 05/11/2026; chờ @thuthuy và thầy duyệt)

Bản 2 (kiểm skill trước khi cài, lấy thống kê làm trục chính) đã bị @thuthuy loại. Bản này giữ thống kê làm **công cụ**, không làm đóng góp chính.

## 1. Câu hỏi

**"Skill hay xúc xắc?"** Khi một skill có vẻ giúp ở task này và hại ở task khác, đó là phụ thuộc ngữ cảnh thật, hay chỉ là nhiễu giữa các lần chạy?

Câu hỏi này là tiền đề của paper gốc ("Scope before Reuse": skill đúng ở chỗ này, sai ở chỗ khác), và cũng là tiền đề của nhiều công trình năm 2026. Không công trình nào kiểm nó bằng **chạy lặp có đối chứng A/A**.

**Tên làm việc:** *Is It the Skill or the Dice? Replicated Evidence on Context-Dependence and Skill-Induced Failures in Coding Agents.*

## 2. Tính mới (đã đọc bản gốc; nhánh `sources-snapshots`)

| Công trình | Làm gì (câu gốc) | Thiếu gì mà mình có |
| --- | --- | --- |
| Dong et al., Microsoft (`skill_induced_failures_2026`) | Quy lỗi bằng cách so lần chạy có skill với "a no-skill or semantically matched-skill reference run that solves the same task"; 307 ca; nói rõ muốn loại "ordinary differences between repeated executions"; "we do not rerun the benchmark tasks". Hồi quy hiệu năng: "min(r_tok, r_time) > 1.0 ∧ max(r_tok, r_time) > T", T = 2,0 | Không chạy lại, không có A/A. Bước tạo ứng viên tự động chưa được kiểm bằng placebo |
| SWE-Skills-Bench (`sskb_paper`) | "we run every task once without the skill and once with it" | Trên dữ liệu công khai của họ (mình tự tính): độ tin cậy split-half của tác dụng skill là 0,16; tương quan giữa các cấu hình là 0,07 |
| SkillJuror (`skilljuror_2026`) | 5 trial mỗi điều kiện; "The benefit is task-dependent" | Không so độ phụ thuộc task với nhiễu A/A |
| ACES, NVIDIA (`continuous_skill_eval_2026`) | "88 cells have two paired trial files and the remaining 113 have one" | Chạy lặp chỉ một phần |
| Agent Evaluation Reliability (`agent_eval_reliability_2026`) | Phân rã phương sai cho leaderboard | Không xét skill. Câu "interaction not separately identifiable" hiện chỉ có trong bản tóm tắt tìm kiếm; **phải trích đúng từ bản gốc trước khi dùng** |
| OpenSkillEval, ORACLE-SWE, PatchDiff, Randomness | Agent có làm theo skill không; đóng góp của thông tin oracle; patch qua test nhưng sai hành vi; nhiễu khi so model | Câu hỏi khác; chỉ trích |

## 3. Câu hỏi nghiên cứu, dữ liệu, trạng thái

| RQ | Câu hỏi | Dữ liệu (đã có) | Phân tích | Trạng thái |
| --- | --- | --- | --- | --- |
| RQ1 | Tác dụng của skill có phụ thuộc task, repo hay cấu hình **vượt quá nhiễu** không? | E2: XRepoSkill (rule rút từ repo khác) × 109 task × 3 seed. E1: 6 skill × 40 task × 3 seed. SWE-Skills-Bench: 4 cấu hình | H18-1 (nhất quán qua seed), H18-2 (τ²); độ tin cậy split-half và tương quan giữa cấu hình | Đã đăng ký §18. E1 đã xem (thăm dò: 0/40 task nhất quán ở 5/6 skill) |
| RQ2 | Bao nhiêu ứng viên "lỗi do skill" (theo đúng quy tắc của Dong et al.) cũng xuất hiện khi **không có skill nào**? | E1 + E2 (A/A giữa các seed) | H18-3 (lỗi chức năng), H18-4 (hiệu năng), H18-5 (có lặp lại không) | Đã đăng ký; **chưa tính trên dữ liệu nào** |
| RQ3 | Phép đo có phát hiện được tác dụng thật khi nó tồn tại không? | Plasmode trên nhiễu E2; T4 (+0,55, 11 task được giúp / 0 task bị hại) | Ghi chú 18-2 (power theo τ) | Đã đăng ký |
| RQ4 | Vậy phải đánh giá skill thế nào? | Các kết quả trên; giao thức Gatekeeper (nhận và thu hồi) | Cần bao nhiêu lần lặp để tách ngữ cảnh khỏi nhiễu; cách làm placebo A/A; Gatekeeper là một cách áp dụng | Thống kê ở vai trò công cụ |

**Vì sao hướng này không phải đặt cược:**
- Mọi RQ đều là phép đo trên dữ liệu đã có (0 USD).
- Kết quả theo chiều nào cũng có giá trị:
  - **"Phần lớn là nhiễu":** phương pháp đánh giá và quy lỗi đang dùng cần đối chứng A/A, và tiền đề "skill phụ thuộc ngữ cảnh" chưa được chứng minh.
  - **"Có phụ thuộc thật":** lần đầu có số đo đã tách khỏi nhiễu, ủng hộ ý tưởng scope của paper gốc.

## 4. Rủi ro và cách xử lý

| # | Rủi ro | Xử lý | Còn lại |
| --- | --- | --- | --- |
| 1 | "Không thấy phụ thuộc ngữ cảnh vì skill vốn không có tác dụng" | Skill có hại ở E1 có trung bình −0,05 tới −0,06, khác 0. Kiểm power bằng plasmode (18-2). Tùy chọn P3: đối chứng dương cho độ không đồng nhất | Cần P3 nếu muốn chắc |
| 2 | Bị coi là "bác bỏ" | Trình bày là **phép đo đầu tiên có lặp lại** và một **giao thức placebo** dùng được ngay. Không viết "307 ca là nhiễu", vì họ còn có audit thủ công | Phụ thuộc cách viết |
| 3 | Một model | SWE-Skills-Bench có 4 cấu hình (độ tin cậy). A/A chỉ có một model, nên P2 trực tiếp lặp lại RQ1 và RQ2 | P2 khoảng 48 USD |
| 4 | Thời gian chạy bị ảnh hưởng vì chạy song song | Có độ nhạy chỉ dùng token (ghi chú 18-1) | — |
| 5 | Dữ liệu khác loại với Dong et al. (SWE-bench sửa lỗi so với SkillsBench và SWE-Skills-Bench) | Nêu rõ. Nếu họ công bố dữ liệu từng lần chạy thì áp placebo trực tiếp (chưa kiểm) | Kiểm xem họ có công bố dữ liệu không |
| 6 | Thăm dò E1 đã xem trước | Đã công bố trong §18. RQ1 xác nhận trên E2. RQ2 chưa xem trên dữ liệu nào | — |
| 7 | Câu trích của Agent Evaluation Reliability chưa xác minh | Phải lấy đúng câu từ bản gốc, hoặc bỏ | Việc F0 |

## 5. To-do

| # | Việc | Chi phí | Kết quả chắc chắn có |
| --- | --- | --- | --- |
| F0 | Trích đúng câu của Agent Evaluation Reliability; kiểm Dong et al. có công bố dữ liệu từng lần chạy không | 0 | Có |
| F1 | `scripts/replicate_attribution.py` + test + review R-38 + chạy thử trên dữ liệu giả | 0 | Có |
| F2 | Lấy quỹ đạo E2 từ `raw-archive` để có token và thời gian | 0 | Có |
| F3 | Chạy H18-1 tới H18-5 và kiểm power 18-2 | 0 | Có |
| F4 | Viết paper. Giữ T1–T4, T2b, nhiễu nền làm phần phương pháp và phần thảo luận | 0 | Có |
| P2 | *(tùy chọn)* A/A trên model thứ hai | khoảng 48 USD | Có |
| P3 | *(tùy chọn)* Đối chứng dương cho độ không đồng nhất: `control-oracle-tests` (+0,158 ở G1) × 40 task × 3 seed | khoảng 19 USD | Có (phép đo) |

**Mức cạnh tranh** (định tính):
- Nhờ góc nhìn mới (lặp lại + placebo) và việc kiểm trực tiếp phương pháp của ba công trình năm 2026: **cạnh tranh được**.
- Có P2 và P3: **cạnh tranh tốt**.
- Mình không hứa được nhận.
