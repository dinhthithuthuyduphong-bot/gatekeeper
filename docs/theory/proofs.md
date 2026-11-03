# Chứng minh các kết quả lý thuyết của Gatekeeper từ kết quả đã công bố

Tài liệu này chứng minh lại các định lý đã sửa trong `docs/theory/corrections.md`. **Mỗi bước thuộc đúng một trong ba loại:**
- **[ĐN]**: suy trực tiếp từ định nghĩa;
- **[TĐ]**: suy từ tiên đề xác suất (Kolmogorov) bằng một dòng đại số;
- **[CB]**: dùng một kết quả đã công bố. Câu gốc được lưu ở nhánh `sources-snapshots` (cấu hình `configs/sources.json`), ghi kèm id nguồn và sha256.

Không bước nào dựa vào trí nhớ. Mục nào chưa có câu gốc được đánh dấu **⏳** và chưa được dùng làm kết luận.

Ký hiệu như `docs/glossary.md` §7: Z = ℓ(x, π) − ℓ(x, ∅) ∈ [−1, 1]; STR_P = E_{x∼P}[Z]; θ ∈ [0, 1); α ∈ (0, 1).

---

## 0. Giả định về cách lấy mẫu (phải nêu trong paper)

**Giả định SP (superpopulation).**
- Các task của một scope là mẫu i.i.d. từ một phân phối P_s, và mỗi task được dùng cho **đúng một** trial, theo một thứ tự ngẫu nhiên độc lập với dữ liệu.
- Khi đó dãy task dùng cho các trial là i.i.d. theo P_s: một hoán vị cố định trước của một dãy i.i.d. vẫn là dãy i.i.d. [TĐ].
- Vì vậy E[Z_i | 𝓕_{i−1}] = STR_{P_s}. Đây chính là Giả thiết 3′ của Theorem 4′.

**Nguồn cho cách mô hình hóa:** Miller (2024, `miller_2024`) phân tích điểm của eval với câu hỏi được rút từ một **super-population**. Câu gốc: "The variance of the conditional mean, Var(x), is a property of the super-population". ⏳ Đang lấy thêm câu định nghĩa bằng từ khóa mới (A64).

**Điều SP không bảo đảm:**
- Nếu P_s được hiểu là **chính pool hữu hạn** (không phải superpopulation), rút không hoàn lại làm E[Z_i | 𝓕_{i−1}] bằng trung bình của phần còn lại của pool, không bằng STR. Khi đó e-process ở §2 không còn chắc là supermartingale.
- Trường hợp này cần cách cá cược riêng cho rút không hoàn lại (Waudby-Smith & Ramdas có công trình riêng về chủ đề này; ⏳ chưa lấy bản gốc, chưa dùng), hoặc rút có hoàn lại (lựa chọn (b) ở `corrections.md` §1.2).
- **Hệ quả cho thí nghiệm:** RQ1 (`scripts/rq1_mini.py`) dùng mỗi task một lần theo thứ tự ngẫu nhiên, nên tính hợp lệ của nó là **theo SP**. Mô phỏng kiểm định trong `scripts/verify_methods.py` sinh trial i.i.d., tức đúng giả định SP.

---

## 1. Bổ đề E (e-process là supermartingale không âm)

**Phát biểu.**
- Cho H₀: E[Z_i | 𝓕_{i−1}] ≥ −θ với mọi i. Lấy λ_i là 𝓕_{i−1}-đo được (dự báo được) với 0 ≤ λ_i ≤ c/(1+θ), 0 < c < 1.
- Đặt E_0 = 1 và E_n = ∏_{i≤n} (1 + λ_i(−θ − Z_i)).
- Khi đó (E_n) là supermartingale không âm đối với (𝓕_n), với E_0 = 1.

**Chứng minh.**
1. **Không âm** [ĐN]: Z_i ≤ 1 nên −θ − Z_i ≥ −(1 + θ), do đó 1 + λ_i(−θ − Z_i) ≥ 1 − c > 0.
2. **Kỳ vọng có điều kiện** [TĐ, tính tuyến tính và lấy ra nhân tử đo được]: E[E_n | 𝓕_{n−1}] = E_{n−1} · (1 + λ_n(−θ − E[Z_n | 𝓕_{n−1}])) ≤ E_{n−1}, vì λ_n ≥ 0 và E[Z_n | 𝓕_{n−1}] ≥ −θ dưới H₀. ∎

**Đối chiếu với nguồn đã công bố:** đây là "capital process" của Waudby-Smith & Ramdas (`waudby_smith_ramdas`, sha `d783b120…`), áp cho hướng một phía.

---

## 2. Ville

**Phát biểu đã công bố** (Ramdas, Grünwald, Vovk & Shafer, *Statistical Science*; `ville_inequality`, sha `19dfc4e9…`):

> "Ville also showed that if M is a test martingale for P, then for any α ≥ 1, P(sup_t M_t ≥ α) ≤ 1/α."

Trong câu gốc, α là ngưỡng ≥ 1. Với ngưỡng 1/α của ta: Pr[∃n : E_n ≥ 1/α] ≤ α.

⏳ **Câu gốc hiện lưu nói về test martingale.** Phát biểu cho **supermartingale** không âm (trường hợp của Bổ đề E, khi STR > −θ thật sự) đang được lấy thêm bằng từ khóa mới (A64). Waudby-Smith & Ramdas viết "applying Ville's maximal inequality [81] to a test (super)martingale" (đã lưu), nên bất đẳng thức được dùng cho cả supermartingale. Tôi vẫn chờ câu phát biểu đầy đủ trước khi coi bước này là xong.

**Hệ quả** (dùng Bổ đề E và Ville): quy tắc "admit khi E_n ≥ 1/α" có Pr[admit] ≤ α dưới H₀, **với mọi thời điểm dừng**, kể cả dừng khi hết ngân sách.

---

## 3. Theorem 4′ (FWER khi triển khai lệch phân phối)

**Giả thiết.**
- (i) Giả định SP, hoặc lựa chọn (b), cho từng bài toán admission j: một ô (S, s), một composite, hoặc một lần re-admit.
- (ii) Ngân sách α_j **cố định trước** theo chỉ số j (ô thứ j, composite thứ k, lần re-admit thứ k), với Σ_j α_j ≤ α.
- (iii) e-process của j dùng dữ liệu thỏa (i) đối với filtration chung. Nếu composite thứ k được chọn dựa trên dữ liệu trước đó, dữ liệu dùng để admit nó phải được thu **sau** khi chọn.
- (iv) Triển khai lấy context từ Q_s với TV(Q_s, P_s) ≤ ξ_s.

**Kết luận:** Pr[∃ j được admit mà STR_{Q_s} > −θ + 2ξ_s] ≤ α.

**Chứng minh.**
1. **Từng bài toán** [CB: Bổ đề E + Ville]: nếu STR_{P_s} > −θ thì H₀ của j đúng, nên Pr[admit j] ≤ α_j.
2. **Hợp các biến cố** [TĐ: tính cộng tính đếm được của độ đo xác suất cho ra Pr(∪A_j) ≤ Σ Pr(A_j), bất đẳng thức Boole]: Pr[∃ j admit với STR_{P_s} > −θ] ≤ Σ_j α_j ≤ α. Không cần các j độc lập. Holm (1979) dùng đúng bất đẳng thức này và gọi nó là "the Boole inequality". ⏳ Câu gốc của Holm đang được tải lại từ bản gốc hoặc từ Shaffer 1986 (A64).
3. **Đổi phân phối** [CB]: với f(x) = E[Z | x] ∈ [−1, 1] (khoảng có độ rộng 2) thì |E_Q f − E_P f| ≤ 2 · TV(Q, P). Đây là hệ quả của đặc trưng ‖μ − ν‖_TV = ½ sup_{|f|≤1} |E_μ f − E_ν f| (Levin & Peres 2017, ch. 4; `levin_peres_2017`, ⏳ đang tải). Trên biến cố bù của bước 2, mọi j được admit có STR_{P_s} ≤ −θ, nên STR_{Q_s} ≤ −θ + 2ξ_s. ∎

**Hệ số 2 là chặt** [ĐN]: chuyển khối lượng ξ từ điểm có Z = −1 sang điểm có Z = +1 cho TV = ξ, và kỳ vọng tăng đúng 2ξ (`tests/test_theory.py::test_tv_shift_factor_two_is_tight`).

**Dãy α_k = α_comp · 6/(π²k²):** tổng bằng α_comp nhờ Σ 1/k² = π²/6 (bài toán Basel, Euler). Có thể thay bằng α_k = α_comp · 2^{−k}, tổng bằng α_comp theo công thức chuỗi hình học [TĐ], để không cần dẫn nguồn. Hai cách cho cùng bảo đảm.

---

## 4. Proposition 9 (lợi ích của ghép cặp), chứng minh **không cần mô hình cộng**

**Phát biểu.**
- Gọi W = ℓ(x, π), O = ℓ(x, ∅) trên cùng task x. Thiết kế không ghép cặp dùng hai task độc lập x, x′ rút từ cùng P_s. Mỗi mẫu của cả hai thiết kế đều tốn 2 lần chạy.
- Tỉ lệ phương sai: Var(W − O′) / Var(W − O) = 1 + 2 Cov(W, O) / Var(W − O).

**Chứng minh** [TĐ]:
- Var(W − O′) = Var W + Var O, vì x và x′ độc lập.
- Var(W − O) = Var W + Var O − 2 Cov(W, O).
- Chia hai đẳng thức cho nhau. ∎

**So với `corrections.md` §6:**
- Không cần giả định ℓ = μ + T(x) + e. Tỉ lệ đúng với mọi phân phối.
- Mô hình cộng chỉ là một cách diễn giải: Cov(W, O) = σ_T² khi sai số của hai nhánh không tương quan.
- `gatekeeper.analysis.variance_components` tính đúng 1 + 2 Cov(W, O) / Var(W − O). Kết quả 4,307 trên SWE-Skills-Bench là **tỉ lệ phương sai đo được**, không phụ thuộc mô hình.

**Từ tỉ lệ phương sai sang tỉ lệ cỡ mẫu** [CB]:
- Waudby-Smith & Ramdas (đã lưu, phương trình (17)): với i.i.d., **nửa độ rộng** (phần ±) của khoảng tin cậy empirical Bernstein cỡ n cố định [PrPl-EB-CI] thỏa √n · (nửa độ rộng) → σ √(2 log(2/α)) hầu chắc chắn. Nửa độ rộng tỉ lệ với σ/√n.
- Đây là kết quả **tiệm cận, cho n cố định**. Với e-process tuần tự, độ rộng có thêm hệ số cỡ log log n (cùng tài liệu, mục E.2.1, ⏳ chưa trích). Vì vậy các công thức cỡ mẫu dưới đây là xấp xỉ bậc một, không phải đẳng thức.
- Do đó, để đạt cùng độ rộng, số mẫu tỉ lệ với phương sai, và tỉ lệ cỡ mẫu bằng tỉ lệ phương sai ở trên (tiệm cận).

**Sửa thêm một chỗ trong `corrections.md` §6:**
- Công thức n_paired ≈ c · σ_S² · log(1/α) / θ² viết **sai mẫu số**.
- Theo (17), để cận trên của CS nằm dưới −θ khi STR thật là μ < −θ, cần độ rộng một phía ≤ (−θ − μ). Vậy, xấp xỉ bậc một, n ≈ 2σ_S² log(1/α) / (|μ| − θ)², tức tỉ lệ nghịch với **bình phương khoảng cách** |STR| − θ, không phải θ².
- Kết luận định tính trong TODO §0.4 ("đòn bẩy lớn nhất là khoảng cách |STR| − θ") đúng với công thức đã sửa.

---

## 5. Theorem 7′ (không có cận cho rủi ro ghép skill)

**Cận trên 1 − θ** [ĐN]:
- STR(A) = E ℓ(A) − E ℓ(∅) ≤ −θ và E ℓ(A) ≥ 0, nên E ℓ(∅) ≥ θ.
- Do đó STR(A∘B) = E ℓ(A∘B) − E ℓ(∅) ≤ 1 − θ.

**Đạt được cận** [ĐN + mã chạy được]:
- Scope có tỉ lệ θ task bị lỗi tạm thời ở lệnh ghi.
- S1 (retry đồng bộ), S2 (async có xử lý lỗi) và S1′ (retry biết async) cho STR = −θ.
- S1∘S2 không await nên lệnh ghi không chạy: STR = 1 − θ. S1′∘S2 cho STR = −θ.
- Cơ chế được chạy thật trong `src/gatekeeper/composition_example.py`, kiểm bằng `tests/test_composition_theorem7.py`.

**Không tồn tại g** [ĐN]:
- (STR(S1), STR(S2)) = (STR(S1′), STR(S2)) = (−θ, −θ), nhưng rủi ro khi ghép là 1 − θ và −θ.
- Vậy mọi g với STR(A∘B) ≤ g(STR A, STR B) phải có g(−θ, −θ) ≥ 1 − θ. ∎

Định lý này là phản ví dụ dựng được và chạy được. Nó không cần nguồn ngoài.

---

## 6. Proposition 6 (không phân biệt được) [ĐN]

Nếu hai repo cho **cùng một đầu vào** cho thủ tục admission, thì phân phối của quyết định là như nhau, kể cả khi thủ tục có ngẫu nhiên. Vì vậy xác suất admit một skill có hại trên repo ẩn bằng xác suất admit trên repo quan sát được. Lập luận chỉ dùng định nghĩa "thủ tục là hàm của đầu vào".

---

## 7. Thí nghiệm kiểm được gì, và không chứng minh được gì

| Kết quả lý thuyết | Thí nghiệm kiểm cái gì | Đã có |
| --- | --- | --- |
| Bổ đề E + Ville | Tỉ lệ admit nhầm ≤ α khi H₀ đúng, trên phân phối giống dữ liệu thật (plasmode) | `results/method_check.json`; `results/simulation.json` (3,0% ≤ 5%) |
| Giả định SP | Không kiểm được bằng thống kê; là giả định thiết kế. Được hỗ trợ bởi cách lấy mẫu ngẫu nhiên đã đăng ký trước | bản đăng ký trước, `random_order` |
| Theorem 4′ | Thành phần ξ_s không quan sát được. Chỉ báo cáo cận theo lưới ξ_s | `corrections.md` §3 |
| Proposition 9 | Đo tỉ lệ phương sai trên dữ liệu thật | 4,307 (SWE-Skills-Bench, 3.920 cặp); sẽ đo thêm trên E1 và E2 |
| Theorem 7′ | Cơ chế chạy được | test |

**Thí nghiệm không chứng minh được định lý.** Một định lý đúng nhờ chứng minh. Thí nghiệm chỉ (a) kiểm rằng giả định của định lý hợp lý trên dữ liệu thật, và (b) đo các đại lượng mà định lý dùng (σ², tỉ lệ phương sai, tỉ lệ admit nhầm).
