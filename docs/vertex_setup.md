# Thiết lập Gemini qua Vertex AI (cho pilot trả phí)

Quyết định ngày 01/11/2026: backend LLM là **Gemini qua Vertex AI**. Agent harness là **mini-swe-agent 2.4.6** (gọi model qua LiteLLM với tên `vertex_ai/<model-id>`).

> Mọi bước dưới đây do bạn làm trên Google Cloud và GitHub (👤). Code không tự tạo tài nguyên hay chi tiền. Workflow trả phí `Pilot (paid, Vertex AI)` **chỉ chạy khi bạn bấm Run** và luôn có trần ngân sách.

## 1. Google Cloud

1. Tạo (hoặc chọn) project → ghi lại **Project ID**.
2. Bật billing cho project. **Đặt budget alert** (Billing → Budgets & alerts), ví dụ 50 USD, cảnh báo ở 50% / 90% / 100%.
3. Bật API: **Vertex AI API** (`aiplatform.googleapis.com`).
4. **`VERTEXAI_LOCATION = global`** (đã thử 02/11/2026: các model Gemini 3.x trả lời ở `global`, báo 404 ở `us-central1`).
5. **Xác nhận mã model** trong Vertex AI → Model Garden (tìm "Gemini"). Sửa `configs/models/vertex_gemini.json`:
   - `litellm_name`: `vertex_ai/<mã model đúng như trong Model Garden>`
   - `usd_per_mtok_in` / `usd_per_mtok_out`: giá trên trang pricing chính thức
   - đổi `"_verified": false` thành `true` khi đã kiểm tra.
   Giá trị hiện tại (`gemini-3.8-flash`, `gemini-3.1-flash-lite`, `gemini-3.1-pro-preview`) lấy từ bảng giá đi kèm LiteLLM 1.106.6, **chưa đối chiếu với trang của Google**.

## 2. Cấp quyền cho GitHub Actions

**Cách khuyến nghị: Workload Identity Federation (không có key bí mật lâu dài).**

1. IAM → Service Accounts → tạo `gatekeeper-pilot`, cấp role **Vertex AI User** (`roles/aiplatform.user`).
2. IAM → Workload Identity Federation → tạo pool + provider kiểu GitHub (OIDC, issuer `https://token.actions.githubusercontent.com`), điều kiện thuộc tính `assertion.repository == "dinhthithuthuyduphong-bot/gatekeeper"`.
3. Cho phép provider impersonate service account (role **Workload Identity User**).
4. GitHub repo → Settings → Secrets and variables → Actions → thêm:
   - `GCP_WORKLOAD_IDENTITY_PROVIDER` = `projects/<số>/locations/global/workloadIdentityPools/<pool>/providers/<provider>`
   - `GCP_SERVICE_ACCOUNT` = `gatekeeper-pilot@<project>.iam.gserviceaccount.com`
   - `VERTEXAI_PROJECT` = Project ID
   - `VERTEXAI_LOCATION` = `global`

**Cách đơn giản hơn (kém an toàn hơn), đang dùng:** JSON key của service account `gatekeeper-pilot` → dán **toàn bộ nội dung file** vào secret `GCP_SA_KEY` (không commit file key vào repo; `.gitignore` đã chặn `*key*.json`). Workflow tự dùng key nếu không có Workload Identity. Sau pilot nên **xoá key cũ và tạo key mới** (IAM → Service Accounts → Keys), vì key đã đi qua đoạn chat.

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

## Khóa nào dùng ở đâu (03/11/2026)

Tài khoản dịch vụ: `gatekeeper-pilot@gatekeeper-research.iam.gserviceaccount.com`. Mỗi khóa được nhận diện bằng **mã khóa** (`private_key_id`, liệt kê ở Google Cloud Console → IAM & Admin → Service Accounts → Keys). Mã khóa chỉ là định danh, không phải bí mật. Không bao giờ ghi file khóa vào repo.

| Mã khóa (8 ký tự đầu) | Dùng ở đâu | Nạp vào bằng | Thu hồi khi nào |
| --- | --- | --- | --- |
| `0cf3193a` | Máy chạy E1 (container của phiên làm việc) | file trong thư mục tạm của phiên, không vào git (preflight [secrets] chặn) | sau pilot (xoay vòng khóa) |
| `566b1f20` (tài khoản `gatekeeper-pilot-E2@…`; kiểm 2026-11-03 bằng `vertex-check.yml`, lần chạy 41637490392: đủ 3 secret, gọi `gemini-3.1-flash-lite` được, 7 token vào, 1 token ra) | GitHub Actions: `pilot.yml`, `e2-shards.yml` | secret `GCP_SA_KEY` (cùng với `VERTEXAI_PROJECT` = `gatekeeper-research`, `VERTEXAI_LOCATION` = `global`) | khi không còn chạy trên Actions |

- **Trên GitHub, mỗi tên secret giữ đúng một giá trị.** Tạo lại một tên đã có thì giá trị mới thay hẳn giá trị cũ. Hai workflow dùng chung `GCP_SA_KEY` là chủ ý, vì cùng một project Vertex.
