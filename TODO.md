# Gatekeeper (FSE-2027-13) – Review & Todo list (bản 2)

Bản 1: 01/11/2026 · @thuthuy · Bản 2 (review lại): 01/11/2026 · Trạng thái: **đã duyệt** (01/11/2026)

> **Đây là kim chỉ nam của dự án.** Mỗi lần xong một việc: tick `[x]`, ghi ngày + link commit/log vào cột "Bằng chứng" của mục [Nhật ký tiến độ](#nhật-ký-tiến-độ), cập nhật `report/index.html`. Việc nào chưa có bằng chứng (file, log CI, số đo) thì chưa được tick.

Ký hiệu người làm: 🤖 = làm được ngay trong repo + GitHub Actions · 👤 = bạn phải tự làm (đọc, họp, quyết định) · 💰 = tốn tiền (API, GPU, máy CPU).

---

## 0. Kết quả review bản 1 (đọc trước)

Bản 1 nhìn chung **đúng và kỹ**: mình tính lại mọi số trong bảng kiểm tra, các lỗi toán, mô phỏng và link GitHub. Phần lớn đúng. Nhưng có **1 vấn đề chặn**, 7 chỗ sai/thiếu cần sửa, và todo list thiếu phần hạ tầng code.

### 0.1 Vấn đề chặn: deadline FSE 2027 đã qua

- Hạn nộp Research Track FSE 2027 là **02/10/2026** (theo PaperPilot và BERI; trang chính thức conf.researchr.org không truy cập được từ máy này, bạn tự mở để xác nhận). Hôm nay là 01/11/2026, nên **không nộp FSE 2027 được nữa**.
- Ước lượng thời gian cho người mới làm hết Phase 0–8: **9–12 tháng** (xem cột thời gian ở mục 6). Mục tiêu thực tế: **FSE 2028** (hạn có thể vào khoảng 09–10/2027) hoặc ASE 2027 / ICSE 2028 nếu tiến độ nhanh. Ngày cụ thể phải tra trên trang chính thức.
- Giữ mã "FSE-2027-13" làm ID dự án, nhưng đổi venue mục tiêu trong README và paper.

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
| Link GitHub còn sống | `git ls-remote` ngày 01/11/2026 | MemGovern, XRepoSkill, gepa, agent-skill-induction, SWE-smith, mini-swe-agent, CooperBench, confseq, ltt: **còn**. SWE-Skills-Bench: **không truy cập được** (đúng như bản 1 ghi) |
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
- **Hiệu ứng thật nhỏ.** SWE-Skills-Bench: ~80% trong 49 skill không đổi pass rate, trung bình +1,2%. Skill có STR ≈ −θ gần như **không bao giờ** được admit. "Clean reuse 84,3%" rất khó đạt.
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

**Lưu ý:** SWE-Skills-Bench (`GeniusHTX/SWE-Skills-Bench`) vẫn không truy cập được → chỉ trích dẫn. Hầu hết paper skill 2026 là preprint: ghi rõ phiên bản arXiv và commit code.

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

**LLM chạy ở đâu:** API model (ghi model ID + ngày) và model open-weight trên vLLM (ghi digest weight). Code + test chạy trong Docker trên máy CPU. Harness: **một harness chung** (R6).

**GitHub Actions làm được gì và không làm được gì:** CI chạy được unit test, mô phỏng e-process, test phản ví dụ Theorem 7, kiểm tra sổ α, sinh report HTML, và tối đa 1–2 task SWE-bench nhỏ (runner miễn phí chỉ có ~14 GB đĩa, giới hạn 6 giờ). CI **không** chạy được agent LLM hay hàng nghìn trial: phần đó chạy trên máy riêng, kết quả (JSON) commit vào `results/` để CI phân tích và vẽ.

**Bốn lớp kiểm chứng nhãn:** (1) nhãn biết trước theo cách dựng (regime C, 46 cặp composition) + test tái hiện; (2) nhóm đối chứng: skill no-op → neutral, skill cài bug → harmful; (3) mutation score + loại test flaky; (4) 2 người gán nhãn 50–100 cặp, Cohen's kappa ≥ 0,7.

**Threats to Validity bắt buộc ghi:** "safe" chỉ nghĩa là không làm test suite tệ hơn, với xác suất sai ≤ α, trong scope đã khai báo.

---

## 7. Todo list chi tiết

Mỗi việc có tiêu chí xong sau dấu →. Thời gian là ước lượng cho người mới, làm bán thời gian ~20 giờ/tuần.

| Phase | Nội dung | Thời gian | Phụ thuộc |
| --- | --- | --- | --- |
| H | Hạ tầng repo, CI, report | 1 tuần | — |
| 0 | Học nền | 4–6 tuần | — |
| 1 | Sửa lý thuyết & paper | 3–4 tuần | 0 |
| 5a | Lõi Gatekeeper (không cần LLM) | 3–4 tuần | 1 (song song được) |
| 2 | Môi trường & tái hiện baseline | 4–6 tuần 💰 | 0 |
| 3 | Pilot & go/no-go | 3–4 tuần 💰 | 2, 5a |
| 4 | Benchmark SkillShift-SE | 6–8 tuần 💰 | 3 |
| 5b | Gatekeeper đầy đủ | 4 tuần | 3 (song song 4) |
| 6 | Chạy thí nghiệm | 8–12 tuần 💰 | 4, 5b |
| 7 | Phân tích & viết | 4–6 tuần | 6 |
| 8 | Artifact & nộp | 2 tuần | 7 |

### Phase H – Hạ tầng repo, CI, report (mới)

- [ ] 🤖 README: giới thiệu đề tài, cấu trúc repo, cách chạy, link tài liệu → README.md trên main
- [ ] 🤖 Đưa 3 PDF (paper, reading list, summary) vào `docs/` → commit trên main
- [ ] 🤖 Đưa TODO.md này lên main → là nguồn sự thật duy nhất về tiến độ
- [ ] 🤖 Khung Python package `gatekeeper/` + `pyproject.toml` (Python 3.11) + `tests/`
- [ ] 🤖 GitHub Actions: lint (ruff) + pytest + mô phỏng nhanh + build report → workflow xanh
- [ ] 🤖 Report HTML `report/index.html` (lý thuyết → thực nghiệm), tự sinh lại từ kết quả trong CI → mở được từ main
- [ ] 🤖 Job CI đối chiếu với `confseq` (cài `libboost-dev`) → chạy được hoặc ghi rõ lý do lỗi
- [ ] 👤 Xin người hướng dẫn PLAN.md, REVIEWS.md, Portfolio Overview và 3 smoke test → đưa vào `docs/`
- [ ] 👤 Tra hạn nộp chính thức, chốt venue mục tiêu (mục 0.1) → ghi vào README

### Phase 0 – Học nền

**Đọc paper (đúng thứ tự)**

- [ ] 👤 XRepoSkill → 1 trang ghi chú: tìm rule, verify (Mantel–Haenszel), chọn rule cho issue
- [ ] 👤 GSE → replay verification hoạt động thế nào, vì sao không làm baseline được
- [ ] 👤 SWE-Skills-Bench → cách đo paired có/không skill và tỉ lệ skill gây hại
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
- [ ] 👤💰 Chạy SWE-bench harness với patch gốc trên 5 task Verified → 5/5 pass (máy riêng; CI chỉ chạy 1 task)
- [ ] 👤💰 Chạy mini-swe-agent giải 5 task bằng 1 model API → có log và kết quả
- [ ] 🤖 Viết e-process (~30 dòng) + test → khớp với `confseq` trên dữ liệu giả (sai khác < 1e-6 về log E)
- [ ] 🤖 Mô phỏng 1.000 lần với STR = −θ → tỉ lệ admit sai ≤ α, chạy trong CI
- [ ] 👤 1 trang "Gatekeeper khác XRepoSkill và GSE ở đâu" → gửi người hướng dẫn góp ý

### Phase 1 – Sửa lý thuyết & paper

**Theorem 7**

- [ ] 👤 Phát biểu lại: cận chặt 1−θ; định nghĩa thứ tự ghép
- [ ] 👤 Chứng minh với ℓ(x,∅) = θ, ℓ(π1) = ℓ(π2) = 0, ℓ(π1∘π2) = 1, thêm cặp thứ hai ℓ(π1∘π2) = 0 để bác bỏ mọi g
- [ ] 👤 Thay cơ chế bằng "retry wrapper gọi hàm async không await"
- [ ] 🤖 Test Python: S1 riêng pass, S2 riêng pass, S1∘S2 fail im lặng → chạy trong CI

**Theorem 4**

- [ ] 👤 Union bound trên mọi ô (S,s), mọi composite, và re-admission
- [ ] 👤 Đổi ξ_s → 2ξ_s
- [ ] 👤 Alpha-spending α·6/(π²k²) cho composite và re-admission
- [ ] 👤 Viết tường minh e-process, khoảng λ_i, H0
- [ ] 👤 Ghi điều kiện 2ξ_s ≤ θ
- [ ] 👤 Cách ước lượng ξ_s, hoặc báo cáo bound theo nhiều giá trị ξ_s
- [ ] 👤 Chọn: số task ≥ số trial, hay P_s = pool (R2)
- [ ] 👤 Chốt FWER hay FDR (R8)

**Định nghĩa & metric**

- [ ] 👤 Chuẩn hóa loss về [0,1]
- [ ] 👤 P_s = phân phối task mà I(x) đúng
- [ ] 👤 Nhãn 3 lớp harmful / neutral / beneficial theo STR trên scoring suite (R3)
- [ ] 👤 Harmful acceptance = số cặp harmful được admit / số cặp harmful
- [ ] 👤 Clean-reuse coverage = beneficial được admit / beneficial; so "at matched coverage" bằng đường harm–coverage
- [ ] 👤 d̄ tính trong từng scope hay toàn library

**Prop. 9**

- [ ] 👤 Mô hình phương sai; tỉ lệ 1 + 2σ_T²/σ_S²
- [ ] 👤 Bỏ câu "net win 1,55×" và "3,1×"

**Chỉnh paper và summary**

- [ ] 👤 Baseline quyết định → XRepoSkill ở abstract, intro, §3.1, §9.2, go/no-go, summary
- [ ] 👤 GSE, MemCoder, enclawed → related work
- [ ] 👤 Harness → một harness chung (R6); sửa "10 systems" (R10)
- [ ] 👤 Figure 1: cần test fault-injection
- [ ] 👤 Sửa câu CI "vượt margin 5 điểm"
- [ ] 👤 Nhờ 1 người biết thống kê đọc chứng minh → sửa hết góp ý

### Phase 5a – Lõi Gatekeeper (chuyển lên sớm, không cần LLM)

- [ ] 🤖 `eprocess.py`: betting e-process trong log-space, λ predictable, có test
- [ ] 🤖 `alpha_ledger.py`: sổ phân bổ α (ô, composite, re-admission) → test tổng ≤ α
- [ ] 🤖 `skill.py`: schema skill ⟨π, D, I, P, K⟩ (JSON/YAML) + validate
- [ ] 🤖 `scope.py`: scope screen (so D, chạy I) → OutOfScope
- [ ] 🤖 `footprint.py`: giao footprint → hàng đợi composite
- [ ] 🤖 `admission.py`: Algorithm 1 với budget, dừng sớm; trial runner là interface (giả lập trong test)
- [ ] 🤖 Mô phỏng: skill có STR biết trước → bảng % admit và số trial, tự cập nhật trong report
- [ ] 🤖 Coverage ≥ 80%

### Phase 2 – Môi trường & tái hiện baseline

**Hạ tầng LLM**

- [ ] 👤💰 Chọn model API → ghi model ID chính xác
- [ ] 👤 Chọn model open-weight → ghi digest weight
- [ ] 👤💰 Dựng vLLM trên GPU thuê/cluster trường → gọi thử thành công từ harness
- [ ] 👤 Cố định tham số sampling và ghi vào config

**Hạ tầng chạy trial**

- [ ] 👤 Tách máy: GPU chạy LLM, CPU chạy container test
- [ ] 🤖 Pin Docker image bằng digest
- [ ] 🤖 Script 1 trial: snapshot → áp/không áp skill → agent → test → JSON (cài interface của 5a)
- [ ] 🤖 Kiểm tra hai nhánh cùng task, seed, snapshot
- [ ] 🤖 Log model ID, số token, thời gian, chi phí mỗi run
- [ ] 👤💰 Chạy cùng 1 task 5 lần → mức dao động của agent
- [ ] 👤 Ước chi phí 1 cặp trial (token + GPU + CPU)

**Baseline có code**

- [ ] 👤 Chốt harness chung (R6) → ghi commit
- [ ] 👤 Clone XRepoSkill, ghi commit, chạy unit test → pass
- [ ] 👤💰 Chạy XRepoSkill trên đúng tập task của paper (hoặc tập con có so từng task) → số paper nằm trong CI 95% (R5)
- [ ] 🤖 Nếu cần, adapter chuyển format skill (không sửa thuật toán)
- [ ] 👤💰 MemGovern trên tập task của paper → cùng tiêu chí R5
- [ ] 👤💰 gskill cho 1 repo → có SKILL.md và kết quả holdout
- [ ] 👤 (Tuỳ chọn) Đánh giá công port ASI → quyết định có/không
- [ ] 👤 Email hỏi tác giả GSE có public code không

**Điều kiện đối chứng**

- [ ] 🤖 B1 No skills
- [ ] 🤖 B2 Unrestricted reuse
- [ ] 🤖 B8 Always-retest
- [ ] 🤖 B9 Budget-matched retries (cùng ngân sách token + CPU)
- [ ] 🤖 README cho mỗi baseline: commit, lệnh chạy, khác biệt so với bản gốc

### Phase 3 – Pilot & go/no-go

**Chuẩn bị**

- [ ] 👤 Đặt trần chi phí pilot (vd ≤ 1.500 USD)
- [ ] 👤 Chọn 2 repo (1 cùng framework, 1 khác framework)
- [ ] 👤 Chọn 10 skill, tạo 20–30 cặp skill/context
- [ ] 👤 Tách pool task admission và pool task chấm (R3)
- [ ] 👤 Gán nhãn 3 lớp cho cặp pilot theo quy trình kiểm chứng nhãn

**Đo đạc**

- [ ] 👤💰 ≥ 30 cặp trial cho mỗi cặp skill/context
- [ ] 🤖 Ước lượng σ_S², σ_T² và hiệu ứng thật trung bình
- [ ] 🤖 Số trial cần mỗi ô với α đã phân bổ (Prop. 9 đã sửa + mô phỏng)
- [ ] 🤖 Đếm số task khác nhau có được mỗi scope → đủ cho số trial không (R2)
- [ ] 🤖 Power analysis: cần bao nhiêu cặp harmful để phát hiện margin 5 điểm với power 80% (R4)
- [ ] 👤 Ước lượng lại tổng chi phí
- [ ] 👤💰 Chạy XRepoSkill và Gatekeeper trên cùng cặp pilot; margin + CI (chỉ tham khảo)

**Quyết định**

- [ ] 👤 Báo cáo pilot 2 trang (số đo, chi phí, rủi ro) → cũng đưa vào report HTML
- [ ] 👤 Go/no-go theo khả thi (R4): đủ task, chi phí trong ngân sách, power ≥ 80% → làm tiếp; thiếu một điều → thu hẹp (cross-repo + adversarial, θ lớn hơn); thiếu nhiều → gộp vào FSE-2027-01
- [ ] 👤 Họp người hướng dẫn → ghi quyết định và lý do
- [ ] 👤 Cập nhật kích thước benchmark, θ, α

### Phase 4 – SkillShift-SE: giao thức đánh giá trên benchmark chuẩn

**Chọn dữ liệu (chỉ từ bảng 6.1)**

- [ ] 🤖 Tải metadata SWE-bench, SWE-bench Verified, SWE-Gym, SWE-bench-Live → bảng repo × số task × version, commit vào `data/`
- [ ] 👤 Chọn ≥ 25 repo từ các benchmark này (train: SWE-Gym; test: SWE-bench + SWE-bench-Live) → ghi benchmark, repo, commit
- [ ] 👤 Chọn 4 dòng version dependency có trong các task đã chọn
- [ ] 🤖 Chia train/test theo repo → lưu file split (danh sách instance_id)
- [ ] 👤 Khai báo scope family S trước khi chạy

**Tạo skill (treatment)**

- [ ] 👤💰 Chạy agent trên task SWE-Gym (train split) → trajectory thành công
- [ ] 🤖 Induce skill thành edit program (AST rewrite + shell step)
- [ ] 🤖 Ghi D, I, P, K cho từng skill
- [ ] 🤖 Kiểm tra không skill nào chứa thông tin repo test
- [ ] 👤 Tạo 52 skill outdated nhưng vô hại

**Task target (không tự sinh)**

- [ ] 🤖 Lấy task target từ SWE-bench / SWE-bench-Live theo scope, ưu tiên task sau ngày cutoff của model
- [ ] 🤖 Kiểm tra mỗi task chạy được bằng harness chính thức (gold patch pass, không flaky)
- [ ] 🤖 Đếm task mỗi scope → đủ cho số trial ở Phase 3; thiếu thì bổ sung từ tập SWE-smith đã công bố hoặc gộp scope
- [ ] 👤 Chạy kiểm tra độ bền trên BugsInPy (tuỳ chọn)

**Test hành vi (phân tích phụ)**

- [ ] 👤 Test fault-injection cho từng behavioural class, để riêng trong `supplementary_tests/`
- [ ] 🤖 Mutation score trước/sau khi thêm test

**Regime & cặp composition**

- [ ] 👤 Regime A: cùng repo SWE-bench, khác version
- [ ] 👤 Regime B: khác repo (SWE-Gym → SWE-bench / SWE-bench-Live), cùng framework
- [ ] 👤 Regime C: skill adversarial (hợp lệ về quyền nhưng cài lỗi chức năng) áp lên task SWE-bench
- [ ] 👤 46 cặp composition: ghép các task SWE-bench cùng sửa một file/hàm, theo 4 cơ chế (exception type, ordering, resource lifetime, transaction scope)

**Kiểm chứng nhãn**

- [ ] 👤 Test tái hiện lỗi cho mọi skill harmful dựng sẵn
- [ ] 🤖 Nhóm đối chứng no-op / bug cài sẵn → tỉ lệ sai của pipeline gán nhãn
- [ ] 👤💰 Chạy baseline nhiều lần → loại test flaky
- [ ] 👤 2 người gán nhãn 50–100 cặp → Cohen's kappa ≥ 0,7
- [ ] 🤖 Cặp không ổn định qua 3 lần chạy → "uncertain", báo cáo riêng
- [ ] 🤖 Scoring suite độc lập ngoài sandbox admission

**Đóng băng**

- [ ] 👤 Pre-register: endpoint, θ, α, phân bổ α, budget, baseline, harness, FWER/FDR
- [ ] 🤖 Đóng băng benchmark v1 (hash trong repo), không sửa sau khi bắt đầu Phase 6

### Phase 5b – Gatekeeper đầy đủ

- [ ] 🤖 D: hash lockfile, interpreter, version framework, behavioural class
- [ ] 🤖 I: predicate thực thi được trên repo target
- [ ] 🤖 P: postcondition kèm context đã quan sát
- [ ] 🤖 K: phân tích read/write trên AST + symbol nhắc trong P
- [ ] 🤖 Nối paired trial runner thật (Phase 2) vào Algorithm 1
- [ ] 🤖 Hàm loss chuẩn hóa về [0,1]
- [ ] 🤖 Phân bổ budget theo độ bất định
- [ ] 🤖 Routing model (gradient boosting) chỉ sắp thứ tự ô
- [ ] 🤖 Retirement khi fingerprint đổi + alpha-spending khi re-admit
- [ ] 🤖 Capability verdict tách riêng khỏi quyết định chức năng
- [ ] 🤖 Xuất certificate: scope, α, ξ_s, số trial, kết quả
- [ ] 🤖 Test tích hợp trên 3 skill có đáp án biết trước
- [ ] 👤💰 Đo chi phí 1 quyết định admission so với 1 lần full validation

### Phase 6 – Chạy thí nghiệm

**Chuẩn bị**

- [ ] 🤖 Script chạy hàng loạt, chạy tiếp được khi lỗi giữa chừng
- [ ] 👤💰 Chạy thử toàn pipeline trên 5 cặp → không lỗi
- [ ] 🤖 Bảng theo dõi chi phí vs ngân sách, cập nhật sau mỗi đợt, hiện trong report

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

- [ ] 🤖 Cluster bootstrap theo repo cho mọi CI
- [ ] 🤖 BH cho so sánh phụ
- [ ] 🤖 Sweep trọng số regression penalty (0,2–2,0)
- [ ] 🤖 Script tự sinh mọi bảng và hình từ kết quả thô (chạy trong CI)
- [ ] 👤 Thay toàn bộ số projected bằng số đo; bỏ banner "Draft status"
- [ ] 👤 Phân tích định tính các ca admit sai
- [ ] 👤 Related work và baseline theo mục 5
- [ ] 👤 Threats to Validity
- [ ] 👤 Kiểm tra từng trích dẫn trên arXiv/DBLP; thay "GSE Authors"… bằng tên thật
- [ ] 👤 2 người đọc nháp → sửa hết góp ý
- [ ] 👤 Giới hạn trang và template ACM của venue đã chốt

### Phase 8 – Artifact & nộp

- [ ] 🤖 Đóng gói artifact: code, pipeline benchmark, baseline, script phân tích, kết quả từng task
- [ ] 🤖 Ghi digest, commit, model ID + ngày, seed, cấu hình phần cứng
- [ ] 🤖 Ẩn danh: xóa tên, email, metadata
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
