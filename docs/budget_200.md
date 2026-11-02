# Dùng 200 USD Vertex AI hiệu quả nhất (pilot G1)

**Mục tiêu duy nhất của 200 USD:** trả lời cổng **G1** (hạn 15/12/2026): *skill của mình có hiệu ứng đủ lớn (|STR| ≥ 0,10) trên task mà nó kích hoạt không?* (R15 trong `TODO.md`). Chưa dùng tiền này cho baseline hay thí nghiệm chính.

Mọi bước chạy bằng Actions → **Pilot (paid, Vertex AI)** → *Run workflow*. Mỗi lần chạy đều có trần `budget_usd`; script **từ chối chạy** nếu (số lần chạy agent × `cost_limit`) vượt trần, và mini-swe-agent dừng từng task khi vượt `cost_limit` (giá đã được đăng ký với LiteLLM, nên không còn chuyện "chi phí = 0 nên không chặn").

## 0. Trước khi tiêu đồng nào (miễn phí)

- [ ] GCP: đặt **Budget alert 200 USD** (Billing → Budgets & alerts, cảnh báo 25/50/75/90/100%).
- [ ] Làm xong `docs/vertex_setup.md` (secrets, Vertex AI API).
- [ ] Xác nhận trong Model Garden có `gemini-3.8-flash` và `gemini-3.1-flash-lite`; đối chiếu giá với `configs/models/vertex_gemini.json` (giá hiện lấy từ bảng LiteLLM 1.106.6; 3.8-flash có thể là **giá ưu đãi đến 31/12/2026** → nên chạy hết trong tháng 11–12).
- [x] Workflow **Validate pilot pool** với `tag = g1` đã xanh: 86/89 task dùng được (run 41375243272).

## Đã thử thật (02/11/2026, 0,26 USD)

Chạy local bằng key service account `gatekeeper-pilot`, task `psf__requests-1142`, Gemini 3.8 Flash (`reasoning_effort: low`), 30 bước, 2 nhánh:

| Nhánh | USD/lần | Token input | Đã cache | Token output | Kết quả |
| --- | --- | --- | --- | --- | --- |
| không skill | 0,134 | 475.584 | 80% | 9.000 | chạm trần 30 bước, chưa nộp |
| đối chứng dương | 0,125 | 384.782 | 68% | 3.653 | chạm trần 30 bước, chưa nộp |

- Toàn bộ pipeline chạy được với Gemini thật: Vertex AI (location **`global`**), gọi tool, Docker SWE-bench, harness, log chi phí.
- **30 bước là quá ít**: agent dùng phần lớn số bước để đọc lịch sử git. Dùng **`step_limit = 60`** cho mọi giai đoạn; ước tính ~0,35 USD/lần (chi phí tăng gần bình phương theo số bước, cache 70–80%).
- Với 0,35 USD/lần: 199 USD ≈ 510 lần chạy → A + B (38 task) + C (193 lần) ≈ 125 USD, còn dư dự phòng.

## 1. Giai đoạn A — đo chi phí thật và chọn model (≤ 6 USD)

Câu hỏi: một lần chạy agent tốn bao nhiêu, cache trúng bao nhiêu, model giải được bao nhiêu task?

| Lần chạy | name | model | skills | n | step_limit | cost_limit | pool_tag | budget_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | `g1-a-lite` | gemini-flash-lite | `configs/skills/control-oracle-files.json` | 4 | 60 | 0.3 | default | 3 |
| A2 | `g1-a-flash` | gemini-flash | `configs/skills/control-oracle-files.json` | 4 | 60 | 0.6 | default | 5 |

Đọc `results/pilot/g1-a-*.json` → mục `usage` (`usd_per_run`, `cached_share`, `solve_rate`) rồi:

```bash
python scripts/plan_budget.py --budget 190 --usd-per-run <usd_per_run đo được>
```

**Chọn model:** model rẻ nhất có `solve_rate` của nhánh `none` trong khoảng **20–70%** (quá thấp thì skill không thể "giúp"; quá cao thì không còn gì để giúp). Nếu Flash-Lite < 20% → dùng Flash.

### Kết quả giai đoạn A (02/11/2026, tổng 2,12 USD)

Cùng 4 task (`pytest-dev__pytest-5840`, `scikit-learn__scikit-learn-10297`, `astropy__astropy-7606`, `pydata__xarray-4075`), 60 bước, 2 nhánh:

| Lượt | Model | USD/lần | Token input/lần | Cache | Bước/lần | Giải được (không skill / gợi ý file) |
| --- | --- | --- | --- | --- | --- | --- |
| A1 (`g1-a-lite2`) | gemini-3.1-flash-lite | **0,022** | 0,25M | 79% | 32 | 3/4 / 3/4 |
| A2 (`g1-a-flash`) | gemini-3.8-flash (`reasoning_effort: low`) | 0,24 | 0,81M | 79% | 42 | 3/4 / 3/4 |

- Lượt A1 đầu tiên (`results/pilot/invalid/g1-a-lite.json`) **không hợp lệ**: 3/8 container không khởi động được (image chưa tải) và bị tính nhầm là "không giải được". Đã sửa pipeline (tải image trước, loại lỗi hạ tầng khỏi phép ghép cặp) rồi chạy lại.
- **Chọn Flash-Lite**: giải được như Flash trên 4 task này nhưng **rẻ hơn ~11 lần**. Tỉ lệ giải 75% hơi cao so với khoảng 20–70% (chỉ 4 task, chưa chắc chắn), nên giai đoạn B sẽ đo lại trên 38 task.
- Gợi ý đúng file chưa giúp gì trên 4 task này: 3 task đã được giải sẵn (trần), task còn lại (`pytest-5840`) không giải được ở cả hai nhánh. Đối chứng dương chỉ có thể cho thấy hiệu ứng trên các task mà agent thất bại khi không có gợi ý → giai đoạn B cần đủ nhiều task như vậy.
- Với 0,022–0,025 USD/lần, toàn bộ G1 (B + C) chỉ khoảng **10 USD**. Ngân sách dư dùng để **lặp lại mỗi cặp với 3 seed** (giảm nhiễu) và chạy lại nhánh skill hứa hẹn bằng Flash, thay vì mở rộng sang skill mới.

## 2. Giai đoạn B — kiểm tra phép đo (khoảng 25% phần còn lại)

Câu hỏi: (1) pairing có đúng không? (2) phép đo có phát hiện được hiệu ứng lớn không? (3) nhiễu σ_S² thật là bao nhiêu?

| name | model | skills | n | pool_tag | budget_usd |
| --- | --- | --- | --- | --- | --- |
| `g1-b` | gemini-flash-lite | `configs/skills/control-none-seed1.json,configs/skills/control-oracle-files.json` | theo `plan_budget.py` (tối đa 38) | default | theo kế hoạch |

- `control-none-seed1`: giống hệt nhánh không skill, chỉ khác seed → hiệu ứng thật = 0; đo nhiễu.
- `control-oracle-files`: gợi ý đúng file cần sửa (lấy từ gold patch) → phải giúp rõ rệt. **Chỉ là đối chứng**, không bao giờ là skill được đánh giá.

```bash
python scripts/analyze_g1.py --stage-b g1-b
```

**Dừng nếu:** nhiễu khác 0 (lỗi pairing/seed) hoặc đối chứng dương không cho Z ≤ −0,10 **trên các task mà nhánh không skill thất bại** (cần ≥ 5 task như vậy). Lý do (sửa 02/11/2026, trước khi thấy kết quả B): agent tự giải ~75% task, gợi ý không thể làm tốt hơn trên những task đó, nên tính trung bình trên mọi task sẽ bị trần và báo sai. Khi dừng thì **không chạy C**, báo lại để sửa thiết kế.

### Kết quả giai đoạn B lần 1 (02/11/2026, 3,95 USD) — **không hợp lệ, chạy lại**

| Nhánh | n | Z trung bình | CI 90% | Giải được |
| --- | --- | --- | --- | --- |
| đối chứng nhiễu (seed + 1) | 37 | −0,104 | [−0,19; −0,02] | 49% so với 38% |
| đối chứng dương (task nhánh gốc thất bại) | 23 | −0,25 | [−0,37; −0,14] | — |

- Quy tắc G1 **báo STOP đúng** (nhiễu khác 0). Rà soát tìm ra nguyên nhân có thật: Vertex AI coi `seed=0` là *không đặt seed*, nên nhánh gốc lấy mẫu ngẫu nhiên còn đối chứng nhiễu (seed 1) tất định → hai nhánh khác nhau về cách lấy mẫu. Đã sửa (seed từ 1, seed 0 bị từ chối), kết quả cũ ở `results/pilot/invalid/g1-b/`.
- 38% lần chạy nhánh gốc chạm trần 60 bước và **không nộp bản sửa** (patch rỗng); phần lớn các cặp "lật" là chạm trần ở một nhánh, nộp ở nhánh kia (C1 trong `docs/audit_pilot.md`).
- Chi phí 0,035 USD/lần (cao hơn A vì nhiều task dài hơn). Tổng pilot sau B: 6,49 USD; B chạy lại (`g1-b2`) thêm ~4 USD.

### Kết quả giai đoạn B lần 2 (`g1-b2`, seed đã sửa, 02/11/2026, 3,94 USD) — **STOP, chưa chạy C**

| Nhánh | n | Z trung bình | CI 90% | Giải được |
| --- | --- | --- | --- | --- |
| không skill (seed 1) | 38 | — | — | 18/38 (47%) |
| đối chứng nhiễu (seed 2) | 38 | −0,021 | [−0,11; +0,08] ✅ chứa 0 | 19/38 |
| gợi ý đúng file (seed 1) | 38 | −0,017 | — | 19/38 |
| gợi ý đúng file, chỉ task nhánh gốc thất bại | 20 | −0,066 | [−0,13; +0,0002] ❌ | 2/20 |

- **Pairing và seed nay đúng**: đối chứng nhiễu ≈ 0, 0 lỗi hạ tầng trên 114 lần chạy.
- Quy tắc đặt trước báo **STOP: đối chứng dương quá yếu** → không chạy C.
- Phân tích thêm (thăm dò, không phải quy tắc): trên chính 20 task đó, đối chứng **nhiễu** giải được 5, gợi ý file chỉ 2. Gợi ý file và đối chứng nhiễu giải gần như cùng tập task (16 chung, 3 chỉ gợi ý giải, 3 chỉ nhiễu giải). Nghĩa là (1) **gợi ý tên file không giúp Flash-Lite** (agent tự tìm đúng file; cái khó là sửa đúng), và (2) quy tắc A11 thiên lệch do hồi quy về trung bình (A19).
- Nhiễu giữa hai lần chạy là lớn: ~1/4 cặp lật kết quả chỉ vì đổi seed → thí nghiệm chính bắt buộc nhiều seed/cặp.

## 3. Giai đoạn C — 4 skill trên task chúng kích hoạt (phần còn lại, giữ 10% dự phòng)

| name | model | skills | n | pool_tag | budget_usd |
| --- | --- | --- | --- | --- | --- |
| `g1-c` | gemini-flash-lite | `configs/skills/null-guard.json,configs/skills/type-guard.json,configs/skills/exception-handling.json,configs/skills/validation-error.json` | 86 | g1 | 193 × USD/lần đo ở A, cộng 10% |

Mỗi skill chỉ chạy trên task mà I(x) đúng (≤ 30 task/skill); nhánh không skill chạy một lần trên hợp các task đó và **dùng chung** cho cả 4 skill.

Pool g1 đã kiểm định (run 41375243272): **86/89 task dùng được** (loại 3 task Django có nhánh no-op không sạch). Theo skill: exception-handling 25, null-guard 25, type-guard 30, validation-error 27 → **193 lần chạy agent** (86 nhánh không skill + 107 nhánh skill) ≈ **39 USD (có cache) – 120 USD (không cache)** với Flash. Nhập `n = 86`.

```bash
python scripts/analyze_g1.py --stage-b g1-b --stage-c g1-c
```

## 4. Quy tắc G1 (đặt trước, áp máy móc — `gatekeeper.analysis.g1_decision`)

- **G1 PASS** nếu có skill với Z trung bình ≤ −0,10 **và** cận trên CI 90% < 0 → đi tiếp Phase 3 với skill đó, xin thêm ngân sách.
- **G1 FAIL** nếu không skill nào đạt → theo mục 0.1: thu hẹp (skill mạnh hơn: edit program thay vì guidance, I(x) tốt hơn — R16) hoặc chuyển hướng/venue. Đây vẫn là kết quả có giá trị (bằng chứng định lượng cho R15).
- Đây là **sàng lọc thăm dò**, không phải kiểm định xác nhận: e-process anytime-valid chỉ dùng ở thí nghiệm chính.

## 5. Dự kiến dùng tiền (Gemini 3.8 Flash, 30 bước/lần, bảng `results/budget_plan.json`)

| Kịch bản | USD/lần | Số lần chạy với 180 USD | B (task) | C (task/skill) | CI ±/skill |
| --- | --- | --- | --- | --- | --- |
| Không có cache | 0,62 | ~288 | ~23 | ~29 | 0,07–0,18 |
| Cache 80% | 0,20 | ~900 | ~74 (tối đa 38 trong pool) | 30 | 0,07–0,18 |

Nếu còn dư sau C (kịch bản có cache): chạy lại nhánh `none` và skill hứa hẹn nhất với `seed` khác để giảm nhiễu, **không** mở rộng sang skill mới.

## 6. Sau mỗi giai đoạn

- Kết quả tự đẩy lên nhánh `pilot-snapshots`; mình (Claude) kéo về, chạy `analyze_g1.py`, cập nhật `TODO.md` và report.
- Ghi chi phí thật vào Nhật ký tiến độ.
