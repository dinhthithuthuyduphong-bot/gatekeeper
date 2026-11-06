# Catalog skill: skill là gì, đã dùng skill nào, tác dụng đo được (06/11/2026)

**Mục đích:** trả lời phản biện của thầy về định nghĩa "skill" và cho xem nguyên văn các skill đã dùng. Tài liệu này thay cho `docs/advisor_qa.md` §1 (bản 03/11).

**Quy ước số:** "mức tăng" = tỉ lệ giải khi có skill − tỉ lệ giải khi không có skill, tính bằng điểm phần trăm, ghép cặp theo task. Mức tăng dương nghĩa là skill giúp. Khoảng trong ngoặc là CI 95% của file kết quả gốc.

## 1. Trả lời ngắn

1. **Skill là gì:** một quy trình tái sử dụng được (π), đóng gói kèm điều kiện áp dụng, rồi đưa cho coding agent khi nó giải một task mới. Định nghĩa này khớp với các nguồn đã công bố, trích ở §2.
2. **Đã kiểm 4 nhóm skill,** chứ không chỉ skill tự viết:
   - (A) hướng dẫn do mình viết;
   - (B) `SKILL.md` công khai của bên thứ ba;
   - (C) skill do một hệ đã công bố **tự sinh**: XRepoSkill, và gskill (đang học);
   - (D) đối chứng có đáp án biết trước.
3. **Nội dung nguyên văn** của mọi skill được phép chép nằm trong `docs/skills/`. Skill không có license thì ghi mã và link tới commit đã ghim.
4. **Tác dụng được đo bằng cặp lần chạy trên cùng task,** chấm bằng test chính thức của benchmark. Trên issue tự nhiên, mọi skill thật đều có mức tăng không phân biệt được với 0 (bảng §4). Chỉ đối chứng dương có mức tăng lớn.
5. **Điểm yếu đã tự phát hiện và đang sửa:**
   - skill nhóm A lệch khỏi định nghĩa của paper gốc (A86);
   - quần thể task không phải P_s (A87);
   - đang kiểm nhóm C trên đúng quần thể của nó (§25).

## 2. Định nghĩa, kèm nguồn đã đối chiếu bản gốc (`sources-snapshots`)

| Nguồn | Câu gốc | Skill là |
| --- | --- | --- |
| Anthropic Agent Skills (`agent_skills`) | "Skills are folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks." … "a folder with a SKILL.md file containing YAML frontmatter and instructions" | Thư mục hướng dẫn và script (`SKILL.md`) |
| SWE-Skills-Bench (`sskb_paper`) | "the LLM-based agent selects the most relevant skill from its skill library … and injects it into the context window" | Văn bản chèn vào ngữ cảnh |
| XRepoSkill (`xreposkill`) | "discovers candidate rules from behavioral divergences between successful and failed attempts … retains only behaviors recurring across repositories as transferable rules" | Rule học từ trajectory thành công và thất bại |
| Voyager (`voyager`) | "an ever-growing skill library of executable code for storing and retrieving complex behaviors" | Chương trình thực thi được |
| Paper gốc (`docs/01-FSE-2027-13-paper.pdf`) | "A skill is S = ⟨π, D, I, P, K⟩: a procedure π (a parameterised edit program) …"; "induced from successful trajectories" | Chương trình sửa code học từ trajectory, kèm điều kiện áp dụng |

**Định nghĩa vận hành của repo** (`docs/theory/corrections.md`): skill là bộ ⟨π, D, I, P, K⟩ của paper gốc:
- π: quy trình;
- D: môi trường áp dụng được;
- I(x): điều kiện kích hoạt trên task x;
- P: hậu điều kiện;
- K: phạm vi tác động.

**Điểm khác nhau giữa các nguồn nằm ở π:**
- văn bản (Agent Skills, SWE-Skills-Bench, XRepoSkill, gskill);
- chương trình (Voyager, paper gốc).

Repo đã kiểm cả hai loại π:
- π dạng văn bản: các nhóm A–D ở §3;
- π dạng chương trình sửa code: khảo sát §24.

## 3. Các skill đã dùng

| Nhóm | Skill | π cụ thể | Ai viết, học từ đâu | Nạp vào agent thế nào | Nguyên văn |
| --- | --- | --- | --- | --- | --- |
| **A** tự viết | `null-guard`, `type-guard`, `exception-handling`, `validation-error` | Hướng dẫn 381–413 ký tự | Họ mẫu sửa được **khai thác tự động** từ gold patch SWE-Gym (≥ 3 repo, `scripts/mine_skills.py`); I(x) chọn trên train theo lift; **lời văn do mình viết** | Thẻ `<skill id="…">…</skill>` nối sau đề bài (`gatekeeper.pilot.arm_rows`) | `docs/skills/own/<id>.md` |
| A | `guidance-reproduce-first`, `repo-test-guide` | Hướng dẫn 259–317 ký tự | Mình viết (ví dụ; skill "cách chạy test" của §17) | Như trên | `docs/skills/own/` |
| **B** bên thứ ba | `viper-configuration`, `asyncio-patterns` (§22, §23a); `go-fx-di`, `pandas-dataframe-patterns`, `langsmith-fetch`, `scipy-scientific-computing`, `sympy-symbolic-math` (§23b) | `SKILL.md` dài 4,4–42,7 nghìn ký tự | Tác giả khác, nằm trong bộ 98 skill của SWE-Skills-Bench (`ControllableModel/SWE-Skills-Bench@4d3450d`) | Nội dung `SKILL.md` đặt trước yêu cầu trong prompt (`scripts/sskb_adapter.py`). Họ dùng lệnh `/skill-id` của Claude Code; đây là khác biệt có chủ đích, đã đăng ký ở §22 | `docs/skills/swe_skills_bench/` (4 skill có license MIT). 3 skill còn lại không có license rõ: chỉ có link |
| **C** hệ tự sinh | XRepoSkill (E2) | 3 rule mỗi issue, chọn từ 36 "general strategies" | **Hệ XRepoSkill tự học** từ trajectory; **bước chọn rule là của họ**, chạy nguyên mã (`26fd703…`) | Khung `SKILL_FRAME` của họ, đặt trước đề bài | **Không chép** (repo không có LICENSE). Mã rule được chọn: `results/e2_selection.json` |
| C | gskill (§25) | `best_skills.txt` do GEPA tự viết, 2.675 ký tự | **Học tự động** từ kết quả chạy agent trên task SWE-smith của jinja (mã gskill nguyên bản) | `{{ skills }}` trong system prompt của gskill | `docs/skills/gskill/jinja_best_skills.txt` |
| **D** đối chứng | `control-oracle-tests`, `control-oracle-patch`, `control-oracle-files` (dương); `harm-swallow-exceptions`, `harm-minimal-edit`, `harm-skip-verification` (âm, dựng có chủ đích) | Hướng dẫn hoặc mẫu chèn đáp án | Mình dựng; đáp án biết trước theo cách dựng | Như nhóm A | `docs/skills/own/` |

**Thống kê bước chọn của XRepoSkill ở E2:**
- 178/179 issue được chọn đúng 3 rule; 1 issue không được chọn rule nào.
- 34/36 chiến lược được dùng ít nhất một lần.
- Các chiến lược dùng nhiều nhất: số 19 (71 issue), 1 (66), 24 (62), 26 (53).

**Ví dụ một prompt thật (nhóm A):** đề bài của task, rồi:
```text
<skill id="null-guard">
The issue may involve a value that can be None (or missing). Before changing logic: …
</skill>
```

## 4. Tác dụng đo được

| Skill | Thí nghiệm | n | Mức tăng (điểm) | Kiểm định | File |
| --- | --- | --- | --- | --- | --- |
| null-guard | E1, đăng ký trước | 53 task × 3 seed | +1,9 [−3,6; +7,4] | p = 0,33 | `results/e1_final.json` |
| type-guard | E1 | 53 × 3 | 0,0 [−5,4; +5,4] | p = 0,59 | như trên |
| exception-handling | E1 | 53 × 3 | −1,3 [−6,3; +3,8] | p = 0,77 | như trên |
| validation-error | G1, xác nhận | 32 × 3 | −3,1 [−12,0; +5,7] | p = 0,83 | `results/g1_final.json` |
| **XRepoSkill** | E2, đăng ký trước | 109 × 3 | +2,1 [−1,0; +5,3] | p = 0,13. Bác bỏ 4/6 mức tăng họ công bố (+6,2 tới +12,4) | `results/e2_final.json`, `results/xreposkill_replication.json` |
| `viper-configuration` | §22, Flash-Lite | 10 batch | +1,5 (họ công bố +17,7) | p = 0,94 | `results/sskb_probe.json` |
| `asyncio-patterns` | §22 | 10 batch | −11,3 (họ công bố −17,0) | p = 0,44 | như trên |
| viper, asyncio | §23a, Pro | 4 batch | 0,0 và 0,0 (nhánh không skill gần trần) | — | `results/sskb_s23a-pro.json` |
| harm-swallow-exceptions | RQ1 thu nhỏ / §21 | 40 task | −2,5 | Hoán vị p = 0,045; không qua Holm (0,05/7) | `results/rq1_mini.json`, `results/section21.json` |
| harm-minimal-edit, harm-skip-verification | như trên | 40 | −2,5 và −2,5 | p = 0,17 và 0,19 | như trên |
| **control-oracle-tests** (dương) | G1 B3, so với lần chạy lặp không skill | 38 task | +12,5, CI **90%** [+3,1; +22,2] | CI không chứa 0 (quy tắc v2) | `results/g1_decision_b3.json` |
| **control-oracle-patch** (dương) | T4 | 20 task | **+55** [+35; +75] | Gatekeeper admit ở trial 20 | `results/t4_decision.json` |
| repo-test-guide | §17 | 4 task (dừng, D-M7) | 0 (4 cặp hòa) | Không kết luận | `docs/preregistration_main.md` §17 |
| **gskill (jinja)**, skill do máy học | §25, trên task SWE-smith của jinja (đúng scope) | 100 task | **+38** [+26; +50] (resolved 15 → 53); theo bộ chấm của gskill +42 | p = 1,6·10⁻⁸; Holm bác bỏ; **Gatekeeper admit ở trial 29**. **Ngoài scope** (bỏ commit "Bug Patch" bị lộ khỏi lịch sử git; §25 bước 3): **+21** [+13; +29] (14 → 35), p = 4,8·10⁻⁷, Gatekeeper admit ở trial 50. Phần do chỗ lộ là +17 [+6; +28], tập trung ở 34 task không có mô tả lỗi (15 → 0) | `results/f1_skill_probe.json`, `docs/skills/gskill/jinja_best_skills.txt` |

**Đọc bảng:**
- Phương pháp đo **có thể thấy** tác dụng khi nó có thật: đối chứng dương cho +12,5 và +55 điểm.
- Mọi skill thật trên issue tự nhiên đều có CI chứa 0. CI của E1 và E2 hẹp, khoảng ±5 điểm. Vì vậy câu đúng là "**không có tác dụng lớn hơn khoảng 5 điểm**", không phải "không có dữ liệu".

## 5. Điểm yếu mà phản biện có thể nêu, và tình trạng

| Phản biện | Tình trạng |
| --- | --- |
| "Skill nhóm A do anh chị tự viết, nên dễ là người rơm" | Đúng một phần: họ mẫu được khai thác tự động nhưng lời văn do mình viết. Vì thế repo đã thêm nhóm B (skill công khai), nhóm C (hệ tự sinh đã công bố) và nhóm D (đối chứng). Kết luận chính dựa trên B và C |
| "Skill của paper gốc là chương trình sửa code, không phải văn bản" | Đúng (A86). §24 đã khảo sát π dạng chương trình sửa code: chỉ 3,6% task SWE-bench có bản sửa cùng hình dạng với bản sửa của train; ô lớn nhất có 5 task, cần 23. Hướng này không khả thi trên SWE-bench |
| "Skill được thử trên task mà nó không liên quan" | Đúng (A87, `docs/root_cause.md`). Sửa: §25 kiểm skill gskill trên đúng quần thể mà nó được học (task SWE-smith của jinja) |
| "Mức tăng đã công bố lớn, sao của anh chị nhỏ?" | §25 cho thấy bộ chấm công khai của gskill nhận bản vá **không sửa gì** ở 96/96 task (F0). Trên patch thật của agent, nó cho 37% so với 15% resolved theo chuẩn SWE-smith (F1). Ngưỡng nhiễu do chạy lại (§12) bao trùm 7/13 mức tăng đã công bố |

## 6. Bản quyền
- **Chép nguyên văn:** skill của chính mình; `SKILL.md` có license MIT (kèm `docs/skills/swe_skills_bench/LICENSE` của repo SSKB, và license ghi trong frontmatter của từng skill).
- **Chỉ ghi mã và link:** XRepoSkill, MemGovern (không có LICENSE), và các `SKILL.md` không có license rõ ràng.
