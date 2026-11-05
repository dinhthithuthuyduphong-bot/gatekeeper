# Khung paper (bản 1, 05/11/2026): "A Placebo Test for Agent-Skill Evaluation"

**Vai trò** (@thuthuy duyệt): kiểm tra phương pháp đánh giá skill cho coding agent. Câu hỏi: các quy tắc đã công bố có qua được placebo A/A trên nhiễu thật không, và cách nào qua được. Thống kê là công cụ, không phải đóng góp chính.

**Mọi con số** lấy từ file trong `results/`; cột "Nguồn" ghi file. Kết quả **thăm dò** (chưa đăng ký trước) được đánh dấu †.

## Cấu trúc

| Mục | Nội dung | Kết quả dùng | Nguồn |
| --- | --- | --- | --- |
| 1. Introduction | Đánh giá skill đang dựa trên so một lần, tiêu chí minibatch và quy lỗi theo cặp. Chưa ai kiểm các cách này bằng placebo. Ba đóng góp | — | `docs/direction_final.md` |
| 2. Background & related work | SWE-Skills-Bench, SkillsBench, Dong et al., OpenSkillEval, ORACLE-SWE, GEPA/gskill, Library Drift, Qu et al., Randomness, Agent Evaluation Reliability, Who&When Pro, PatchDiff | Câu trích từ bản gốc | `sources-snapshots` |
| 3. Placebo design | Placebo A/A = hai lần chạy không skill trên cùng task. Dữ liệu: E1 (6 skill × 40 task × 3 seed), E2 (XRepoSkill × 109 × 3), T4. Định nghĩa trial, endpoint resolved, token và thời gian | 1.056 + 688 lần chạy | `run_metrics_e*.json` |
| 4. RQ1: decision rules under placebo | Bảng A: so một lần 0,46 / 0,80; GEPA nhận 14% đề xuất no-op (14–28 mỗi ngân sách); MH 0,025 / 0,111; e-SR 1,00; Library Drift 0,003; Gatekeeper 0,003 / 0,002. SWE-Skills-Bench: 6/392 ô (kỳ vọng 19,6); 8/98 skill có ý nghĩa so với 4,9 do may rủi † | §19 A, B | `placebo_suite.json` |
| 5. RQ2: attribution under placebo | Bước tạo ứng viên: E2 13 so với 14 (R = 1,08), hiệu năng 15 so với 14; E1 mọi CI của R chứa 1; ứng viên không lặp lại. Audit bằng skill giả: Flash-Lite quy lỗi cho skill giả ở 25/25 cặp. Flash và Pro: **chờ kết quả** | §18, §19 C, 19-2 | `replicate_attribution.json`, `sham_audit*.json` |
| 6. RQ3: placebo-calibrated rules | D2 (so số ứng viên với placebo): dương tính giả 0,006, độ nhạy 0,41 / 0,77 ở q = 0,2 / 0,3. D1 (lặp seed) chưa đủ. D3 Gatekeeper: dương tính giả 0,001, nhưng kém nhạy. F: quy lỗi theo từng task phân biệt kém ở k ≤ 10. Admission và thu hồi có kiểm soát: T4 (đối chứng dương trên agent thật, admit ở trial 20, khớp dự đoán đăng ký), T2b | §19 D, F; §14, §15 | `placebo_suite.json`, `t4_decision.json`, `two_stage_retirement.json` |
| 7. RQ4: context-dependence | Độ không đồng nhất theo task: bác được τ ≥ 0,20 (8% số mô phỏng), **không** bác được τ = 0,10–0,15. Phép thử nhất quán qua seed không có power. SWE-Skills-Bench: độ tin cậy split-half 0,16; tương quan giữa cấu hình 0,07 † | §18 H18-1, H18-2; D-M8 | `replicate_attribution.json`, `heterogeneity_power_v2.json`, `sskb_analysis.json` |
| 8. Discussion | Khi nào một lần chạy là đủ (biến đổi tất định, p6 T/T2; hiệu ứng lớn, T4). Khuyến nghị cho người làm benchmark và hệ thống skill | p6 T/T2 (tính lại từ dữ liệu thô) | `docs/p6_review.md` |
| 9. Threats to validity | Một model agent; một loại tác vụ (sửa lỗi trên SWE-bench); auditor là LLM, không phải người; skill trong E1 có hiệu ứng nhỏ; định nghĩa trial; nghi test PASS_TO_PASS chập chờn; các lỗi A75–A81 và sai lệch D-M7…D-M9 | — | `docs/audit_pilot.md` |
| 10. Data availability | Dữ liệu lặp lại có A/A (trajectory ở `raw-archive`), mã, các bản đăng ký trước | — | — |

## Việc còn lại để có bản thảo

| # | Việc | Chi phí |
| --- | --- | --- |
| W1 | Kết quả 19-2 (auditor Flash, Pro) vào mục 5 | đang chạy |
| W2 | Viết lại `paper/main.tex` theo khung này; bảng và hình sinh tự động từ `results/` | 0 |
| W3 | `refs.bib`: chỉ trích từ bản gốc đã đọc; `number_provenance.md`, `glossary.md` | 0 |
| W4 | 👤 Người biết thống kê đọc phần phương pháp; 👤 thầy duyệt | 0 |
| P2 | *(tùy chọn, @thuthuy duyệt)* Model agent thứ hai: lặp lại §18 và §19 A | khoảng 48 USD |
