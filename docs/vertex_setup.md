# Thiết lập Gemini qua Vertex AI (cho pilot trả phí)

Quyết định ngày 01/11/2026: backend LLM là **Gemini qua Vertex AI**. Agent harness là **mini-swe-agent 2.4.6** (gọi model qua LiteLLM với tên `vertex_ai/<model-id>`).

> Mọi bước dưới đây do bạn làm trên Google Cloud và GitHub (👤). Code không tự tạo tài nguyên hay chi tiền. Workflow trả phí `Pilot (paid, Vertex AI)` **chỉ chạy khi bạn bấm Run** và luôn có trần ngân sách.

## 1. Google Cloud

1. Tạo (hoặc chọn) project → ghi lại **Project ID**.
2. Bật billing cho project. **Đặt budget alert** (Billing → Budgets & alerts), ví dụ 50 USD, cảnh báo ở 50% / 90% / 100%.
3. Bật API: **Vertex AI API** (`aiplatform.googleapis.com`).
4. Chọn region có model Gemini, ví dụ `us-central1` (hoặc `global` nếu model hỗ trợ) → đây là `VERTEXAI_LOCATION`.
5. **Xác nhận mã model** trong Vertex AI → Model Garden (tìm "Gemini"). Sửa `configs/models/vertex_gemini.json`:
   - `litellm_name`: `vertex_ai/<mã model đúng như trong Model Garden>`
   - `usd_per_mtok_in` / `usd_per_mtok_out`: giá trên trang pricing chính thức
   - đổi `"_verified": false` thành `true` khi đã kiểm tra.
   Giá trị hiện tại (`gemini-3.1-pro`, `gemini-3.8-flash`) lấy từ blog bên thứ ba, **chưa xác minh**.

## 2. Cấp quyền cho GitHub Actions

**Cách khuyến nghị: Workload Identity Federation (không có key bí mật lâu dài).**

1. IAM → Service Accounts → tạo `gatekeeper-pilot`, cấp role **Vertex AI User** (`roles/aiplatform.user`).
2. IAM → Workload Identity Federation → tạo pool + provider kiểu GitHub (OIDC, issuer `https://token.actions.githubusercontent.com`), điều kiện thuộc tính `assertion.repository == "dinhthithuthuyduphong-bot/gatekeeper"`.
3. Cho phép provider impersonate service account (role **Workload Identity User**).
4. GitHub repo → Settings → Secrets and variables → Actions → thêm:
   - `GCP_WORKLOAD_IDENTITY_PROVIDER` = `projects/<số>/locations/global/workloadIdentityPools/<pool>/providers/<provider>`
   - `GCP_SERVICE_ACCOUNT` = `gatekeeper-pilot@<project>.iam.gserviceaccount.com`
   - `VERTEXAI_PROJECT` = Project ID
   - `VERTEXAI_LOCATION` = region

**Cách đơn giản hơn (kém an toàn hơn):** tạo JSON key cho service account, lưu vào secret `GCP_SA_KEY` (không commit file key vào repo). Workflow tự dùng key nếu không có Workload Identity.

## 3. Chạy

1. Chạy miễn phí trước: Actions → **Pilot dry run** → Run workflow. Phải xanh (kiểm tra toàn bộ pipeline với model giả).
2. Actions → **Pilot (paid, Vertex AI)** → Run workflow, bắt đầu nhỏ:
   - `model`: `gemini-flash`, `n`: `5`, `cost_limit`: `0.5`, `budget_usd`: `10`
   - Script **từ chối chạy** nếu (số nhánh × n × cost_limit) > budget.
3. Kết quả: artifact `pilot-<name>` và nhánh `pilot-snapshots` (`results/pilot/<name>.json`, `runs/<name>/trials.jsonl`).
4. Ghi chi phí thật vào TODO (Phase 2 "Ước chi phí 1 cặp trial") trước khi tăng `n`.

## 4. Chạy trên máy riêng (tuỳ chọn)

```bash
pip install -e . "swebench==5.0.2" "mini-swe-agent==2.4.6"
gcloud auth application-default login          # hoặc export GOOGLE_APPLICATION_CREDENTIALS=key.json
export VERTEXAI_PROJECT=<project> VERTEXAI_LOCATION=us-central1
python scripts/run_pilot.py --name local-test --model gemini-flash --n 2 \
    --skills configs/skills/guidance-reproduce-first.json --cost-limit 0.5 --budget-usd 3
```

Cần Docker và khoảng 120 GB đĩa trống cho image SWE-bench (khuyến nghị của SWE-bench).

## 5. Tái lập

`TrialRecord` bắt buộc ghi: model ID (`vertex_ai/...`), ngày gọi, digest image Docker, commit repo, seed. Gemini trên Vertex là model đóng: ghi đúng mã phiên bản (không dùng alias tự cập nhật), và ghi ngày gọi API cho mọi lần chạy.
