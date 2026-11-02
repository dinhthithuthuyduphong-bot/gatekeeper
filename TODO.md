# Gatekeeper (FSE-2027-13) – Review & Todo list

> **Đây là kim chỉ nam của dự án.** Mỗi lần xong một việc: tick `[x]`, ghi ngày + link commit/log vào cột "Bằng chứng" của mục [Nhật ký tiến độ](#nhật-ký-tiến-độ), cập nhật `report/index.html`. Việc nào chưa có bằng chứng (file, log CI, số đo) thì chưa được tick.

Ký hiệu người làm: 🤖 = làm được ngay trong repo + GitHub Actions · 👤 = bạn phải tự làm (đọc, họp, quyết định) · 💰 = tốn tiền (API, GPU, máy CPU).

---

## 0. Kết quả review bản 1 (đọc trước)

Bản 1 nhìn chung **đúng và kỹ**: mình tính lại mọi số trong bảng kiểm tra, các lỗi toán, mô phỏng và link GitHub. Phần lớn đúng. Nhưng có **1 vấn đề chặn**, các chỗ sai/thiếu R1–R14 cần sửa, và todo list thiếu phần hạ tầng code.

### 0.1 Venue: **ASE 2027** (@thuthuy chốt ngày 01/11/2026)

- Hạn FSE 2027 (02/10/2026) đã qua → đổi sang **IEEE/ACM ASE 2027**. Giữ mã "FSE-2027-13" làm ID dự án.
- **Hạn nộp ASE 2027 chưa công bố / chưa tra được.** Các năm trước ASE Research Track có hạn vào **cuối tháng 5**. Lịch dưới đây giả định **~29/05/2027**; phải xác nhận trên trang chính thức ngay khi có (👤).
- Còn khoảng **7 tháng**, ngắn hơn ước lượng 9–12 tháng cho người mới, nên mọi phase bị nén và có **3 cổng dừng** (G1–G3). Lỡ một cổng thì chuyển mục tiêu sang **ICSE 2028 / FSE 2028**, không cố nộp bản thiếu.
- Template ASE: IEEE/ACM conference format (kiểm tra số trang và yêu cầu double-blind trong CfP ASE 2027).

**Lịch ngược từ hạn nộp (giả định 29/05/2027):**

| Mốc | Hạn | Nội dung | Cổng |
| --- | --- | --- | --- |
| M0 | 15/11/2026 | Vertex AI thiết lập xong (`docs/vertex_setup.md`); Pilot dry run xanh; đọc 5 paper đầu | |
| M1 | 15/12/2026 | **R15 mini-pilot**: 3–5 skill × 30 cặp trên Verified với Gemini Flash; đo hiệu ứng thật và chi phí/cặp | **G1**: có skill với \|STR\| ≥ 0,1? Không → thu hẹp / đổi hướng |
| M2 | 15/01/2027 | Pilot Phase 3 đầy đủ, power analysis, chốt θ / α / FWER, pre-register | **G2**: go/no-go theo R4 |
| M3 | 28/02/2027 | Benchmark v1 đóng băng (Phase 4), Gatekeeper đầy đủ (5b), baseline XRepoSkill chạy được | |
| M4 | 15/04/2027 | Phase 6 xong: RQ1–RQ4, 3 lần × 2 backend (Gemini Pro + Flash) | **G3**: endpoint chính đạt? Không → báo cáo trung thực hoặc lùi venue |
| M5 | 15/05/2027 | Bản nháp đầy đủ, 2 người đọc, artifact | |
| M6 | ~29/05/2027 | Nộp ASE 2027 | |

### 0.2 Những gì bản 1 đúng (đã kiểm chứng lại)

| Nội dung | Cách kiểm | Kết quả |
| --- | --- | --- |
| 13 dòng kiểm tra số học (Table 1–3, abstract) | Tính lại tay | Đúng hết |
| B2 "harmful acceptance 22,7%" mâu thuẫn định nghĩa | B2 admit mọi thứ, mà Table 2 ghi clean reuse của B2 = 100% | Đúng: mâu thuẫn thật |
| CI [3,1; 9,8] không "vượt 5 điểm" | Cận dưới < 5 | Đúng |
| d̄ = 0,34 vs ≈ 10,6 | Table 1: 94 skill, L = 17 scope. 11,4% × 93 skill còn lại ≈ 10,6 | Đúng (93 = 94 − chính nó) |
| Số ô 94 × 17 = 1.598, α = 0,05/1.600 = 3,1e-5 | Tính lại | Đúng |
| Theorem 7 sai khi ε < θ | STR(S1) ≤ −θ buộc E ℓ(x,∅) ≥ θ | Đúng |
| Theorem 4 thiếu hệ số 2 | Z ∈ [−1,1] độ rộng 2 → \|E_Q Z − E_P Z\| ≤ 2ξ_s | Đúng |
| Prop. 9: tỉ lệ 1 + 2σ_T²/σ_S², bỏ "net 1,55×" | Tính lại phương sai | Đúng. Với σ_T²/σ_S² = 2,1 của paper thì tỉ lệ đúng là **5,2×**, không phải 3,1× |
| E-process ∏(1 + λ(−θ − Z)), λ ≤ 1/(1+θ) | Kiểm tra supermartingale + không âm | Đúng |
| Link GitHub còn sống | `git ls-remote` ngày 01/11/2026 | MemGovern, XRepoSkill, gepa, agent-skill-induction, SWE-smith, mini-swe-agent, CooperBench, confseq, ltt: **còn**. `GeniusHTX/SWE-Skills-Bench` không truy cập được (đúng như bản 1 ghi), **nhưng code + dữ liệu đã có ở `ControllableModel/SWE-Skills-Bench`** (phát hiện qua abstract arXiv v2, mục 0.4) |
| Mô phỏng khả thi | Chạy lại với bộ betting khác (bảng 4) | Cùng bậc độ lớn; bộ của mình cần nhiều trial hơn 30–50% và kém power hơn ở hiệu ứng nhỏ |

### 0.3 Những chỗ sai hoặc thiếu trong bản 1 (đã sửa trong bản này)

| # | Chỗ | Vấn đề | Đã sửa thành |
| --- | --- | --- | --- |
| R1 | "Có sẵn trong `confseq`, không cần tự code" | `pip install confseq` **build lỗi** trên Python 3.11 và 3.13 vì cần thư viện C++ Boost (`Boost_INCLUDE_DIR-NOTFOUND`). | Tự viết e-process (~30 dòng) làm bản chính; `confseq` chỉ để đối chiếu, cài kèm `libboost-dev` trong một job CI riêng. Nhớ đổi biến: confseq làm việc trên [0,1], nên dùng Y = (Z+1)/2 và ngưỡng (1−θ)/2. |
| R2 | Giả định "rút task mới i.i.d. từ P_s" | Mỗi ô cần 150–1.400 cặp trial, nhưng một scope chỉ có vài chục task. Chạy lại cùng task nhiều lần **không phải** mẫu mới từ P_s; nếu rút có hoàn lại thì bound chỉ đúng cho **phân phối của pool task**, không phải P_s. | Thêm yêu cầu: số task khác nhau ≥ số trial cần, **hoặc** định nghĩa P_s = phân phối đều trên pool và đưa phần chênh lệch pool–P_s vào ξ_s. Phải chọn trước khi pre-register. |
| R3 | Nhãn harmful/beneficial chưa nối với đại lượng STR | Không nói một cặp (skill, context) "harmful" nghĩa là gì về mặt số. Và nếu task dùng để admit trùng với task dùng để chấm thì kết quả bị rò rỉ. | 3 lớp nhãn đo trên scoring suite: **harmful** (STR > 0), **neutral** (−θ < STR ≤ 0), **beneficial** (STR ≤ −θ). Clean reuse chỉ tính trên beneficial; neutral báo cáo riêng. Pool task admission và pool task chấm **tách rời**. |
| R4 | Go/no-go dựa trên margin của pilot 20–30 cặp | Pilot chỉ có khoảng 10 cặp harmful, mỗi cặp = 10 điểm phần trăm. Margin "≥ 5 điểm" trên pilot là nhiễu, không quyết định được gì. | Go/no-go dựa trên **tính khả thi đo được** (σ_S², hiệu ứng thật, số task đủ không, chi phí) + **power analysis** cho benchmark đầy đủ. Margin của pilot chỉ để tham khảo, có ghi CI. |
| R5 | "XRepoSkill trên 20–50 task lệch < 3 điểm so với paper" | Với 50 task, sai số chuẩn của pass rate khoảng 7 điểm. Tiêu chí 3 điểm không kiểm được. | So trên **đúng tập task** paper đã dùng (từng task một), hoặc tiêu chí "số của paper nằm trong CI 95% của mình". Tương tự cho MemGovern. |
| R6 | Harness | Paper ghi OpenHands, còn XRepoSkill chạy trên mini-swe-agent. So sánh mà mỗi hệ thống một harness thì không công bằng. | Chốt **một harness cho mọi hệ thống**. Đề xuất mini-swe-agent (XRepoSkill đã dùng sẵn, gọn hơn), rồi sửa paper và summary. |
| R7 | α cho composition và re-admission | Bản 1 nói "phân bổ trước", nhưng không biết trước sẽ có bao nhiêu cặp composite hay bao nhiêu lần re-admit. | Giữ riêng một phần α_comp (vd 20% α), cặp composite thứ k nhận α_comp · 6/(π²k²); tổng luôn ≤ α_comp. Re-admission làm tương tự với α_re. |
| R8 | Đổi sang FDR (e-BH) để giảm số trial | Đổi FWER → FDR là **đổi định lý**, không chỉ là mẹo kỹ thuật. | Quyết định ở Phase 1, trước pre-register; nếu đổi thì viết lại Theorem 4 và mục tiêu bài toán. |
| R9 | Thiếu phần hạ tầng | Không có việc nào về repo, CI, report HTML, theo dõi tiến độ. Gatekeeper ("≈10,9k dòng Python") **chưa tồn tại**; PLAN.md, REVIEWS.md và 3 smoke test paper nhắc tới **không có trong tài liệu gửi kèm**. | Thêm **Phase H** (hạ tầng). Phần lõi Gatekeeper (e-process, sổ α, scope screen) chuyển lên sớm vì viết và test được bằng CI không tốn tiền. Thêm việc xin PLAN.md / REVIEWS.md từ người hướng dẫn. |
| R10 | Số hệ thống trong protocol | Paper ghi "10 systems". Sau khi đổi baseline còn 8–9 (B1, B2, B8, B9, MemGovern, XRepoSkill, gskill, [ASI], Gatekeeper). | Sửa protocol + tính lại chi phí. |
| R11 | Theorem 7, chi tiết nhỏ | Cận chặt là STR(S1∘S2) = 1−θ (với ℓ(∅) = θ). Kết luận "không có hàm g" cần **hai** cấu trúc có cùng STR riêng lẻ mà STR ghép khác nhau. Phép ghép S1∘S2 cũng chưa định nghĩa thứ tự. | Thêm: định nghĩa thứ tự áp dụng; cặp thứ hai có ℓ(π1∘π2) = 0 (composite = −θ) để chứng minh không có g. |
| R12 | Bảng công thức, dòng #4 | Dấu `\|` trong công thức làm vỡ bảng markdown. | Đã sửa định dạng. |
| R13 | Benchmark tự dựng (yêu cầu của @thuthuy) | Bản 1 dựng SkillShift-SE gần như từ đầu: tự chọn 25 repo, tự sinh task, tự thêm test. Reviewer sẽ nghi ngờ benchmark "vừa khít" với phương pháp. | **Task và test lấy từ benchmark có thật, được công nhận rộng** (bảng 6.1), giữ nguyên test chính thức. SkillShift-SE chỉ còn là **giao thức đánh giá** đặt lên trên (split, skill, scope, nhãn), không phải dataset mới. Endpoint chính chấm bằng test chính thức; test fault-injection tự thêm chỉ dùng cho phân tích phụ, báo cáo riêng. |
| R14 | Endpoint chính "cận dưới CI của margin > 5 điểm" (phát hiện 01/11 bằng mô phỏng power) | Với chính số dự kiến của paper (11,5% → 5,1%, margin thật 6,4) và 63 cặp harmful, power chỉ **~3–5%**; kể cả giả định thuận lợi nhất (nested) cũng cần > 2.000 cặp harmful mới đạt 74%. Endpoint như đang viết gần như **không thể đạt**, kể cả khi Gatekeeper đúng là tốt hơn 6,4 điểm. | Đổi giả thuyết chính thành **ưu thế** (cận dưới CI > 0) và báo cáo ước lượng điểm so với ngưỡng 5 điểm có ý nghĩa thực tế; tăng số cặp harmful lên **200–500**: power ưu thế 56–100% ở 200 cặp và 97–100% ở 500 cặp, tuỳ tương quan giữa hai hệ thống (đo ở pilot); với 63 cặp chỉ 26–56%. Công cụ: `analysis.endpoint_power(coupling=...)`. |
| R15 | Hiệu ứng thật của skill (phát hiện 01/11, dữ liệu SWE-Skills-Bench) | SD thật của STR khoảng 0,03; skill dạng tài liệu gần như không đổi kết quả | Cổng G1: đo hiệu ứng skill của mình trước mọi việc khác (mục 0.1, 0.4) |
| R16 | Predicate kích hoạt I(x) từ nội dung issue (phát hiện 01/11, `data/activation.json`) | Trên 3.991 task test: lift chỉ 1,25–1,71, precision 14–33%; `null-guard` trên train có lift 0,99 (không có tín hiệu). P_s sẽ chứa nhiều task không liên quan → hiệu ứng bị pha loãng | Đã thử chọn biến thể regex trên train, đánh giá trên test: lift test 1,46–1,85 (khớp train, không overfit) nhưng recall chỉ 5–15%, precision ≤ 34%. Regex đã chạm trần. Tiếp theo: I(x) dựa trên repo/traceback hoặc phân loại bằng Gemini Flash (tính vào chi phí); báo cáo precision/recall của I(x) trong paper |

### 0.4 Phát hiện từ dữ liệu thật (01/11/2026)

Lấy bằng workflow `Data snapshots` (HuggingFace, arXiv), không tốn tiền.

**Số task trong benchmark chuẩn** (`data/benchmarks/summary.json`):

| Benchmark | Task | Repo | (repo, version) |
| --- | --- | --- | --- |
| SWE-bench | 2.294 | 12 | 126 |
| SWE-bench Verified | 500 | 12 | 80 |
| SWE-Gym | 2.438 | 11 | 200 |
| SWE-bench-Live (full) | 1.888 | 223 | không có trường version |
| SWE-smith | 59.136 | 222 | — |

- SWE-Gym và SWE-bench **không trùng repo nào** → train (SWE-Gym) / test (SWE-bench) tách theo repo được. SWE-Gym và SWE-bench-Live trùng 4 repo (conan, hydra, dvc, mypy), đã bỏ khỏi test.
- **R2 được xác nhận bằng số thật:** sau khi gộp SWE-bench ∪ Verified ∪ Live, chỉ 7 scope (repo, version) có ≥ 100 task, **0 scope** có ≥ 219 task. 219 là trung vị số trial để admit ngay cả skill rất mạnh (STR = −0,25) với α Bonferroni. Scope lớn nhất là django@3.2 với 157 task. Tính theo repo thì chỉ 5 repo có ≥ 219 task.
- **Hệ quả:** phương án (a) "mỗi trial một task mới" không khả thi. Phải dùng (b) rút có hoàn lại từ pool (bound theo pool, đưa chênh lệch vào ξ_s), và/hoặc scope thô hơn (theo repo hoặc framework), và/hoặc α lớn hơn mỗi ô (ít ô hơn, FDR). Cần chốt trước pre-register.

**Trích dẫn** (`data/citations.json`): cả 16 mã arXiv đều tồn tại, nhưng nhiều tiêu đề trong paper **không khớp** bài thật:

| Ref | Paper ghi | Bài thật trên arXiv |
| --- | --- | --- |
| [9] 2608.06153 | GSE: Globally reusable skill evolution for coding agents (tác giả "GSE Authors") | *Learning Globally Reusable Skills for Coding Agents*, Chen Yang, Jiashuo Tian, Ziqi Wang… |
| [13] 2601.06789 | MemGovern: Governed development histories as reusable experience cards | *MemGovern: Enhancing Code Agents through Learning from Governed Human Experiences*, Qihao Wang… |
| [12] 2603.13258 | MemCoder: Structured intent-to-code experience memory | *Your Code Agent Can Grow Alongside You with Structured Memory*, Yi-Xuan Deng… |
| [7] 2605.23951 | Formal verification of learned agent skills and capability containment | *Methods for Formal Verification of Agent Skills: Three Layers…*, Alfredo Metere (1 tác giả) |
| [8] 2605.26252 | GEM/MemState: Dependency-aware correctness for agent memory | *Is Agent Memory a Database? Rethinking Data Foundations…*, Orogat & Mansour (**có thể sai mã arXiv**) |
| [6] 2601.13295 | CooperBench: Measuring collaborative conflicts between coding agents | *CooperBench: Why Coding Agents Cannot be Your Teammates Yet*, Khatua, Zhu, Tran… |
| [22] 2505.23419 | SWE-bench-Live: A continuously updated benchmark… | *SWE-bench Goes Live!* |

[15] ReasoningBank và [16] TMA-NM không có mã arXiv trong paper → phải tìm và kiểm tra tay.

**Bảng thiết kế** (`results/design_table.json`, `scripts/design_table.py`): số cặp trial mỗi ô để admit với power 80%.

| θ | Số ô | STR −0,25 | STR −0,15 | STR −0,10 |
| --- | --- | --- | --- | --- |
| 0,05 | 10 | 193 | 696 | 2.521 |
| 0,05 | 1.600 | 327 | 1.138 | > 3.000 |
| 0,02 | 10 | 141 | 390 | 960 |
| 0,02 | 1.600 | 241 | 662 | 1.581 |

- Số ô (tức mức gộp scope) chỉ ảnh hưởng theo log(1/α): từ 1.600 ô xuống 10 ô chỉ giảm khoảng 1,5 lần.
- **Đòn bẩy lớn nhất là θ** (khoảng cách |STR| − θ): hạ θ từ 0,05 xuống 0,02 giảm khoảng 2 lần với hiệu ứng nhỏ. Nhưng θ nhỏ nghĩa là chấp nhận skill chỉ giúp 2 điểm, nên phải bàn với người hướng dẫn và pre-register.
- Mỗi cặp trial = 2 lần chạy agent + test. Skill có hiệu ứng −0,10 cần khoảng 2.000–5.000 lần chạy cho mỗi ô; đây là con số để ước chi phí pilot.

**Pilot ngoài trên dữ liệu paired thật** (SWE-Skills-Bench, MIT, 3.920 cặp; `scripts/analyze_sskb.py` → `results/sskb_analysis.json`). Chỉ dùng để ước lượng tham số, không phải benchmark:

| Đại lượng | Giá trị | Hệ quả |
| --- | --- | --- |
| σ_T² / σ_S² | 0,067 / 0,040 | **Pairing tiết kiệm 4,3×** (Prop. 9 đã sửa). Thiết kế paired được ủng hộ bằng dữ liệu thật |
| Cặp có Z = 0 | 69% | Phần lớn skill không đổi kết quả |
| SD thật của STR giữa các ô (đã trừ nhiễu) | 0,032 | Chỉ 20% phương sai quan sát là thật; khoảng 6% skill có STR thật ≤ −0,05 |
| Trial tối thiểu để admit skill **hoàn hảo** | 9–23 (θ, α) | 10 requirement mỗi skill như SWE-Skills-Bench là không đủ; e-process admit 0/392 ô với 5 trial |
| Plug-in "trung bình 5 trial ≤ −θ", chấm trên 5 trial còn lại | harmful acc. 18,5–29,8% | Admission không có thống kê hợp lệ admit nhầm nhiều skill có hại |
| Tương quan hiệu ứng giữa cấu hình / độ tin cậy trong cấu hình | 0,07 / 0,16 | Quá nhiễu để kết luận về phụ thuộc ngữ cảnh |

**R15 (rủi ro go/no-go lớn nhất).** Với skill dạng tài liệu, hiệu ứng thật quá nhỏ để admission hợp lệ có ý nghĩa thực tế. Đề tài chỉ khả thi nếu skill dạng *edit program* của Gatekeeper có hiệu ứng lớn hơn rõ rệt (|STR| ≳ 0,15). **Đây là điều pilot phải đo đầu tiên**, trước mọi việc khác ở Phase 3.

**Ước tính chi phí với Gemini** (`results/cost_estimate.json`; giá chưa xác minh, token mỗi lần chạy là **giả định** 150k–1,5M input):

| Khối lượng | Lần chạy agent | Gemini Flash | Gemini Pro |
| --- | --- | --- | --- |
| G1 mini-pilot (4 skill × 30 cặp) | 150 | 43–394 USD | 59–540 USD |
| Pilot Phase 3 (pre-registration §8) | 3.900 | 1,1k–10k USD | 1,5k–14k USD |
| Thí nghiệm Phase 6 (ước lượng thô) | 8.640 | 2,5k–23k USD | 3,4k–31k USD |

Dải rộng tới 10 lần → **việc đầu tiên khi có credential: chạy `Pilot (paid)` với n = 2, budget 3 USD để đo token thật**, rồi tính lại bảng này.

---

## 1. Đề tài nói gì (cho người mới)

Câu hỏi: một "skill" (quy trình sửa code mà agent học được) có nên **chạy ở repo này** không? Skill có thể hợp lệ về quyền, pass replay test ở repo gốc, mà vẫn sai ở repo mới (ví dụ retry wrapper gây ghi trùng khi client là exactly-once).

Gatekeeper trả lời bằng 4 bước:

1. **Scope screen:** kiểm tra fingerprint môi trường (D) và các điều kiện đầu vào (I). Trượt thì không chạy; qua cũng chưa chắc an toàn.
2. **Quarantine bằng paired trial:** chạy cùng một task 2 lần, có skill và không có skill, lấy hiệu số loss Z = ℓ(có skill) − ℓ(không skill).
3. **E-process (kiểm định tuần tự):** cộng dồn bằng chứng; khi E ≥ 1/α thì **admit** (skill thực sự giúp ít nhất θ). Hết budget mà chưa đạt thì giữ quarantine.
4. **Composition check:** hai skill cùng chạm một vùng code (footprint K giao nhau) thì phải test riêng cặp đó.

Đại lượng chính là **selective transfer risk**:

```latex
\mathrm{STR}(S,s) = \mathbb{E}_{x\sim P_s}\big[\ell(x,\pi) - \ell(x,\varnothing)\big], \quad \text{admit nếu } \mathrm{STR}\le -\theta
```

Kiến thức cần học trước: SWE-bench (chấm bằng test), e-value / betting confidence sequence (Waudby-Smith & Ramdas 2024), union bound, total variation distance, cluster bootstrap.

---

## 2. Kiểm tra số liệu trong paper

Tất cả số trong paper là **dự kiến** (paper tự ghi "projected"). Phần lớn cộng trừ khớp; 4 chỗ cần sửa nằm ở cuối bảng.

| Kiểm tra | Paper ghi | Tính lại | Kết quả |
| --- | --- | --- | --- |
| Tổng số cặp 68+74+38 | 180 | 180 | Đúng |
| Số cặp harmful 14+27+22 | 63 | 63 | Đúng |
| Tỉ lệ harm A/B/C | 20,6 / 36,5 / 57,9% | 20,6 / 36,5 / 57,9% | Đúng |
| Chênh lệch regime 57,9/20,6 | 2,8× | 2,81× | Đúng |
| Margin vs B6: 11,5−5,1 | 6,4 | 6,4 | Đúng |
| Margin vs B2: 22,7−5,1 | 17,6 | 17,6 | Đúng |
| (22,7−11,5)/17,6 | ~64% | 63,6% | Đúng |
| Cost 3,87/2,02 | 1,9× | 1,92× | Đúng |
| Composition 41/46 | 89,1% | 89,1% | Đúng |
| Ablation +8,8 / +7,5 / ×1,45 / ×1,34 / +7,8 / +0,8 | như bên | khớp hết | Đúng |
| Repair 52,3−49,8 và 52,3−44,1 | 2,5 / 8,2 | 2,5 / 8,2 | Đúng |
| Phân loại lỗi 58+27+15 | 100% | 100% | Đúng |
| **B2: harmful acceptance** | 22,7% | B2 admit mọi thứ → tỉ lệ cặp harmful được admit = **100%**; nếu tính trên tất cả cặp thì 63/180 = **35,0%** | **Mâu thuẫn**, phải định nghĩa lại metric |
| **CI margin [3,1; 9,8] "vượt margin 5 điểm"** | vượt | Cận dưới 3,1 < 5 | **Sai cách diễn đạt** |
| **"At matched clean reuse"** | 84,3 vs 86,0% | Không bằng nhau | **Cần sửa**: so trên đường cong harm–coverage |
| **d̄ = 0,34 partner** | 0,34 | 11,4% × 93 ≈ 10,6 (toàn library) | **Cần giải thích**: chỉ đúng nếu tính trong từng scope L_s |
| **Prop. 9 "tiết kiệm 3,1×"** | 3,1× | Với σ_T²/σ_S² = 2,1: 1 + 2·2,1 = **5,2×** | **Sai công thức** (xem mục 3) |

---

## 3. Công thức & chứng minh

**Cao** = sai về toán, reviewer sẽ bắt; **Trung bình** = thiếu chặt chẽ; **Thấp** = nên thêm.

| # | Chỗ | Vấn đề | Cách sửa | Mức độ |
| --- | --- | --- | --- | --- |
| 1 | Theorem 7 (phát biểu) | "STR(S1∘S2) ≥ 1−ε với mọi ε" sai: STR(S1) ≤ −θ buộc loss khi không skill ≥ θ, nên STR của cặp tối đa là 1−θ. | Phát biểu: STR(S1∘S2) có thể đạt 1−θ (cận chặt). Chứng minh "không có g" bằng 2 cấu trúc cùng STR riêng lẻ (−θ, −θ) nhưng STR ghép là 1−θ và −θ. Định nghĩa thứ tự ghép. | Cao |
| 2 | Theorem 7 (cơ chế) | "Handler không bắt X′ nhưng vẫn nuốt lỗi": tự mâu thuẫn. | Cơ chế có thật: S2 đổi hàm sang `async`, retry wrapper đồng bộ của S1 gọi mà **không await** → trả về coroutine, không raise, lệnh ghi không bao giờ chạy. Viết thành test Python. | Cao |
| 3 | Theorem 4 (union bound) | Σ_s α_s ≤ α theo scope, nhưng mỗi scope có nhiều skill và cặp composite. | Σ α_(S,s) + Σ α_(S∘S′,s) + α_re ≤ α; phần composite và re-admission dùng dãy α·6/(π²k²) (R7). | Cao |
| 4 | Theorem 4 (đổi phân phối) | Z ∈ [−1, 1] có độ rộng 2, nên chênh lệch kỳ vọng giữa Q_s và P_s ≤ 2ξ_s, không phải ξ_s. | Đổi ξ_s → 2ξ_s trong phát biểu và chứng minh. | Cao |
| 5 | Định nghĩa loss | ℓ ∈ [0,1] nhưng §7 cộng 0,5 cho mỗi regression, có thể vượt 1. | ℓ = min(1, …) hoặc chia cho giá trị max. | Trung bình |
| 6 | Mục tiêu vs định lý | Mục tiêu Pr[∃ admit STR > 0] ≤ α; định lý chỉ cho STR ≤ −θ + 2ξ_s. | Ghi rõ điều kiện 2ξ_s ≤ θ. | Trung bình |
| 7 | Prop. 9 | Unpaired cũng tốn 2 lần chạy/mẫu; "net 1,55×" sai. Tỉ lệ đúng là 1 + 2σ_T²/σ_S². | Viết mô hình phương sai (dưới), đo lại từ dữ liệu. | Trung bình |
| 8 | P_s | Skill chỉ liên quan 10% task thì hiệu ứng bị pha loãng 10 lần. | P_s = phân phối task mà I(x) đúng. | Trung bình |
| 9 | i.i.d. và pool task (mới, R2) | Không đủ task khác nhau để rút "mới" mỗi trial. | Số task ≥ số trial, hoặc P_s = pool + đưa chênh lệch vào ξ_s. | Trung bình |
| 10 | Figure 1 tự phản bác | "No test in R_b injects [partial failure]" → paired trial bằng test của R_b cũng không thấy lỗi. | Scoring suite phải có test fault-injection; ghi rõ Gatekeeper chỉ mạnh bằng test suite của target. | Trung bình |
| 11 | Prop. 6 | Đúng. | Thêm 1 câu cho thủ tục ngẫu nhiên. | Thấp |

**E-process viết tường minh.** H0: E[Z] ≥ −θ; λ_i chọn trước khi thấy Z_i:

```latex
E_n = \prod_{i=1}^{n}\big(1 + \lambda_i(-\theta - Z_i)\big),\qquad 0 \le \lambda_i \le \frac{1}{1+\theta},\qquad \text{admit khi } E_n \ge 1/\alpha_{S,s}
```

Dưới H0, E_n là supermartingale không âm, E_0 = 1; bất đẳng thức Ville cho Pr[∃n: E_n ≥ 1/α] ≤ α. Tự cài (R1); `confseq` chỉ để đối chiếu.

**Theorem 4 sau khi sửa:**

```latex
\Pr\Big[\exists \text{ admitted } (S,s):\ \mathrm{STR}_{Q_s}(S,s) > -\theta + 2\xi_s\Big] \le \sum_{(S,s)} \alpha_{S,s} + \sum_{(S\circ S',s)} \alpha_{S\circ S',s} + \alpha_{\text{re}} \le \alpha
```

**Prop. 9 sau khi sửa** (ℓ(x,π) = μ_π + T(x) + e_π, ℓ(x,∅) = μ_∅ + T(x) + e_∅, Var T = σ_T², Var(e_π − e_∅) = σ_S²):

```latex
\frac{n_{\text{unpaired}}}{n_{\text{paired}}} = 1 + \frac{2\sigma_T^2}{\sigma_S^2},\qquad n_{\text{paired}} \approx \frac{c\,\sigma_S^2 \log(1/\alpha_{S,s})}{\theta^2}
```

---

## 4. Tính khả thi

**Khả thi về kỹ thuật, rủi ro cao về số trial, số task và chi phí.** Mô phỏng: Z ∈ {−1, 0, 1}, θ = 0,05, budget tối đa 2.000 cặp trial. Bản 1 dùng 200 lần lặp; bản 2 chạy lại độc lập với bộ betting plug-in kiểu aGRAPA (P(Z=+1) = 0,10), 1.000 lần lặp mỗi dòng, 5.000 lần cho kiểm tra sai loại I. Tái lập bằng `python scripts/run_simulations.py` → `results/simulation.json` (CI chạy lại mỗi lần push).

| STR thật | α mỗi ô | Bản 1: % admit / trung vị trial | Bản 2: % admit / trung vị trial |
| --- | --- | --- | --- |
| −0,25 | 0,05 | 100% / 52 | 100% / 71 |
| −0,25 | 3,1e-5 | 100% / 167 | 100% / 219 |
| −0,15 | 3,1e-5 | 100% / 491 | 99,7% / 752 |
| −0,10 | 3,1e-5 | 64% / 1.405 | 25,7% / 1.553 |
| −0,08 | 3,1e-5 | 24% / 1.361 | 1,5% / 1.613 |
| −0,05 (= −θ) | 3,1e-5 | — | 0% |
| −0,05 (= −θ), kiểm tra sai loại I | 0,05 | — | 3,0% (≤ 5%: **hợp lệ**) |

Ghi chú: trung vị chỉ tính trên các lần được admit nên ở dòng hiệu ứng nhỏ con số bị lệch (vì vậy −0,08 của bản 1 thấp hơn −0,10). Bộ betting tốt hơn có thể giảm 20–40%, nhưng bậc độ lớn không đổi. Hệ quả:

- **Thiếu task (nghiêm trọng hơn bản 1 nói).** Mỗi scope cần hàng trăm task *khác nhau* có test (R2). SWE-bench mỗi repo chỉ có vài chục đến vài trăm task (django ~850, nhiều repo < 50). Chỉ được lấy thêm từ các benchmark chuẩn ở bảng 6.1 (R13); nếu vẫn thiếu thì gộp scope thô hơn hoặc chấp nhận bound theo pool.
- **Hiệu ứng thật nhỏ.** SWE-Skills-Bench (arXiv v2; số của bản 1 lấy từ v1 đã lỗi thời): 98 skill, **92/98 không có tác dụng đáng kể**, pass ratio trung bình chỉ 76,6% → 76,9%, skill có hại làm giảm tới −17 điểm. Phân tích lại dữ liệu thật của họ (mục 0.4): SD thật của STR chỉ khoảng 0,03. Skill có STR ≈ −θ gần như **không bao giờ** được admit. "Clean reuse 84,3%" rất khó đạt.
- **Chi phí.** Ước tính gốc ~900 triệu token, 10–15 nghìn USD, ~15.000 CPU-giờ. Nếu mỗi ô cần 200–800 cặp, con số có thể tăng nhiều lần.

**Cách giảm rủi ro:** (1) pilot đo σ_S² và hiệu ứng thật trước; (2) chỉ test ô có reuse thật; (3) θ lớn hơn hoặc FDR (đổi định lý, R8); (4) model open-weight để giảm tiền API; (5) đặt **trần chi phí cho pilot** (vd ≤ 1.500 USD) trước khi chạy.

**Về GSE:** paper GSE không dùng SWE-bench và **không có fingerprint**, cũng không có code → B6 "GSE + fingerprints" là tự cài hoàn toàn → loại (mục 5).

---

## 5. Baseline: giữ, loại, thêm

Nguyên tắc: chỉ giữ baseline có code công khai, không tự cài lại phương pháp người khác. Baseline quyết định đổi từ GSE + fingerprints sang **XRepoSkill**. Mọi link dưới đây đã kiểm tra bằng `git ls-remote` ngày 01/11/2026.

| Baseline | Quyết định | Source code | Lý do |
| --- | --- | --- | --- |
| B1 No skills | Giữ | Không cần | Điều kiện đối chứng |
| B2 Unrestricted reuse | Giữ | Không cần | Admit mọi skill |
| B8 Always-retest | Giữ | Không cần | Chạy full test target trước mỗi lần reuse |
| B9 Budget-matched retries | Giữ (co-primary) | Không cần | Cùng budget, dùng để retry |
| B4 MemGovern | Giữ | [QuantaAlpha/MemGovern](https://github.com/QuantaAlpha/MemGovern) | Plugin SWE-agent, SWE-bench Verified |
| **XRepoSkill** (baseline quyết định) | Thêm | [XREPOSKILL/XRepoSkill](https://github.com/XREPOSKILL/XRepoSkill) | Skill cross-repo, kiểm chứng bằng Mantel–Haenszel, chạy trên mini-swe-agent |
| **gskill (GEPA)** | Thêm | [gepa-ai/gepa](https://github.com/gepa-ai/gepa) | Skill theo từng repo, validate bằng task SWE-smith |
| ASI (tuỳ chọn) | Thêm nếu còn thời gian | [zorazrw/agent-skill-induction](https://github.com/zorazrw/agent-skill-induction) | Thiết kế cho web agent, port sang code tốn công |
| B5 GSE replay | Loại | Không có code | Related work; có code thì thêm lại |
| B6 GSE + fingerprints | Loại | Không có | Hoàn toàn tự cài |
| MemCoder | Loại | Không có code | Chỉ trích dẫn |
| B3 Semantic routing | Loại | Không có bản chuẩn | XRepoSkill đã có bước chọn skill |
| B7 Capability-only (enclawed) | Loại khỏi bảng chính | [metereconsulting/enclawed](https://github.com/metereconsulting/enclawed) | Preprint 1 tác giả, không có thực nghiệm; giữ làm minh họa "authorized ≠ safe" |

**Công cụ có code:** [SWE-bench harness](https://github.com/SWE-bench/SWE-bench), [SWE-smith](https://github.com/SWE-bench/SWE-smith), [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent), [CooperBench](https://github.com/cooperbench/CooperBench) (preprint 2026, chưa được công nhận rộng → chỉ dùng tham khảo, không làm nguồn dữ liệu chính), [confseq](https://github.com/gostevehoward/confseq) (cần Boost), [LTT](https://github.com/aangelopoulos/ltt), [conformal-risk](https://github.com/aangelopoulos/conformal-risk).

**Lưu ý:** SWE-Skills-Bench đã công bố code + dữ liệu tại [ControllableModel/SWE-Skills-Bench](https://github.com/ControllableModel/SWE-Skills-Bench) (MIT); dùng dữ liệu paired của họ làm **pilot ngoài** (mục 0.4), không làm benchmark. Hầu hết paper skill 2026 là preprint: ghi rõ phiên bản arXiv và commit code.

**Go/no-go viết lại:** "≥ 5 điểm harmful acceptance so với XRepoSkill (+ fingerprint screen của chính Gatekeeper), so trên đường harm–coverage", pre-register lại.

---

## 6. Tiêu chuẩn build & kiểm chứng nhãn

### 6.1 Benchmark chuẩn được phép dùng (R13)

Tiêu chí "được công nhận rộng": (a) đã qua peer review ở hội nghị/tạp chí lớn **hoặc** là leaderboard chuẩn của cộng đồng; (b) dữ liệu và harness công khai; (c) task chấm bằng test thật, chạy trong Docker. Venue ghi dưới đây phải kiểm lại trên DBLP trước khi trích dẫn.

| Benchmark | Công nhận | Dùng cho | Ghi chú |
| --- | --- | --- | --- |
| [SWE-bench](https://github.com/SWE-bench/SWE-bench) (2.294 task, 12 repo Python) | ICLR 2024; chuẩn của ngành | Nguồn task target chính, regime A (cùng repo, khác version) | Mỗi task có `FAIL_TO_PASS` / `PASS_TO_PASS`, harness Docker chính thức |
| SWE-bench Verified (500 task) | Tập con được người kiểm duyệt (OpenAI, 2024); leaderboard chính | Pilot, tái hiện baseline, endpoint chính | Ít nhiễu nhãn nhất |
| [SWE-Gym](https://github.com/SWE-Gym/SWE-Gym) (2.438 task, 11 repo khác SWE-bench) | ICML 2025 | **Train split**: thu trajectory, induce skill | Repo không trùng SWE-bench → tách train/test theo repo dễ |
| [SWE-bench-Live](https://github.com/microsoft/SWE-bench-Live) | Microsoft, cập nhật hàng tháng, cùng format | Regime B (khác repo), task sau ngày cutoff model | Kiểm venue trước khi trích dẫn |
| [SWE-smith](https://github.com/SWE-bench/SWE-smith) | NeurIPS 2025 (Datasets & Benchmarks) | **Chỉ** dùng tập task đã công bố, khi thiếu task cho một scope | Không tự sinh task mới cho bảng chính |
| [BugsInPy](https://github.com/soarsmu/BugsInPy) (493 bug, 17 dự án Python) | ESEC/FSE 2020 | Kiểm tra độ bền (robustness) ngoài hệ SWE-bench | Không có issue text, cần adapter đầu vào |
| SWE-bench Pro | Scale AI 2025, leaderboard công khai | Chỉ để tái hiện XRepoSkill đúng như paper của họ | Không dùng trong bảng chính |

Những gì **không** phải benchmark mà là "treatment" của thí nghiệm, vẫn do mình dựng: skill (kể cả regime C adversarial, 52 skill outdated, cặp composition), scope family, nhãn. Cặp composition dựng từ **các task SWE-bench cùng sửa một file/hàm**, không lấy từ CooperBench.

### 6.2 Các lớp chuẩn

| Lớp | Chuẩn áp dụng | Cụ thể phải làm |
| --- | --- | --- |
| Từng task | Format SWE-bench | Repo + commit + Docker image + issue + `FAIL_TO_PASS` / `PASS_TO_PASS`; chấm bằng harness, không dùng LLM làm giám khảo |
| Nguồn task | Chỉ benchmark ở bảng 6.1 | Ghi rõ benchmark + instance_id cho từng task; không tự sinh task cho bảng chính |
| Test hành vi | Fault injection + mutation testing | Test tiêm lỗi (partial failure, retry, exactly-once, async); đo mutation score (mutmut). **Chỉ cho phân tích phụ**: endpoint chính dùng test chính thức chưa sửa (R13) |
| Nhãn | Scoring suite độc lập, 3 lớp (R3) | Ngoài sandbox admission; pool task chấm tách khỏi pool task admission |
| Chia dữ liệu | Theo repo | Mọi context của một skill chung một split |
| Thống kê | ACM SIGSOFT Empirical Standards | Pre-register; 3 lần × 2 backend; cluster bootstrap theo repo; BH cho so sánh phụ; báo cáo từng regime |
| Gatekeeper | Unit test + mô phỏng | pytest, mô phỏng tỉ lệ admit sai ≤ α, chạy trong GitHub Actions |
| Artifact | ACM Badges (Available, Functional, Reusable) | Digest, commit, model ID + ngày, seed, kết quả từng task, script sinh bảng/hình |

**LLM chạy ở đâu:** **Gemini qua Vertex AI** (2 backend: bậc Pro và bậc Flash; mã model trong `configs/models/vertex_gemini.json`, ghi kèm ngày gọi API). Code + test chạy trong Docker trên runner GitHub Actions hoặc máy CPU. Harness: **mini-swe-agent 2.4.6** cho mọi hệ thống (R6). Hướng dẫn: `docs/vertex_setup.md`.

**GitHub Actions làm được gì và không làm được gì:** CI chạy được unit test, mô phỏng e-process, test phản ví dụ Theorem 7, kiểm tra sổ α, sinh report HTML, và tối đa 1–2 task SWE-bench nhỏ (runner miễn phí chỉ có ~14 GB đĩa, giới hạn 6 giờ). CI **không** chạy được agent LLM hay hàng nghìn trial: phần đó chạy trên máy riêng, kết quả (JSON) commit vào `results/` để CI phân tích và vẽ.

**Bốn lớp kiểm chứng nhãn:** (1) nhãn biết trước theo cách dựng (regime C, 46 cặp composition) + test tái hiện; (2) nhóm đối chứng: skill no-op → neutral, skill cài bug → harmful; (3) mutation score + loại test flaky; (4) 2 người gán nhãn 50–100 cặp, Cohen's kappa ≥ 0,7.

**Threats to Validity bắt buộc ghi:** "safe" chỉ nghĩa là không làm test suite tệ hơn, với xác suất sai ≤ α, trong scope đã khai báo.

---

## 7. Todo list chi tiết

Mỗi việc có tiêu chí xong sau dấu →. Thời gian là ước lượng cho người mới, làm bán thời gian ~20 giờ/tuần.

| Phase | Nội dung | Thời gian (ước lượng gốc) | Lịch ASE 2027 | Phụ thuộc |
| --- | --- | --- | --- | --- |
| H | Hạ tầng repo, CI, report | 1 tuần | ✅ xong 01/11 | — |
| 0 | Học nền | 4–6 tuần | → 30/11 | — |
| 1 | Sửa lý thuyết & paper | 3–4 tuần | lý thuyết ✅; đưa vào LaTeX → 15/12 | 0 |
| 5a | Lõi Gatekeeper (không cần LLM) | 3–4 tuần | ✅ xong 01/11 | 1 |
| 2 | Môi trường & tái hiện baseline | 4–6 tuần 💰 | → 15/12 (song song M1) | 0 |
| 3 | Pilot & go/no-go | 3–4 tuần 💰 | → 15/01 (G2) | 2, 5a |
| 4 | Benchmark SkillShift-SE | 6–8 tuần 💰 | → 28/02 | 3 |
| 5b | Gatekeeper đầy đủ | 4 tuần | phần lớn ✅; nối runner thật → 31/01 | 3 |
| 6 | Chạy thí nghiệm | 8–12 tuần 💰 | → 15/04 (G3) | 4, 5b |
| 7 | Phân tích & viết | 4–6 tuần | → 15/05 | 6 |
| 8 | Artifact & nộp | 2 tuần | → ~29/05 | 7 |

### Phase H – Hạ tầng repo, CI, report (mới)

- [x] 🤖 README: giới thiệu đề tài, cấu trúc repo, cách chạy, link tài liệu → README.md trên main · ✅ commit 22159ef
- [x] 🤖 Đưa 3 PDF (paper, reading list, summary) vào `docs/` → commit trên main · ✅ `docs/`, commit 22159ef
- [x] 🤖 Đưa TODO.md này lên main → là nguồn sự thật duy nhất về tiến độ · ✅ commit 22159ef
- [x] 🤖 Khung Python package `gatekeeper/` + `pyproject.toml` (Python 3.11) + `tests/` · ✅ `src/gatekeeper/`, commit 22159ef
- [x] 🤖 GitHub Actions: lint (ruff) + pytest + mô phỏng nhanh + build report → workflow xanh · ✅ CI run 41330369429 xanh
- [x] 🤖 Report HTML `report/index.html` (lý thuyết → thực nghiệm), tự sinh lại từ kết quả trong CI → mở được từ main · ✅ `report/index.html`, CI artifact `gatekeeper-report`
- [x] 🤖 Job CI đối chiếu với `confseq` (cài `libboost-dev`) → chạy được hoặc ghi rõ lý do lỗi · ✅ CI run 41330369429: cần `numpy<2` + Python 3.10 + Boost
- [ ] 👤 Xin người hướng dẫn PLAN.md, REVIEWS.md, Portfolio Overview và 3 smoke test → đưa vào `docs/`
- [ ] 👤 Xin file LaTeX nguồn của paper → để đưa các sửa đổi ở `docs/theory/corrections.md` vào bài
- [x] 👤 Chốt venue mục tiêu → ghi vào README · ✅ **ASE 2027** (@thuthuy, 01/11/2026), lịch ngược ở mục 0.1
- [ ] 👤 Xác nhận hạn nộp chính thức ASE 2027 khi CfP công bố → sửa lịch mục 0.1 nếu khác 29/05/2027

### Phase 0 – Học nền

**Đọc paper (đúng thứ tự)**

- [ ] 👤 XRepoSkill → 1 trang ghi chú: tìm rule, verify (Mantel–Haenszel), chọn rule cho issue
- [ ] 👤 GSE → replay verification hoạt động thế nào, vì sao không làm baseline được · 🔧 theo abstract: GSE đánh giá trên **sinh test lộ bug và lọc false-positive bug report**, không phải sửa code; dùng Skill Relation Graph + replay verification
- [ ] 👤 SWE-Skills-Bench → cách đo paired có/không skill và tỉ lệ skill gây hại · 🔧 tóm tắt + phân tích dữ liệu thật ở mục 0.4
- [ ] 👤 HSE (Hierarchical Skill Evolution, arXiv 2610.35616) → **công trình sát nhất**: học skill từ SWE-Gym, đánh giá trên SWE-bench Verified (trùng split của mình); ghi rõ Gatekeeper khác gì (HSE không có admission theo target)
- [ ] 👤 MemGovern → 5 dòng tóm tắt
- [ ] 👤 gskill (GEPA) → 5 dòng tóm tắt
- [ ] 👤 ASI → 5 dòng + nhận xét port sang coding khó không
- [ ] 👤 Voyager → mô hình skill library gốc
- [ ] 👤 Waudby-Smith & Ramdas 2024 → giải thích được vì sao dừng sớm vẫn hợp lệ
- [ ] 👤 Learn Then Test và Conformal Risk Control → phân biệt với e-process
- [ ] 👤 Lướt Howard et al. 2021
- [ ] 👤 Ý tưởng Cameron et al. 2008 (cluster bootstrap)
- [ ] 👤 Benjamini–Hochberg 1995 (và e-BH nếu cân nhắc FDR)
- [ ] 👤 Đọc lại paper FSE-2027-13 → đánh dấu mọi số "projected" cần thay
- Ghi chú đọc lưu ở `docs/notes/<paper>.md`.

**Ôn kiến thức**

- [ ] 👤 Kỳ vọng, phương sai, phương sai của hiệu hai biến (paired)
- [ ] 👤 Union bound, supermartingale, bất đẳng thức Ville → hiểu chứng minh Theorem 4
- [ ] 👤 Total variation và |E_Q f − E_P f| ≤ (độ rộng của f) × TV
- [ ] 👤 FWER vs FDR; khi nào dùng cái nào

**Thực hành**

- [ ] 👤 Cài Docker, Python 3.11, uv
- [x] 👤💰 Chạy SWE-bench harness với patch gốc trên 5 task Verified → 5/5 pass (máy riêng; CI chỉ chạy 1 task) · ✅ **5/5 gold resolved, R = 0**, miễn phí trong GitHub Actions (workflow `Harness smoke`, run 41335635404, swebench 5.0.2, `results/harness_smoke.json`)
- [ ] 👤💰 Chạy mini-swe-agent giải 5 task bằng 1 model API → có log và kết quả
- [x] 🤖 Viết e-process (~30 dòng) + test → đối chiếu với `confseq` trên dữ liệu giả: cả hai giữ sai loại I ≤ α và cùng admit skill mạnh (hai bộ betting khác nhau nên log E không trùng từng số) · ✅ đồng ý 97% với confseq tại biên H0, cả hai admit sai ≤ α, cùng admit 100% skill mạnh (`results/confseq_crosscheck.json`)
- [x] 🤖 Mô phỏng 1.000 lần với STR = −θ → tỉ lệ admit sai ≤ α, chạy trong CI · ✅ 5.000 lần, admit sai 3,0% ≤ 5% (`results/simulation.json`)
- [ ] 👤 1 trang "Gatekeeper khác XRepoSkill và GSE ở đâu" → gửi người hướng dẫn góp ý · 🔧 bản nháp từ abstract: `docs/notes/positioning.md` (chờ đọc full paper)

### Phase 1 – Sửa lý thuyết & paper

**Theorem 7**

- [x] 👤 Phát biểu lại: cận chặt 1−θ; định nghĩa thứ tự ghép · ✅ `docs/theory/corrections.md` §5 (chờ người thống kê đọc)
- [x] 👤 Chứng minh với ℓ(x,∅) = θ, ℓ(π1) = ℓ(π2) = 0, ℓ(π1∘π2) = 1, thêm cặp thứ hai ℓ(π1∘π2) = 0 để bác bỏ mọi g · ✅ `docs/theory/corrections.md` §5 (chờ người thống kê đọc)
- [x] 👤 Thay cơ chế bằng "retry wrapper gọi hàm async không await" · ✅ `docs/theory/corrections.md` §5 (chờ người thống kê đọc)
- [x] 🤖 Test Python: S1 riêng pass, S2 riêng pass, S1∘S2 fail im lặng → chạy trong CI · ✅ `tests/test_composition_theorem7.py`

**Theorem 4**

- [x] 👤 Union bound trên mọi ô (S,s), mọi composite, và re-admission · ✅ `docs/theory/corrections.md` §2–3; kiểm chứng số `tests/test_theory.py`
- [x] 👤 Đổi ξ_s → 2ξ_s · ✅ `docs/theory/corrections.md` §2–3; kiểm chứng số `tests/test_theory.py`
- [x] 👤 Alpha-spending α·6/(π²k²) cho composite và re-admission · ✅ `docs/theory/corrections.md` §2–3; kiểm chứng số `tests/test_theory.py`
- [x] 👤 Viết tường minh e-process, khoảng λ_i, H0 · ✅ `docs/theory/corrections.md` §2–3; kiểm chứng số `tests/test_theory.py`
- [x] 👤 Ghi điều kiện 2ξ_s ≤ θ · ✅ `docs/theory/corrections.md` §2–3; kiểm chứng số `tests/test_theory.py`
- [x] 👤 Cách ước lượng ξ_s, hoặc báo cáo bound theo nhiều giá trị ξ_s · ✅ `docs/theory/corrections.md` §2–3; kiểm chứng số `tests/test_theory.py`
- [ ] 👤 Chọn: số task ≥ số trial, hay P_s = pool (R2) · 🔧 đề xuất (b) rút có hoàn lại từ pool, `corrections.md` §1.2; chờ chốt
- [ ] 👤 Chốt FWER hay FDR (R8) · 🔧 đề xuất giữ FWER, e-BH làm phân tích phụ, `corrections.md` §3; chờ chốt

**Định nghĩa & metric**

- [x] 👤 Chuẩn hóa loss về [0,1] · ✅ `docs/theory/corrections.md` §1, §5; code `loss.py`, `analysis.harm_coverage_curve`
- [x] 👤 P_s = phân phối task mà I(x) đúng · ✅ `docs/theory/corrections.md` §1, §5; code `loss.py`, `analysis.harm_coverage_curve`
- [x] 👤 Nhãn 3 lớp harmful / neutral / beneficial theo STR trên scoring suite (R3) · ✅ `docs/theory/corrections.md` §1, §5; code `loss.py`, `analysis.harm_coverage_curve`
- [x] 👤 Harmful acceptance = số cặp harmful được admit / số cặp harmful · ✅ `docs/theory/corrections.md` §1, §5; code `loss.py`, `analysis.harm_coverage_curve`
- [x] 👤 Clean-reuse coverage = beneficial được admit / beneficial; so "at matched coverage" bằng đường harm–coverage · ✅ `docs/theory/corrections.md` §1, §5; code `loss.py`, `analysis.harm_coverage_curve`
- [x] 👤 d̄ tính trong từng scope hay toàn library · ✅ `docs/theory/corrections.md` §1, §5; code `loss.py`, `analysis.harm_coverage_curve`

**Prop. 9**

- [x] 👤 Mô hình phương sai; tỉ lệ 1 + 2σ_T²/σ_S² · ✅ `corrections.md` §6; `tests/test_theory.py::test_prop9_variance_ratio`
- [x] 👤 Bỏ câu "net win 1,55×" và "3,1×" · ✅ `corrections.md` §6 (chờ sửa vào LaTeX)

**Chỉnh paper và summary**

- [ ] 👤 Baseline quyết định → XRepoSkill ở abstract, intro, §3.1, §9.2, go/no-go, summary
- [ ] 👤 GSE, MemCoder, enclawed → related work
- [ ] 👤 Harness → một harness chung (R6); sửa "10 systems" (R10)
- [ ] 👤 Figure 1: cần test fault-injection
- [ ] 👤 Sửa câu CI "vượt margin 5 điểm"
- [ ] 👤 Nhờ 1 người biết thống kê đọc chứng minh → sửa hết góp ý

### Phase 5a – Lõi Gatekeeper (chuyển lên sớm, không cần LLM)

- [x] 🤖 `eprocess.py`: betting e-process trong log-space, λ predictable, có test · ✅ xem Nhật ký 01/11
- [x] 🤖 `alpha_ledger.py`: sổ phân bổ α (ô, composite, re-admission) → test tổng ≤ α · ✅ xem Nhật ký 01/11
- [x] 🤖 `skill.py`: schema skill ⟨π, D, I, P, K⟩ (JSON/YAML) + validate · ✅ xem Nhật ký 01/11
- [x] 🤖 `scope.py`: scope screen (so D, chạy I) → OutOfScope · ✅ xem Nhật ký 01/11
- [x] 🤖 `footprint.py`: giao footprint → hàng đợi composite · ✅ xem Nhật ký 01/11
- [x] 🤖 `admission.py`: Algorithm 1 với budget, dừng sớm; trial runner là interface (giả lập trong test) · ✅ xem Nhật ký 01/11
- [x] 🤖 Mô phỏng: skill có STR biết trước → bảng % admit và số trial, tự cập nhật trong report · ✅ xem Nhật ký 01/11
- [x] 🤖 Coverage ≥ 80% · ✅ xem Nhật ký 01/11

### Phase 2 – Môi trường & tái hiện baseline

**Hạ tầng LLM**

- [x] 👤💰 Chọn model API → ghi model ID chính xác · ✅ **Gemini qua Vertex AI** (@thuthuy, 01/11); cấu hình `configs/models/vertex_gemini.json` (Pro + Flash làm 2 backend)
- [x] 👤 Xác nhận mã model + giá Gemini trong Vertex Model Garden → sửa `configs/models/vertex_gemini.json`, đặt `_verified: true` · ✅ gọi thử được cả 3 model ở location `global` (404 ở us-central1); chi phí LiteLLM khớp giá cấu hình; giá chưa đối chiếu trang Google
- [ ] 👤 Thiết lập GCP project, billing alert, Workload Identity, secrets GitHub theo `docs/vertex_setup.md`
- [ ] ~~👤 Chọn model open-weight → ghi digest weight~~ · bỏ: backend thứ hai là Gemini Flash (cùng Vertex AI) thay cho model open-weight; nêu trong Threats to Validity (một nhà cung cấp)
- [ ] ~~👤💰 Dựng vLLM trên GPU~~ · bỏ (không dùng open-weight)
- [x] 👤💰 Gọi thử Gemini qua Vertex từ harness: chạy workflow `Pilot (paid, Vertex AI)` với n = 2, budget 3 USD → thành công + có chi phí thật · ✅ chạy local 02/11: 1 task × 2 nhánh, Gemini 3.8 Flash, **0,26 USD**, pipeline chạy hết (`results/pilot/smoke-flash-1.json`)
- [x] 👤 Cố định tham số sampling và ghi vào config · ✅ `temperature: 0`, `seed: 0` trong `configs/models/vertex_gemini.json`; giới hạn bước/chi phí mỗi instance trong `scripts/run_pilot.py`

**Hạ tầng chạy trial**

- [x] 👤 Tách máy: GPU chạy LLM, CPU chạy container test · ✅ không cần GPU: LLM chạy trên Vertex AI, container test chạy trên runner GitHub Actions / máy CPU
- [x] 🤖 Pin Docker image bằng digest · 🔧 `TrialRecord` từ chối image không có `sha256:`; còn chọn image · ✅ pilot tự ghi digest thật của image SWE-bench vào từng `TrialRecord` (vd `sha256:bde4fbda…` cho flask-5014), Pilot dry run run 41357916901
- [x] 🤖 Script 1 trial: snapshot → áp/không áp skill → agent → test → JSON (cài interface của 5a) · 🔧 interface `TrialRunner.run_pair` sẵn; cần harness + Docker thật; paired trial gold/no-op chạy thật qua harness: `scripts/harness_smoke.py`; pipeline agent đầy đủ: `scripts/run_pilot.py` (dataset theo nhánh → mini-swe-agent → harness → Z → log), dry run trong CI
- [x] 🤖 Kiểm tra hai nhánh cùng task, seed, snapshot · ✅ hai nhánh dùng cùng hàng dataset, cùng image, cùng seed; chỉ khác guidance/startup của skill (`pilot.arm_rows`, `pilot.arm_config`, `tests/test_pilot.py`)
- [x] 🤖 Log model ID, số token, thời gian, chi phí mỗi run · ✅ `runlog.TrialRecord` bắt buộc model ID + ngày, digest, commit, seed
- [ ] 👤💰 Chạy cùng 1 task 5 lần → mức dao động của agent
- [ ] 👤 Ước chi phí 1 cặp trial (token + GPU + CPU)

**Baseline có code**

- [x] 👤 Chốt harness chung (R6) → ghi commit · ✅ **mini-swe-agent 2.4.6** + swebench 5.0.2 (ghim trong workflow); pipeline dry run: `.github/workflows/pilot-dryrun.yml`
- [ ] 👤 Clone XRepoSkill, ghi commit, chạy unit test → pass
- [ ] 👤💰 Chạy XRepoSkill trên đúng tập task của paper (hoặc tập con có so từng task) → số paper nằm trong CI 95% (R5)
- [ ] 🤖 Nếu cần, adapter chuyển format skill (không sửa thuật toán)
- [ ] 👤💰 MemGovern trên tập task của paper → cùng tiêu chí R5
- [ ] 👤💰 gskill cho 1 repo → có SKILL.md và kết quả holdout
- [ ] 👤 (Tuỳ chọn) Đánh giá công port ASI → quyết định có/không
- [ ] 👤 Email hỏi tác giả GSE có public code không

**Điều kiện đối chứng**

- [x] 🤖 B1 No skills · ✅ logic trong `baselines.py`, test `tests/test_analysis.py`
- [x] 🤖 B2 Unrestricted reuse · ✅ logic trong `baselines.py`, test `tests/test_analysis.py`
- [x] 🤖 B8 Always-retest · ✅ logic trong `baselines.py`, test `tests/test_analysis.py`
- [x] 🤖 B9 Budget-matched retries (cùng ngân sách token + CPU) · ✅ logic trong `baselines.py`, test `tests/test_analysis.py`
- [x] 🤖 README cho mỗi baseline: commit, lệnh chạy, khác biệt so với bản gốc · ✅ `docs/baselines.md` (commit của bên thứ ba điền khi clone)

### Phase 3 – Pilot & go/no-go

**Chuẩn bị**

- [ ] 👤💰 **Đầu tiên (R15):** đo hiệu ứng của 3–5 skill dạng edit program trên 1 repo, khoảng 30 cặp mỗi skill → nếu |STR| < 0,1 cho mọi skill thì dừng, thu hẹp hoặc đổi hướng trước khi chi thêm · 🔧 kế hoạch 200 USD (@thuthuy, 02/11): `docs/budget_200.md` — A đo chi phí + chọn model (≤ 6 USD), B kiểm tra phép đo (đối chứng nhiễu + đối chứng dương), C 4 skill trên pool g1; quy tắc G1 cố định trong `analysis.g1_decision`
- [ ] 👤 Đặt trần chi phí pilot (vd ≤ 1.500 USD)
- [ ] 👤 Chọn 2 repo (1 cùng framework, 1 khác framework)
- [ ] 👤 Chọn 10 skill, tạo 20–30 cặp skill/context · 🔧 4 skill theo họ mẫu sửa đã khai thác (null-guard, type-guard, exception-handling, validation-error) với predicate `issue_regex` cho I(x), trong `configs/skills/`; độ chính xác kích hoạt đo bằng `scripts/activation_check.py` (CI)
- [ ] 👤 Tách pool task admission và pool task chấm (R3)
- [ ] 👤 Gán nhãn 3 lớp cho cặp pilot theo quy trình kiểm chứng nhãn

**Đo đạc**

- [ ] 👤💰 ≥ 30 cặp trial cho mỗi cặp skill/context
- [ ] 🤖 Ước lượng σ_S², σ_T² và hiệu ứng thật trung bình · 🔧 công cụ sẵn: `analysis.variance_components`, chờ dữ liệu pilot; ước lượng ngoài từ SWE-Skills-Bench: σ_T² = 0,067, σ_S² = 0,040, pairing 4,3×
- [ ] 🤖 Số trial cần mỗi ô với α đã phân bổ (Prop. 9 đã sửa + mô phỏng) · 🔧 công cụ sẵn: `analysis.trials_needed`; bảng thiết kế `results/design_table.json` (mục 0.4)
- [x] 🤖 Đếm số task khác nhau có được mỗi scope → đủ cho số trial không (R2) · ✅ **không đủ** cho phương án (a), xem mục 0.4
- [ ] 🤖 Power analysis: cần bao nhiêu cặp harmful để phát hiện margin 5 điểm với power 80% (R4) · 🔧 công cụ sẵn: `analysis.endpoint_power`; kết quả với số dự kiến của paper: `results/endpoint_power.json` → R14
- [ ] 👤 Ước lượng lại tổng chi phí
- [ ] 👤💰 Chạy XRepoSkill và Gatekeeper trên cùng cặp pilot; margin + CI (chỉ tham khảo)

**Quyết định**

- [ ] 👤 Báo cáo pilot 2 trang (số đo, chi phí, rủi ro) → cũng đưa vào report HTML
- [ ] 👤 Go/no-go theo khả thi (R4): đủ task, chi phí trong ngân sách, power ≥ 80% → làm tiếp; thiếu một điều → thu hẹp (cross-repo + adversarial, θ lớn hơn); thiếu nhiều → gộp vào FSE-2027-01
- [ ] 👤 Họp người hướng dẫn → ghi quyết định và lý do
- [ ] 👤 Cập nhật kích thước benchmark, θ, α

### Phase 4 – SkillShift-SE: giao thức đánh giá trên benchmark chuẩn

**Chọn dữ liệu (chỉ từ bảng 6.1)**

- [x] 🤖 Tải metadata SWE-bench, SWE-bench Verified, SWE-Gym, SWE-bench-Live → bảng repo × số task × version, commit vào `data/` · ✅ workflow Data snapshots run 41331567384 → `data/benchmarks/` (5 benchmark tải được)
- [ ] 👤 Chọn ≥ 25 repo từ các benchmark này (train: SWE-Gym; test: SWE-bench + SWE-bench-Live) → ghi benchmark, repo, commit
- [ ] 👤 Chọn 4 dòng version dependency có trong các task đã chọn
- [x] 🤖 Chia train/test theo repo → lưu file split (danh sách instance_id) · ✅ `data/splits/split_v0.json` hash fb74140ef67fe769: train 11 repo SWE-Gym; test 223 repo, bỏ 4 repo trùng
- [ ] 👤 Khai báo scope family S trước khi chạy · 🔧 đề xuất từ dữ liệu: scope = (họ skill, framework) cho hàng trăm task/scope (giảm R2); (repo, version) chỉ có ≤ 157 task

**Tạo skill (treatment)**

- [ ] 👤💰 Chạy agent trên task SWE-Gym (train split) → trajectory thành công
- [ ] 🤖 Induce skill thành edit program (AST rewrite + shell step) · 🔧 bước đầu: 12 họ mẫu sửa từ gold patch SWE-Gym, đều lặp lại ở 5–11 repo train (`results/skill_mining.json`); chưa thành edit program
- [ ] 🤖 Ghi D, I, P, K cho từng skill
- [ ] 🤖 Kiểm tra không skill nào chứa thông tin repo test
- [ ] 👤 Tạo 52 skill outdated nhưng vô hại

**Task target (không tự sinh)**

- [ ] 🤖 Lấy task target từ SWE-bench / SWE-bench-Live theo scope, ưu tiên task sau ngày cutoff của model
- [x] 🤖 Kiểm tra mỗi task chạy được bằng harness chính thức (gold patch pass, không flaky) · 🔧 pool 40 task Verified cho pilot G1 (`configs/pools/default.json`, 12 repo) đang được kiểm bằng workflow `Validate pilot pool` (gold ×2 + no-op) · ✅ pool G1: **38/40 dùng được** (loại `psf__requests-1921`: gold không giải được; `pylint-dev__pylint-8898`: nhánh no-op không sạch), run 41359076353, `results/pool_validation/default/summary.json`
- [x] 🤖 Đếm task mỗi scope → đủ cho số trial ở Phase 3; thiếu thì bổ sung từ tập SWE-smith đã công bố hoặc gộp scope · ✅ **không đủ**: 0 scope (repo, version) có ≥ 219 task; lớn nhất django@3.2 = 157 (mục 0.4)
- [ ] 👤 Chạy kiểm tra độ bền trên BugsInPy (tuỳ chọn)

**Test hành vi (phân tích phụ)**

- [ ] 👤 Test fault-injection cho từng behavioural class, để riêng trong `supplementary_tests/`
- [ ] 🤖 Mutation score trước/sau khi thêm test

**Regime & cặp composition**

- [ ] 👤 Regime A: cùng repo SWE-bench, khác version
- [ ] 👤 Regime B: khác repo (SWE-Gym → SWE-bench / SWE-bench-Live), cùng framework
- [ ] 👤 Regime C: skill adversarial (hợp lệ về quyền nhưng cài lỗi chức năng) áp lên task SWE-bench
- [ ] 👤 46 cặp composition: ghép các task SWE-bench cùng sửa một file/hàm, theo 4 cơ chế (exception type, ordering, resource lifetime, transaction scope) · 🔧 3.690 ứng viên (cùng repo, cùng hàm) trong `results/skill_mining.json`; còn lọc theo 4 cơ chế

**Kiểm chứng nhãn**

- [ ] 👤 Test tái hiện lỗi cho mọi skill harmful dựng sẵn
- [ ] 🤖 Nhóm đối chứng no-op / bug cài sẵn → tỉ lệ sai của pipeline gán nhãn
- [ ] 👤💰 Chạy baseline nhiều lần → loại test flaky
- [ ] 👤 2 người gán nhãn 50–100 cặp → Cohen's kappa ≥ 0,7
- [ ] 🤖 Cặp không ổn định qua 3 lần chạy → "uncertain", báo cáo riêng
- [ ] 🤖 Scoring suite độc lập ngoài sandbox admission

**Đóng băng**

- [ ] 👤 Pre-register: endpoint, θ, α, phân bổ α, budget, baseline, harness, FWER/FDR · 🔧 bản nháp: `docs/preregistration.md` (đánh dấu ✅/❓/⏳)
- [ ] 🤖 Đóng băng benchmark v1 (hash trong repo), không sửa sau khi bắt đầu Phase 6

### Phase 5b – Gatekeeper đầy đủ

- [x] 🤖 D: hash lockfile, interpreter, version framework, behavioural class · ✅ `scope.py`/`footprint.py`/`admission.py`/`loss.py`, test `tests/test_admission.py`, `tests/test_modules.py`
- [x] 🤖 I: predicate thực thi được trên repo target · ✅ `scope.py`/`footprint.py`/`admission.py`/`loss.py`, test `tests/test_admission.py`, `tests/test_modules.py`
- [x] 🤖 P: postcondition kèm context đã quan sát · ✅ `scope.py`/`footprint.py`/`admission.py`/`loss.py`, test `tests/test_admission.py`, `tests/test_modules.py`
- [x] 🤖 K: phân tích read/write trên AST + symbol nhắc trong P · ✅ `scope.py`/`footprint.py`/`admission.py`/`loss.py`, test `tests/test_admission.py`, `tests/test_modules.py`
- [ ] 🤖 Nối paired trial runner thật (Phase 2) vào Algorithm 1
- [x] 🤖 Hàm loss chuẩn hóa về [0,1] · ✅ `scope.py`/`footprint.py`/`admission.py`/`loss.py`, test `tests/test_admission.py`, `tests/test_modules.py`
- [x] 🤖 Phân bổ budget theo độ bất định · ✅ `scope.py`/`footprint.py`/`admission.py`/`loss.py`, test `tests/test_admission.py`, `tests/test_modules.py`
- [ ] 🤖 Routing model (gradient boosting) chỉ sắp thứ tự ô · 🔧 hiện là heuristic `_priority`; GBT cần dữ liệu pilot để train
- [x] 🤖 Retirement khi fingerprint đổi + alpha-spending khi re-admit · ✅ `scope.py`/`footprint.py`/`admission.py`/`loss.py`, test `tests/test_admission.py`, `tests/test_modules.py`
- [x] 🤖 Capability verdict tách riêng khỏi quyết định chức năng · ✅ `scope.py`/`footprint.py`/`admission.py`/`loss.py`, test `tests/test_admission.py`, `tests/test_modules.py`
- [x] 🤖 Xuất certificate: scope, α, ξ_s, số trial, kết quả · ✅ `scope.py`/`footprint.py`/`admission.py`/`loss.py`, test `tests/test_admission.py`, `tests/test_modules.py`
- [x] 🤖 Test tích hợp trên 3 skill có đáp án biết trước · ✅ `scope.py`/`footprint.py`/`admission.py`/`loss.py`, test `tests/test_admission.py`, `tests/test_modules.py`
- [ ] 👤💰 Đo chi phí 1 quyết định admission so với 1 lần full validation

### Phase 6 – Chạy thí nghiệm

**Chuẩn bị**

- [x] 🤖 Script chạy hàng loạt, chạy tiếp được khi lỗi giữa chừng · ✅ `runlog.run_batch` + sửa dòng ghi dở khi crash
- [ ] 👤💰 Chạy thử toàn pipeline trên 5 cặp → không lỗi
- [ ] 🤖 Bảng theo dõi chi phí vs ngân sách, cập nhật sau mỗi đợt, hiện trong report · 🔧 công cụ sẵn: `runlog.CostSummary`; chưa có dữ liệu

**RQ1 – So sánh quyết định**

- [ ] 👤💰 Gatekeeper, XRepoSkill, MemGovern, gskill, B1, B2, B8, B9 trên toàn bộ cặp
- [ ] 🤖 Đường harm–coverage, so tại cùng coverage
- [ ] 🤖 Gatekeeper vs always-retest: an toàn và chi phí

**RQ2 – Composition**

- [ ] 🤖 Số cặp jointly-harmful bắt được theo từng hệ thống
- [ ] 🤖 Tỉ lệ cặp footprint giao nhau và chi phí thêm

**RQ3 – Regime & budget-matched**

- [ ] 🤖 Báo cáo riêng regime A, B, C
- [ ] 🤖 Gatekeeper vs B9 về tỉ lệ sửa được task

**RQ4 – Retirement, ablation, break-even**

- [ ] 👤💰 Độ trễ retirement sau khi đổi môi trường
- [ ] 👤💰 6 ablation
- [ ] 🤖 Điểm hòa vốn so với always-retest và no-skills

**Lặp lại & lưu trữ**

- [ ] 👤💰 3 lần chạy × 2 backend cho mọi cấu hình
- [ ] 👤 Lưu kết quả từng task + backup nơi thứ hai

### Phase 7 – Phân tích & viết

- [ ] 🤖 Cluster bootstrap theo repo cho mọi CI · 🔧 công cụ sẵn: `analysis.cluster_bootstrap_ci`
- [ ] 🤖 BH cho so sánh phụ · 🔧 công cụ sẵn: `analysis.benjamini_hochberg`
- [ ] 🤖 Sweep trọng số regression penalty (0,2–2,0) · 🔧 công cụ sẵn: `analysis.penalty_sweep`
- [ ] 🤖 Script tự sinh mọi bảng và hình từ kết quả thô (chạy trong CI) · 🔧 `scripts/build_report.py` sinh report; bảng RQ chờ dữ liệu · khung LaTeX IEEE `paper/main.tex` + `scripts/make_tables.py` → `paper/tables/*.tex`, CI workflow `Paper` biên dịch PDF
- [ ] 👤 Sửa refs.bib theo bảng mục 0.4: tiêu đề + tác giả thật cho [6], [7], [8], [9], [12], [13], [22]; kiểm tra lại mã arXiv của [8]; tìm [15], [16]
- [ ] 👤 Thay toàn bộ số projected bằng số đo; bỏ banner "Draft status"
- [ ] 👤 Phân tích định tính các ca admit sai
- [ ] 👤 Related work và baseline theo mục 5
- [ ] 👤 Threats to Validity
- [ ] 👤 Kiểm tra từng trích dẫn trên arXiv/DBLP; thay "GSE Authors"… bằng tên thật · 🔧 workflow `Data snapshots` tra arXiv + DBLP → `data/citations.json` · arXiv: 16/16 mã tồn tại, 7 tiêu đề trong paper sai (mục 0.4); DBLP chưa lấy được
- [ ] 👤 2 người đọc nháp → sửa hết góp ý
- [ ] 👤 Giới hạn trang và template ACM của venue đã chốt · 🔧 ASE dùng template IEEE conference: khung `paper/main.tex` (IEEEtran); kiểm số trang khi CfP ASE 2027 ra

### Phase 8 – Artifact & nộp

- [ ] 🤖 Đóng gói artifact: code, pipeline benchmark, baseline, script phân tích, kết quả từng task
- [ ] 🤖 Ghi digest, commit, model ID + ngày, seed, cấu hình phần cứng
- [ ] 🤖 Ẩn danh: xóa tên, email, metadata · 🔧 công cụ sẵn: `scripts/check_anonymity.py`
- [ ] 👤 Chạy lại toàn bộ từ artifact trên máy sạch → đúng bảng
- [ ] 👤 Kiểm tra badge Available, Functional, Reusable
- [ ] 👤 Kiểm tra deadline và hướng dẫn nộp trên trang chính thức
- [ ] 👤 Nộp bài

---

## Nhật ký tiến độ

| Ngày | Việc | Bằng chứng (commit / log CI / file) |
| --- | --- | --- |
| 01/11/2026 | Review lại todo list (bản 2) | TODO.md |
| 01/11/2026 | Đổi tên người viết → @thuthuy; benchmark chỉ lấy từ chuẩn được công nhận (R13); @thuthuy duyệt | TODO.md |
| 01/11/2026 | Phase H: README, 3 PDF, package, CI, report lên main | commit 22159ef, b59d447 |
| 01/11/2026 | CI đỏ ở job confseq (`np.float_` bị xoá trong NumPy 2) → ghim `numpy<2`; nâng action lên Node 24 | commit 4fd886c, CI run 41330369429 xanh |
| 01/11/2026 | Phase 1: lý thuyết đã sửa (Theorem 4′, 7′, Prop. 9, định nghĩa, metric) + test số (hệ số 2ξ chặt, FWER với sổ α, tỉ lệ 1+2σ_T²/σ_S²) + tự kiểm tra số liệu paper | `docs/theory/corrections.md`, `tests/test_theory.py`, `src/gatekeeper/paper_checks.py` |
| 01/11/2026 | Phase 5a/5b (phần không cần LLM): skill, scope, footprint AST, Algorithm 1, composite, phân bổ, retirement, certificate, loss | `src/gatekeeper/*.py`, 58 test, coverage 96% |
| 01/11/2026 | Công cụ Phase 2/3/6/7/8: baseline B1/B2/B8/B9, log chạy tiếp được (sửa bug dòng ghi dở), chi phí, σ, power, bootstrap, BH, harm–coverage, sweep w, kiểm tra ẩn danh | `baselines.py`, `runlog.py`, `analysis.py`, `scripts/check_anonymity.py` |
| 01/11/2026 | Workflow `Data snapshots`: metadata benchmark (HuggingFace) + trích dẫn (arXiv, DBLP), vì máy dev bị chặn các host này | `.github/workflows/data.yml` |
| 01/11/2026 | Data snapshot đầu tiên: 5 benchmark, split theo repo; **R2 xác nhận**: 0 scope có ≥ 219 task; 7 tiêu đề trích dẫn sai | run 41331567384, `data/`, mục 0.4 |
| 01/11/2026 | Bảng thiết kế: số ô chỉ ảnh hưởng theo log, θ là đòn bẩy chính (θ 0,05 → 0,02 giảm ~2× trial) | `results/design_table.json`, mục 0.4 |
| 01/11/2026 | **R14**: endpoint chính (margin > 5 điểm) có power ~5% với số của chính paper → đề xuất kiểm định ưu thế + 200–500 cặp harmful; bản nháp pre-registration | `analysis.endpoint_power`, `tests/test_analysis.py::test_paper_endpoint_is_underpowered`, `docs/preregistration.md` |
| 01/11/2026 | Harness smoke đỏ 2 lần (`--cache_level` không còn; swebench 5 cần dataset `SWE-bench/SWE-bench_Verified`) → sửa, ghim `swebench==5.0.2` | runs 41334781481, 41335112903 |
| 01/11/2026 | Abstract arXiv: SWE-Skills-Bench đã có code/dữ liệu (ControllableModel), số v2 khác v1; GSE không làm sửa code; HSE trùng split → **pilot ngoài trên 3.920 cặp thật: pairing 4,3×, SD thật của STR ≈ 0,03, R15** | `data/external/swe-skills-bench/`, `results/sskb_analysis.json`, mục 0.4 |
| 01/11/2026 | Harness smoke xanh: gold 5/5 resolved, R = 0; nhánh không skill đổi từ patch rỗng (bị harness bỏ qua) sang patch no-op để đo thật | run 41335635404, `results/harness_smoke.json` |
| 01/11/2026 | Bản nháp định vị so với XRepoSkill, GSE, HSE, SWE-Skills-Bench (từ abstract) | `docs/notes/positioning.md` |
| 01/11/2026 | Harness với patch no-op: nhánh không skill **đo thật** F = 1, R = 0 trên 5/5 task; paired trial end-to-end qua harness chính thức được kiểm chứng | run 41336208056, `results/harness_smoke.json` |
| 01/11/2026 | @thuthuy chốt **ASE 2027** + **Gemini qua Vertex AI** → lịch ngược với 3 cổng G1–G3; pipeline pilot mini-swe-agent + Vertex (`run_pilot.py`, `pilot.py`, `harness.py`), workflow dry run (miễn phí) và workflow trả phí (chạy tay, trần ngân sách), `docs/vertex_setup.md` | commit 55a6af4 |
| 01/11/2026 | **Pilot dry run xanh** lần đầu: mini-swe-agent + Docker SWE-bench + harness + log trial, model giả + skill oracle → Z = −0,667 trên 2/2 task; digest image + commit gốc ghi tự động. Còn lại chỉ là thêm credential Vertex | run 41357916901, `results/pilot/dryrun.json` |
| 01/11/2026 | Ước tính chi phí Gemini (dải 10×, cần đo token thật bằng n = 2); khai thác gold patch: 12 họ mẫu sửa lặp lại ở 5–11 repo train, 3.690 ứng viên cặp composition; đề xuất scope theo (họ skill, framework) | `results/cost_estimate.json`, `results/skill_mining.json`, run 41358048556 |
| 01/11/2026 | Pool 40 task Verified cho G1 + workflow kiểm định (gold ×2, no-op); 4 skill theo họ mẫu sửa + predicate `issue_regex` (I(x) từ nội dung issue); pilot chỉ chạy nhánh skill trên task kích hoạt và chỉ lấy task đã kiểm định | `configs/pilot_pool.json`, `configs/skills/`, `scripts/run_pilot.py` |
| 01/11/2026 | Pilot dry run đỏ ở bước publish (run 41359134995): token Actions không được sửa file workflow, mà nhánh snapshot đang được tạo lại từ `main` → `scripts/publish_snapshot.sh` chỉ thêm commit dữ liệu lên nhánh snapshot cũ, áp dụng cho cả 5 workflow | commit 6b44613 |
| 01/11/2026 | Kiểm định pool: 38/40 task dùng được; **R16**: predicate I(x) theo issue chỉ có lift 1,25–1,71; khung bài LaTeX IEEE + bảng tự sinh, biên dịch xanh | runs 41359076353, 41359285869, 41360404259 |
| 01/11/2026 | Script publish mới chạy đúng trên cả 3 nhánh snapshot; I(x) chọn trên train: lift test 1,46–1,85, recall 5–15% → regex chạm trần (R16) | runs 41360262544/579/573, 41360723396 |
| 02/11/2026 | @thuthuy có **200 USD Vertex AI** → kế hoạch 3 giai đoạn (`docs/budget_200.md`, `scripts/plan_budget.py`): Flash 3.8 đủ cho G1 kể cả không có cache (~288 lần chạy). Sửa: mã Pro → `gemini-3.1-pro-preview` (bảng LiteLLM), thêm Flash-Lite + giá cache; đăng ký giá với LiteLLM để `cost_limit` luôn hiệu lực; đối chứng nhiễu/dương; pool g1 theo kích hoạt; quy tắc G1 `g1_decision` | commit c6e72f8 |
| 02/11/2026 | Pool g1: 89 task Verified (null-guard 25, exception-handling 25, type-guard 30, validation-error 30); giai đoạn C ≈ 199 lần chạy agent (~123 USD nếu không có cache) → A+B+C vừa 180 USD | run 41371099871, `configs/pools/g1.json` |
| 02/11/2026 | Kiểm định pool g1 đỏ (run 41372092739): 1 shard lỗi (mất 22 task), và 18 task bị loại **nhầm** vì harness không tải được Docker image (`Image ... not found`, nghi Docker Hub giới hạn tải) → script đã gộp lỗi hạ tầng với "gold không giải được". Sửa: tách `infra_error`, tự chạy lại 2 lần (chờ 90 s), báo task thiếu; 8 shard, tối đa 4 chạy song song | commit 0ee9b80 |
| 02/11/2026 | Kiểm định lại pool g1 xanh: **86/89 dùng được**, 0 lỗi hạ tầng (cơ chế chạy lại gỡ đúng 18 task bị loại nhầm), 3 task Django loại thật (no-op không sạch). Giai đoạn C = 193 lần chạy ≈ 39–120 USD | run 41375243272, `results/pool_validation/g1/summary.json` |
| 02/11/2026 | Kiểm định lại pool default bằng script mới: vẫn 38/40, 0 lỗi hạ tầng → `psf__requests-1921` và `pylint-dev__pylint-8898` bị loại vì lỗi thật (có report), không phải do tải image | run 41379385559 |
| 02/11/2026 | **Vertex AI chạy được** (key `gatekeeper-pilot`): 3 model OK ở `global`; Flash mặc định tốn ~11× token output vì thinking → `reasoning_effort: low`; thêm `mcp` cho tool-calling của LiteLLM. Bài thử 0,26 USD: 0,13 USD/lần chạy 30 bước, cache 68–80%; cả 2 nhánh chạm trần 30 bước → dùng 60 bước | `results/pilot/smoke-flash-1.json` |
| 02/11/2026 | **Giai đoạn A** (2,12 USD): Flash-Lite 0,022 USD/lần, Flash 0,24 USD/lần; cả hai giải 3/4 task, gợi ý file chưa giúp (trần) → **chọn Flash-Lite**, G1 (B + C) chỉ ~10 USD. Lượt A1 đầu không hợp lệ (container không khởi động, bị tính là thất bại) → pipeline tải image trước và loại lỗi hạ tầng khỏi phép ghép cặp | `results/pilot/g1-a-lite2.json`, `results/pilot/g1-a-flash.json`, `results/pilot/invalid/` |
| 02/11/2026 | **Giai đoạn B** (3,95 USD, 38 task): quy tắc G1 báo **STOP** đúng như thiết kế: đối chứng nhiễu Z = −0,104, CI 90% [−0,19; −0,02] (đối chứng dương đạt: Z = −0,25 trên 23 task nhánh gốc thất bại). Rà soát tìm ra **lỗi seed**: Vertex coi `seed=0` là không đặt seed → nhánh gốc lấy mẫu ngẫu nhiên, đối chứng nhiễu (seed 1) tất định. Sửa: seed từ 1, `arm_config` từ chối seed 0; trần tích luỹ không đếm file phân tích; file gộp ghi đúng `solved`. Lượt B cách ly, chạy lại `g1-b2` | `results/pilot/invalid/g1-b/`, `docs/audit_pilot.md` A14–A16, `test_seed_zero_is_rejected` |
| 02/11/2026 | Chạy lại B (`g1-b2`, seed đã sửa): xong 18/38 task (lô p00–p04), tổng pilot 8,41 USD; tiến trình bị dừng ở giới hạn 2 giờ của phiên khi đang chạy lô p05 (chi phí lô dở chưa ghi, tối đa ~1 USD). Docker Hub trả 429 nhiều lần, driver tự chờ đúng như thiết kế. **Chạy tiếp** bằng cùng lệnh (bỏ qua task đã xong) | `results/pilot/g1-b2-p00..p04.json` |
| 02/11/2026 | **`g1-b2` xong** (38 task, 3,94 USD, tổng pilot 10,43 USD): đối chứng nhiễu Z = −0,02, CI chứa 0 ✅ (lỗi seed đã hết); đối chứng dương Z = −0,066 trên 20 task nhánh gốc thất bại, CI [−0,13; +0,0002] ❌ → **STOP, không chạy C**. Gợi ý tên file không giúp Flash-Lite; quy tắc đối chứng dương bị thiên lệch hồi quy về trung bình (A19). Chờ @thuthuy chọn hướng | `results/pilot/g1-b2.json`, `results/g1_decision.json`, `docs/budget_200.md` |
| 02/11/2026 | Rà soát lý thuyết + lỗi sau B (miễn phí): công thức loss/Z/CI đúng (CI bootstrap khớp CI t); hai lần STOP do **thiết kế kiểm tra** (D1 hồi quy về trung bình, D2 đối chứng dương yếu, D3 báo động giả 10%), không phải lỗi tính toán; cấu hình giống hệt vẫn lật 8/37 task (seed không làm quỹ đạo tất định); nhiễu SD 0,36/cặp → C 1 seed thiếu power. Chờ @thuthuy quyết | `docs/review_pilot_b.md` |

---

## Nguồn

Tài liệu gốc: FSE-2027-13 paper, reading list, summary (`docs/`).

- [GSE, arXiv 2608.06153](https://arxiv.org/pdf/2608.06153)
- [XRepoSkill, arXiv 2609.36807](https://arxiv.org/html/2609.36807v1)
- [MemGovern, arXiv 2601.06789](https://arxiv.org/html/2601.06789v2)
- [MemCoder, arXiv 2603.13258](https://arxiv.org/html/2603.13258v1)
- [Methods for Formal Verification of Agent Skills, arXiv 2605.23951](https://arxiv.org/html/2605.23951)
- [SWE-Skills-Bench, arXiv 2603.15401](https://arxiv.org/html/2603.15401v1)
- [gskill / GEPA](https://gepa-ai.github.io/gepa/blog/2026/02/18/automatically-learning-skills-for-coding-agents/)
- [ASI, arXiv 2504.06821](https://arxiv.org/html/2504.06821v2)
- [CODESKILL, arXiv 2605.25430](https://arxiv.org/pdf/2605.25430) (không có code)
- [Hierarchical Skill Evolution, arXiv 2610.35616](https://arxiv.org/abs/2610.35616) (không có code)
- [CooperBench, arXiv 2601.13295](https://arxiv.org/html/2601.13295) (chỉ tham khảo)
- Benchmark chuẩn: [SWE-bench, ICLR 2024](https://arxiv.org/abs/2310.06770), [SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/), [SWE-Gym](https://arxiv.org/abs/2412.21139), [SWE-bench-Live](https://arxiv.org/abs/2505.23419), [SWE-smith](https://arxiv.org/abs/2504.21798), [BugsInPy](https://github.com/soarsmu/BugsInPy)
- Hạn FSE 2027: [PaperPilot](https://www.getpaperpilot.com/deadlines/fse-2027.html), [BERI](https://www.beri.net/events/fse-2027), trang chính thức [conf.researchr.org](https://conf.researchr.org/track/fse-2027/fse-2027-papers)
