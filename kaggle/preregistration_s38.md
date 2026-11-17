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
- **38-5 (16/11, sau phiên chạy 2; chưa tính endpoint nào).** 324 lần gọi, 321 có câu trả lời; 0 lần gọi trùng. Seed 1 và 2 đủ cho cả 5 model (32/32 mỗi seed); 3 lần gọi Gemini bị từ chối hôm 15/11 đã được gửi lại và có câu trả lời. Tiền Kaggle báo cộng dồn: 13,73 USD. Còn seed 3 (159 lần gọi, khoảng 7 USD): một phiên nữa.

- **38-6 (17/11, sau phiên 3; kết quả).**
  - **Dữ liệu:** 480/480 lần gọi có câu trả lời (5 model × 32 lần gọi × 3 seed). Phiên 3: 159 lần gọi, 4,61 triệu token vào, 0,50 triệu token ra. Cả mục A: 14,05 triệu token vào, 1,61 triệu token ra. Tiền Kaggle báo cộng dồn: 20,06 USD, dưới trần 40.
  - **Lỗi đọc dữ liệu được sửa trước khi tính (K23):** script phân tích có thêm bước khử trùng; 483 dòng đọc, 480 lần gọi.
  - **Lệnh:** `python kaggle/scripts/a38_analyse.py --prompts kaggle/data/a38_prompts.jsonl.gz --results kaggle/results/a38_results_2026111*.jsonl --reference google/gemini-3.1-pro-preview --alpha 0.025 --out kaggle/results/a38_analysis.json`.

  | Model | `leak/ablated` (6) | `noleak_leaky_env/ablated` (7) | D (H) | p một phía | `clean/ablated` (14) | D (G) | p (G) |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | Gemini 3.1 Pro (mốc, ngoài họ) | 0,94 | 0,29 | 0,66 | 0,0076 | 0,05 | 0,66 | 0,0076 |
  | GPT-5.4 nano | 0,72 | 0,19 | 0,53 | 0,0076 | 0,14 | 0,57 | 0,0064 |
  | gpt-oss-120b | 0,83 | 0,38 | 0,45 | 0,031 | 0,71 | 0,63 | 0,0058 |
  | Grok 4.6 | 1,00 | 0,86 | 0,14 | 0,12 | 0,79 | 0,14 | 0,12 |
  | Haiku 5.5 | 1,00 | 0,90 | 0,10 | 0,27 | 0,90 | 0,10 | 0,27 |

  (Các ô là tỉ lệ seed có H, trung bình theo lần gọi. Cột `clean` là H.)

  - **Phép kiểm chính (H, Holm, α = 0,025 một phía, 4 model khác hãng):** p nhỏ nhất 0,0076 (nano) > 0,025/4 = 0,00625. **Không model nào bác bỏ H0.**
  - **Diễn giải theo bảng đặt trước:**
    - Diễn giải 1 không đạt: không model khác hãng nào được bác bỏ.
    - Diễn giải 3 đúng **cho Haiku và Grok**: hai model này viết dòng lịch sử ở 0,79–0,90 cả khi quỹ đạo không cho thấy rò rỉ (`noleak`, `clean`). Với hai model này, chỉ dẫn là thói quen của model, không do rò rỉ.
    - Với nano và gpt-oss, chênh lệch cùng chiều với model mốc (0,53 và 0,45 theo H). Chênh lệch không đủ để chứng nhận ở mức của họ. Theo G, ô `clean` của gpt-oss bằng 0,05: phần lớn H của ô đó là các dòng khớp `RULE` mà không có `git log`/`git show` (giống ca "uncommitted" ở mục 6).
    - Model mốc (đúng tên model viết skill gốc): 0,94 so với 0,29, và 0,05 ở `clean`. Phù hợp với cơ chế ở §36. Đây là phép mô tả: model mốc nằm ngoài họ kiểm định.
  - **Câu được viết trong paper:**
    - Bước viết skill được lặp lại với 5 model viết skill.
    - Model của gskill viết chỉ dẫn khi quỹ đạo cho thấy commit lỗi, và gần như không viết khi lịch sử chỉ có một commit.
    - Hai model khác hãng cùng chiều nhưng không qua Holm. Hai model khác viết dòng lịch sử bất kể có rò rỉ hay không.
    - Vì vậy cơ chế "rò rỉ được biến thành chỉ dẫn" chỉ được nói cho model viết skill của gskill. Với các model khác, việc có một dòng lịch sử trong skill không phải bằng chứng là có rò rỉ.
    - Kết quả chính (mức tăng mất đi khi bịt rò rỉ, C10) không phụ thuộc vào phần này.
- **38-7 (17/11, sau 38-6; phân tích sau dữ liệu, chỉ mô tả, 0 USD): khác biệt nền tảng.** Kiểm theo câu hỏi phản biện của @thuthuy: kết quả có bị lẫn giữa model và nền tảng không.
  - **Cả 5 model, kể cả model mốc Gemini Pro, đều chạy trên Kaggle** trong cùng 480 lần gọi, cùng prompt, cùng cách gửi (32 prompt × 3 seed mỗi model). Mọi phép so trong bảng 38-6 là giữa các model trên cùng một nền tảng. Không có lẫn giữa model và nền tảng bên trong §38.
  - **§38 không chạy agent.** Mỗi lần gọi gửi một prompt đã lưu (văn bản cố định, kiểm bằng sha256) và nhận một câu trả lời. Không có repo, lịch sử git, thư mục làm việc, shell hay công cụ. Các khác biệt môi trường của agent (đường dẫn, mount, phiên bản git, sandbox) không tác động tới đại lượng H.
  - Khác biệt nền tảng **còn lại** chỉ nằm ở đường gọi model: proxy của Kaggle so với Vertex AI gọi từ workflow GitHub. Có thể có system prompt riêng của thư viện Kaggle (giới hạn đã nêu ở mục 6).
  - **Phép so trực tiếp hai nền tảng** (`kaggle/scripts/a38_platform_check.py` → `kaggle/results/a38_platform_check.json`):
    - Dùng 23 prompt được gửi lên Kaggle đúng từng byte như đã lưu (không bỏ dòng nào của skill cha).
    - So câu trả lời gốc (lượt học trong workflow GitHub, `vertex_ai/gemini-3.1-pro-preview`, 1 câu trả lời mỗi prompt) với Gemini Pro trên Kaggle (3 seed).
    - **Khớp ở 64/69 cặp (prompt, seed).** Theo đa số của 3 seed, khớp 22/23 prompt.
    - Theo ô: rò rỉ 1,00 (gốc) so với 0,94 (Kaggle); không rò rỉ 0,00 so với 0,11 (3 prompt); môi trường một commit 0,07 so với 0,05 (14 prompt).
  - **Giới hạn:**
    - Bản gốc chỉ có 1 câu trả lời mỗi prompt, nên không tách được nhiễu lấy mẫu với khác biệt nền tảng. 5 cặp lệch phù hợp với mức lệch giữa các seed trên chính Kaggle, nhưng đây không phải phép kiểm tương đương.
    - Không chạy được các model khác hãng trên workflow GitHub: mỗi model cần một tài khoản hay khóa riêng.
  - **Hệ quả cho câu viết:** câu ở 38-6 so các model trên cùng nền tảng, nên giữ nguyên. Câu "model của gskill cư xử như trong lượt học gốc" được phép viết, kèm số khớp 64/69.
- **38-8 (17/11, kiểm toán khả năng âm tính giả theo phản biện của @thuthuy; 0 USD; không đổi phép thử, không đổi kết luận đã đăng ký).**
  1. **Đơn vị suy luận.** `a38_analyse.py` (`per_call`) gộp các seed của một prompt thành **một** giá trị: tỉ lệ seed có H. Phép hoán vị chạy trên prompt: 6 prompt `leak/ablated` so với 7 prompt `noleak_leaky_env/ablated`, C(13, 6) = 1.716 cách gán. Không có giả lặp: các seed không được tính là quan sát độc lập.
  2. **Ánh xạ và khử trùng (K23).**
     - 483 dòng đọc, 480 giữ lại.
     - 3 dòng bỏ đi là 3 lần gọi Gemini bị từ chối hôm 15/11. Cả 3 khóa đều có câu trả lời ở lần gửi lại.
     - Mọi sha256 của kết quả có trong 32 prompt. Mỗi (model, prompt) có đúng 3 câu trả lời.
  3. **Seed.**
     - `temperature=None` cho mọi lần gọi (như gskill).
     - Ở cả 5 model, không prompt nào có 3 skill giống hệt nhau (0/32 mỗi model), nên các lần gọi có lấy mẫu thật.
     - Với Grok, thư viện bỏ tham số seed (đã ghi ở P0).
     - Vì đơn vị là prompt, độ phụ thuộc giữa các seed không ảnh hưởng tính hợp lệ của phép thử. Nó chỉ ảnh hưởng độ chính xác của tỉ lệ mỗi prompt.
  4. **Bộ phân loại H.**
     - H khớp mọi dòng chứa `commit`, `history`, `git log` hoặc `git show` (không phân biệt hoa thường). Đây là phép khớp chuỗi, không phải phân loại ngữ nghĩa, và không cần người đọc nên không có vấn đề "người chấm biết nhãn".
     - **Bỏ sót:** trong 162 skill không có H, 0 skill có lệnh đọc lịch sử không chứa các từ trên (`git blame`, `git reflog`, `git rev-list`, `HEAD~`, `HEAD^`, `git diff <mã băm>`).
     - **Báo nhầm:** các dòng có H mà không có `git log`/`git show` chủ yếu là "uncommitted" và "git diff trước khi commit". Đây là lý do có G. Kết luận theo G không đổi (bảng 38-6).
     - Ở ô không rò rỉ, dòng của Haiku và Grok là chỉ dẫn đọc lịch sử thật. Ví dụ của Haiku: "`git log --oneline -n 5`. Look for a recent non-test commit that changed source code."
  5. **Khả năng so sánh giữa hai ô (K24, phản biện đúng).**
     - Câu ở mục 6 "chênh lệch chỉ đến từ việc quỹ đạo có cho thấy rò rỉ hay không" là **quá đà**.
     - Hai ô cùng hai lượt học và cùng cách bỏ dòng ở skill cha. Nhưng chúng là **các lần gọi khác nhau**, với quỹ đạo, task và độ dài khác nhau; ô `noleak` gồm các lần gọi 1–3 của mỗi lượt học.
     - Phép so vì vậy là phép so giữa các nhóm có sẵn, không phải can thiệp trên cùng một prompt. Câu đúng: "chênh lệch gồm việc quỹ đạo có cho thấy rò rỉ hay không, và mọi khác biệt khác giữa các lần gọi".
     - Thiết kế mạnh hơn là ghép cặp: cùng prompt, bỏ các quan sát chứa "Bug Patch" khỏi quỹ đạo. Đây là một thí nghiệm mới, chưa chạy.
  6. **Holm:** đúng như đăng ký. P nhỏ nhất 0,0076 > 0,025/4 = 0,00625. Không bỏ hiệu chỉnh.
  - **Kết luận của kiểm toán:** không tìm thấy lỗi đo hay lỗi đơn vị làm kết quả âm tính giả. Điểm yếu thật là thiết kế không ghép cặp (mục 5): nó có thể làm phép so kém nhạy, và nó giới hạn mọi câu về nguyên nhân.
- **38-9 (17/11, tiếp kiểm toán theo phản biện; 0 USD; phân tích độ nhạy sau dữ liệu, chỉ báo cáo, không thay phép thử đã đăng ký).**
  1. **Mã của phép hoán vị.**
     - `perm_p` liệt kê đủ `itertools.combinations(range(13), 6)` (1.716 cách gán) và đếm các cách có chênh lệch ≥ chênh lệch quan sát.
     - Test `test_perm_p_matches_brute_force_and_holm` so với phép tính tay: 1/35 cho 3 so với 4 giá trị.
  2. **Khả năng hoán đổi nhãn: không được thiết kế bảo đảm, và không cân bằng.**
     - Nhãn không được gán ngẫu nhiên. Ô `leak` là các lần gọi 4–6 của mỗi lượt học. Ô `noleak` là các lần gọi 1–3 (cộng lần gọi 7 của Bleve). Thứ tự lần gọi tách hoàn toàn hai ô.
     - Độ dài prompt: ô `leak` 70.314–114.612 ký tự; ô `noleak` 50.210–178.265 ký tự, phần lớn dài hơn.
     - Vì vậy phép hoán vị chỉ kiểm "giá trị không phụ thuộc nhãn", với giả định các lần gọi hoán đổi được. Bác bỏ sẽ không chứng minh nguyên nhân là rò rỉ. Không bác bỏ cũng có thể do yếu tố lẫn (thứ tự lần gọi, độ dài).
     - **Độ nhạy: hoán vị trong từng repo** (Jinja 3 so với 3, Bleve 3 so với 4; 700 cách gán).
       - p của Gemini 0,0114, nano 0,0114, gpt-oss 0,0171, Grok 0,143, Haiku 0,286.
       - Lớn hơn bản không phân tầng ở 3 model, và không model nào dưới 0,00625.
  3. **Tính giá trị của đại lượng đo: hiệu ứng trần ở Haiku và Grok.**
     - H đo "skill có chỉ dẫn đọc lịch sử", không đo "chỉ dẫn được học từ rò rỉ". Phép so D (rò rỉ − không rò rỉ) là phần nhắm vào "học từ rò rỉ".
     - D lớn nhất có thể = 1 − tỉ lệ ở ô không rò rỉ: Haiku 0,10, Grok 0,14. D quan sát được đúng bằng các giá trị đó, vì ô rò rỉ đạt 1,00.
     - Với hai model này, phép kiểm **không còn chỗ** để thấy hiệu ứng. Kết quả của chúng là không có thông tin, không phải âm tính.
  4. **Lấy mẫu giữa các prompt.**
     - 32 prompt là **toàn bộ** các lần gọi model viết skill còn lưu (27 lần gọi; xem mục 3), không phải một mẫu ngẫu nhiên.
     - Suy luận có điều kiện trên đúng các lần gọi này. Không có câu nào về "các prompt nói chung".
  5. **Câu viết trong paper (thay câu của 38-6, theo R5 câu cũ vẫn ghi):**
     - Các model khác hãng không được chứng nhận.
     - Với Haiku và Grok, phép so không có thông tin, vì cả hai viết chỉ dẫn lịch sử gần như ở mọi prompt.
     - Với nano và gpt-oss, chênh lệch cùng chiều với model của gskill.
     - Phép so là giữa các lần gọi có sẵn, không phải can thiệp trên cùng prompt.

### Ghi chú 38-10 (17/11/2026): thí nghiệm A′, ghép cặp với model mốc. Đăng ký trước mọi lần gọi của A′

**Duyệt:** @thuthuy 17/11: "Duyệt chạy". Phương án trình duyệt: Gemini Pro, 6 cặp, 3 seed, khoảng 1,8 USD hạn mức Kaggle, trong trần 40 USD của §38.

**Vì sao đổi tên commit, không cắt quỹ đạo** (tôi chọn; @thuthuy không chọn khi được hỏi):
- Trong 12/15 quỹ đạo có rò rỉ, agent thấy "Bug Patch" ở 3–7% đầu của quỹ đạo. Sau đó lời của agent nhắc lại tên commit và nội dung diff.
- Cắt quỹ đạo tại chỗ đó sẽ bỏ tới khoảng 95% quỹ đạo, cả kết quả của task. Hiệu ứng khi đó lẫn với độ dài và kết quả.
- Đổi tên là cặp duy nhất làm sạch được: mọi byte khác giữ nguyên.
- **Câu hỏi hẹp hơn, nêu trước:** tên "Bug Patch" có làm model viết chỉ dẫn đọc lịch sử không, khi diff và việc agent đọc lịch sử vẫn còn trong prompt.
- Câu hỏi "thấy rò rỉ có làm model viết chỉ dẫn không" **không** được trả lời bằng A′.

**Dữ liệu** (`kaggle/scripts/a38p_build.py` → `kaggle/data/a38p_prompts.jsonl.gz`):
- Với mỗi prompt của ô `leak/ablated`, mọi chuỗi khớp `bug[ _-]?patch` (không phân biệt hoa thường) được thay bằng câu trung tính của §43, "Merge branch 'stable'" (`configs/c10.json`).
- 75 lần thay: 6, 26, 31, 3, 3, 6 theo thứ tự Jinja c04–c06, Bleve c04–c06. Dạng gặp: "Bug Patch", "bug patch", "bug-patch".
- Một lần thay nằm trong skill cha của Jinja c06 ("bug patch").
- Script kiểm: dựng ngược từ bản đã đổi tên và vị trí các lần thay ra đúng bản gốc, từng byte.
- sha256 gz `0f3fe9b4a337fc177f9c2f262b858b7694684d5ead557599bde0c28f824a30b3`, jsonl `51aded479f0cbbe02b6e43412e8e36db46264caacdcdac720abe850e014aa91b`.

**Gửi:**
- `google/gemini-3.1-pro-preview` trên Kaggle; seed 1, 2, 3; `temperature=None`; một tin nhắn user, như §38.
- Ô `kaggle/notebooks/a38p_run_cell.py`: bản sao của ô §38, chỉ khác khối cấu hình.

**Trần:**
- 2,1 USD hạn mức (ngày và cả mục).
- Theo L66: mô phỏng đúng bước kiểm của ô (ước tính × 1,5 trước mỗi lần gọi), trên chi phí đo được của chính 6 prompt này ở §38 (18 lần gọi, 1,762 USD), với nhiễu ±15%.
- Xác suất chạy đủ 18 lần gọi: 0,997 ở trần 2,0; 1,000 ở trần 2,1. Chi dự kiến 1,76 USD.

**Đại lượng và phép thử:**
- d_j = tỉ lệ seed có H trên prompt gốc − tỉ lệ trên prompt đã đổi tên, j = 1..6.
  - Phần gốc dùng lại câu trả lời của §38 (Kaggle, cùng model, seed 1–3).
  - Hai phần chạy ở hai ngày khác nhau. Giới hạn này được nêu trước; ghi chú 38-7 cho thấy model này ổn định giữa hai nền tảng (64/69).
- **Phép thử chính:** đổi dấu chính xác một phía trên 2⁶ = 64 cách gán; bác bỏ khi p ≤ 0,025.
  - Phép thử chỉ bác bỏ được khi cả 6 cặp có d_j > 0 (p = 1/64). Một cặp bằng 0 cho p = 2/64.
  - Phép thử đơn lẻ, ngoài họ Holm của §38. Không có kết luận nào về các model khác hãng.
- **Phụ:** cùng phép thử với G; báo từng cặp.
- Lần gọi bị từ chối: gửi lại ở phiên sau (như §38). Thiếu cặp nào thì không bác bỏ.

**Power** (`kaggle/scripts/a38p_power.py` → `kaggle/results/a38p_power.json`; seed 4405; 20.000 lần):

| Tỉ lệ H mỗi seed trên prompt đổi tên | Tỉ lệ bác bỏ |
| --- | --- |
| 0,05 (như ô một commit) | 0,992 |
| 0,29 (như ô không rò rỉ) | 0,703 |
| 0,50 | 0,257 |
| bằng tỉ lệ gốc (H0) | 0,000 |

**Diễn giải đặt trước:**

| Kết quả | Câu được viết |
| --- | --- |
| Bác bỏ | Với model viết skill của gskill, chỉ đổi tên commit "Bug Patch" (diff giữ nguyên) làm giảm việc viết chỉ dẫn đọc lịch sử trên cả 6 lần gọi: thông điệp là một nguyên nhân của chỉ dẫn. |
| Không bác bỏ, trung bình d gần 0 | Tên commit một mình không giải thích chỉ dẫn. Chỉ dẫn có thể đến từ việc agent dùng lịch sử thành công, mà A′ không tách được. |
| Không bác bỏ, d dương ở một số cặp | Báo từng cặp. Không có kết luận nhân quả. |

**Phân tích:** `kaggle/scripts/a38p_analyse.py`, viết trước dữ liệu; test ở `kaggle/tests/test_a38p.py`.

### Ghi chú 38-11 (17/11/2026): kết quả A′

- **Dữ liệu:**
  - 18/18 lần gọi có câu trả lời (6 prompt × 3 seed). File `kaggle/results/a38p_results_20261117.jsonl`.
  - Nguồn: @thuthuy dán nguyên văn JSONL vào cuộc trò chuyện. Tôi chép từng byte từ nhật ký phiên, không gõ lại.
  - **Kiểm toàn vẹn:**
    - `new_skills` của cả 18 dòng đúng bằng kết quả của `extract_skills` (bản sao nguyên văn của gskill) chạy trên `response`.
    - Mọi sha256 nằm trong 6 prompt đã đăng ký; mỗi (prompt, seed) có đúng một dòng.
- **Chi phí:** 0,498 triệu token vào, 0,065 triệu token ra; Kaggle tính 1,30 USD hạn mức (trần 2,1; dự kiến 1,76).
- **Phép thử đã đăng ký** (`kaggle/results/a38p_analysis.json`):
  - Đủ 3 seed ở cả 6 prompt (`complete`).
  - d_j: Jinja c04 +0,33 (gốc 2/3, đổi tên 1/3); 5 cặp còn lại bằng 0 (gốc 3/3, đổi tên 3/3).
  - Trung bình d = 0,056; p một phía = 0,5. **Không bác bỏ.** G cho cùng kết quả.
- **Câu viết, theo bảng diễn giải đặt trước (hàng "không bác bỏ, trung bình d gần 0"):** "Tên commit một mình không giải thích chỉ dẫn. Chỉ dẫn có thể đến từ việc agent dùng lịch sử thành công, mà A′ không tách được."
- **Mô tả (không phải phép thử):** 11/18 skill viết từ prompt đổi tên (đếm bằng máy: chuỗi `Merge branch 'stable'` trong `new_skills`; bản đầu của ghi chú này ghi nhầm 15/18, K26) gọi đích danh commit "Merge branch 'stable'" là nơi lỗi được chèn. Ví dụ: "The bug is intentionally injected in a recent commit (often named "Merge branch 'stable'"). Run `git log -n 5`…".
  - Model vẫn chỉ đường tới commit chèn lỗi, chỉ là theo tên mới. Chỉ dẫn bám theo việc agent dùng lịch sử trong quỹ đạo, không bám theo nhãn "Bug Patch".
  - Khớp với C10 (§43): thông điệp giúp agent tìm diff, nhưng tên thông điệp không phải nguồn gốc của chỉ dẫn.
