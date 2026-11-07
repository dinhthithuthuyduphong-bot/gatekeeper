# Rà tài liệu về tính mới (05/11/2026; bản gốc lưu ở `sources-snapshots`, id trong ngoặc)

| Công trình | Làm gì (câu gốc) | Trùng với Gatekeeper ở đâu |
| --- | --- | --- |
| Propose, Don't Judge (`anytime_referee_2026`, arXiv 2609.27051, 22/09/2026) | "a frozen statistical referee … by betting, so its false-discovery guarantee holds at every stopping time for any proposal policy". Admit bằng "online e-BH"; thu hồi bằng "an e-detector" với ngưỡng "viability threshold δ … the edge that just pays" | **Trùng phần lõi:** nhận và thu hồi các thứ do LLM agent đề xuất bằng e-process, chống dừng tùy ý và đa giả thuyết, có ngưỡng chi phí. Khác: lĩnh vực tài chính; kiểm soát FDR (không phải FWER); không có scope; không có ghép skill |
| Library Drift (`library_drift_2026`) | Thu hồi skill theo kết quả, với "Evidence floor N_min … 100" và cận Hoeffding (ε ≈ 0,20) | Trùng phần thu hồi skill cho coding agent; quy tắc cỡ mẫu cố định, không anytime-valid |
| HDSO (`hdso_2026`) | "a skill is not accepted because it sounds plausible, but because a falsifiable hypothesis survives prospective validation" | Trùng ý tưởng nhận skill bằng kiểm định ghép cặp; không có bảo đảm sai số hình thức |
| EvoUndo (`evoundo_2026`) | Cổng nhận đột biến của harness dựa trên tập phát triển và tập giữ lại; tỉ lệ dương tính giả quan sát được | Cổng nhận có tỉ lệ sai đo được, không có bảo đảm |
| CELEUS (`celeus_2026`); Efficient Sequential Evaluation (`seq_eval_llm_2026`) | Đánh giá LLM có chứng nhận bằng e-process | Trùng phần "chi phí chứng nhận / đánh giá tuần tự" |
| Online FWER / alpha-spending (Tian & Ramdas 2021, qua tài liệu onlineFDR) | Phiên bản online của Bonferroni | Trùng phần sổ α |

**Còn lại có vẻ mới (phải kiểm thêm khi viết bài):**
1. FWER (không phải FDR) cho cả thư viện skill, theo từng (skill, scope).
2. Bảo đảm cho skill ghép (Định lý 4′, hệ số TV).
3. Đo trên khoảng 2.000 lần chạy ghép cặp của coding agent thật, kèm so sánh trực tiếp với các quy tắc đã công bố ở trên.

## Thu hồi hai bước (§15): rà tính mới (05/11/2026)

- **Universality of e-detectors** (`universality_edetectors_2026`): bài lý thuyết. Có các phụ lục "Residual criteria and restartable detector fields", "Repeated alarms and counting e-detectors", "Local-window control". Cách hai bước của mình (báo động, cách ly, xác nhận với α chia nhỏ, dùng lại) rất có thể là **một trường hợp riêng** của khung này.
  → **Không** tuyên bố tính mới về lý thuyết.
  → Đóng góp, nếu có, là **cách xây dựng cụ thể cho việc thu hồi skill**, cùng phép đo đánh đổi trên lần chạy agent thật, so với e-SR (Qu et al.) và Library Drift.
- **Sequential Control of False Positives in Online CPD** (`seq_fp_cpd_2026`): hiệu chỉnh ngưỡng bằng mô phỏng, FWER theo cửa sổ thời gian, dữ liệu điện thoại. Khác lĩnh vực; không có bước xác nhận.

## Rà tính mới: chỗ lộ lịch sử git, bộ chấm của gskill, skill học được khai thác chỗ lộ (06/11/2026)

**Nguồn:** tìm bằng web search ngày 06/11/2026. Các trang đã được thêm vào `configs/sources.json`. **Chỉ được trích sau khi workflow `sources` lưu bản gốc và kiểm đoạn trích (R1).** Các ý dưới đây là tóm tắt từ kết quả tìm kiếm, chưa phải câu trích.

| Ý | Đã có người báo? | Nguồn (id) | Hệ quả cho paper |
| --- | --- | --- | --- |
| Lịch sử git trong môi trường SWE-bench để lộ bản sửa (`git log --all`, commit tương lai) | **Có**, đã biết rộng rãi và đã sửa | `swebench_git_log_leak`, `swebench_git_log_fix`, `swebench_pro_verified`, `cursor_reward_hacking`, `poolside_benchmark_hacking` | Không tuyên bố là mới; trích làm bối cảnh |
| **Riêng SWE-smith:** commit "Bug Patch" ngay dưới HEAD, hoàn tác được để lấy mã trước lỗi | **Có**, ít nhất 3 báo cáo gần đây (vài ngày đến khoảng 3 tuần trước) | `marin_swesmith_git_leak`, `debuggym_swesmith_git_leak`, `debuggym_swesmith_git_fix`, `rllm_hide_git_history` | **Không** tuyên bố phát hiện chỗ lộ. Trích các báo cáo này |
| **Skill học tự động (GEPA/gskill) tự tìm ra và ghi chỗ khai thác vào văn bản skill**, và phần lớn mức tăng trong scope đến từ đó (§25: 29/53) | **Chưa thấy** | Chưa có nguồn. Kết quả tìm cho "GEPA" + "reward hacking" / "leak" không có bài nào nối hai ý | **Ứng viên đóng góp mới.** Cần §25 bước 3 (môi trường không lộ) để có số đo thay cho phân tích sau khi có dữ liệu |
| Bộ chấm công khai của gskill (`verify_with_patch`) cho "qua" bản vá rỗng | **Chưa thấy** issue hay bài nào | Kết quả tìm chỉ ra trang hướng dẫn và blog của gskill | **Ứng viên đóng góp mới.** Nên báo tác giả trước khi công bố (@thuthuy quyết) |
| Chứng nhận có bảo đảm trong scope, rồi đo việc không chuyển sang scope khác, trên skill thật | **Chưa thấy** ở dạng này. Có công trình gần: chuyển giao skill và memory (`Demystifying Agent Skills`, SkillRevise, EvoClawBench), "lucky pass" (AgentLens) | Cần thêm vào `sources.json` và đọc bản gốc trước khi so sánh | Đúng câu hỏi của paper gốc; phụ thuộc kết quả §25 bước 3 |

**Hệ quả cho cách định vị:**
- **Không** viết "chúng tôi phát hiện SWE-smith lộ đáp án qua git". Viết: "chỗ lộ đã được báo (trích dẫn); đóng góp của chúng tôi là cho thấy **một bộ học skill tự động khai thác nó**, đo phần mức tăng do nó gây ra, và cho thấy chứng nhận trong scope không chuyển sang scope không lộ".
- Rủi ro thời điểm: các báo cáo về SWE-smith mới xuất hiện trong vài tuần gần đây, nên có thể sớm có bài khác về đúng chủ đề "skill học được khai thác chỗ lộ". Nên viết và đăng sớm.

**Bổ sung (07/11/2026): chỉ dẫn đọc lịch sử git do quá trình tối ưu đưa vào, không có sẵn.** Kiểm trên mã ghim `gepa@8c7b697` (bản lưu `gskill_seed_candidate`, `gskill_mini_yaml`, `gskill_original_mini_yaml`):
- Skill khởi đầu là rỗng: *"# 3. Initial Candidate (Baseline Prompt) # Start with empty skills - GEPA will learn a…"*.
- `mini.yaml` (2.166 ký tự) không chứa "git".
- Prompt viết skill và prompt gộp skill trong `train_optimize_anything.py` (31.634 ký tự) chỉ chứa "git" **1 lần**, trong danh sách lệnh: *"Access to bash commands (grep, find, cat, sed, python, pytest, git, etc.)"*.
- Các chuỗi `history`, `History`, `HISTORY`, `commit`, `Commit`, `COMMIT`, `git log`, `log -`, `recent`, `Bug Patch` đều có **0** lần xuất hiện. Phép tìm phân biệt chữ hoa (`scripts/fetch_sources.py::excerpts`), nên đã kiểm từng biến thể.
- **Hệ quả:** câu "Check Git History … 'Bug Patch'" trong skill jinja và câu "look at recent git commits (`git log -p -n 3`)" trong skill bleve do bộ phản chiếu viết ra từ dữ liệu đánh giá. Điều này làm mạnh ứng viên đóng góp "bộ học skill tự khai thác chỗ lộ".
- **Giới hạn:** chỉ kiểm mã của gskill. Thư viện GEPA bên dưới có thể có prompt riêng; gskill dùng proposer tự định nghĩa (`LoggingProposer`, `LoopProposer`) trong chính file này.
