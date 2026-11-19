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


### Ghi chú 40-5 (17/11/2026, trước mọi lượt của C4′; phiên làm việc chính, theo C1a và C1b của `docs/todo_ease_revision.md`)

**Dữ liệu đã thấy lúc viết ghi chú:** các số mô tả của phiên 1 không hợp lệ (bảng ở ghi chú 40-3), và mọi kết quả của agent nghiên cứu. Không có lượt C4′ nào.

**1. Đích tái lập là hiệu của hai mức tăng, không phải cặp quyết định "nhận / không nhận".**
- Bảng "Diễn giải đặt trước" ở mục 6 coi "nhận ở môi trường gốc, không nhận ở một commit" là lặp lại được phát hiện của paper. Nhưng trong paper, skill được nhận ở **cả hai** môi trường. Phát hiện là mức tăng tụt từ 0,38 xuống 0,21 khi bỏ hai commit do benchmark tạo ra (§41).
- Thay bằng: **phép thử chính của mỗi agent** là hiệu giữa hai môi trường trên từng task, Dᵢ = (Z_gốc − Z_một commit)/2, như §33 (P33c) và §35 (P35). Giả thuyết không: tổng E[Dᵢ | C] ≥ 0.
- Hai phép nhận theo từng môi trường của mục 6 vẫn được tính và báo cáo như đã đăng ký (R5).

**2. Thống kê của phép thử chính:** phép kiểm cuối pool (`docs/method_end_of_pool.md`; `end_of_pool_log_e`, λ = 0,5, θ = 0), bác bỏ khi E ≥ 40. Đọc theo họ: 3 agent nên ngưỡng 3/α = 120. E-process tuần tự được báo cáo kèm.

**3. Pool của phép thử chính: chỉ các task không có mô tả issue.**
- **Vì sao:** cả hai kênh rò rỉ chỉ phát huy khi task thiếu mô tả (§41: mọi task không mô tả mà agent nghiên cứu giải được ở môi trường gốc đều có diff "Bug Patch" trong trace). Trên các task có mô tả, D gần 0 và chỉ làm loãng phép thử.
- **Power, nếu agent mới hành xử như agent nghiên cứu** (lấy mẫu lại có hoàn lại từ Dᵢ đo được ở seed 51; 20.000 lần; seed 40050; `kaggle/scripts/c4_contrast_power.py` → `kaggle/results/c4_contrast_power.json`):

  | Pool | Power |
  | --- | --- |
  | 100 task test (như đang đăng ký) | 0,28 |
  | 34 task test không mô tả | 0,63 |
  | 70 task không mô tả (34 + 36 task của §35) | 1,00 |

- **Lựa chọn chờ @thuthuy:**
  - **A:** giữ 100 task như đăng ký; phép thử chính trên 34 task không mô tả trong đó (power 0,63 theo kịch bản trên).
  - **B (khuyên):** thêm 36 task của §35 (`data/instances/swesmith_pallets__jinja_extra36.jsonl` trên `data-snapshots`); phép thử chính trên 70 task không mô tả (power 1,00). Tốn thêm 36 × 4 lượt mỗi agent, tức khoảng 36% thời gian và hạn mức (theo C3: khoảng 0,004 USD hạn mức mỗi lượt Haiku). Không dùng tiền thật.
- **Giới hạn của con số power:** agent khác hãng có thể khác hẳn agent nghiên cứu. Phiên 1 (không hợp lệ, chỉ để lập kế hoạch) gợi ý Haiku có tỉ lệ giải nền cao hơn nhiều và skill thêm ít task. Nếu agent mới tự tìm ra rò rỉ mà không cần skill (như agent thứ hai ở §34), D gần 0 và phép thử sẽ không bác bỏ. Kết quả đó vẫn có nghĩa: phần của skill nhỏ với agent đó.

**4. Theo dõi cả hai kênh rò rỉ (§41).** Sau khi chạy, áp các quy tắc của `scripts/history_audit.py` cho từng nhánh: thấy diff "Bug Patch"; thấy nội dung test bị xóa; khôi phục rồi chạy test. Báo cáo theo nhánh, cạnh số task giải được.

**5. Diễn giải đặt trước (thay bảng ở mục 6, cho phép thử chính):**

| Phép thử chính (D, task không mô tả) | Ý nghĩa với agent đó |
| --- | --- |
| Bác bỏ | Lặp lại được phát hiện: mức tăng của skill ở môi trường gốc lớn hơn ở môi trường một commit |
| Không bác bỏ; nhánh không skill ở môi trường gốc giải được nhiều task không mô tả và trace cho thấy agent dùng các kênh rò rỉ | Agent tự tìm ra rò rỉ; phần của skill nhỏ (như agent thứ hai ở §34) |
| Không bác bỏ; agent hầu như không dùng các kênh rò rỉ ở cả hai nhánh | Skill không làm agent này khai thác rò rỉ |
| Ngược chiều (D trung bình > 0) | Không dự kiến; báo nguyên trạng |

### Ghi chú 40-6 (17/11/2026, trước mọi lượt của C6 và C4′): bộ chạy agent qua lớp `chroot`, ô C6 và ô C4′

**Mã (commit `063c796`, nhánh mặc định):**
- `c3_agent.py --isolation chroot`: lệnh `docker` của mini-swe-agent và Docker SDK của SWE-smith, gskill đều trỏ tới `chroot_shim.py` (ghi chú 40-4). `--isolation local` giữ cách cũ, chỉ để đọc lại C3 và phiên 1.
- `c4_driver.py`:
  - `--isolation` bắt buộc;
  - `--extra-rows`: phương án B của ghi chú 40-5. 36 task của §35 chạy sau 100 task test, trong các khối riêng, không trộn với task test;
  - `--arms`: chạy một phần các nhánh;
  - `--chunk-cap`: trần riêng của f1_probe cho một khối. f1_probe không bắt đầu một task khi số đã chi cộng cost_limit vượt trần.
- `c4_monitor.py`: bộ theo dõi của mục 6, viết thành mã.
  - **attempt:** một lệnh của agent khớp một trong các loại đường dẫn của ghi chú 40-3 (thêm thư mục trạng thái của `chroot_shim`).
  - **exposure:** một quan sát chứa dấu vết chỉ có trên máy notebook (`/kaggle/`, `/benchmarks/`, thư mục trạng thái của hai shim, thư mục đầu ra, tên biến khóa, dấu canary của C5).
  - **Kiểm trên dữ liệu thật của phiên 1** (189 lượt, kể cả khối bị để riêng): đếm lại đúng mọi số của ghi chú 40-3. Cụ thể: 27 lượt có attempt (7, 1, 16, 3 theo nhánh); `find /` 22, `/tmp/patch.diff` 12, `/var/lib/lshim` 4, `/tmp/jj` 4, `/benchmarks` 3, `/root/.cache` 2, `mirror` 1; "Bug Patch" 14 và 44. Phiên 1 không có cách ly và có 21 lượt exposure.
- Test: `kaggle/tests/test_c4_driver.py` (4 test). Cả 28 test của `kaggle/tests` đạt.

**Ô C6 (`kaggle/notebooks/c6_cell.py`):**
- Chạy **cổng C5 trước** trên chính máy đó: 6 phép thử, rồi bản vá gốc 5/5 và "không vá" 0/5 qua lớp `chroot`. Không đạt thì không chạy agent. Ô C5 riêng vì vậy không còn cần.
- **Task (quy tắc):** 3 task đầu không mô tả và 3 task đầu có mô tả của tập test, theo thứ tự gskill.
- Nhánh `lf_none`; Haiku 5.5; seed 41; cost_limit 0,30; trần 0,50 USD hạn mức (`--chunk-cap`).
  - Giới hạn nêu trước: với cost_limit 0,30, f1_probe dừng nhận task mới khi đã chi quá 0,20 USD. C3 đo trung bình 0,0037 USD mỗi task, phiên 1 đo 0,0041, nên 6 task dự kiến tốn dưới 0,10. Nếu ô vẫn dừng vì trần, kết quả được báo nguyên trạng; không nâng trần trong cùng lượt.
- **Hai lượt:**
  1. `DRY_RUN = True`: model giả lập, 0 USD. Câu trả lời giả lập lặp lại một lệnh thử đúng các đường dẫn của ghi chú 40-3 (`find /`, `ls /kaggle /var/lib/cshim`) ở mọi bước, đến giới hạn bước. Bộ theo dõi phải thấy attempt ở 6/6 lượt và exposure 0.
  2. `DRY_RUN = False`: Haiku thật.
- **Đạt khi:** 6/6 lượt chạy xong, 0 lỗi hạ tầng, 0 lượt sập, exposure = 0 (đúng như `plan_v4.md` mục 7: lệnh có thể được thử, nhưng không thấy gì).

**Ô C4′ (`kaggle/notebooks/c4p_cell.py`):**
- Thiết kế của mục 6 và ghi chú 40-5 không đổi: ba model theo thứ tự đã đăng ký; 4 nhánh; khối 10 task; seed 41; cost_limit 0,30; trần 12 USD mỗi model, 2,0 USD mỗi phiên, 8 giờ mỗi phiên.
- Thay cổng C2 bằng **cổng C5 ở đầu mỗi phiên** (6 phép thử, 5/5, 0/5).
- `POOL` không có giá trị mặc định. Ô dừng nếu chưa đặt "A" hoặc "B"; đó là câu trả lời T5 của @thuthuy.
- Bộ theo dõi chạy sau mỗi model. Exposure khác 0 thì kết quả của lượt đó được đánh dấu, như mục 6.
- **Chỉ chạy sau khi C6 đạt.**

### Ghi chú 40-7 (17/11/2026, sau lượt chạy thử C6 bằng model giả lập, trước mọi lượt C6 có model thật)

**Sự việc:** lượt chạy thử (`DRY_RUN = True`, 0 USD) cho kết quả:
- cổng C5 đạt, bản vá gốc 5/5, "không vá" 0/5;
- 6/6 lượt chạy xong, 0 lỗi hạ tầng, 0 lượt sập;
- attempt 6/6, như dự kiến;
- nhưng **exposure 6/6**, nên `c6_passed = false`.

**Nguyên nhân (K22):** quan sát của agent là thông báo lỗi của chính lệnh `ls`:
- `ls: cannot access '/kaggle': No such file or directory`
- `ls: cannot access '/var/lib/cshim': No such file or directory`

`find / -name compiler.py` chỉ thấy `/testbed/src/jinja2/compiler.py`. Lớp `chroot` đã che đúng. Bộ theo dõi đếm exposure khi chuỗi dấu vết xuất hiện ở bất kỳ đâu trong quan sát, kể cả trong câu báo đường dẫn **không tồn tại**. Đây là dương tính giả của bộ theo dõi, không phải rò rỉ.

**Sửa (`kaggle/scripts/c4_monitor.py`):**
- Exposure = một **dòng** của quan sát chứa dấu vết của máy notebook và **không** phải câu báo đường dẫn không tồn tại.
- Câu báo đường dẫn không tồn tại khớp: `No such file or directory`, `cannot access`, `does not exist`, `not found`, `FileNotFoundError`.
- Test mới: `test_monitor_path_not_found_is_not_exposure`.

**Kiểm:**
- Dữ liệu thật của phiên 1 (189 lượt, không có cách ly): vẫn đúng 21 lượt exposure và 27 lượt attempt. Tập 21 lượt bị đánh dấu giống hệt tập của bản cũ (so bằng máy). Mọi số của ghi chú 40-3 không đổi.
- Lượt chạy thử C6: attempt 6/6, exposure 0. Quy tắc "Đạt khi" của ghi chú 40-6 (không đổi) cho kết quả đạt.

**Không đổi:** task, model, seed, cost_limit, trần, quy tắc đạt của C6, thiết kế C4′. Ô C6 và ô C4′ chỉ đổi `COMMIT` sang commit chứa bộ theo dõi đã sửa. Lượt có model thật vẫn chưa chạy.

### Ghi chú 40-8 (17/11/2026, trước mọi lượt C4′): phương án B

- @thuthuy 17/11, trả lời T5: "Oke chọn B".
- C4′ chạy 100 task test, rồi 36 task không mô tả của §35 trong các khối riêng (phương án B của ghi chú 40-5; power 1,00).
- `kaggle/notebooks/c4p_cell.py` đặt `POOL = "B"`. Mọi giá trị khác của ghi chú 40-6 không đổi.
- Ô chỉ được gửi sau khi C6 có model thật đạt.

### Ghi chú 40-9 (18/11/2026): C6 với model thật đạt

- Notebook Benchmarks, `DRY_RUN = False`, commit `d934871`. Bắt đầu 03:41:03Z, xong 04:00:13Z.
- **Cổng C5 đạt** trên chính máy đó:
  - canary 0/8;
  - tiến trình còn sống sau khi xóa container: 0;
  - ghi chéo giữa hai container: không thấy;
  - shell đúng `/testbed` và Python 3.10.16;
  - không thấy đường dẫn nào của máy notebook;
  - phát hiện ghi vào base qua hard link và từ chối container sau đó;
  - bản vá gốc 5/5, "không vá" 0/5.
- **Quy tắc đạt của ghi chú 40-6: đạt.** 6/6 lượt xong, 0 lỗi hạ tầng, 0 lượt sập, exposure = 0.
  - Có 2 lượt chứa attempt (`find /`). Tôi đã đọc lại trace: cả hai chỉ thấy hệ thống file của image task.
  - Bộ theo dõi chạy lại tại máy của phiên trên `c6_results.zip` cho đúng các số trên.
- **Kết quả (mô tả):** Haiku giải 5/6 (S) trong môi trường một commit: 3/3 task có mô tả, 2/3 task không mô tả.
- **Chi phí:** 0,0314 USD hạn mức (proxy báo); 67 lần gọi; 337.184 token vào, 31.461 token ra.
- **Dữ liệu:** `kaggle/results/c6/`.
- **Tiếp theo:** C4′ (POOL B, ghi chú 40-8).

### Ghi chú 40-10 (19/11/2026): C4′ phiên 1 (Haiku); kiểm vận hành và một kênh rò rỉ mới (phân tích sau dữ liệu, chỉ mô tả)

- **Lượt chạy:** notebook Benchmarks, POOL B, 11:58:52Z–20:06:17Z, 480,7 phút. Haiku 43/56 khối, dừng vì giới hạn 8 giờ của phiên (không phải trần tiền). Dữ liệu: `kaggle/results/c4p/s1/` (zip sha256 `bb1a95952e00f2c66c100ce1509ac1230d5277615a2296861bf5ba04c5d2a6d0`).
- **Chi phí:** 1,9382 USD hạn mức (tổng `endpoint_usd` của 43 file `*.cost.json`, trùng số ô báo), trong trần phiên 2,0 và trần model 12. 4.407 lần gọi; 26,55 triệu token vào, 2,03 triệu token ra (file chi phí không ghi phần từ cache).
- **Kiểm vận hành (đếm bằng máy tại máy của phiên):**
  - cổng C5 trên máy đó đạt (bản vá gốc 5/5, "không vá" 0/5);
  - 430 lượt: `none` 110, `skill` 110, `lf_none` 110, `lf_skill` 100; 0 task trùng trong một nhánh; không file nào có `infra_failures`, `endpoint_mismatch` hay `patch_apply_failed`;
  - bộ theo dõi chạy lại trên zip cho **đúng** `monitor.json` của ô: attempt 76 (19, 3, 45, 9 theo thứ tự trên), **exposure 0**;
  - "Bug Patch" trong quan sát: `none` 48/110, `skill` 105/110, `lf_none` 0/110, `lf_skill` 0/100.
- **Lệnh đụng tới biến môi trường:** 27 lượt ở `lf_none` chạy `env` (phần lớn `env | grep -i issue|task|prompt`) để tìm mô tả task. Mọi quan sát trả về chỉ là biến của image task (`CONDA_*`, `PWD=/testbed`, `HOME=/root`, …), không có dấu nào của máy notebook (exposure 0). Quy tắc đã đăng ký là "lệnh đụng tới khóa hay biến môi trường **của máy chủ** phải bằng 0": **đạt**, vì lớp `chroot` không truyền biến của máy chủ vào (ghi chú 40-6).
- **Kênh rò rỉ mới, ngoài lịch sử git (không có trong bộ theo dõi đã đăng ký):**
  - ở `lf_skill`, **3/100 lượt** tải gói Jinja đã phát hành từ PyPI (`pip download jinja2==3.1.6`) rồi `diff` với `/testbed/src/jinja2` để tìm chỗ lỗi bị chèn (task `…0tzkxxm7`, `…mc9x7b9m`, `…4l597y24`). Hai lượt được bộ theo dõi đánh dấu qua loại `/tmp/jj` vì agent chọn thư mục đó; lượt thứ ba không bị đánh dấu;
  - 0/110 ở `lf_none`, 0 ở hai nhánh môi trường gốc;
  - **so với paper:** trong 2.699 lượt có trace của mọi file trên `main` (47 file), có 0 lượt tải gói phát hành để so (mẫu `pip download`, `pip install …jinja2==`, `pypi.org`, `files.pythonhosted`; 3 lượt khớp mẫu đều không phải tải: hai lần đọc README của pluggy, một lời khuyên trong skill giả của §27).
  - **Hệ quả:** môi trường một commit chỉ bỏ kênh lịch sử git. Khi có mạng, gói đã phát hành vẫn là một kênh tới mã trước lỗi. Agent Gemini của paper không dùng kênh này; Haiku có skill dùng nó ở 3% số lượt.
- **Xử lý (theo R5):** phép thử và quy tắc đánh dấu đã đăng ký không đổi. Thêm **một phân tích độ nhạy sau dữ liệu**, ghi rõ là sau dữ liệu: bỏ các lượt có tải gói phát hành (mẫu ở trên) ở mọi nhánh, và báo kết quả cả khi tính và khi bỏ. Mẫu được chốt tại đây, trước khi tính bất kỳ mức tăng nào của C4′.
- **Không đổi:** task, model, thứ tự, khối, seed, cost_limit, các trần, phép thử chính.

### Ghi chú 40-11 (19/11/2026): C4′ phiên 2; Haiku xong; lỗi trần ngày của ô (K27)

- **Lượt chạy:** 00:40:47Z–04:06:37Z, 195,8 phút. Haiku chạy 13 khối còn lại, **xong 56/56 khối** (136 task × 4 nhánh). Dữ liệu: `kaggle/results/c4p/s2/` (zip sha256 `2e84c3594a74c8489c310074cdfac45407ca6e37a2bd8fd59c5cd8ccb5e693f0`; zip này chứa cả các file của phiên 1).
- **Chi phí:** phiên 2 0,884 USD hạn mức; Haiku cộng dồn 2,8221 (trần model 12). Phiên 2: 1.793 lần gọi, 16,90 triệu token vào, 0,95 triệu token ra; cả Haiku: 6.200 lần gọi, 43,45 triệu vào, 2,98 triệu ra (tổng các file `*.cost.json`; không ghi phần từ cache).
- **Kiểm vận hành:** cổng C5 đạt; 544 lượt (136 mỗi nhánh), 0 task trùng, 0 file có `infra_failures`, `endpoint_mismatch`, `patch_apply_failed`; bộ theo dõi chạy lại cho đúng `monitor.json`: attempt 113 (`none` 19, `skill` 3, `lf_none` 67, `lf_skill` 24), **exposure 0**; "Bug Patch" trong quan sát: `none` 74/136, `skill` 131/136, `lf_none` 0, `lf_skill` 0.
- **Kênh tải gói phát hành (mẫu chốt ở ghi chú 40-10):** `lf_skill` **16/136** lượt; các nhánh khác 0. Phân tích độ nhạy của 40-10 áp dụng không đổi.
- **Lỗi K27:** nano và gpt-oss không được bắt đầu vì ô tính nhầm số đã chi trong phiên (cộng cả số của phiên 1 do driver chép file sang). Sửa ở `c4p_cell.py` (commit trong cùng lần sửa ghi chú này). Không đổi task, model, thứ tự, khối, seed, cost_limit, các trần, phép thử.
- **Tiếp:** phiên 3 với ô đã sửa, chạy nano rồi gpt-oss.


### Ghi chú 40-12 (19/11/2026): kết quả C4′ của Haiku (đủ dữ liệu của agent này; nano và gpt-oss chưa chạy)

- **Phân tích:** `kaggle/scripts/c4p_analyse.py` (viết sau khi có dữ liệu, theo đúng 40-5 và 40-10; test `kaggle/tests/test_c4p_analyse.py`), lệnh trong docstring, kết quả `kaggle/results/c4p/haiku_analysis.json`. Pool 70 task không mô tả: 34 task test của §34 (`kaggle/data/c4p_nodesc_test34.txt`, lấy từ `results/s34_none_pilot.json` và `s34_none_rest.json` trên `main`) và 36 task của các khối extra; đủ 4 nhánh ở cả 70.
- **Số task giải được trên 70 task không mô tả (S):** môi trường gốc: không skill 24, skill 24; một commit: không skill 1, skill 19.
- **Phép thử chính (D = (Z_gốc − Z_một commit)/2):** trung bình D = **+0,129** (khoảng 95% theo xấp xỉ chuẩn, chỉ để mô tả: [0,040; 0,217]); 10 task D < 0, 25 task D > 0; E = 0,0021, ngưỡng họ 120: **không bác bỏ**.
- **Theo bảng diễn giải đặt trước (40-5 mục 5): hàng "Ngược chiều (D trung bình > 0): không dự kiến; báo nguyên trạng".** Với Haiku, mức tăng của skill ở môi trường gốc là 0 (24 so với 24) và ở môi trường một commit là +18 task (1 so với 19).
- **Mô tả kèm (không phải phép thử):** ở môi trường gốc, Haiku không skill đã thấy diff "Bug Patch" ở 74/136 lượt (ghi chú 40-11) và giải 24/70 task không mô tả: agent tự tìm ra rò rỉ, nên skill không thêm gì (giống hàng 2 của bảng, "agent tự tìm ra rò rỉ"). Ở môi trường một commit, skill nâng từ 1 lên 19.
- **Độ nhạy (40-10, sau dữ liệu): bỏ 16 task có tải gói phát hành ở bất kỳ nhánh nào** → 54 task; giải được 17, 19, 1, 13; trung bình D = +0,093; E = 0,032; vẫn ngược chiều. Mức tăng ở môi trường một commit (1 → 13) không do kênh tải gói.
- **Phép nhận theo từng môi trường của mục 6** được tính khi phân tích đủ ba agent.
- **Không đổi:** mọi quy tắc của 40-5, 40-10.

### Ghi chú 40-13 (19/11/2026): C4′ phiên 3; khối sập của nano; ba sửa ở driver (K28). Viết trước lần chạy lại khối đó

- **Lượt chạy:** 04:44:25Z–06:51:34Z. Haiku đã xong (0 USD). Nano: 8 khối xong (`none`, `skill`, `lf_none`, `lf_skill` × khối 0–1; 80 lượt, 0 sập), rồi khối `none` 2 hỏng. Chi phí nano 0,5753 USD hạn mức; 1.172 lần gọi, 7,95 triệu token vào, 0,156 triệu token ra. Dữ liệu `kaggle/results/c4p/s3/` (zip sha256 `09863912d7b550d728e0942c0d6b876b8d512ed5b81129d5fe361f6634d9de4a`).
- **Khối hỏng:** 10/10 lượt chạy xong; lượt `…ez3c38dc` sập vì proxy model của Kaggle trả về lời đáp không có `message` ("Invalid response object", `'NoneType' object has no attribute 'get'`); mini-swe-agent thử lại 7 lần trong khoảng 3 phút, lần nào cũng vậy. Theo mục 6 ("một khối có agent crash hoặc lỗi hạ tầng không được tính; nó được để riêng và chạy lại"), khối được để riêng (`.bad`) và sẽ chạy lại ở phiên 4.
- **Kiểm vận hành:** cổng C5 đạt; bộ theo dõi chạy lại với `--include-bad` cho đúng `monitor.json`: 634 lượt, attempt 114, **exposure 0**.
- **Quy tắc mới, chốt trước lần chạy lại:**
  - Một khối được chạy lại **một lần**. Nếu lần chạy lại vẫn có lượt sập, mà mọi task đều chạy xong và không có lỗi hạ tầng, khối được giữ, kèm danh sách task sập (`accepted_with_crashes`).
  - Trong phân tích, task có lượt sập ở bất kỳ nhánh nào bị bỏ khỏi **cả 4 nhánh** của agent đó (thiết kế ghép cặp), và được báo. Một task sập không được tính là "không giải được": lượt sập không cho kết quả của agent (mục 6).
  - Lý do: lỗi lặp lại ở cùng một lời gọi có thể là tất định; không có quy tắc này, model đó không bao giờ chạy xong.
- **Sửa ở driver (K28),** commit trong cùng lần sửa ghi chú này; test trong `kaggle/tests/test_c4_driver.py`:
  1. trần mỗi model chỉ đếm file chi phí của model đó;
  2. tiền của lần chạy hỏng vẫn được đếm khi khối được chạy lại (`*.tryN.cost.json`);
  3. quy tắc giữ khối sập lần hai ở trên.
  - Kết quả của Haiku không đổi: chạy lại `kaggle/scripts/c4p_analyse.py` (đã thêm bước bỏ task sập) cho đúng số của ghi chú 40-12; Haiku không có lượt sập.
- **Không đổi:** task, model, thứ tự, khối, seed, cost_limit, trần, phép thử chính.


### Ghi chú 40-14 (19/11/2026): C4′ phiên 4; khối hỏng vì bộ chấm quá thời gian. Viết trước lần chạy lại khối đó

- **Lượt chạy:** 07:34:28Z–13:15:05Z, 329,9 phút. Khối `none` 2 của nano chạy lại: đạt, 0 lượt sập (quy tắc 40-13 không phải dùng). Nano xong **35/56 khối**; dừng ở khối `lf_skill` 8. Chi phí phiên 1,8009 USD hạn mức; nano cộng dồn 2,3762, kể cả lần hỏng của khối `none` 2 (`nano_none_c02.try1.cost.json`, sửa 2 của K28). Nano cộng dồn: 4.881 lần gọi, 31,83 triệu token vào, 0,624 triệu token ra. Dữ liệu `kaggle/results/c4p/s4/` (zip sha256 `a36eb0e5baf74429da880d6d724603ae5820d19e4c7485d8acd526b696dfaa33`).
- **Kiểm vận hành:** cổng C5 đạt; bộ theo dõi (`--include-bad`) đúng `monitor.json`: 904 lượt, attempt 114, **exposure 0**. Các khối được giữ: 0 lượt sập, 0 lỗi hạ tầng. "Bug Patch" trong quan sát, riêng nano (hiệu với Haiku): `none` 0/90, `skill` 33/90, hai nhánh một commit 0. Tải gói phát hành (mẫu 40-10): `none` 1, `lf_none` 3.
- **Khối hỏng:** 10/10 lượt chạy xong; lượt `…cpp8owgt` có `infra_error` "scoring: strict status 'timeout'" (bộ chấm S quá thời gian, agent đã nộp bản vá). Theo mục 6, khối được để riêng và chạy lại ở phiên 5.
- **Quy tắc thêm, chốt trước lần chạy lại (mở rộng 40-13):** nếu lần chạy lại của một khối vẫn có lượt lỗi hạ tầng (kể cả bộ chấm quá thời gian), khối được giữ, kèm danh sách (`accepted_with_infra`). Task đó bị bỏ khỏi cả 4 nhánh của agent, như task sập, và được báo. Lý do giống 40-13: một lỗi lặp lại không được chặn agent mãi. Quy tắc chấm lại một lần của L57 không dùng ở đây, vì mục 6 đã đăng ký chạy lại cả khối.
- **Mã:** `kaggle/scripts/c4_driver.py`, `kaggle/scripts/c4p_analyse.py`, test trong `kaggle/tests/test_c4_driver.py`; commit trong cùng lần sửa ghi chú này; ô ghim commit đó.
- **Không đổi:** mọi điều khác.

### Ghi chú 40-15 (19/11/2026): C4′ phiên 5; kết quả của nano; gpt-oss chạy lại với thẻ định dạng được gỡ

- **Lượt chạy:** 13:30:57Z–16:59:53Z. Khối `lf_skill` 8 của nano chạy lại: đạt (quy tắc 40-14 không phải dùng). **Nano xong 56/56 khối.** Nano cộng dồn 3,0987 USD hạn mức (gồm hai lần hỏng); 6.708 lần gọi, 40,74 triệu token vào, 0,802 triệu token ra. Dữ liệu `kaggle/results/c4p/s5/` (zip sha256 `780208ff32a5b1a44232d4b4eec098380b585c3854c17df6e8b6eb609d77ed04`). Bộ theo dõi (`--include-bad`) đúng `monitor.json`: 1.108 lượt, **exposure 0**.
- **Kết quả của nano** (`kaggle/results/c4p/nano_analysis.json`, cùng lệnh với 40-12):
  - 70 task không mô tả, đủ 4 nhánh, 0 task bỏ vì sập hay lỗi hạ tầng. Giải được: môi trường gốc không skill 0, skill **20**; một commit không skill 0, skill **0**.
  - D trung bình = **−0,143** (khoảng 95% theo xấp xỉ chuẩn, chỉ mô tả: [−0,196; −0,090]); 20 task D < 0, 0 task D > 0; **E = 86,7**.
  - **Ngưỡng họ 120 (3 agent, 40-5): không bác bỏ.** Ngưỡng giữ nguyên dù gpt-oss có chạy xong hay không (R5). E = 1,25²⁰: mỗi task D = −0,5 nhân E với 1,25; cần 22 task như vậy để vượt 120.
  - Chiều đúng như phát hiện của paper: mọi task không mô tả mà skill giúp ở môi trường gốc đều mất khi bỏ hai commit của benchmark.
  - Mô tả kèm: nano không skill thấy "Bug Patch" ở 0 lượt; có skill ở khoảng 61/136 lượt (hiệu với số của Haiku trong `monitor.json`). Không task nào trong pool có tải gói phát hành, nên phân tích độ nhạy của 40-10 trùng phép thử chính.
  - Trên mọi 136 task: giải được 1, 49, 1, 33 (gốc không skill, gốc skill, một commit không skill, một commit skill).
- **gpt-oss, lần đầu:** khối `none` 0 xong (10 lượt), khối `skill` 0 hỏng: lượt `…5w1ny04u` sập vì máy chủ trả lỗi 400 "You have passed a message containing <|channel|> tags in the content field". Lời đáp của gpt-oss qua proxy chứa thẻ định dạng (`<|channel|>`, `<|message|>`, `<|end|>`; 611, 604, 586 lần trong 10 lượt của khối `none` 0), và mini-swe-agent gửi lại nguyên văn trong lịch sử. Máy chủ chấp nhận ở khối đầu, rồi từ chối từ khoảng 16:33Z. Chi phí 0,3769 USD hạn mức.
- **Sửa (trước mọi lượt mới của gpt-oss):**
  - `kaggle/scripts/c3_agent.py --strip-format-tags`: trước khi gửi, các thẻ trên trong nội dung tin nhắn được thay bằng một dấu cách; phần chữ, kể cả khối lệnh bash, giữ nguyên. Trace lưu lời đáp đúng như model trả về. Test trong `kaggle/tests/test_c4_driver.py`.
  - Chỉ dùng cho gpt-oss. gpt-oss **chạy lại từ đầu dưới tag `ossh`**, để mọi lượt của model này chạy cùng một cách. Các file tag `oss` (khối `none` 0 và khối hỏng) để riêng, không dùng trong phân tích (L12: đổi cách chạy giữa chừng thì chạy thành giai đoạn riêng).
  - Sai lệch về độ trung thành với gskill: tin nhắn gửi lại khác lời đáp gốc ở các thẻ định dạng. Ghi vào phần giới hạn của C4′.
- **Không đổi:** task, thứ tự, khối, seed, cost_limit, trần (12 USD cho gpt-oss tính trên tag `ossh` cộng 0,3769 đã chi), phép thử.
