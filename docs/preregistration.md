# Pre-registration (bản nháp) — Gatekeeper / SkillShift-SE

> **Trạng thái: NHÁP, chưa đóng băng.** Đóng băng (commit + hash) trước khi bắt đầu Phase 6, sau khi pilot (Phase 3) xong. Sau khi đóng băng, mọi thay đổi phải ghi vào mục "Sai lệch so với pre-registration" của paper.
>
> Ký hiệu: ✅ đề xuất đã có bằng chứng trong repo · ❓ cần bạn / người hướng dẫn quyết · ⏳ chờ số pilot.

## 1. Câu hỏi và giả thuyết

| | Nội dung |
| --- | --- |
| RQ1 (chính) | Gatekeeper có giảm harmful acceptance so với **XRepoSkill (+ fingerprint screen)** tại cùng clean-reuse coverage không? |
| H1 | **Ưu thế:** cận dưới CI 95% của margin (XRepoSkill − Gatekeeper) **> 0**, so tại cùng coverage trên đường harm–coverage. Ngưỡng 5 điểm là mức có ý nghĩa thực tế, báo cáo bằng ước lượng điểm. ✅ đổi theo R14: phiên bản "cận dưới > 5" có power ~5% với số của chính paper. |
| Co-primary | Gatekeeper vs B9 (budget-matched retries) về tỉ lệ sửa được task target. |
| Phụ (BH) | RQ2 composition, RQ3 theo regime A/B/C, RQ4 retirement / ablation / break-even. |

## 2. Dữ liệu (chỉ benchmark chuẩn, TODO.md R13)

| Mục | Giá trị | |
| --- | --- | --- |
| Train (induce skill) | SWE-Gym, 11 repo, 2.438 task | ✅ `data/benchmarks/summary.json` |
| Test | SWE-bench ∪ Verified ∪ SWE-bench-Live, bỏ repo trùng train | ✅ `data/splits/split_v0.json` (hash `fb74140ef67fe769`) |
| Endpoint chính chấm bằng | test chính thức `FAIL_TO_PASS` / `PASS_TO_PASS`, harness SWE-bench | ✅ |
| Test fault-injection tự thêm | chỉ phân tích phụ, báo cáo riêng | ✅ |
| Pool admission vs pool chấm | tách rời theo instance_id (ngẫu nhiên 50/50 trong mỗi scope, seed cố định) | ❓ tỉ lệ chia |

## 3. Đại lượng và nhãn

| Mục | Giá trị | |
| --- | --- | --- |
| Loss | ℓ = (F + wR)/(1 + w), w = 0,5; sweep w ∈ [0,2; 2,0] | ✅ `docs/theory/corrections.md` §1.1 |
| P_s | task trong scope mà I(x) đúng | ✅ |
| Lấy mẫu trial | **(b) rút có hoàn lại từ pool**; bound theo pool, chênh lệch pool–P_s vào ξ_s | ✅ đề xuất (0 scope có ≥ 219 task) · ❓ chốt |
| Nhãn | harmful (STR > 0) / neutral (−θ < STR ≤ 0) / beneficial (STR ≤ −θ), đo trên pool chấm | ✅ |
| Harmful acceptance | admitted harmful / harmful | ✅ |
| Clean-reuse coverage | admitted beneficial / beneficial | ✅ |

## 4. Tham số thống kê

| Mục | Đề xuất | Lý do | |
| --- | --- | --- | --- |
| α họ (family) | 0,05 | chuẩn | ❓ |
| Phân bổ α | 70% ô (skill, scope) theo tần suất reuse dự kiến; 20% composite; 10% re-admission; dãy 6/(π²k²) | `alpha_ledger.py` | ✅ |
| Kiểm soát | **FWER** (Theorem 4′); e-BH chỉ là phân tích phụ | đổi sang FDR là đổi định lý | ✅ đề xuất · ❓ chốt |
| θ | **0,02 hoặc 0,05** | θ 0,05 → 0,02 giảm ~2 lần trial (`results/design_table.json`); θ nhỏ = chấp nhận skill chỉ giúp 2 điểm | ❓ quyết định quan trọng nhất |
| ξ_s báo cáo | lưới {0; 0,01; 0,025; 0,05} | `corrections.md` §3 | ✅ |
| Budget mỗi ô | ⏳ theo pilot; tham khảo design table: 200–1.600 cặp | | ⏳ |
| Bettor | aGRAPA plug-in, c = 0,5, prior (0; 0,25; 1) | đã kiểm chứng sai loại I 3,0% ≤ 5% | ✅ |

## 5. Hệ thống so sánh

| Hệ thống | Vai trò | |
| --- | --- | --- |
| Gatekeeper | đề xuất | ✅ |
| XRepoSkill (+ fingerprint screen của Gatekeeper) | baseline quyết định | ✅ |
| MemGovern, gskill (GEPA) | baseline có code | ✅ |
| B1, B2, B8, B9 | đối chứng | ✅ `baselines.py` |
| ASI | tuỳ chọn | ❓ |
| Harness chung | mini-swe-agent (commit ghi khi clone) | ✅ đề xuất · ❓ chốt |
| Model | 1 API model + 1 open-weight (digest) | ❓ chọn model |
| Lặp lại | 3 lần chạy × 2 backend | ✅ |

## 6. Phân tích

- CI: cluster bootstrap theo repo, 2.000 lần lặp (`analysis.cluster_bootstrap_ci`).
- So sánh tại cùng coverage: nội suy trên đường harm–coverage (`analysis.harm_at_coverage`).
- So sánh phụ: Benjamini–Hochberg q = 0,05.
- Regime A/B/C báo cáo riêng, **không gộp** vào headline.
- Power (`analysis.endpoint_power`), với số dự kiến của paper (11,5% → 5,1%):

  | Cặp harmful | Cận dưới > 5 điểm (độc lập / nested) | Ưu thế > 0 (độc lập / nested) |
  | --- | --- | --- |
  | 63 (như paper) | 4% / 3% | 26% / 56% |
  | 200 | 6% / 9% | 65% / ~100% |
  | 500 | 13% / 21% | 97% / 100% |
  | 2.000 | 38% / 75% | 100% / 100% |

  Nguồn: `results/endpoint_power.json` (`scripts/power_table.py`). → Cần giả thuyết ưu thế và **200–500 cặp harmful**, tuỳ mức tương quan giữa quyết định của hai hệ thống (đo ở pilot). ⏳

## 7. Go/no-go sau pilot (R4)

Đi tiếp nếu **cả ba** đúng:
1. Số trial cần mỗi ô (với θ đã chọn và σ_S² đo được) × số ô ≤ ngân sách.
2. Power của endpoint chính ≥ 80% với số cặp harmful dự kiến.
3. Chi phí ước lượng (token + GPU + CPU) ≤ ngân sách đã duyệt.

Thiếu một điều kiện thì thu hẹp (cross-repo + adversarial, θ lớn hơn, ít ô hơn). Thiếu nhiều thì gộp vào FSE-2027-01.

## 8. Ước lượng khối lượng pilot (không tốn tiền để tính)

Giả sử 10 skill × 2 scope = 20 ô; mỗi ô tối thiểu 30 cặp trial để ước lượng σ (Phase 3); ô beneficial chạy tiếp tới khi admit hoặc tới budget 300 cặp:

| Mục | Số cặp trial | Số lần chạy agent + test |
| --- | --- | --- |
| Ước lượng σ (20 ô × 30) | 600 | 1.200 |
| Admission thêm (giả sử 5 ô beneficial × 270) | 1.350 | 2.700 |
| **Tổng pilot** | **~1.950** | **~3.900** |

Chi phí = 3.900 × (chi phí một lần chạy). Chi phí một lần chạy phải **đo** ở Phase 2 (chạy cùng một task 5 lần, `runlog.CostSummary`) trước khi đặt trần ngân sách. ⏳
