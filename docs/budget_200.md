# Dùng 200 USD Vertex AI hiệu quả nhất (pilot G1)

**Mục tiêu duy nhất của 200 USD:** trả lời cổng **G1** (hạn 15/12/2026): *skill của mình có hiệu ứng đủ lớn (|STR| ≥ 0,10) trên task mà nó kích hoạt không?* (R15 trong `TODO.md`). Chưa dùng tiền này cho baseline hay thí nghiệm chính.

Mọi bước chạy bằng Actions → **Pilot (paid, Vertex AI)** → *Run workflow*. Mỗi lần chạy đều có trần `budget_usd`; script **từ chối chạy** nếu (số lần chạy agent × `cost_limit`) vượt trần, và mini-swe-agent dừng từng task khi vượt `cost_limit` (giá đã được đăng ký với LiteLLM, nên không còn chuyện "chi phí = 0 nên không chặn").

## 0. Trước khi tiêu đồng nào (miễn phí)

- [ ] GCP: đặt **Budget alert 200 USD** (Billing → Budgets & alerts, cảnh báo 25/50/75/90/100%).
- [ ] Làm xong `docs/vertex_setup.md` (secrets, Vertex AI API).
- [ ] Xác nhận trong Model Garden có `gemini-3.8-flash` và `gemini-3.1-flash-lite`; đối chiếu giá với `configs/models/vertex_gemini.json` (giá hiện lấy từ bảng LiteLLM 1.106.6; 3.8-flash có thể là **giá ưu đãi đến 31/12/2026** → nên chạy hết trong tháng 11–12).
- [x] Workflow **Validate pilot pool** với `tag = g1` đã xanh: 86/89 task dùng được (run 41375243272).

## 1. Giai đoạn A — đo chi phí thật và chọn model (≤ 6 USD)

Câu hỏi: một lần chạy agent tốn bao nhiêu, cache trúng bao nhiêu, model giải được bao nhiêu task?

| Lần chạy | name | model | skills | n | step_limit | cost_limit | pool_tag | budget_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | `g1-a-lite` | gemini-flash-lite | `configs/skills/control-oracle-files.json` | 4 | 40 | 0.3 | default | 3 |
| A2 | `g1-a-flash` | gemini-flash | `configs/skills/control-oracle-files.json` | 4 | 40 | 0.5 | default | 5 |

Đọc `results/pilot/g1-a-*.json` → mục `usage` (`usd_per_run`, `cached_share`, `solve_rate`) rồi:

```bash
python scripts/plan_budget.py --budget 190 --usd-per-run <usd_per_run đo được>
```

**Chọn model:** model rẻ nhất có `solve_rate` của nhánh `none` trong khoảng **20–70%** (quá thấp thì skill không thể "giúp"; quá cao thì không còn gì để giúp). Nếu Flash-Lite < 20% → dùng Flash.

## 2. Giai đoạn B — kiểm tra phép đo (khoảng 25% phần còn lại)

Câu hỏi: (1) pairing có đúng không? (2) phép đo có phát hiện được hiệu ứng lớn không? (3) nhiễu σ_S² thật là bao nhiêu?

| name | model | skills | n | pool_tag | budget_usd |
| --- | --- | --- | --- | --- | --- |
| `g1-b` | (model chọn ở A) | `configs/skills/control-none-seed1.json,configs/skills/control-oracle-files.json` | theo `plan_budget.py` (tối đa 38) | default | theo kế hoạch |

- `control-none-seed1`: giống hệt nhánh không skill, chỉ khác seed → hiệu ứng thật = 0; đo nhiễu.
- `control-oracle-files`: gợi ý đúng file cần sửa (lấy từ gold patch) → phải giúp rõ rệt. **Chỉ là đối chứng**, không bao giờ là skill được đánh giá.

```bash
python scripts/analyze_g1.py --stage-b g1-b
```

**Dừng nếu:** nhiễu khác 0 (lỗi pairing/seed) hoặc đối chứng dương không cho Z ≤ −0,10 (phép đo quá kém nhạy; kết quả "không hiệu ứng" ở C sẽ vô nghĩa). Khi đó **không chạy C**, báo lại để sửa thiết kế.

## 3. Giai đoạn C — 4 skill trên task chúng kích hoạt (phần còn lại, giữ 10% dự phòng)

| name | model | skills | n | pool_tag | budget_usd |
| --- | --- | --- | --- | --- | --- |
| `g1-c` | (model chọn ở A) | `configs/skills/null-guard.json,configs/skills/type-guard.json,configs/skills/exception-handling.json,configs/skills/validation-error.json` | 86 | g1 | 193 × USD/lần đo ở A, cộng 10% |

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
