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

## 6. C4: thiết kế chạy chính
(chốt sau C3, trước khi chạy; gồm model agent, số task, quy tắc nhận của §25, trần tiền)
