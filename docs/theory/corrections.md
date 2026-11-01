# Lý thuyết Gatekeeper — bản đã sửa (Phase 1)

Tài liệu này thay cho §4, §6 của paper (`docs/01-FSE-2027-13-paper.pdf`). Mỗi mục ghi rõ: paper viết gì, sai ở đâu, bản sửa, và **test nào trong repo kiểm chứng**. Các chứng minh vẫn cần một người biết thống kê đọc lại (việc 👤 trong `TODO.md`).

Ký hiệu: skill S = ⟨π, D, I, P, K⟩; scope s thuộc họ khai báo trước 𝒮; context x = (repo, revision, môi trường, task); ∅ = không dùng skill.

---

## 1. Định nghĩa (sửa)

### 1.1 Loss chuẩn hoá về [0, 1]

Paper: ℓ = 1 − pass rate + 0,5 × (số regression). Có thể vượt 1, nên mọi bound dựa trên ℓ ∈ [0,1] đều không áp dụng được.

**Sửa.** Với F = tỉ lệ test `FAIL_TO_PASS` vẫn fail và R = tỉ lệ test `PASS_TO_PASS` bị hỏng (cả hai ∈ [0,1]), trọng số w > 0:

```
ℓ(x, π) = (F + w · R) / (1 + w)  ∈ [0, 1]
```

w = 0,5 giữ đúng tinh thần paper. Sweep w ∈ [0,2; 2,0] ở Phase 7. Cài trong `gatekeeper.loss.functional_loss`.

### 1.2 Phân phối task P_s

Paper: P_s là mọi task trong scope. Skill chỉ liên quan 10% task thì STR bị pha loãng 10 lần.

**Sửa.** P_s = phân phối các task x trong scope s mà **điều kiện đầu vào I(x) đúng** (skill thật sự được kích hoạt).

**Lưu ý pool hữu hạn (R2).** Trong thực tế chỉ có pool hữu hạn T_s các task. Có hai lựa chọn, phải chốt trước pre-register:

- (a) Mỗi trial dùng một task **khác nhau**: cần |T_s| ≥ số trial. Khi đó bound đúng cho P_s.
- (b) Rút **có hoàn lại** từ T_s: các Z_i i.i.d. theo phân phối đều trên T_s, nên bound đúng cho P̂_s (pool). Chênh lệch P̂_s và P_s phải được tính vào ξ_s.

Khuyến nghị: (b), vì (a) không khả thi với số trial ở `results/simulation.json`.

### 1.3 Selective transfer risk

```
STR(S, s) = E_{x∼P_s}[ ℓ(x, π) − ℓ(x, ∅) ],   Z = ℓ(x, π) − ℓ(x, ∅) ∈ [−1, 1]
```

### 1.4 Nhãn và metric (sửa mâu thuẫn B2 = 22,7%)

Nhãn của cặp (skill, context) đo trên **scoring suite độc lập**, dùng pool task **tách rời** với pool dùng để admit:

| Nhãn | Điều kiện |
| --- | --- |
| harmful | STR > 0 |
| neutral | −θ < STR ≤ 0 |
| beneficial | STR ≤ −θ |

- **Harmful acceptance** = (số cặp harmful được admit) / (số cặp harmful). Với B2 (admit tất cả) = **100%**.
- **Clean-reuse coverage** = (số cặp beneficial được admit) / (số cặp beneficial). Neutral báo cáo riêng.
- **So sánh "at matched coverage"**: mỗi hệ thống có tham số ngưỡng → vẽ đường (coverage, harmful acceptance); so harmful acceptance nội suy tại cùng coverage. Cài trong `gatekeeper.analysis.harm_coverage_curve`.
- **Margin có ý nghĩa** chỉ khi **cận dưới** CI của margin > 5 điểm (paper: CI [3,1; 9,8] **không** vượt 5).

---

## 2. E-process tường minh

H0: E[Z] ≥ −θ (skill không giúp ít nhất θ). Với λ_i chọn từ Z_1..Z_{i−1}:

```
E_n = ∏_{i≤n} (1 + λ_i (−θ − Z_i)),   0 ≤ λ_i ≤ c/(1+θ),  0 < c < 1
admit khi E_n ≥ 1/α_{S,s}
```

**Bổ đề (supermartingale).** Dưới H0, E[1 + λ_i(−θ − Z_i) | 𝓕_{i−1}] = 1 + λ_i(−θ − E[Z_i | 𝓕_{i−1}]) ≤ 1. Vì Z_i ≤ 1 nên mỗi thừa số ≥ 1 − c(1+θ)/(1+θ) = 1 − c > 0. Vậy (E_n) là supermartingale không âm, E_0 = 1.

**Ville.** Pr[∃n: E_n ≥ 1/α] ≤ α. Đúng với **mọi** thời điểm dừng phụ thuộc dữ liệu, nên dừng sớm khi đủ bằng chứng hay khi hết budget đều hợp lệ.

Cài đặt: `gatekeeper.eprocess` (λ kiểu aGRAPA, c = 0,5). Kiểm chứng: `tests/test_simulation.py::test_type_one_error_at_boundary_null`, `results/simulation.json` (5.000 lần: 3,0% ≤ 5%), đối chiếu với `confseq` (`results/confseq_crosscheck.json`).

---

## 3. Theorem 4 (sửa)

**Paper sai ở 3 chỗ:** (i) union bound chỉ theo scope Σ_s α_s, trong khi mỗi scope có nhiều skill và composite; (ii) đổi phân phối thiếu hệ số 2; (iii) không tính lần re-admit sau retirement.

**Giả thiết 3′.** Trong scope s, Z của các trial dùng để admit thoả E[Z_i | 𝓕_{i−1}] = STR_{P_s} (vd i.i.d. từ P_s hoặc từ pool, xem 1.2); triển khai lấy context từ Q_s với TV(Q_s, P_s) ≤ ξ_s; ℓ ∈ [0,1].

**Phân bổ α** (cố định trước khi chạy, `gatekeeper.alpha_ledger`):

```
Σ_{(S,s)} α_{S,s}  +  Σ_k α^comp_k  +  Σ_k α^re_k  ≤ α,
α^comp_k = α_comp · 6/(π² k²),   α^re_k = α_re · 6/(π² k²)
```

Dãy 6/(π²k²) có tổng = 1, nên **không cần biết trước** số composite hay số lần re-admit.

**Theorem 4′.**

```
Pr[ ∃ (S,s) hoặc composite được admit:  STR_{Q_s} > −θ + 2ξ_s ] ≤ α
```

**Chứng minh.**
1. Với mỗi bài toán admission j (một ô, một composite, hoặc một lần re-admit) có ngân sách α_j: nếu STR_{P_s} > −θ thì H0 đúng, nên theo Ville Pr[admit j] ≤ α_j.
2. Union bound qua mọi j (không cần độc lập): Pr[∃ j admit mà STR_{P_s} > −θ] ≤ Σ_j α_j ≤ α.
3. Đổi phân phối: Z = f(x) với f: 𝒳 → [−1, 1] có độ rộng 2, nên |E_Q f − E_P f| ≤ 2 · TV(Q, P) ≤ 2ξ_s. Trên biến cố bù của bước 2, mọi j được admit có STR_{P_s} ≤ −θ, nên STR_{Q_s} ≤ −θ + 2ξ_s. ∎

Hệ số 2 là **chặt**: chuyển khối lượng ξ từ Z = −1 sang Z = +1 cho TV = ξ và kỳ vọng tăng đúng 2ξ (`tests/test_theory.py::test_tv_shift_factor_two_is_tight`).

**Hệ quả (khớp mục tiêu bài toán).** Nếu 2ξ_s ≤ θ với mọi s thì Pr[∃ admit có STR_{Q_s} > 0] ≤ α. Nếu 2ξ_s > θ thì bound không bảo đảm "không có hại"; certificate phải ghi rõ điều này.

**Ước lượng ξ_s.** Không quan sát được trực tiếp; báo cáo bound theo lưới ξ_s ∈ {0; 0,01; 0,025; 0,05}. Với lựa chọn (b) ở 1.2, ξ_s ít nhất phải bao phần chênh lệch pool–P_s.

Kiểm chứng FWER trên nhiều ô dùng chung một sổ α: `tests/test_theory.py::test_family_wise_error_with_ledger`.

**FWER hay FDR (R8).** Theorem 4′ là bảo đảm FWER. Đổi sang FDR (e-BH) giảm số trial nhưng **đổi phát biểu**: chỉ bảo đảm tỉ lệ kỳ vọng các admit có hại ≤ α, không còn "xác suất có bất kỳ admit có hại nào". Khuyến nghị: giữ FWER làm định lý chính, báo cáo e-BH như phân tích phụ.

---

## 4. Proposition 6 (giữ, thêm một câu)

Phát biểu và chứng minh của paper đúng (lập luận "không phân biệt được"). **Thêm:** nếu thủ tục admission có ngẫu nhiên thì trên R† và trên repo quan sát được, đầu vào giống hệt nhau nên **phân phối** của quyết định giống hệt nhau; xác suất admit skill có hại trên R† bằng xác suất admit trên repo gốc, có thể gần 1.

---

## 5. Theorem 7 (sửa)

**Paper:** "∀ε > 0 ∃ S1, S2: STR(S1), STR(S2) ≤ −θ và STR(S1∘S2) ≥ 1 − ε." **Sai** khi ε < θ: STR(S1) ≤ −θ buộc E ℓ(x,∅) ≥ θ (vì ℓ(x,π1) ≥ 0), nên STR(S1∘S2) = E ℓ(π1∘π2) − E ℓ(∅) ≤ 1 − θ. Chứng minh của paper giả sử ℓ(x,∅) ≤ ε, mâu thuẫn với chính giả thiết.

**Thứ tự ghép.** S1∘S2 nghĩa là áp dụng edit của S2 trước, rồi S1 bọc lên kết quả.

**Theorem 7′.** Với mọi θ ∈ (0,1) tồn tại S1, S2, S1′ và scope s sao cho:

```
STR(S1) = STR(S2) = STR(S1′) = −θ,   STR(S1∘S2) = 1 − θ,   STR(S1′∘S2) = −θ
```

Giá trị 1 − θ là lớn nhất có thể (cận chặt). Vì (STR(S1), STR(S2)) = (STR(S1′), STR(S2)) mà rủi ro ghép khác nhau, **không tồn tại hàm g** nào sao cho STR(A∘B) ≤ g(STR(A), STR(B)) với g < 1 − θ.

**Chứng minh (cấu trúc).** Scope có tỉ lệ θ task gặp lỗi tạm thời (transient) ở một lệnh ghi DB, nên ℓ(x,∅) = 1 trên các task đó, = 0 trên phần còn lại, và E ℓ(∅) = θ.
- S1: retry đồng bộ bao quanh lệnh ghi → sửa lỗi tạm thời, ℓ = 0 mọi task → STR = −θ.
- S2: chuyển lệnh ghi sang `async` có xử lý lỗi tạm thời → ℓ = 0 → STR = −θ.
- S1∘S2: retry đồng bộ của S1 gọi hàm async của S2 mà **không await** → nhận coroutine, không raise, lệnh ghi không bao giờ chạy → ℓ = 1 mọi task → STR = 1 − θ.
- S1′: retry "biết async" (await nếu là coroutine): một mình STR = −θ; ghép với S2 vẫn đúng → STR = −θ. ∎

**Cơ chế** thay cho câu tự mâu thuẫn của paper ("handler không bắt X′ nữa nhưng vẫn nuốt lỗi"). Code: `src/gatekeeper/composition_example.py`; test: `tests/test_composition_theorem7.py`.

**Corollary 8 (làm rõ d̄).** Chi phí composition là O(|L_s| · d̄), với d̄ = số partner có footprint giao nhau **trung bình trong cùng scope L_s**. Nếu tính trên toàn library (94 skill, 11,4% cặp giao nhau) thì d̄ ≈ 0,114 × 93 ≈ 10,6, không phải 0,34. Paper phải ghi rõ tính theo scope và báo cáo cả hai số.

---

## 6. Proposition 9 (sửa)

**Mô hình.** ℓ(x,π) = μ_π + T(x) + e_π, ℓ(x,∅) = μ_∅ + T(x) + e_∅, với Var T = σ_T² (độ khó task, chung cho hai nhánh), e_π, e_∅ độc lập với T, Var(e_π − e_∅) = σ_S².

- **Paired** (cùng task x cho hai nhánh): Var(Z) = Var(e_π − e_∅) = σ_S².
- **Unpaired** (hai task độc lập x, x′): Var(ℓ(x,π) − ℓ(x′,∅)) = 2σ_T² + σ_S².

Cả hai thiết kế đều tốn **2 lần chạy cho mỗi mẫu**, nên tỉ lệ số mẫu chính là tỉ lệ chi phí:

```
n_unpaired / n_paired = 1 + 2σ_T²/σ_S²,    n_paired ≈ c · σ_S² · log(1/α_{S,s}) / θ²
```

Paper ghi 1 + σ_T²/σ_S² và "net 1,55×" (chia đôi vì tưởng paired tốn gấp đôi). Cả hai đều sai. Với σ_T²/σ_S² = 2,1 (số dự kiến của paper) thì mức tiết kiệm đúng là **5,2×**. Kiểm chứng Monte-Carlo: `tests/test_theory.py::test_prop9_variance_ratio`. Ước lượng σ_T², σ_S² từ dữ liệu pilot: `gatekeeper.analysis.variance_components`.

---

## 7. Việc còn lại cho người (👤)

- [ ] Nhờ một người biết thống kê đọc mục 2–6.
- [ ] Chốt lựa chọn (a)/(b) ở mục 1.2 và FWER/FDR ở mục 3 trước khi pre-register.
- [ ] Đưa các sửa đổi này vào bản LaTeX của paper (nguồn .tex chưa có trong repo).
