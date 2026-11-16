# §40 (đăng ký trước): agent khác hãng, chạy không cần container (mục C của `plan_v3.md`)

**Ngày đăng ký:** 16/11/2026.
**Duyệt:** @thuthuy 16/11/2026: "Duyệt hết nếu bạn thấy có ích, hôm nay hạn mức còn 2.5 usd kaggle nên dưới đó là được".
**Ngân sách:** chỉ hạn mức AI miễn phí của Kaggle. C0–C2: 0 USD. C3: trần 1 USD. C4: chốt trần sau C3, ghi vào bản này trước khi chạy. Hôm nay (16/11) tổng chi trên Kaggle dưới 2,5 USD.

## 1. Câu hỏi

Hai phép nhận chính của paper (skill gskill có tác dụng ở môi trường gốc; mất tác dụng ở môi trường một commit) mới được đo với một họ agent (Gemini). Với agent của hãng khác thì sao?

Kaggle không chạy được container (K14). Mục này thử một đường khác: dựng môi trường task **không dùng image**, rồi cho agent chạy ngay trong notebook Benchmarks.

## 2. Căn cứ (cổng C0: đã đọc bản gốc)

- **SWE-smith 0.0.9**, `profiles/python.py::PythonProfile.build_image`: image của một repo Python gồm
  - `git clone -o origin {mirror_url} /testbed`;
  - môi trường conda `testbed` với `python_version = "3.10"`;
  - `install_cmds` mặc định `["python -m pip install -e ."]`;
  - lệnh test: `source /opt/miniconda3/bin/activate; conda activate testbed; pytest --disable-warnings --color=no --tb=no --verbose`.
- `profiles/base.py::get_container`: container của agent chạy `git checkout {instance_id}` trong `/testbed`.
- `harness/utils.py::run_patch_in_container`: "each branch has two commits: 1. Bug commit 2. F2P Test File(s) removal commit". Khi chấm, harness chuyển về `HEAD~1`.
- **Đo trên mirror công khai** (`swesmith/pallets__jinja.ada0a9a6`): nhánh của một task có đúng 3 commit: "Initial commit", "Bug Patch", "Remove F2P Tests". Vậy lịch sử git mà agent thấy (kể cả commit rò rỉ) có đủ trong mirror, không cần image.
- **Image Jinja** (`swebench/swesmith.x86_64.pallets_1776_jinja.ada0a9a6`, 12 lớp, đọc trực tiếp từ các lớp): Python 3.10.16, 60 gói. Danh sách ở `kaggle/data/jinja_image_packages.json`.

## 3. Môi trường không-container (`kaggle/scripts/local_shim.py`)

| Trong image | Dựng lại |
| --- | --- |
| `/testbed`: clone của mirror | `/testbed` là thư mục thật, clone từ `/opt/mirror.git` (bản sao bare của mirror công khai). Mỗi "container" có bản sao riêng; đổi chỗ bằng rename trước mỗi lệnh |
| conda `testbed`, Python 3.10.16 | `uv venv` Python 3.10.16, cài đúng phiên bản 58 gói của image (trừ `pip` và chính `jinja2`), rồi chạy `install_cmds` của profile trong `/testbed` |
| `/opt/miniconda3/bin/activate` | file thay thế: `conda activate testbed` đưa môi trường trên lên đầu `PATH` |
| Docker SDK | lớp thay thế chạy lệnh thành tiến trình thường; mã chấm của SWE-smith giữ nguyên |

**Khác biệt nêu trước:**
- không cách ly với máy chủ;
- không giới hạn bộ nhớ;
- mỗi lúc chỉ một `/testbed`, nên chạy tuần tự;
- Python và các gói được cài lại theo danh sách, không sao chép từ image;
- thư viện hệ thống là của máy chủ.

Việc điểm chấm có giống Docker hay không **không được giả định**; cổng C1 đo.

## 4. Các cổng

| Cổng | Việc | Đạt khi | Nếu không đạt |
| --- | --- | --- | --- |
| C0 | Đọc bản gốc (mục 2) | Có câu trích cho từng thành phần | Dừng |
| C1 | Trên một máy sạch (không có `/testbed`): chấm lại mọi bản vá khác rỗng của 4 file kết quả Jinja đã có điểm Docker (`f1_probe`, `f1_skill_probe`, `s25_leakfree_none`, `s25_leakfree_skill`), cộng bản vá gốc và "không vá" của 20 task test đầu | Trùng điểm đã ghi **100%**; gốc 20/20; "không vá" 0/20; 0 lỗi hạ tầng | Dừng. Không sửa môi trường cho trùng |
| C2 | Trên Kaggle, không gọi model (`notebooks/c2_cell.py`): dựng môi trường, chấm bản vá gốc và "không vá" của 5 task test đầu | 5/5 và 0/5; phiên không bị ngắt | Thử một lần cách thay thế nếu lỗi do quyền ghi `/`; nếu vẫn hỏng thì dừng |
| C3 | 3 task test đầu, agent thật, không skill, để đo token và tiền mỗi task | Agent chạy hết vòng lặp ở cả 3 task; có số đo chi phí | Dừng |
| C4 | Chạy chính, đăng ký ở mục 6 | — | — |

Ngưỡng 100% ở C1 là ngưỡng của K0b (§37): mọi lệch điểm đều là một khác biệt giữa hai môi trường, không có mức lệch nào được coi là chấp nhận được.

## 5. Kết quả các cổng

- **C0 (16/11): đạt.** Các câu trích ở mục 2.
- **C1 (16/11): đạt.** Chạy trên một máy sạch (image `python:3.13`, không có `/testbed`), `kaggle/results/c1_local.jsonl`:

  | Loại | Số lượt chấm | Kết quả |
  | --- | --- | --- |
  | Bản vá đã có điểm Docker | 224 (`f1_probe` 38, `f1_skill_probe` 79, `s25_leakfree_none` 41, `s25_leakfree_skill` 66) | **224/224 trùng** (117 đạt, 107 không đạt) |
  | Bản vá gốc | 20 | 20/20 đạt |
  | Không vá | 20 | 0/20 đạt |
  | Lỗi hạ tầng | | 0 |

  Trung vị 2,9 giây mỗi lượt chấm.
- **Hai lỗi của chính môi trường, gặp và sửa trước khi có điểm nào được dùng** (`audit.md` K17, K18):
  - bản đầu dùng liên kết tượng trưng cho `/testbed`: "không vá" được chấm đạt, vì gói cài ở chế độ editable trỏ vào bản clone gốc. Đã đổi sang thư mục thật, đổi chỗ bằng rename;
  - lần chạy đầy đủ đầu tiên: cả 264 lượt báo lỗi hạ tầng, vì trạng thái ở `/opt` còn mà `/testbed` đã mất cùng máy cũ. `prepare()` giờ tự dựng lại phần thiếu. Không lượt nào của lần đó được tính.
- **Chạy thử ô C2 trên máy sạch (không phải Kaggle):** 5/5 và 0/5, 44 giây kể cả dựng môi trường.
- **C2 trên Kaggle (16/11): đạt.** Bản vá gốc 5/5, "không vá" 0/5, 0 lỗi hạ tầng, 69 giây. Máy Kaggle: quyền root, ghi được `/` và `/opt`, có `git`, `patch`, `uv`, 4 CPU, 19,5 GB đĩa trống.

### Ghi chú 40-1 (16/11, sau C2, trước C3)

- **Môi trường lệnh của agent, đo trong image gốc** (`docker run <image> bash -lc env`):
  - `PATH` bắt đầu bằng `/opt/miniconda3/envs/testbed/bin`;
  - `python`, `pytest`, `pip` nằm ở đó; Python 3.10.16;
  - `HOME=/root`, `TZ=Etc/UTC`, `CONDA_DEFAULT_ENV=testbed`.
- **Thay đổi sau C1 và C2:** môi trường dựng lại được đặt ở **đúng đường dẫn đó** (`/opt/miniconda3/envs/testbed`), thay cho `/opt/local_shim/env`. Mọi lệnh (của agent và của bộ chấm) chạy với đúng các biến trên và không biến nào khác của máy chủ.
  - Hệ quả về an toàn: lệnh của agent không thấy khóa của Kaggle. Chạy thử: 0 biến của máy chủ lọt vào.
  - Vì đường dẫn môi trường đổi, **C1 được chạy lại** với bản này. Kết quả ghi bên dưới. C4 chỉ chạy nếu lượt chạy lại cũng trùng 100%.
- **Agent chạy thế nào khi không có Docker:**
  - `scripts/f1_probe.py` của nhánh `trial` (`97cd0a5`), script của mọi lượt agent trong paper, chạy **nguyên văn**;
  - gskill ở `8c7b697`, mini-swe-agent 1.17.5, swesmith 0.0.9, swebench 4.1.0 như các lượt của paper; litellm 1.108.2;
  - mini-swe-agent gọi lệnh `docker exec … bash -lc <lệnh>`. Biến `MSWEA_DOCKER_EXECUTABLE` trỏ lệnh đó tới `kaggle/scripts/fake_docker.py`, chạy lệnh thành tiến trình thường trong `/testbed` của task;
  - `bash -c` thay cho `bash -lc`: file đăng nhập của image chỉ bật môi trường `testbed`, điều mà các biến ở trên đã mô tả.
- **Chạy thử miễn phí (model giả lập, máy sạch, 2 task):** agent chạy đủ vòng lặp; thấy `python` ở đường dẫn của image, `pwd -P` là `/testbed`, `git log` cho 3 commit ("Remove F2P Tests", "Bug Patch", "Initial commit"). Bản vá vô hại được bộ chấm L của gskill cho đạt và bộ chấm S cho không đạt, đúng như phát hiện F0 của paper.
- **Giá, đo từ 321 lần gọi của §38** (chi phí Kaggle báo = token vào × giá vào + token ra × giá ra, sai số 0 ở 4 model):

  | Model | USD mỗi triệu token vào | ra |
  | --- | --- | --- |
  | Haiku 5.5 | 0,10 | 0,50 |
  | GPT-5.4 nano | 0,20 | 1,25 |
  | gpt-oss-120b | 0,09 | 0,36 |
  | Gemini 3.1 Pro preview | 2,00 | 12,00 |

  Grok 4.6 không khớp công thức tuyến tính (sai số tới 0,07 USD), nên không dùng làm agent ở C3.
- **C3 (`notebooks/c3_cell.py`), chốt trước khi chạy:**
  - model agent: Haiku 5.5, model khác Google có giá token vào thấp nhất trong các model đo được giá chính xác và không phải model trọng số mở cỡ nhỏ. Lựa chọn này chỉ để đo chi phí; model của C4 chốt ở mục 6;
  - 3 task test đầu theo thứ tự của gskill, không skill, môi trường gốc;
  - `seed=41`, giới hạn mỗi task 0,30 USD, như §25; trần cả ô 1,00 USD;
  - giới hạn tiền tính bằng giá ở bảng trên (LiteLLM); chi phí Kaggle báo trên từng câu trả lời được ghi song song để đối chiếu;
  - trước khi chạy agent, ô gọi thử model một lần. Nếu endpoint từ chối tham số `parallel_tool_calls` thì bỏ tham số đó và ghi là sai lệch.
- **Rủi ro còn lại, nêu trước:** agent chạy bằng quyền root trên máy notebook. Nó không thấy khóa qua biến môi trường, nhưng về nguyên tắc có thể đọc bộ nhớ tiến trình khác. Nhiệm vụ của agent là sửa bug trong `/testbed`; mọi lệnh nó chạy đều được ghi vào trace và được kiểm sau khi chạy.

### Ghi chú 40-2 (16/11, trước C3)

- Hai lần chạy ô C3 đầu dừng trước khi gọi model (0 USD): notebook được dùng **không phải notebook Benchmarks** (`No module named 'kaggle_benchmarks'`, không có `MODEL_PROXY_*`). Xem `audit.md` K19, K20.
- **Hệ quả cho C2:** lần C2 đạt hôm nay chạy trên một notebook Kaggle thường (Python 3.13, quyền root). Máy của notebook Benchmarks có thể khác. Ô C3 vì vậy ghi lại thông tin máy và tự dựng lại môi trường ở đó; phần chấm của C3 (bộ chấm S chạy trên từng bản vá) đóng vai kiểm tra lại. **C2 phải được chạy lại trong notebook Benchmarks trước C4.**
- **C1 chạy lại với môi trường ở đường dẫn của image (16/11): đạt.** `kaggle/results/c1_local_envpath.jsonl`: 224/224 bản vá trùng điểm Docker đã ghi; bản vá gốc 20/20; "không vá" 0/20; 0 lỗi hạ tầng.

## 6. C4: thiết kế chạy chính (chốt 16/11, sau C3, trước mọi lượt chạy của C4)

### Kết quả C3 (16/11): đạt

- Notebook Benchmarks: quyền root, ghi được `/`, có `git`, `patch`, `uv`, Python 3.12.10.
- Endpoint nhận đủ tham số của paper (`seed`, `parallel_tool_calls`); không tham số nào bị bỏ.
- 3/3 task: agent chạy hết vòng lặp (7, 9, 10 bước), không lỗi hạ tầng, cả ba bản vá được S và L chấm đạt.
- Chi phí: 26 lần gọi, 83.792 token vào, 12.341 token ra. Kaggle báo 0,0110 USD; LiteLLM tính theo bảng giá 0,0145 USD (cao hơn, nên giới hạn tiền theo LiteLLM là an toàn). Trung bình 0,0037 USD mỗi task.
- Trace (`kaggle/results/c3/`): không lệnh nào đọc lịch sử git, không lệnh nào đụng tới khóa, biến môi trường hay đường dẫn của máy chủ.
- Cả 3 task này đều có mô tả lỗi. Chi phí của 34 task không có mô tả chưa đo.

### Câu hỏi và giả thuyết

Với agent của hãng khác, trên 100 task test Jinja của gskill:
- **H-ship:** trong môi trường gốc, skill đã học làm giảm tỉ lệ thất bại (bộ chấm S).
- **H-single:** trong môi trường một commit, skill đó không còn làm giảm.
Hai phép nhận này đúng là hai phép nhận của §25 và §25 bước 3, lặp lại với agent khác.

### Thiết kế

| Thành phần | Giá trị | Căn cứ |
| --- | --- | --- |
| Task | 100 task test Jinja, thứ tự `_gskill_order` | như §25 |
| Nhánh | `none`, `skill` (môi trường gốc); `lf_none`, `lf_skill` (một commit, `f1_probe.py --leak-free`) | như §25 và bước 3 |
| Skill | `docs/skills/gskill/jinja_best_skills.txt` (2.681 byte), skill của paper | không đổi |
| Agent | gskill `8c7b697`, mini-swe-agent 1.17.5, `f1_probe.py` của `trial` nguyên văn; `seed=41`; giới hạn 0,30 USD mỗi task; 50 bước | như §25 |
| Model agent | Haiku 5.5, GPT-5.4 nano, gpt-oss-120b, chạy theo thứ tự đó | quy tắc: mọi model khác Google có giá token đo được chính xác (bảng ở ghi chú 40-1) |
| Thứ tự chạy | từng khối 10 task; trong mỗi khối chạy lần lượt 4 nhánh | hai lượt của một cặp cách nhau vài phút (model có thể thay đổi theo thời gian) |
| Bộ chấm | S (SWE-smith) là chính; L (gskill) báo kèm | như §25 |

### Quy tắc quyết định (mỗi model, mỗi môi trường): `scripts/s25_ab.py` của `trial`, không sửa

- **Gatekeeper:** `BettingEProcess` trên Z = 1[skill thất bại] − 1[không skill thất bại], theo thứ tự task; θ = 0, c = 0,5, α = 0,025 (ngưỡng 40).
- Kèm phép kiểm dấu chính xác một phía trên các cặp lệch và khoảng bootstrap của mức tăng, như §25.
- **Đọc theo họ:** 3 model × 2 môi trường = 6 phép nhận. Báo cả mức riêng (α = 0,025) và mức Bonferroni (α / 6), như paper đã làm với K = 12.
- **Lỗi hạ tầng:** một khối có agent crash hoặc lỗi hạ tầng không được tính; nó được để riêng (`.bad`) và chạy lại. Đây không phải chạy lại lỗi của agent: agent chưa cho kết quả.

### Diễn giải đặt trước (mỗi model)

| Môi trường gốc | Một commit | Ý nghĩa |
| --- | --- | --- |
| nhận | không nhận | Lặp lại được phát hiện chính của paper với agent này |
| không nhận | không nhận | Skill không giúp agent này. Báo tỉ lệ giải nền và tỉ lệ lượt có thấy commit rò rỉ ở nhánh không skill (agent có tự tìm ra không) |
| nhận | nhận | Với agent này skill giúp cả khi không còn rò rỉ; kết luận "mất tác dụng" của paper không mở rộng sang agent này |
| không nhận | nhận | Không dự kiến; báo nguyên trạng |

"Không nhận" không có nghĩa là không có hiệu ứng: e-process cần hiệu ứng đủ lớn trên 100 task. Mức tăng và khoảng tin cậy luôn được báo kèm.

### Kiểm sau khi chạy (đếm bằng máy)

- **Bộ theo dõi rò rỉ** (định nghĩa M1, M2 của §36): số lượt có lệnh `git log`/`git show`, số lượt có "Bug Patch" trong quan sát, theo từng nhánh.
- **Rò rỉ ngoài `/testbed`, riêng của môi trường không-container:** máy notebook còn chứa bản clone gốc và mirror (ở `/var/lib/lshim`) và file task (ở `/kaggle/working`). Mọi lượt có lệnh đụng tới `/var/lib/lshim`, `/kaggle`, `mirror`, hoặc có "Bug Patch" trong quan sát ở nhánh một commit, đều bị **đánh dấu**. Kết quả được báo cả khi tính và khi loại các lượt đó.
- Mọi lệnh đụng tới khóa hay biến môi trường của máy chủ: phải bằng 0; nếu khác 0 thì dừng và báo @thuthuy.

### Tiền và thời gian (chỉ hạn mức miễn phí)

- **Trần mỗi model: 12 USD hạn mức.** Căn cứ: C3 đo 0,0037 USD mỗi task có mô tả với Haiku. Một lượt dài nhất (50 bước, khoảng 20 nghìn token mỗi bước) tốn khoảng 0,1 USD với Haiku và 0,2 USD với nano. 400 lượt ở mức đó là 40–80 USD, nhưng ở §25 chỉ khoảng một phần ba số task chạm 50 bước. Trần 12 USD là mức dừng để xem lại, không phải dự toán.
- **Trần mỗi phiên: 2,0 USD cho cả ba model**, để ngày nào cũng còn chỗ cho phiên cuối của §38 (khoảng 7 USD). Một trần có thể bị vượt tối đa bằng chi phí của một khối (10 task của một nhánh).
- **Tổng C4 tối đa: 36 USD.** Hạn mức tháng đã dùng 17,3 USD; §38 còn khoảng 7 USD. Tổng vẫn dưới 100 USD.
- Mỗi phiên dừng nhận khối mới sau 8 giờ.
- **Trước mỗi phiên, ô chạy lại cổng C2 trên chính máy đó** (bản vá gốc 5/5, "không vá" 0/5). Không đạt thì không chạy agent.

### Giới hạn nêu trước

- Một repo (Jinja), một seed, mỗi model một lượt.
- Môi trường không có lớp cách ly (xem bộ theo dõi ở trên).
- Ba model đều là hạng nhỏ của hãng (giá thấp). Kết luận chỉ nói về các model đã chạy.
- Skill được học bởi agent Gemini; ở đây chỉ đo skill đó trên agent khác.

### Ghi chú 40-3 (16/11, sau phiên 1 của C4): **C4 dừng; kết quả phiên 1 không được tính**

- **Đã chạy:** Haiku 5.5, 18/40 khối (189 lượt có kết quả), 139,6 phút, 1.703 lần gọi, 8,57 triệu token vào, 0,88 triệu token ra, **0,766 USD hạn mức**. Cổng C2 trên máy đó đạt (5/5, 0/5). Dữ liệu: `kaggle/results/c4_session1_invalid/`.
- **Vì sao dừng:** khối `lf_none` thứ 5 báo lỗi hạ tầng "Failed to checkout … Your local changes … would be overwritten". Bản clone gốc trên máy notebook đã bị sửa. Đọc trace cho thấy nguyên nhân: ở task không có mô tả (thứ tự 290), agent chạy `find / -name compiler.py`, tìm thấy bản clone gốc ở `/var/lib/lshim/testbed`, làm việc trong đó và chép đè hai file nguồn vào đó.
- **Bộ theo dõi đã đăng ký (mục 6) trên 189 lượt:**

  | Nhánh | n | Lượt có lệnh đụng đường dẫn ngoài `/testbed` |
  | --- | --- | --- |
  | `none` | 50 | 7 |
  | `skill` | 50 | 1 |
  | `lf_none` | 49 | 16 |
  | `lf_skill` | 40 | 3 |
  | Tổng | 189 | **27** |

  Loại đường dẫn (một lượt có thể có nhiều loại): `find /` 22; `/tmp/patch.diff` (file bản vá mà bộ chấm của task trước để lại) 12; `/var/lib/lshim` 4; `/tmp/jj` (bản Jinja 3.1.6 một lượt trước tải về) 4; `/benchmarks` 3; `/root/.cache` 2; mirror 1.
  Lệnh đụng tới khóa hay biến môi trường của máy chủ: **0**.
- **Đánh giá:** C1 và C2 chỉ chứng minh **bộ chấm** cho điểm giống Docker. Chúng không chứng minh **môi trường agent nhìn thấy** giống Docker. Trong Docker, mỗi task có `/tmp`, `/root` và hệ thống file riêng; ở đây các task dùng chung, và agent thật đã dùng tới phần chung đó. Vì vậy mọi con số của phiên 1 chỉ là dữ liệu thử, **không dùng để kết luận** và không đưa vào paper.
- **Số mô tả của phiên 1 (chỉ để lập kế hoạch, bộ chấm S):**

  | Nhánh | Giải được | Task không mô tả giải được | Có lệnh `git log`/`git show` | Thấy "Bug Patch" |
  | --- | --- | --- | --- | --- |
  | `none` | 33/50 | 1/13 | 14 | 14 |
  | `skill` | 36/50 | 3/13 | 44 | 44 |
  | `lf_none` | 28/40 | 0/9 | 11 | 0 |
  | `lf_skill` | 29/40 | 1/9 | 36 | 0 |

  Hai điều đáng chú ý cho kế hoạch: tỉ lệ giải nền của Haiku cao (khoảng hai phần ba, cao hơn nhiều so với agent của paper); và skill làm agent đọc lịch sử git ở 44/50 lượt nhưng số task giải thêm nhỏ.
- **Theo quy tắc của mục 4** ("không sửa môi trường cho trùng"): không vá từng chỗ rồi chạy tiếp. Muốn tiếp tục mục C thì phải có lớp cách ly thật và một cổng mới kiểm chính điều đó (`plan_v4.md`, cổng C5). 189 lượt này không được dùng lại.

### Ghi chú 40-4 (16/11): lớp cách ly bằng `chroot` trên hệ thống file của image gốc (cổng C5)

- **@thuthuy 16/11:** "có làm C5".
- **Thăm dò notebook Benchmarks** (`notebooks/c5_probe_cell.py`, 0 USD): quyền root; có `CAP_SYS_CHROOT` và `CAP_MKNOD`; **không** có `CAP_SYS_ADMIN` (mọi lệnh `unshare` bị từ chối); `ptrace_scope` = 1; không có `proot`, `bwrap`, `runc`. Vậy cách S1 của `plan_v4.md` không dùng được.
- **Cách được chọn (S4, mới, mạnh hơn S2 và S3):** `kaggle/scripts/chroot_shim.py`.
  - **Nền:** các lớp của **image gốc** (`swebench/swesmith.x86_64.pallets_1776_jinja.ada0a9a6`) tải bằng `curl`, kiểm sha256, giải nén bằng `tarfile` có xử lý whiteout; rồi hai bước của Dockerfile đã dùng ở §25 (mirror ở `/opt/mirror.git`, `git fetch` trong `/testbed`). Không còn dựng lại môi trường Python theo danh sách gói: dùng đúng file của image.
  - **Mỗi task:** một cây thư mục riêng. Mọi file của nền là liên kết cứng; riêng `/testbed`, `/tmp`, `/root`, `/var/tmp`, `/opt/mirror.git`, `/dev` là bản sao thật. Lệnh chạy sau `chroot()` vào cây đó, với biến môi trường của image và `bash -lc` của image.
  - **Khi task xong:** mọi tiến trình có thư mục gốc là cây đó bị dừng; cây bị xóa; nền được so với ảnh chụp (kích thước, thời điểm sửa) của từng file. Một lần ghi tại chỗ qua liên kết cứng bị phát hiện: lượt đó hỏng, không container nào được tạo tiếp, nền được dựng lại.
- **Khác Docker, nêu trước:**
  - không có `/proc` và `/sys` bên trong (không gắn được): `ps`, `/dev/fd`, `/dev/stdin` không dùng được;
  - `/dev` chỉ có `null`, `zero`, `full`, `random`, `urandom`, `tty`;
  - không giới hạn bộ nhớ;
  - ghi tại chỗ vào file của nền được **phát hiện**, không được ngăn;
  - root trong `chroot` có thể cố ý thoát ra. Agent chỉ thăm dò thì không thấy gì bên ngoài (phép thử 1 và 5).
- **Cổng C5, sáu phép thử đo bằng máy** (`kaggle/scripts/c5_gate.py`), giá trị đạt đặt trước:

  | # | Phép thử | Đạt khi |
  | --- | --- | --- |
  | 1 | File đánh dấu đặt trên máy chủ (thư mục trạng thái, `/tmp` của máy chủ, thư mục làm việc, thư mục thêm) và trong `/testbed`, `/tmp`, `/root`, mirror của container khác; tìm bằng `find /` từ trong một container | tìm thấy 0 |
  | 2 | Tiến trình nền của một container | còn sống sau khi lệnh trả về (như Docker); 0 còn sống sau khi container bị xóa |
  | 3 | File container A ghi; container B thấy; nền bị đổi | 0 và 0 |
  | 4 | Môi trường lệnh | `python` ở `/opt/miniconda3/envs/testbed/bin/python`; `pwd -P` là `/testbed`; 3 commit đúng tên; `HOME=/root`; biến đánh dấu của máy chủ không có trong `env` |
  | 5 | `/proc/1`, `/kaggle`, `/benchmarks`, thư mục trạng thái, mã chấm, file task | không tồn tại bên trong |
  | 6 | Ghi tại chỗ vào một file của nền | bị phát hiện khi xóa container; container sau bị từ chối; nền dựng lại nguyên vẹn |

  Kèm: chạy lại C1 qua lớp này (224 bản vá, gốc 20, "không vá" 20) phải trùng 100%; trên Kaggle: 6 phép thử đạt và bản vá gốc 5/5, "không vá" 0/5.
- **Kết quả tại máy của phiên** (máy có đúng mức quyền của Kaggle: có `chroot`, `mknod`, không `SYS_ADMIN`), `kaggle/results/c5_gate_local.json`: **đạt cả 6**. 8 file đánh dấu, tìm thấy 0. Dựng nền 69 giây; tạo một container 2,4 giây; dựng lại nền 98 giây. Lần chấm thử: 38/38 bản vá trùng, gốc 2/2, "không vá" 0/2; mỗi lượt chấm khoảng 15 giây (bộ chấm không-container cũ: 3 giây).
- **C1 qua lớp `chroot` (16/11): đạt.** `kaggle/results/c1_chroot.jsonl`: 224/224 bản vá trùng điểm Docker đã ghi; bản vá gốc 20/20; "không vá" 0/20; 0 lỗi hạ tầng; trung vị 13,6 giây mỗi lượt chấm.

