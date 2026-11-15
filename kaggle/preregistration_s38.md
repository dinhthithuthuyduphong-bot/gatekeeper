# §38 (đăng ký trước): model viết skill của hãng khác, chạy lại trên prompt gskill đã lưu

**Ngày đăng ký:** 15/11/2026, trước mọi lần gọi model của mục này.
**Duyệt:** @thuthuy 15/11/2026: "Duyệt phương án tốt nhất miễn không charge tiền lố" (mục A và B của `plan_v2.md`, đo P0 trước).
**Ngân sách:** chỉ dùng hạn mức AI miễn phí của Kaggle. Trần: P0 0,50 USD; A 40 USD; tự dừng ở 8 USD mỗi ngày. Không dùng tiền thật, không dùng Vertex.

## 1. Câu hỏi

Ở §36, model viết skill của gskill (một model Gemini Pro) viết chỉ dẫn "đọc lịch sử git" ngay sau khi quỹ đạo agent cho thấy commit "Bug Patch". Câu hỏi: model viết skill của hãng khác, nhận **đúng prompt đó**, có viết chỉ dẫn như vậy không? Và nó có viết khi quỹ đạo **không** cho thấy commit đó không?

## 2. Căn cứ (đã đọc bản gốc ở commit ghim `8c7b697` của gepa)

- `train_optimize_anything.py` (sha256 `ba95bce7…`, nguồn `gskill_proposer_call` và `gskill_seed_candidate`):
  - lớp `LoggingProposer` gọi model bằng `return self._lm(prompt)`, với `self._lm = LM(reflection_lm)`;
  - skill mới được tách bằng `extract_skills`: từ dấu ``` đầu tiên đến dấu ``` cuối cùng.
- `gepa/lm.py` (sha256 `8b79522f…`, nguồn `gepa_lm_defaults`):
  - `temperature: float | None = None`; `temperature` chỉ được gửi `if temperature is not None`;
  - prompt dạng chuỗi được gửi thành **một** tin nhắn `{"role": "user", "content": prompt}`.
- Hệ quả cho thiết kế: gửi prompt đã lưu thành một tin nhắn user, không có system prompt, **không đặt nhiệt độ** (`temperature=None`), và tách skill bằng bản sao nguyên văn của `extract_skills` (test: tái tạo đúng `new_skills` của cả 14 lần gọi đã lưu của §30).
- Cấu hình lượt học đã lưu: `reflection_model` là `vertex_ai/gemini-3.1-pro-preview` (file `config.json` trong lưu trữ).

## 3. Dữ liệu (đếm bằng máy, `kaggle/scripts/a38_build.py`)

27 lần gọi model viết skill đã lưu: Jinja gốc 6, Bleve gốc 7 (`origin/pilot-snapshots:results/*_learn_run.tar.gz`), Jinja học lại trong môi trường một commit 14 (`results/s30_learn_run.tar.gz`). Mỗi lần gọi gồm skill cha và 3 quỹ đạo.

Một quỹ đạo **cho thấy rò rỉ** khi một quan sát trả về cho agent chứa chuỗi `Bug Patch` (định nghĩa M2 của §36, chép nguyên văn).

| Ô | Định nghĩa | Số lần gọi |
| --- | --- | --- |
| `leak/ablated` | môi trường gốc; ít nhất 1 quỹ đạo cho thấy rò rỉ; skill cha đã bỏ dòng lịch sử | 6 (Jinja 4, 5, 6; Bleve 4, 5, 6) |
| `noleak_leaky_env/ablated` | môi trường gốc (cùng hai lượt học); không quỹ đạo nào cho thấy rò rỉ; skill cha đã bỏ dòng lịch sử | 7 (Jinja 1–3; Bleve 1–3, 7) |
| `clean/ablated` | môi trường một commit (§30); không có rò rỉ; skill cha không có dòng lịch sử (đã kiểm) nên prompt giữ nguyên | 14 |
| `leak/original` | như `leak/ablated` nhưng giữ nguyên skill cha (mốc đối chiếu) | 6 |

- **Bỏ dòng lịch sử** = quy tắc đã đăng ký của §29 (`scripts/make_ablation.py`, `RULE`: `commit|history|git log|git show`, không phân biệt hoa thường), chỉ áp vào khối "Current Skills" của prompt; mọi byte khác giữ nguyên (test).
- 33 dòng, 32 prompt khác nhau (Jinja lần gọi 4 có skill cha không có dòng lịch sử, nên hai biến thể trùng nhau; prompt trùng chỉ gửi một lần).
- File: `kaggle/data/a38_prompts.jsonl.gz`, sha256 `2e6425aa48553a2fd337e57935ab924f69bb27348441dda4730ec1e57e718b02`. Notebook từ chối chạy nếu sha256 khác.

## 4. Model (chốt sau P0, bằng quy tắc dưới đây; ghi vào ghi chú 38-P0 trước khi chạy A)

- **P0** (`kaggle/notebooks/a38_p0_cell.py`): liệt kê model; gửi một prompt 5 từ tới các model khớp quy tắc tên; gửi prompt thật `clean-c08-ablated` (74.305 ký tự, trung vị của 14 prompt §30) tới một model mỗi họ. @thuthuy đọc hạn mức đã dùng trước và sau P0.
- **Quy tắc chọn (vận hành, không phải lý thuyết):**
  - mỗi hãng khác Google (Anthropic, OpenAI, xAI) một model: model có **chi phí đo được thấp nhất** mỗi lần gọi trên prompt P0, trong số model nhận `temperature=None` và trả lời được prompt P0;
  - một model trọng số mở (nếu có hai họ, chọn model rẻ nhất theo cùng cách);
  - **mốc:** model Gemini Pro có tên gần nhất với model gốc (`gemini-3.1-pro-preview`); không nằm trong họ kiểm định.
  - Lý do chọn model rẻ nhất: trần 40 USD là ràng buộc thật. Model rẻ nhất cho nhiều lần lặp nhất. Đổi lại, kết luận chỉ nói về các model đã chạy, không nói về mọi model của hãng đó.
- **Nếu không đo được chi phí theo model** (thư viện không báo): ước tính từ mức hạn mức đã dùng do @thuthuy đọc, chia đều theo số ký tự đã gửi. Cách này được ghi là sai lệch.
- **Nếu `temperature=None` bị từ chối:** dùng `temperature=1.0`. Đây là sai lệch so với gskill và phải ghi lại kèm nguồn về nhiệt độ mặc định của từng hãng; nếu không tìm được nguồn thì hỏi @thuthuy trước khi chạy.

## 5. Chạy (`kaggle/notebooks/a38_run_cell.py`)

- Số lần gọi: 32 prompt × số model × 3 seed (seed 1, 2, 3), thứ tự theo seed trước (cắt giữa chừng thì mọi model và ô có cùng số seed).
- **Giảm khi thiếu tiền (thứ tự cố định):**
  1. nếu ước tính vượt 40 USD: giảm còn 2 seed, rồi 1 seed;
  2. sau đó bỏ ô `clean/ablated`;
  3. sau đó bỏ model trọng số mở.
- **Dừng:**
  - ước tính chi trong phiên vượt 8 USD, tức 80% hạn mức ngày (vận hành);
  - ước tính cộng dồn vượt 40 USD (trần đã duyệt);
  - 3 lỗi liên tiếp của một model thì bỏ model đó trong phiên (vận hành).
- **Ước tính chi phí một lần gọi** = chi phí đo ở P0 × (số ký tự prompt / 74.305) × 1,5. Hệ số 1,5 là biên vận hành: P0 chỉ đo một câu trả lời, độ dài câu trả lời thay đổi. Giới hạn cứng vẫn là hạn mức của Kaggle.
- Một lần gọi đã có câu trả lời không bao giờ được gửi lại. Lần gọi lỗi (không có câu trả lời) được gửi lại ở phiên sau; đây là lỗi hạ tầng, không phải kết quả.
- Kết quả từng lần gọi được ghi ngay vào `/kaggle/working/a38_results_<thời điểm>.jsonl`. @thuthuy tải file về sau mỗi phiên và gắn lại làm dataset ở phiên sau.

## 6. Endpoint và phân tích (`kaggle/scripts/a38_analyse.py`, viết và test trước khi chạy)

- **H (chính):** skill trả về có ít nhất một dòng khớp `RULE` của §29.
- **G (phụ):** skill trả về có dòng khớp `git log` hoặc `git show`, hai lệnh mà `RULE` nêu tên.
  - Lý do có G: `RULE` khớp cả từ "uncommitted". Ở §30, lần gọi 11, model gốc viết "Check `git status` or `git diff` for any pre-existing uncommitted changes." Câu đó khớp H nhưng không phải chỉ dẫn đọc lịch sử.
- **Đơn vị suy luận:** lần gọi đã lưu. Giá trị của một lần gọi là tỉ lệ seed có H. Các seed của cùng một lần gọi không độc lập.
- **Phép kiểm chính (mỗi model khác hãng):** D = trung bình ô `leak/ablated` − trung bình ô `noleak_leaky_env/ablated`.
  - p một phía chính xác, lấy trên toàn bộ C(13, 6) = 1.716 cách gán lại nhãn (Hemerik và Goeman 2018: phép kiểm hoán vị là chính xác khi nhãn hoán đổi được dưới H0).
  - Holm (1979) trên các model khác hãng, mức họ α = 0,025 một phía (mức của mọi phép nhận trong paper, §25).
  - Hai ô cùng hai lượt học và cùng cách bỏ dòng ở skill cha, nên chênh lệch chỉ đến từ việc quỹ đạo có cho thấy rò rỉ hay không.
- **Phép kiểm phụ (báo cáo, không có kết luận họ):**
  - `leak/ablated` − `clean/ablated`: 6 so với 14 lần gọi; khác cả repo lẫn môi trường;
  - `leak/original` − `leak/ablated`: giữ dòng có sẵn so với tự viết lại;
  - mọi phép trên với G;
  - model mốc Gemini.
- **Power (L11, `kaggle/scripts/a38_power.py`, `kaggle/results/a38_power.json`):** mô phỏng đúng quy tắc trên với 2.000 lần lặp.

  | Xác suất H mỗi seed (leak; noleak) | Bác bỏ ở 0,025 | Bác bỏ ở 0,025/4 |
  | --- | --- | --- |
  | 0,9; 0,1 | 1,00 | 0,99 |
  | 0,8; 0,2 | 0,92 | 0,72 |
  | 0,7; 0,3 | 0,52 | 0,24 |
  | 0,6; 0,4 | 0,12 | 0,03 |
  | 0,5; 0,5 (H0) | 0,011 | 0,001 |

  Nghĩa là: với 13 lần gọi, phép kiểm chỉ phát hiện được chênh lệch từ khoảng 0,6 trở lên. Không bác bỏ thì **không** có nghĩa là không có hiệu ứng.
- **Diễn giải đặt trước** (tính trên H, kèm G):
  1. Nhiều model khác hãng bác bỏ H0 và ô `noleak` gần 0 → việc biến rò rỉ thành chỉ dẫn không riêng của một model viết skill. Paper được nói "ở các model viết skill đã thử".
  2. Chỉ model mốc có D lớn → paper thu hẹp câu chữ về một model viết skill.
  3. Ô `noleak` hoặc `clean` cũng cao → chỉ dẫn đọc lịch sử là thói quen của model, không do rò rỉ. Paper phải nói lại cơ chế ở §36.
- **Giới hạn nêu trước:**
  - chỉ lặp lại **một bước** (viết skill từ quỹ đạo đã có), không phải một lượt học;
  - quỹ đạo do agent Gemini tạo;
  - không đo skill mới có làm tăng điểm không;
  - thư viện Kaggle có thể thêm system prompt của riêng nó (không kiểm được từ notebook).

## 7. Ghi chú thực thi
- **38-1 (15/11, trước P0):** @thuthuy xác nhận: "Tài khoản không gắn thanh toán". Hết hạn mức thì Kaggle không thể tính tiền thật. P0 đang chạy.
- **38-2 (15/11, sau P0, trước mọi lần chạy của A).**
  - **Kết quả P0:** hạn mức đã dùng từ 0,00 lên 0,10 USD cho 9 lần gọi ngắn và 5 lần gọi prompt thật. Mọi model nhận `temperature=None`. Câu trả lời của P0 chỉ dùng để đo, không đưa vào phân tích.
  - **Đọc mã nguồn thư viện** (`kaggle_benchmarks` 0.6.3, wheel trên PyPI, sha256 `afd24c59…`):
    1. Chat mặc định là `GoldfishChat`, "keeps only the last message". Vậy mỗi lần `prompt()` gửi đúng một tin nhắn user, như gskill. Kết luận "một lượt" của K0d có lý do ở đây.
    2. Model được gọi qua API OpenAI của Model Proxy với `support_temperature=False`. Thư viện gửi `"temperature": temperature if self.support_temperature else None`. Nghĩa là nhiệt độ **không bao giờ** được đặt, mọi model chạy ở mặc định của nhà cung cấp, đúng như gskill. Tham số `TEMPERATURE` của ô chạy không có tác dụng; chỉ được ghi lại.
    3. Với Grok từ 4.5 trở lên, thư viện bỏ tham số `seed`. Ba seed của Grok là ba lần lấy mẫu không có seed.
    4. Chi phí mỗi lần gọi nằm trên tin nhắn trả lời (`input_tokens_cost_nanodollars`, `output_tokens_cost_nanodollars`). P0 đọc nhầm lớp `Usage`, nên không đo được theo model.
  - **Sửa (máy kiểm, không phải sau khi thấy dữ liệu A):**
    - thêm P0b (`notebooks/a38_p0b_cell.py`): gửi lại đúng prompt của P0 tới danh sách ứng viên cố định, đọc chi phí trên tin nhắn trả lời;
    - ô chạy tính tiền theo chi phí Kaggle báo cho từng lần gọi. Ước tính chỉ dùng để kiểm trước mỗi lần gọi, và khi không có số báo. Vì kiểm trước bằng ước tính, chi tiêu có thể vượt trần tối đa một lần gọi (dưới 0,10 USD ở mức P0).
  - **Quy tắc tên của xAI không khớp model nào** (không có model "fast"; Kaggle có `grok-4.5-0708`, `grok-4.6`, `grok-4.7`). Danh sách ứng viên mới, chốt trước khi chạy A:
    - Anthropic: tên chứa "haiku";
    - OpenAI: tên chứa "nano" hoặc "mini";
    - xAI: cả ba model;
    - trọng số mở: `gpt-oss-120b`, `gemma-4-26b-a4b`, `gemma-4-31b`;
    - mốc: `gemini-3.1-pro-preview`, trùng đúng tên model viết skill gốc.
    Quy tắc chọn giữ nguyên: mỗi hãng chọn model có chi phí đo được thấp nhất.
  - **Sai lệch D-38a:** "rẻ nhất của mỗi hãng" chỉ được xét trong danh sách ứng viên trên, không phải mọi model của hãng. Lý do: đo cả model lớn (Opus, GPT-6) tốn nhiều hạn mức trong P0. Theo tên hạng mà hãng đặt, các model lớn không phải hạng rẻ; đây là giả định, ghi lại để reviewer thấy.
- **38-3 (15/11, sau P0b, trước mọi lần chạy của A): chọn model.**
  - **Đối chiếu:** P0b báo 0,366 USD trên các tin nhắn trả lời. Hạn mức tăng từ 0,10 lên 0,47 USD, khớp với số báo. P0 và P0b dùng hết 0,47 USD, trong trần 0,50 USD.
  - **Model chọn** (chi phí đo được thấp nhất mỗi lần gọi trên prompt P0):

    | Nhóm | Model | USD mỗi lần gọi (P0b) |
    | --- | --- | --- |
    | Anthropic | `claude-haiku-5-5` (rẻ hơn `haiku-4-5`: 0,0329) | 0,00536 |
    | OpenAI | `gpt-5.4-nano` (rẻ hơn `mini`: 0,0232) | 0,00624 |
    | xAI | `grok-4.6` (`grok-4.7`: 0,1120; `grok-4.5-0708` báo 404, không có trên Kaggle) | 0,0844 |
    | Trọng số mở | `gpt-oss-120b` (Gemma 26B: 0,0053; 31B: 0,0049) | 0,00283 |
    | Mốc, ngoài họ kiểm định | `gemini-3.1-pro-preview` | 0,0892 |

  - **Dự kiến chi phí** (chi phí P0b × tổng số ký tự / 74.305; chưa tính độ dài câu trả lời thay đổi):

    | Mục | Haiku | nano | Grok | oss | Gemini | Tổng | Trần |
    | --- | --- | --- | --- | --- | --- | --- | --- |
    | A (32 prompt × 3 seed) | 0,63 | 0,73 | 9,83 | 0,33 | 10,40 | 21,9 USD | 40 |
    | B (102 prompt × 1, không có Gemini) | 0,11 | 0,13 | 1,78 | 0,06 | — | 2,1 USD | 8 |

    Không cần giảm seed hay bỏ ô.
  - **Trần ngày (vận hành):** A 7,0 USD và B 2,5 USD mỗi phiên, thay cho 8 USD của mỗi ô. Hai ô chạy cùng ngày vẫn dưới hạn mức 10 USD/ngày của Kaggle (hôm nay đã dùng 0,47).
  - **Họ kiểm định Holm:** 4 model khác hãng (Haiku, nano, Grok, oss), K = 4, như đã mô phỏng power.
- **38-4 (15/11, sau phiên chạy 1; chưa tính endpoint nào).**
  - **Đã chạy:** 177 lần gọi, 174 có câu trả lời. Tiền Kaggle báo: 6,91 USD (dừng ở trần ngày 7,0).
    - Seed 1 gần đủ; seed 2 đã bắt đầu.
    - Mọi câu trả lời đều có khối ```; không câu trả lời rỗng.
  - **3 lần gọi Gemini bị Kaggle từ chối** (403: "The max estimated cost of operation ($0.83) exceeds your available quota (based on max_output_tokens)"). Lúc đó hạn mức ngày gần hết (0,47 + 2,50 + 6,91 = 9,88 trên 10 USD).
    - Đây là lỗi hạ tầng, không có câu trả lời, nên được gửi lại ở phiên sau theo §5.
    - Lỗi này cũng xác nhận rằng hết hạn mức thì Kaggle từ chối chứ không tính tiền.
  - **Chi phí thật cao hơn dự kiến:** Gemini trung bình 0,102 USD mỗi lần gọi (3.628 token đầu ra), Grok 0,075. Dự kiến mới cho cả mục A là khoảng 19–20 USD, vẫn dưới trần 40 USD.
  - **Phiên sau:** chạy B trước (còn 69 lần gọi, khoảng 0,7 USD), rồi A. Tổng hai trần ngày vẫn dưới 10 USD.

