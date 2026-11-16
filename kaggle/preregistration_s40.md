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
(điền khi có)

## 6. C4: thiết kế chạy chính
(chốt sau C3, trước khi chạy; gồm model agent, số task, quy tắc nhận của §25, trần tiền)
