# Độ trung thành với hệ thống của người khác: câu hỏi reviewer có thể đặt và câu trả lời

> Lập ngày 07/11/2026 theo yêu cầu của @thuthuy: "Không được implement lại vì mình bias làm người ta thua", "Nhớ note kĩ chi tiết này để reviewer phản biện".
>
> - Mọi so sánh dưới đây đã đối chiếu từng dòng với mã gốc ở commit đã ghim: gskill tại `gepa-ai/gepa@8c7b697`, MemGovern tại `QuantaAlpha/MemGovern@a8456580`. Bản đối chiếu nằm trong `docs/review_log.md` R-54.
> - Mục **"Viết trong paper"** của mỗi câu là câu chữ được phép dùng. Không viết mạnh hơn mức đó.

## A. gskill

### A1. "Các tác giả có tự viết lại gskill rồi làm nó yếu đi không?"
Không. Bảng dưới liệt kê từng thành phần.

| Thành phần | Mã của ai | Bằng chứng |
| --- | --- | --- |
| Học skill (GEPA `optimize_anything`, reflection, chọn ứng viên, dừng theo `max_metric_calls`) | **gskill**, gọi nguyên `train_optimize_anything.main()` với tham số dòng lệnh của gskill | `scripts/gskill_learn.py` chỉ bọc một đồng hồ tiền quanh `litellm.completion`, không đổi logic |
| Cấu hình agent khi học | **gskill**: `mini.yaml` mặc định (`cost_limit` 3, không có `model_kwargs`) | `docs/preregistration_main.md` §25, mục cấu hình học |
| Chạy agent khi chấm | **gskill**: `SWEHarness.setup_task` và `run_agent`, `mini.yaml` của gskill | `scripts/f1_probe.py` |
| Giới hạn 50 bước | **gskill** đặt cứng: `swe_harness.py:177`, `agent_config["step_limit"] = 50` | áp như nhau khi học và khi chấm, cho cả hai nhánh |
| Bộ chấm L (của gskill) | hàm `verify_with_patch` của **gskill**. Mình chép lại khoảng 10 dòng điều khiển của `evaluate/mini_swe_agent.py::evaluate_single_task` (dòng 92–115): không có patch → `no_patch`; F2P; nếu F2P qua thì chạy cả bộ test | `scripts/f0_scorer_check.py::score_lenient`, khớp từng nhánh |
| Bộ chấm S (của SWE-smith) | **SWE-smith** 0.0.9, `run_evaluation` | mã gốc |
| Chia train/val/test | mình chép lại số học của `load_and_split_data` (`train_optimize_anything.py:381–434`) | `scripts/export_swesmith.py::gskill_split`, khớp từng bước: lọc `swesmith/<repo>`, dừng khi đủ dòng, `random.seed(seed)` rồi `shuffle`, thu nhỏ theo tỉ lệ, cắt lát |

**Viết trong paper:** "We run gskill's released code (commit 8c7b697) unmodified for learning, agent execution and its own scoring; the only changes are the model seed and a per-run cost cap, applied identically to both arms."

### A2. "Trần chi phí 0,30 USD mỗi lượt (mặc định của gskill là 3,0) có làm nhánh có skill thua không?"
Không. Trần này **chưa từng chặn lượt nào**.

- Trên 500 lượt chấm (F1, chấm skill, hai nhánh không rò rỉ, Bleve 4a), lượt đắt nhất tốn **0,127 USD**. Số lượt tốn ≥ 0,27 USD là **0**.
- Lý do đặt trần: chỉ để chặn trường hợp xấu nhất của ngân sách (số vận hành, `docs/number_provenance.md`).
- Nhánh có skill chạm 50 bước 14/100 lần, nhánh không skill 1/100 lần. Đây là giới hạn bước của chính gskill, giống hệt khi gskill tự chấm.

**Viết trong paper:** "A per-run cost cap of 0.30 USD was never binding (maximum observed 0.127 USD over 500 runs)."

### A3. "Seed 41 có làm sai lệch so với gskill không?"
- Cả hai nhánh dùng cùng seed.
- Trên Vertex AI, seed 0 nghĩa là "không đặt" (A14). Seed ≥ 1 cho đầu ra gần như tất định, đo được 107/109 ở phép kiểm §5.
- Lúc học, gskill **không** có seed, đúng như mã gốc (không có `model_kwargs`).

### A4. "Kết luận 'bộ chấm của gskill quá lỏng' có phải do bộ chấm mình viết lại không?"
Không.
- Bộ chấm L gọi chính `verify_with_patch` của gskill, và luồng điều khiển khớp `evaluate_single_task`.
- F0: một patch **không làm gì** (no-op) qua bộ chấm của gskill trên 96/96 task jinja, nhưng qua bộ chấm SWE-smith 0/96. Trên 5 repo khác, kết quả cùng chiều (`docs/preregistration_main.md` §25, bảng F0).
- Lời giải thích dùng mã của gskill: `verify_with_patch` coi là "đạt" khi chuỗi `"passed"` xuất hiện trong đầu ra.

**Viết trong paper:** cách gọi là "no-op patch", không phải "empty patch". Với patch rỗng, gskill trả `no_patch` trước khi chạy test.

### A5. "Nhánh 'không rò rỉ' có phải là sửa gskill không?"
- Đó là một **can thiệp của mình**: trong container của agent, lịch sử git được thay bằng một commit mồ côi, gỡ commit "Bug Patch". Container dùng để chấm không đổi.
- Nó được đăng ký trước là thí nghiệm **ngoài phạm vi** (§25 bước 3).
- Paper phải tách rõ hai kết quả:
  - kết quả trên đúng thiết lập của gskill: δ = +0,38;
  - kết quả khi không còn rò rỉ: δ_LF = +0,21; phần do rò rỉ Δ_leak = +0,17 [0,06; 0,28].
- Phần cải thiện do rò rỉ đều nằm ở các task **không có mô tả issue** (15 → 0).

**Viết trong paper:** "about 45% of the in-scope gain", không viết "most".

### A6. "Bleve có chạy đúng như gskill không?"
- Cùng mã, cùng quy trình, cùng các trần như jinja (§25 bước 4).
- Bleve là Go. Các bộ chấm vẫn là của gskill và SWE-smith; F0 trên Bleve: 30/30 qua bộ chấm L, 0/30 qua bộ chấm S.

### A7. "Skill Bleve ghi 'lệnh `go` không có'. Có phải môi trường của các tác giả làm agent thiếu công cụ không?"
Không. Đây là đặc điểm của chính image SWE-smith khi chạy qua cách gọi lệnh của mini-swe-agent. Đã kiểm thật ngày 07/11/2026 trên image gốc `swebench/swesmith.x86_64.blevesearch_1776_bleve.f2876b5e`, **chưa có thay đổi nào của mình**:
- image khai báo `PATH=/go/bin:/usr/local/go/bin:…` (Go 1.24.5);
- `docker exec … bash -lc 'which go'` cho **không thấy `go`**, vì login shell đặt lại `PATH` thành `/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`;
- `docker exec … sh -c 'which go'` cho `/usr/local/go/bin/go`;
- mini-swe-agent 1.17.5 gọi mọi lệnh bằng `bash -lc` (viết cứng trong `environments/docker.py`). Bản ghim này có lý do riêng: README của gskill không ghim phiên bản, và mã của gskill dùng trường cấu hình v1 (`docs/preregistration_main.md` §25);
- image mình dựng thêm (`FROM` image gốc, rồi chép mirror và `git fetch`) không đổi `PATH` hay biến môi trường nào.

Hệ quả:
- cả hai nhánh, cũng như lúc gskill tự học, đều không chạy được `go test`;
- skill học được đã tự ghi lại điều này. Việc chấm điểm vẫn chạy test Go trong container chấm riêng của SWE-smith và gskill.

**Viết trong paper:** "In the SWE-smith Go image, the agent's login shell (`bash -lc`, as mini-swe-agent runs commands) does not have `go` on PATH; this holds for both arms and for gskill's own training, and the learned Bleve skill records it."

## B. MemGovern

### B1. "Ô MemGovern có phải là MemGovern thật không?"
**Chỉ một phần, và paper phải nói rõ.**

| Thành phần | Của MemGovern? | Ghi chú |
| --- | --- | --- |
| Thẻ kinh nghiệm (121.475 thẻ, 48 repo) | có | `experience_data.json`, sha256 khớp con trỏ LFS |
| Chỉ mục ChromaDB, model embedding Qwen3-Embedding-0.6B | có | chromadb 1.5.9 (bản đầu tiên mở được chỉ mục), Qwen bản `97b0c614` |
| Server tìm kiếm `tools/experience_server.py`, công cụ `exp_search` / `exp_read` | có, import hoặc mount từ bản clone đã ghim, không chép | `scripts/memgovern.py` |
| Đoạn hướng dẫn (bước 3 "Search and Retrieve Experience" và docstring của công cụ) | có, nguyên văn | `memgovern.py::orig_instructions` |
| **Harness của agent** | **không**: mini-swe-agent 2.4.6, không phải SWE-agent | để nhánh `none` cùng harness với mọi ô khác |
| **Model** | **không**: cấu hình gốc ghi `openai/gpt-5`, temperature 1.0, `per_instance_cost_limit` 20; ô này dùng model nhỏ của thí nghiệm, seed 41, trần 1 USD, 250 bước | `config/dsv31t_agenticMemSearch_1220_13w.yaml` dòng 90–99 |
| Bộ lọc thẻ cùng repo | của mình (chống rò rỉ đáp án) | loại **0** thẻ, vì 48 repo của MemGovern không trùng repo nào trong 61 repo của E2 |

### B2. "Có phải các tác giả đặt hướng dẫn sai chỗ nên MemGovern thua?"
- **Bản 1 thì có (lỗi A102).** Hướng dẫn bị nối vào cuối mô tả issue, rồi tới workflow riêng của mini-swe-agent không có bước tìm kinh nghiệm. Kết quả: 0/10 task gọi công cụ.
- **Bản 2 đã sửa đúng vị trí và lời của cấu hình gốc:** bước 3 của workflow, kèm "(Apply insights from step 3 if available)" ở bước sửa mã. Vị trí được kiểm trên 10/10 prompt. Kết quả vẫn **0/10**.
- Hai bản đều được báo cáo. Bản 1 không được dùng làm bằng chứng về MemGovern.

### B3. "Vậy kết luận được gì?"
**Viết trong paper (đúng phạm vi):** "On our harness (mini-swe-agent) with a small model, the agent never invoked MemGovern's optional retrieval tools (0 of 20 runs across two instruction placements). We therefore could not evaluate MemGovern as a skill source; this says nothing about MemGovern with its own harness and model."

**Không được viết:** "MemGovern does not help", "MemGovern is ineffective", hay bất kỳ câu nào suy rộng ra harness SWE-agent hay model khác.

### B4. "Sao không ghép với nhánh `none` của E2 cho rẻ?"
- Phép kiểm "model không đổi" (§5, đăng ký trước) không đạt: chỉ 74–75/109 câu trả lời đầu tiên trùng E2, dù trường `model` trùng 109/109.
- Vì vậy cả hai nhánh được chạy mới, cùng lúc.
- Đây là bằng chứng rằng chỉ ghép theo **tên** model là không an toàn.

### B5. "Ô dừng sau 10 task có phải là dừng tùy tiện không?"
- Quy tắc kiểm thao tác được chốt trong M-4 **trước** khi có dữ liệu bản 2: dừng nếu 0/10 task gọi `exp_search`.
- @thuthuy quyết định đóng ô (07/11).
- Chưa tính Z hay e-process nào của ô, nên không có kết quả Gatekeeper nào bị chọn lọc.

## C. Quy tắc chung rút ra (để không tái phạm)

1. **Dùng mã gốc.** Khi không gọi được hàm gốc (ví dụ phải tải dữ liệu ở nơi khác), phần chép lại phải được đối chiếu từng dòng và ghi số dòng của bản gốc, như ở A1.
2. **Mọi thay đổi cấu hình của hệ thống bên thứ ba** (seed, trần, harness, model, vị trí hướng dẫn) phải nằm trong một bảng như B1. Thay đổi nào có thể làm hệ thống đó thua (một trần, một giới hạn) phải kèm số đo chứng minh nó không chặn (như A2), hoặc được ghi là giới hạn.
3. **Hệ thống dựa trên công cụ** cần một phép kiểm thao tác trên model thật (L48t) và đối chiếu vị trí hướng dẫn trong prompt với bản gốc. Mục này đã có trong `docs/research_rules.md` §4.
4. **Câu chữ trong paper** chỉ được rộng bằng thiết lập đã chạy (B3).
