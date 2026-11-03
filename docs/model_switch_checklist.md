# Danh sách việc khi đổi hoặc thêm model (chỉ làm khi @thuthuy ra lệnh)

> **Tiền thật.** Thứ tự các bước là bắt buộc. Không bước có chi phí nào (Phần D) được chạy khi Phần A, B, C chưa đánh dấu xong **và** chưa ghi một mục review trong `docs/review_log.md`.
> Lý thuyết, phép đo và chuẩn **không đổi** theo model (xem §0). Danh sách này chỉ gồm những gì **phụ thuộc vào model** trong mã, cấu hình, con số và tài liệu, đã soát ngày 03/11/2026 trên mã hiện có.

Ký hiệu: 👤 = @thuthuy làm hoặc quyết, 🤖 = tôi làm. Mỗi mục có **tiêu chí xong** kiểm được.

## 0. Phần không đổi (để không làm thừa)

- **Không đổi:**
  - lý thuyết e-process (Ville; Waudby-Smith & Ramdas): giả định duy nhất là loss nằm trong [0, 1];
  - loss = 1[không giải được] do harness chấm;
  - ICH E9(R1);
  - quy ước SWE-bench cho bản vá không áp được và test quá giờ;
  - thiết kế cặp, kiểm định đổi dấu chính xác, Holm.
- **Không cần pilot lại.** Phần phụ thuộc model được đo trên các lô đầu của chính thí nghiệm (D3) hoặc lấy từ tài liệu công bố của nhà cung cấp (Phần B).
- **Thay đổi về diễn giải (viết trong paper):** STR(S, s) được định nghĩa với một agent π cụ thể. Mọi kết luận admit hay không admit là **cho model đó**. Mỗi model là một phần riêng, **không gộp dữ liệu**.

## A. Quyết định của @thuthuy (trước mọi việc khác)

| # | Việc | Tiêu chí xong |
| --- | --- | --- |
| A1 👤 | Chọn model và **kênh gọi**: API của nhà cung cấp, hay Vertex AI Model Garden | Ghi tên model, kênh, ngày vào §E |
| A2 👤 | Duyệt ngân sách cho model này, **bằng USD** | Ghi vào `CLAUDE.md` (dòng "Mức hiện tại"). Nếu chị duyệt bằng VND: tỉ giá quy đổi lấy từ một nguồn có ngày (ngân hàng phát hành thẻ), ghi kèm. Phí thẻ ngoại tệ tính vào phần đã chi. |
| A3 👤 | Thiết lập key hoặc quyền cho kênh đã chọn. **Tôi hỏi tình trạng trước, không gợi ý thiết lập khi chưa hỏi** (L21) | Chị xác nhận đã có. Tên secret trên GitHub được ghi vào bảng khóa của `docs/vertex_setup.md` (chỉ tên và 8 ký tự đầu của mã khóa, không ghi khóa) |
| A4 👤 | Model là thí nghiệm **thay thế** hay **thêm** (lặp lại trên model thứ hai) | Ghi vào bản đăng ký trước (C1) |

## B. Đọc nguồn công bố (R1: bản gốc, lấy qua `configs/sources.json` → workflow `sources`, kiểm đoạn trích chứa đúng câu)

| # | Thông tin cần | Vì sao bắt buộc | Tiêu chí xong |
| --- | --- | --- | --- |
| B1 🤖 | **Giá** mỗi 1M token: đầu vào, đầu vào có cache, đầu ra, và token suy luận tính vào loại nào | Bộ chặn ngân sách và `spent_usd` tính từ giá này (`estimate_cost_usd`, `litellm_registry`). Giá hiện của Gemini lấy từ bảng của litellm (`_verified: false` trong `configs/models/vertex_gemini.json`), **chưa phải trang của Google**. Lỗi này áp dụng cả cho model mới. | Trang giá chính thức có trong `sources-snapshots`. File cấu hình model có `_verified: true` và trích câu nguồn. |
| B2 🤖 | **Định danh phiên bản** của model (bản ghim có ngày, hay tên gọi chung có thể trỏ sang bản mới) | Một tên gọi chung đổi bản giữa chừng thì hai nửa thí nghiệm là hai model khác nhau | Ghi trong §E; nếu chỉ có tên gọi chung thì bật kiểm tra D4 |
| B3 🤖 | **Mốc cắt dữ liệu huấn luyện** do nhà cung cấp công bố | Phân tích nhiễm dữ liệu (bản đăng ký trước E2, mục nhiễm dữ liệu) hiện dùng mốc của Gemini (01/2025, nguồn `gemini_31_flash_lite_cutoff`). Không có nguồn thì không được viết "không nhiễm" cho model mới. | Có nguồn trong `configs/sources.json` và đoạn trích |
| B4 🤖 | **Seed**: API có nhận tham số seed không, có lặp lại được không | Mã hiện chặn seed = 0 vì Vertex coi 0 là "không đặt" (`arm_config`, đã thử). Nhánh đối chứng nhiễu `control-none-seed1` dựa trên "chỉ khác seed". Nếu API bỏ qua seed: các lần lặp vẫn độc lập, đại lượng ước lượng không đổi, nhưng phải ghi rõ trong paper là seed chỉ là nhãn của lần lặp. | Ghi câu trích, và kết quả thử 2 lời gọi cùng seed (giống hay khác) như đã làm với Vertex ngày 02/11 |
| B5 🤖 | **Gọi công cụ** (function calling) và gọi song song | mini-swe-agent 2.4.6 gọi công cụ `bash`, với `parallel_tool_calls: true` (đọc trong trajectory thật) | Câu trích xác nhận có hỗ trợ; nếu không thì dừng, báo @thuthuy |
| B6 🤖 | **Cửa sổ ngữ cảnh** (số token tối đa mỗi lời gọi) | Đo trên 1.071 lần chạy thật của pilot với Gemini (1.061 Flash-Lite, 10 Flash): lời gọi lớn nhất **130.532 token**. 1 lần chạy vượt 128.000; không lần nào vượt 163.840. Model có cửa sổ nhỏ hơn sẽ gặp `ContextWindowExceededError` thường hơn. Lỗi này tính là hành vi của agent (không giải được), hợp lệ, nhưng phải báo cáo. `litellm_registry` đang ghi cứng `max_input_tokens: 1_048_576` | Số chính thức ghi trong §E và trong file cấu hình model |
| B7 🤖 | Giới hạn tốc độ (số yêu cầu và số token mỗi phút) | Lỗi vượt giới hạn là lỗi hạ tầng, không phải agent. Số worker phải nằm dưới giới hạn. | Ghi số; chọn `--workers` × `--arm-parallel` không vượt |
| B8 🤖 | Chế độ suy luận (thinking) và nhiệt độ mặc định | Đây là **định nghĩa can thiệp** (R2): phải đăng ký trước, không chọn sau khi xem kết quả. Cấu hình Gemini Flash-Lite hiện không đặt `reasoning_effort` và không đặt nhiệt độ (dùng mặc định của nhà cung cấp). | Ghi giá trị chọn, câu trích về giá trị mặc định, vào bản đăng ký trước |
| B9 🤖 | Điều khoản dùng dữ liệu của API | Đề bài, mã repo và nội dung rule XRepoSkill được gửi tới API (gửi đi không phải phân phối lại, nhưng phải biết chính sách) | Câu trích trong `docs/number_provenance.md` hoặc phụ lục |

## C. Sửa mã và tài liệu (review trước khi chạy, R3)

| # | Chỗ phải sửa | Vấn đề hiện tại | Tiêu chí xong |
| --- | --- | --- | --- |
| C1 🤖 | Bản đăng ký trước của thí nghiệm dùng model mới | Model, kênh, phiên bản, chế độ suy luận, ngân sách, phân tích riêng theo model. Ghi **trước** khi chạy (R5) | Commit có ngày, trước mọi lần chạy có chi phí |
| C2 🤖 | File cấu hình model mới trong `configs/models/` | Giá từ B1, cửa sổ ngữ cảnh từ B6, các tham số từ B8, biến môi trường cần có | Có `_verified: true` và nguồn |
| C3 🤖 | `src/gatekeeper/pilot.py` `load_model_specs` | **Từ chối mọi model không bắt đầu bằng `vertex_ai/`.** Nếu dùng API của nhà cung cấp thì phải mở rộng, nhưng giữ kiểm tra theo danh sách kênh được phép. | Test cho kênh mới và test vẫn từ chối kênh lạ |
| C4 🤖 | `litellm_registry` | Ghi cứng `"litellm_provider": "vertex_ai"` và `max_input_tokens` 1.048.576. Đã đọc `minisweagent/models/litellm_model.py` (dòng 108–126, chế độ `cost_tracking: default` mà ta dùng). Hai trường hợp: (a) litellm không tính được giá thì mỗi lần chạy dừng ngay ở lời gọi đầu với lỗi, nên tốn ít nhưng không chạy được; (b) litellm tính được giá nhưng bằng **giá khác giá thật** (ví dụ lấy từ bảng đi kèm của nó thay vì bảng ta đăng ký), khi đó `cost_limit` và `spent_usd` đều theo giá sai. Trường hợp (b) là trường hợp tốn tiền. | Lấy nhà cung cấp và cửa sổ từ file cấu hình. Ở D2: `instance_cost` của một lời gọi bằng đúng số tính tay từ giá B1 và số token |
| C5 🤖 | `traj_usage` (đọc token từ trajectory) | `spent_usd` lấy `instance_cost` do mini-swe-agent/litellm tính. Chỉ khi số này bằng 0 mới tính bù bằng `estimate_cost_usd` từ token. Token còn dùng cho báo cáo (token vào, cache, ra). Mã đọc `prompt_tokens`, `completion_tokens`, `prompt_tokens_details.cached_tokens` hoặc `cache_read_input_tokens`. Tên trường của nhà cung cấp mới có thể khác. Ở đường tính bù: đọc thiếu token cache thì ghi **cao hơn thật**; token suy luận không nằm trong `completion_tokens` thì ghi **thấp hơn thật**. | Kiểm trên trajectory của D2: tổng token khớp số nhà cung cấp trả về; kiểm lại ở D5 |
| C6 🤖 | `arm_config` chặn seed = 0 | Quy tắc dành cho Vertex | Giữ hoặc đổi theo B4, có test |
| C7 🤖 | `AGENT_EXIT_STATUSES` và `is_infra_failure` | Danh sách loại lỗi lập từ Gemini/litellm. Lỗi mới của nhà cung cấp phải được xếp đúng nhóm theo **quy tắc đã có** (ICH E9(R1); A37: lỗi của agent không bao giờ được chạy lại) | Mỗi loại lỗi mới gặp ở D2–D3 được xếp nhóm, ghi vào `docs/audit_pilot.md` |
| C8 🤖 | `scripts/combine_runs.py`, `analyze_g1_final.py`, `rq1_mini.py` | **Hiện không kiểm** các file gộp có cùng model hay không | Dừng khi trường `model` khác nhau giữa các file gộp; có test |
| C9 🤖 | `scripts/preflight.py` [secrets] | Chỉ nhận dạng khóa PEM và trường `private_key` (khóa Google). **Key dạng chuỗi của nhà cung cấp khác sẽ lọt qua.** | Thêm mẫu theo **định dạng key do nhà cung cấp công bố** (B1/A3, không đoán). Test bằng key giả bị chặn. |
| C10 🤖 | `xreposkill_select.py` (`--model` mặc định Gemini), `e2-shards.yml` (`MODEL=gemini-flash-lite`, bước xác thực GCP), `pilot.yml`, `vertex-check.yml`, `run_e2.sh`, các script trong scratchpad | Tên model và xác thực ghi cứng | Model là tham số bắt buộc, không mặc định (quy tắc "hàm nhận con số khoa học không có mặc định" mở rộng cho model) |
| C11 🤖 | E2: bước chọn rule XRepoSkill dùng cùng backbone với agent | Đổi model thì rule được chọn đổi, nên tập task kích hoạt và SHA-256 của file hướng dẫn đổi | Chạy lại `xreposkill_select.py` với model mới **trước** khi chạy agent; ghi SHA mới; tập task chốt trước |
| C12 🤖 | `docs/number_provenance.md` | Các con số đo trên Gemini: 0,0706 USD/lần chạy, khoảng 1,42M token vào/lần, 92% cache, thời gian lô (lề dừng `--stop-after-min` / `--batch-min`), power trong `docs/method_check.md` | Mỗi số được đánh dấu "của Gemini". Số của model mới chỉ thêm sau D3, kèm nguồn đo |
| C13 🤖 | `tests/test_pilot.py` | Test khẳng định đúng 3 model Gemini | Sửa test theo file cấu hình mới, không xóa test cũ |
| C14 🤖 | Chạy `python scripts/preflight.py`, review theo `docs/research_rules.md` §4, ghi `docs/review_log.md` | — | PASS và có mục review |

## D. Chạy có chi phí, theo bậc (dừng ngay khi một bậc không đạt)

| # | Bậc | Chi phí | Tiêu chí đạt |
| --- | --- | --- | --- |
| D1 🤖 | Chạy thử miễn phí (mô hình giả lập) trên ít nhất 1 task thật, như quy trình bước 6 | 0 | oracle giải được, nhánh không skill không giải được, `runs == scored` |
| D2 🤖 | **Một lời gọi thật** (như `vertex-check.yml`: vài token) | gần 0 | Trả lời được. Trường `model` trả về khớp B2. Có `instance_cost > 0` hoặc giá tính được (C4). Tên trường token đọc đúng (C5). |
| D3 🤖 | **Một lô bình thường đầu tiên** của thí nghiệm (không phải lô bỏ đi: kết quả được tính nếu đạt) | bị chặn bởi bộ chặn sẵn có: số nhánh × số task × `cost_limit` ≤ trần còn lại | Đo chi phí, token, tỉ lệ cache, số lời gọi, thời gian lô, tỉ lệ lỗi theo nhóm. Kiểm `infra_failures`, `endpoint_mismatch`, `patch_apply_failed`, `harness_test_timeout`. |
| D4 🤖 | Kiểm phiên bản model | 0 | Mọi lời gọi trong lô có cùng trường `model` trả về. Nếu khác: dừng, báo @thuthuy (L12: đổi thiết kế giữa chừng là giai đoạn riêng). |
| D5 👤🤖 | **Đối chiếu hóa đơn** của nhà cung cấp với `spent_usd` sau lô D3 | 0 | Lệch thì dùng số của hóa đơn làm số đã chi (L8: trần tính từ số đã chi thực tế). **Mục C5 trong `docs/audit_pilot.md` (đối chiếu hóa đơn Google) vẫn đang mở cho Gemini.** |
| D6 🤖 | Kiểm `cost_limit` không ràng buộc | 0 | Lần chạy đắt nhất ở D3 < `cost_limit`, như cách đã kiểm cho Gemini trong `docs/number_provenance.md`. Lần chạy chạm giới hạn được ghi là kết quả bị cắt. |
| D7 🤖 | Chạy tiếp trong ngân sách đã duyệt | theo A2 | Chạm mức đã duyệt thì dừng, chờ @thuthuy |

## E. Sổ ghi (điền khi đổi)

| Mục | Giá trị | Nguồn hoặc lần đo |
| --- | --- | --- |
| Model, kênh, ngày | | A1 |
| Phiên bản ghim | | B2 |
| Giá vào / cache / ra (USD mỗi 1M token) | | B1 |
| Mốc cắt dữ liệu | | B3 |
| Seed được nhận? Lặp lại được? | | B4 |
| Cửa sổ ngữ cảnh | | B6 |
| Giới hạn tốc độ | | B7 |
| Chế độ suy luận, nhiệt độ | | B8 |
| Ngân sách đã duyệt (USD), tỉ giá nếu có | | A2 |
| Chi phí mỗi lần chạy, token, tỉ lệ cache (đo) | | D3 |
| Chênh lệch giữa hóa đơn và số tự tính | | D5 |
