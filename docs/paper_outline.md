# Dàn ý paper (bản 1, 07/11/2026; chờ @thuthuy duyệt)

**Ba nguyên tắc của bản này (@thuthuy, 07/11):**
1. Câu chuyện thuyết phục.
2. Số liệu thuyết phục: mọi con số có file kết quả và mục đăng ký trước.
3. **Không tự chế khái niệm:** mọi thuật ngữ lấy từ paper gốc (FSE-2027-13) hoặc từ một nguồn trong `configs/sources.json`. Bảng ở mục 0 liệt kê từng thuật ngữ.

**Quy ước:**
- "S" là resolved theo bộ chấm của SWE-smith hoặc SWE-bench; "L" là luồng chấm trong mã công khai của gskill.
- Số trong bản này lấy từ bản đăng ký trước. Khi viết `paper/main.tex`, mọi số được **sinh tự động** từ `results/` (`scripts/make_tables.py`), không chép tay.
- **[CHỜ]** đánh dấu kết quả chưa có. Quy tắc diễn giải của chúng đã được viết trước.

---

## 0. Thuật ngữ dùng trong paper và nguồn

| Thuật ngữ (tiếng Anh trong paper) | Nghĩa | Nguồn |
| --- | --- | --- |
| skill, scope, selective transfer risk (STR), admission, retirement | Như paper gốc: STR(S, s) = E_{x∼P_s}[ℓ(x, π) − ℓ(x, ∅)] | Paper gốc (FSE-2027-13), `paper/main.tex` §2 |
| Agent Skill (`SKILL.md`) | Định dạng skill | `agent_skills` |
| e-process, anytime-valid | Quá trình cược; bất đẳng thức Ville | `waudby_smith_ramdas`, `ville_inequality` |
| resolved, FAIL_TO_PASS, PASS_TO_PASS | Endpoint của SWE-bench | `swebench` |
| A/A test | So hệ thống với chính nó để kiểm hệ thống đo | `kohavi_aa` |
| negative control | Đối chứng không thể có tác dụng | `negative_controls_llm_2026` |
| length-matched irrelevant skill (C2) | Skill không liên quan, độ dài byte lệch không quá ±5%; tách tác dụng của nội dung khỏi độ dài prompt | `webdev_skills_bench_2026` (nhánh `trial`), `skillcenter_2026` |
| reward hacking | "agent searching for or exploiting information that may reveal the reference solution" | `swebench_pro_verified` (phải trích đúng câu trong bản lưu) |
| git-history leak | Lịch sử git trong môi trường để lộ bản sửa | `swebench_git_log_leak`, `marin_swesmith_git_leak`, `debuggym_swesmith_git_leak` |
| single-commit (leak-free) history | Thay lịch sử bằng một commit duy nhất chứa cây có lỗi | Cách sửa của `debuggym_swesmith_git_fix`; mình áp đúng cách này (§25 bước 3) |
| exact sign-flip test, Holm | Kiểm định chính, đa giả thuyết | `hemerik_goeman_2018`, `holm` |
| data splitting | Chọn và xác nhận trên dữ liệu tách biệt | `rinaldo_splitting` |
| preregistration; confirmatory / exploratory | Phân biệt phân tích xác nhận và thăm dò | `nosek_2018` |
| estimand, treatment policy, sensitivity analysis | Cách xử lý biến cố xen giữa | `ich_e9_r1` |
| plasmode | Mô phỏng trên dữ liệu thật, cấy hiệu ứng đã biết | `franklin_2014_plasmode` |
| multiverse analysis | Báo cáo qua mọi lựa chọn hợp lý | `steegen_2016` |

**Không dùng** các tên tự đặt đã từng xuất hiện trong trao đổi, ví dụ "nghịch lý trần–sàn" hay "hai lớp thổi phồng". Thay bằng mô tả trực tiếp: "tỉ lệ nền đã gần trần", "phần mức tăng do bộ chấm", "phần mức tăng do chỗ lộ".

---

## 1. Tiêu đề và thông điệp chính

- **Tiêu đề:** giữ tiêu đề của paper gốc, *Scope before Reuse: Risk-Controlled Admission of Learned Coding Skills*.
- **Thông điệp một câu (dùng ở abstract và cuối phần mở đầu):**
  > A learned coding skill can be certified with an anytime-valid guarantee, yet up to about half of its in-scope gain can come from a leak in the evaluation environment that the skill learner itself discovered and wrote into the skill. A skill should therefore be (re)admitted per scope, and only under evaluation controls that detect such effects.
- **Ba con số ở abstract** (theo thứ tự câu chuyện):
  1. **+0,38** trong scope (jinja), trong đó **+0,17** do chỗ lộ; **+0,21** còn lại khi không có chỗ lộ, vẫn được Gatekeeper chứng nhận (§25 bước 2–3).
  2. Bộ chấm trong mã công khai của gskill cho **bản vá rỗng qua 206/216**; bộ chấm của SWE-smith cho 0/216 (§25 F0, ghi chú 25-2).
  3. Kết quả lặp lại trên repo thứ hai, viết bằng ngôn ngữ khác (bleve, Go): **+0,30**, Gatekeeper admit ở trial 34 (§25 bước 4c).

---

## 2. Mở đầu (Introduction)

**Ví dụ mở đầu: dùng ví dụ thật thay cho ví dụ minh họa của bản gốc.**
- Skill học bằng gskill cho jinja (`docs/skills/gskill/jinja_best_skills.txt`) nâng tỉ lệ resolved từ 15/100 lên 53/100.
- Văn bản skill có câu: *"Run `git log -n 5` to identify suspicious recent commits (e.g., 'Bug Patch') …"* (trích nguyên văn từ file).
- Khi lịch sử git bị thay bằng một commit duy nhất, như cách sửa của `debuggym_swesmith_git_fix`, mức tăng còn +0,21.

**Câu hỏi của paper gốc:** "should this skill run here?" Muốn trả lời thì phải biết con số nói skill "có ích" có đáng tin không.

**Đóng góp** (mỗi đóng góp gắn với một RQ và có số):
- **C1 (RQ1):** các con số đánh giá skill thường gặp không qua được đối chứng.
  - bộ chấm công khai của gskill nhận bản vá rỗng;
  - quy tắc quy lỗi kiểu Dong et al. cho số ca placebo bằng số ca có skill;
  - các quy tắc nhận skill đã công bố nhận nhầm dưới A/A;
  - 7/13 mức tăng công bố của XRepoSkill và MemGovern nằm trong mức nhiễu khi chạy lại.
- **C2 (RQ2):** lần đầu chứng nhận có bảo đảm (anytime-valid) cho một skill **thật**, đã công bố cách học, trên hai repo; và đo được phần mức tăng do chỗ lộ của môi trường.
- **C3 (RQ3):** chứng nhận gắn với scope.
  - Cùng skill, đổi môi trường (có lộ → không lộ) hoặc đổi repo (jinja → pygments, [CHỜ] §27b), thì tác dụng đổi.
  - Trên dữ liệu công khai của SWE-Skills-Bench, chỉ khoảng 7% phương sai tác dụng là chung giữa 4 cấu hình agent–model.
- **C4:** một bộ đối chứng cho đánh giá skill (A/A, skill giả, bản vá rỗng, bản vá gốc, skill không liên quan cùng độ dài), áp lên chính harness của mình. Harness qua được, trong khi bộ chấm của gskill không qua đối chứng bản vá rỗng.
- **C5:** artifact: mã, bản đăng ký trước, dữ liệu gốc của mọi lần chạy, sổ lỗi.

**Phải nói rõ ngay ở mở đầu (tránh nói quá):**
- Chỗ lộ git trong SWE-smith **đã có người báo** (`marin_swesmith_git_leak`, `debuggym_swesmith_git_leak`). Đóng góp của mình là cho thấy **bộ học skill tự khai thác nó** và đo phần mức tăng do nó.
- Không nói "con số trong blog gskill sai". Chỉ nói về **mã công khai** (`gepa@8c7b697`), vì chưa biết blog dùng mã nào.

---

## 3. Nền tảng và bài toán (Problem Formulation)

Giữ của paper gốc, gồm skill, scope, ℓ, STR, harmful / neutral / beneficial. Thêm:
- **Mệnh đề P** (phép trừ placebo cho việc quy lỗi): kỳ vọng của S − P bằng số ca do skill gây ra, dưới giả thiết "chỉ gây hại" (`docs/theory/proofs.md`).
- **Kiểm định hoán vị chính xác** cho S − P (§21): mức thật 0,042 khi danh nghĩa 0,05; độ nhạy 0,72 / 0,93 ở q = 0,2 / 0,3 (`results/section21.json`; `hemerik_goeman_2018`).

---

## 4. Gatekeeper (Method)

Giữ của paper gốc: e-process ghép cặp, cách chia α, thu hồi. Chỉ trình bày những gì có số:
- e-process §2: θ = 0, α = 0,025, c = 0,5 (`waudby_smith_ramdas`), K = 1 mỗi ô.
- **Thu hồi hai bước** (§15): chỉ có kết quả trên plasmode (`results/two_stage_retirement.json`). Ghi rõ là chưa có trên agent thật.

---

## 5. Thiết kế đánh giá và đối chứng (Evaluation Design)

| Đối chứng | Kiểm điều gì | Nguồn của thiết kế | Áp ở đâu |
| --- | --- | --- | --- |
| A/A (hai lần chạy không skill) | Nhiễu của agent; quy tắc quy lỗi | `kohavi_aa` | §18, §19, E1, E2 |
| Skill giả (sham) | Auditor LLM có đổ lỗi cho skill không có tác dụng không | `negative_controls_llm_2026` | §19–§21 |
| Bản vá rỗng (no-op) | Bộ chấm có nhận bản vá không sửa gì không | (đối chứng âm; `negative_controls_llm_2026`) | §25 F0, §27a của nhánh này |
| Bản vá gốc (gold) | Bộ chấm có từ chối bản vá đúng không | `swebench` (định nghĩa resolved) | §25 F0, §26 |
| Skill không liên quan cùng độ dài (C2) | Tác dụng của nội dung so với độ dài | `webdev_skills_bench_2026` | §27a ([CHỜ]) |
| Lịch sử git một commit | Phần tác dụng do chỗ lộ | `debuggym_swesmith_git_fix` | §25 bước 3, bước 4d |

- **Agent:** mini-swe-agent 2.4.6, cùng loại agent mà blog gskill dùng (`gskill`).
- **Model:** Flash-Lite. Model thứ hai: [CHỜ] Mistral Small 3.1 (§26 của nhánh `trial`). Nếu không có, chỉ được viết "trong họ Gemini".
- **Môi trường:** dùng nguyên văn môi trường và skill của gskill, kiểm bằng `cmp` và `sha256sum` (§27, theo yêu cầu "không chỉnh sửa gì" của @thuthuy).

---

## 6. RQ1: Các con số đánh giá skill có qua được đối chứng không?

| Kết quả | Số | File | Mục |
| --- | --- | --- | --- |
| Bộ chấm L nhận bản vá rỗng | 206/216 trên 5 repo (jinja 96/96, bleve 30/30, prettytable 30/30, pygments 26/30, gunicorn 24/30); S: 0/216; S với bản vá gốc ≥ 29/30 mỗi repo | `results/f0_scorer_check*.json` (nhánh `trial`) | §25 F0, ghi chú 25-2 |
| L so với S trên bản vá thật, không skill | jinja 0,37 so với 0,15; bleve 0,30 so với 0,13 | `results/f1_probe.json`, `results/s25bleve_*` | §25 F1, bước 4a |
| L so với S trên bản vá thật, có skill | jinja 79 so với 53; bleve 73 so với 43 | `results/f1_skill_probe.json`, `results/s25bleve_skill_probe.json` | §25 bước 2, 4c |
| Quy tắc quy lỗi của Dong et al. dưới placebo | R = 1,08 [0,68; 1,75] (E2) | `results/replicate_attribution.json` | §18 |
| Auditor LLM đổ lỗi cho skill giả; cận dưới đổ lỗi sai | Flash-Lite / Flash / Pro: 0,51 / 0,00 / 0,09 | `results/section21.json` (P_A) | §19–§21 |
| Quy tắc nhận skill dưới A/A (221 task, 10.000 luồng) | so một lần (plug-in), n = 200: 0,459, nhìn mỗi 10 trial: 0,802; thống kê MH của XRepoSkill (B-X2, cổng do mình dựng theo công bố): 0,025, nhìn mỗi 10 trial: 0,111; GEPA nhận 0,140 đề xuất no-op mỗi lần; Library Drift 0,003; e-SR 1,000 (đúng lý thuyết, chỉ bảo đảm ARL); Gatekeeper: admission 0,0032, thu hồi hai bước 0,0018 | `results/placebo_suite.json` | §19 |
| Mức tăng công bố so với mức nhiễu khi chạy lại | 7/13 nằm trong mức nhiễu | `results/noise_floor_audit.json` | §12 |
| MemGovern: agent có dùng bộ nhớ không | 0/20 lượt chạy gọi `exp_search`/`exp_read`; ô bị dừng theo phép kiểm đã đăng ký | nhánh `trial` (ô memgovern) | M-4 |

**Lời văn cần cẩn thận:**
- XRepoSkill không dùng thống kê của họ làm cổng (`docs/paper_argument.md`, "Sửa sau khi rà tính trung thực"), nên kết quả B-X2 **không** bác thực hành của họ.
- "Nằm trong mức nhiễu" không có nghĩa là "không có tác dụng".

---

## 7. RQ2: Chứng nhận được skill thật không, và mức tăng đến từ đâu?

| Kết quả | jinja (Python) | bleve (Go) | Mục |
| --- | --- | --- | --- |
| Nền, S | 15/100 | 13/100 | F1, 4a |
| Có skill, môi trường có lộ, S | 53/100; **+0,38** [0,26; 0,49]; p = 1,6·10⁻⁸ | 43/100; **+0,30** [0,19; 0,40]; p = 3,0·10⁻⁷ | bước 2, 4c |
| Gatekeeper (θ = 0, α = 0,025) | admit ở **trial 29** | admit ở **trial 34** | như trên |
| Có skill, môi trường không lộ, S | 35/100 so với 14/100; **+0,21** [0,13; 0,29]; admit ở **trial 50** | [CHỜ] bước 4d | bước 3, 4d |
| Phần do chỗ lộ, Δ_leak | **+0,17** [0,06; 0,28], khoảng 45% | [CHỜ] | bước 3, 4d |
| Task không có mô tả lỗi: có lộ / không lộ | 15/34 / **0/34** | 11 / [CHỜ] | bước 3, 4c |
| Skill tự ghi chỉ dẫn đọc git | "Check Git History … 'Bug Patch' … `git show`" | "look at recent git commits (`git log -p -n 3`)" | văn bản skill |
| Lệnh `git log`/`git show` trong trajectory | [CHỜ] §27c | — | §27c |
| Nội dung so với độ dài (skill thật so với C2) | [CHỜ] §27a | — | §27a |

**Phải nói rõ:**
- Phân tích "29/53 bản vá là bản hoàn tác đúng từng dòng" là **sai** (A96 của nhánh `trial`), vì bản sửa đúng thường chính là bản hoàn tác. Paper chỉ dùng số từ thí nghiệm hai môi trường.
- 1 seed mỗi nhánh. Mỗi nhánh có 100 task ghép cặp, và p rất nhỏ.

---

## 8. RQ3: Chứng nhận có chuyển sang scope khác không?

| Chiều đổi scope | Kết quả | Mục |
| --- | --- | --- |
| Môi trường (có lộ → không lộ), cùng repo | +0,38 → +0,21; trial admit 29 → 50 | §25 bước 3 |
| Repo (jinja → pygments), cùng skill nguyên văn | [CHỜ] P27b, kiểm định hai phía | §27b |
| Cấu hình agent–model, dữ liệu công khai của SWE-Skills-Bench | ρ = 0,067 [−0,10; 0,25]; trong các skill có \|Δ\| ≥ 6 điểm, cấu hình khác cho kết quả cùng chiều 25%, ngược chiều 19% | `results/sskb_transfer.json`, §27b của nhánh này (thăm dò) |
| Model (Flash-Lite → Pro), 2 skill SWE-Skills-Bench | Pro: 8/8 cặp giống hệt, vì tỉ lệ nền đã gần trần; mô tả | §23a |

---

## 9. Độ vững của chính hệ thống đo (đưa vào RQ1 hoặc mục riêng)

| Kiểm | Kết quả | Mục |
| --- | --- | --- |
| Endpoint S, F (chỉ FAIL_TO_PASS), B (bỏ test hỏng) cho E1, E2, T4 | E1, E2 không đổi kết luận; T4 +0,55 → +0,65 theo F | §26 phần 1 |
| Bản vá gốc × 3 trên runner có mạng | 33/35 ổn | §26 phần 2 |
| Bản vá rỗng trên harness của mình | **0/40** | §27a của nhánh này |
| Chấm lại 1.200 bản vá của agent với mạng | E1: 3/1.540 mặt cặp đổi; E2: 0/30; T4: +0,55 → +0,60 | §28 |
| Chấm lại 224 bản vá jinja, mỗi bản 2 lần | 0 kết quả đổi | P26 (nhánh `trial`) |
| E1, E2 (skill tự viết; XRepoSkill) | mọi CI chứa 0; E2 +2,1 điểm, CI t [−1,0; +5,3] (đã đăng ký), bootstrap theo task [−0,9; +5,5] (§28) | `results/e1_final.json`, `results/e2_final.json`, `results/s28_effects.json` |
| Đối chứng dương T4 | admit ở trial 20; +0,60 sau §28 | §14, §28 |

---

## 10. Threats to Validity (liệt kê đủ, không giấu)

1. **Một model chính** (Flash-Lite). Model đã đổi giữa E2 và các lần chạy sau (74–75/109 lời gọi đầu trùng; ô memgovern §5), nên không so trực tiếp giữa hai thời điểm.
2. **Hai repo cho bước học** (jinja, bleve). 1 seed mỗi nhánh.
3. **Môi trường SWE-smith là task tổng hợp.** Môi trường không lộ cũng xóa lịch sử thật của repo, nên khác repo thật (đã ghi ở §25 bước 3).
4. **Chưa biết blog gskill dùng mã nào.** Mọi kết luận về bộ chấm chỉ nói về `gepa@8c7b697`.
5. **Mốc dữ liệu huấn luyện của Gemini chưa xác minh được**, nên không tuyên bố "không nhiễm dữ liệu" (P19 của nhánh `trial`).
6. **Harness cục bộ không có mạng** ở E1 và T4. Đã đo và sửa (§26–§28); kết luận không đổi.
7. **Thu hồi** chỉ được kiểm trên plasmode.
8. **Phân tích thăm dò** (§10, §13, §20 S4, §22–§23, §27b của nhánh này) được tách khỏi phân tích xác nhận (`nosek_2018`).

---

## 11. Related Work (chỉ trích nguồn đã có trong `sources.json`; đọc bản gốc trước khi viết)

- **Học và quản lý skill:** `gskill`, `xreposkill`, `memgovern_repo`, `voyager`, `skilljuror_2026`, `skillsbench_2026`, `sok_agentic_skills_2026`, `skillops_2026`, `regression_tax_2026`, `evoundo_2026`, `library_drift_2026`.
- **Độ tin cậy của đánh giá coding agent:** `patchdiff_2025`, `utboost_2025`, `test_overfitting_2025`, `randomness_agentic_evals_2026`, `same_model_harness_2026`, `agent_eval_reliability_2026`, `identical_runs_2026`.
- **Chỗ lộ và reward hacking:** `swebench_git_log_leak`, `swebench_git_log_fix`, `swebench_pro_verified`, `cursor_reward_hacking`, `poolside_benchmark_hacking`, `marin_swesmith_git_leak`, `debuggym_swesmith_git_leak`, `debuggym_swesmith_git_fix`, `rllm_hide_git_history`.
- **Quy lỗi và placebo:** `skill_induced_failures_2026`, `negative_controls_llm_2026`, `whowhen_pro_2026`, `webdev_skills_bench_2026`, `skillcenter_2026`.
- **Đánh giá tuần tự, anytime-valid:** `waudby_smith_ramdas`, `celeus_2026`, `seq_eval_llm_2026`, `evaluator_2025`, `who_drifted_2026`.
- **Cần thêm vào `sources.json` trước khi trích** (đã thấy khi rà tính mới, chưa lưu): Demystifying Agent Skills (arXiv 2608.14036), SkillRevise (2606.01139), EvoClawBench (2607.09711), AgentLens (2605.12925).

---

## 12. Bảng và hình (sinh tự động)

1. **Hình 1:** tỉ lệ resolved theo nhánh (không skill, có skill, C2) × môi trường (có lộ, không lộ) × bộ chấm (S, L), cho jinja và bleve.
2. **Bảng 1:** đối chứng bộ chấm (bản vá rỗng, bản vá gốc) cho bộ chấm gskill và harness của mình.
3. **Bảng 2:** quy tắc đã công bố dưới A/A (§19).
4. **Bảng 3:** chứng nhận theo scope: trial admit, mức tăng, CI.
5. **Hình 2:** e-process theo trial cho jinja (có lộ, không lộ) và bleve.

---

## 13. Việc còn chờ trước khi viết các mục có [CHỜ]

| Việc | Ai | Ảnh hưởng tới mục |
| --- | --- | --- |
| §27a (C2), §27b (pygments), §27c (trajectory) | nhánh `trial` | 7, 8 |
| Bleve bước 4d (môi trường không lộ) | nhánh `trial` | 7 |
| Model thứ hai (Mistral) | nhánh `trial`; @thuthuy duyệt 3,5 USD | 5, 10 |
| Gộp nhánh `trial` → `main`, đánh số lại các mục | sau khi các lần chạy xong | mọi mục |
| Báo tác giả gskill | @thuthuy quyết | 2, 6, 10 |
| Thêm 4 nguồn related work còn thiếu, đọc bản gốc | phiên này | 11 |

---

## 14. Tiến độ viết (07/11/2026)

| Mục của `paper/main.tex` | Trạng thái |
| --- | --- |
| Abstract, Introduction | Đã viết; mọi số là macro sinh từ `results/` (`scripts/make_numbers.py`, kiểm khớp với bản đăng ký) |
| Problem Formulation, Admission, Sample Complexity | Giữ của bản gốc. **Mục Composition đã cắt** (08/11; @thuthuy giao quyết: "1 với 3 bạn tự quyết"): mục này không có thực nghiệm và không nằm trong câu chuyện chính; các số hạng α cho composite cũng bỏ theo. Ví dụ chạy được vẫn ở `src/gatekeeper/composition_example.py`. **Tên model** giữ một lần trong paper (macro `\agentmodel`), vì cần để tái lập; quy tắc không ghi mã model áp cho commit và tài liệu nội bộ |
| Evaluation Design | Đã viết: agent, task, bộ chấm S/L, 5 đối chứng có nguồn, phân tích. Bỏ bảng power dựng trên số dự kiến |
| RQ1 | Đã viết đủ số. Còn `\todo` cho MemGovern (chờ gộp nhánh) |
| RQ2 | Đã viết, có bảng. Còn `\todo`: 27a, 27c, bleve 4d |
| RQ3 | Đã viết phần môi trường và cấu hình. Còn `\todo`: 27b |
| Threats to Validity | Đã viết 6 mục |
| Related Work | Đã viết; chỉ dùng câu trích đã kiểm. Các bài chưa đọc chỉ trích tên, kèm `\todo` |
| `refs.bib` | Sinh tự động (`scripts/make_bib.py`). Mục `VERIFY` là mục chưa có tác giả từ nguồn đã lưu |

**Phát hiện mới khi viết (đã đưa vào paper):** chỉ dẫn đọc lịch sử git **không có** trong skill khởi đầu, cấu hình agent hay prompt của gskill. Quá trình tối ưu đã đưa nó vào (`docs/novelty_review.md`, bổ sung 07/11).

### Cập nhật 07/11/2026 (chiều)

- **Đã đưa vào paper:**
  - 27a: tác dụng của nội dung +0,29 so với placebo cùng độ dài; độ dài một mình +0,09, không có ý nghĩa thống kê;
  - 27c: 34/34 trajectory đọc commit "Bug Patch", đếm lại từ trajectory;
  - MemGovern: 0/20 lượt chạy gọi công cụ, đếm từ lệnh của agent trong bản lưu (`scripts/mg_tool_use.py`).
- **Kiểm mã gskill:** skill khởi đầu rỗng; cấu hình và prompt không nhắc lịch sử hay commit. Paper viết: chỉ dẫn đọc git do quá trình tối ưu đưa vào.
- **Mệnh đề 6:** lấy nguyên văn bản gốc, kèm chứng minh của bản gốc và câu bổ sung trong `docs/theory/corrections.md`.
- **Phạm vi:** hai đoạn lý thuyết cũ được giữ, kèm câu nói rõ là không có đánh giá thực nghiệm.
- **Model thứ hai:** tạm ngưng (@thuthuy 07/11). Paper nêu ở Threats.
- **Tên model:** ghi một lần trong macro `\agentmodel`.
- **`refs.bib`:** 36/36 mục có tiêu đề và tác giả lấy từ bản lưu nguồn. Mục ngoài arXiv đi qua `configs/bib_overrides.json`, và mỗi chuỗi trong đó được kiểm nguyên văn với văn bản nguồn (A110).
- **Còn `\todo`:** 27b (pygments) và bleve 4d, đang chạy ở nhánh `trial`.
