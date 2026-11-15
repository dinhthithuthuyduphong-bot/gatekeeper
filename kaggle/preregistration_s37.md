# §37. Giai đoạn 0 của hướng Kaggle (bản đăng ký trước)

> Chuyển từ `docs/preregistration_main.md` §37 trên `main` (commit đăng ký `17c6634`, 14/11/2026) theo yêu cầu của @thuthuy: mọi thứ của hướng Kaggle nằm ở thư mục này trên nhánh mặc định cho tới khi chạy ổn. Nội dung giữ nguyên, chỉ đổi đường dẫn file.


**Lý do:** @thuthuy 14/11: "làm trước bước 0đ là giai đoạn 0". Kaggle cho hạn mức gọi model miễn phí và máy CPU, nhưng notebook Kaggle không có Docker daemon (chưa xác nhận; K0a đo). Task SWE-smith chạy trong Docker image. Muốn dùng Kaggle thì phải chạy image bằng công cụ không cần daemon, và phải **chứng minh** điểm chấm không đổi.

**Đã thấy trước khi đăng ký** (chạy thử ở máy của phiên làm việc, không phải Kaggle): udocker 1.2.11 kéo và chạy được image Jinja; 4 bản vá của `s33_ship_skill.json` được chấm qua lớp thay thế và cả 4 trùng với điểm đã ghi (3 giải được, 1 không).

**Can thiệp (định nghĩa can thiệp):**
- Mã chấm của SWE-smith (`run_evaluation`, `run_patch_in_container`, `get_eval_report`; bản 0.0.9) dùng **nguyên văn**.
- Chỉ thay hai chỗ: đối tượng `docker.from_env()` và lệnh kéo image, bằng `kaggle/scripts/udocker_shim.py` (udocker, image kéo nguyên từ Docker Hub).
- Khác biệt so với Docker, ghi trước:
  - mỗi image giải nén một lần; mỗi "container" nhận một bản sao mới của `/testbed`, phần còn lại của hệ thống file dùng chung, nên chạy **tuần tự**;
  - không áp giới hạn bộ nhớ 10 GB;
  - lệnh chạy qua chế độ thực thi mặc định của udocker.

**Các cổng:**
- **K0a (môi trường):** ghi có Docker daemon hay không; udocker giải nén và chạy được image. Đạt khi chạy được test của ít nhất 1 task.
- **K0b (điểm chấm không đổi):** chấm lại một lần mọi bản vá khác rỗng của `f1_probe.json` và `f1_skill_probe.json` (Jinja, môi trường gốc, seed 41; đây là các bản vá đã được chấm lại 448 lần dưới Docker với 0 lần lệch, P26). Thêm bản vá gốc và "không vá" cho 20 task test đầu theo thứ tự của gskill.
  - **Đạt** khi: 100% bản vá trùng điểm đã ghi; bản vá gốc giải được 20/20; "không vá" giải được 0/20; không lượt nào ở trạng thái khác `completed`.
  - **Không đạt** (dù chỉ một bản vá lệch): hướng Kaggle dừng ở đây cho tới khi tìm ra nguyên nhân. Không dùng bộ chấm lệch để ra kết quả.
  - Lượt lỗi hạ tầng được chạy lại và không tính là điểm (L1, A105).
- **K0c (hạn mức và giá):** trong notebook Kaggle: hạn mức ngày và tháng hiển thị, danh sách model, và chi phí (do Kaggle báo) của một hội thoại ngắn. Chỉ ghi số đo; không có ngưỡng.
- **K0d (giao diện gọi model):** hội thoại nhiều lượt có giữ lịch sử không; có đặt được nhiệt độ hoặc seed không.
- **K0e (điều khoản):** @thuthuy đọc điều khoản dùng hạn mức trên trang Kaggle; ghi nguyên văn câu liên quan.

**Thứ tự chạy:** K0b chạy hai lần: ở máy của phiên làm việc (kiểm lớp thay thế), rồi trong notebook Kaggle (kiểm môi trường Kaggle). Chỉ kết quả trong Kaggle mới mở cổng cho các bước sau.

**Chưa đăng ký ở đây:** chạy agent trong Kaggle (cần một lớp thay thế tương tự cho harness của gskill) và mọi thí nghiệm mới. Chúng có mục riêng sau khi cổng này đạt và @thuthuy quyết.

### §37: kết quả K0b ở máy của phiên làm việc (14/11/2026; `kaggle/results/k0b_local.jsonl`; chưa phải Kaggle)
- **Môi trường (K0a):** không có Docker daemon; udocker 1.2.11; 4 CPU.
- **Điểm chấm:** 117/117 bản vá khác rỗng của `f1_probe.json` và `f1_skill_probe.json` trùng điểm đã ghi dưới Docker (68 giải được, 49 không). Bản vá gốc 20/20; "không vá" 0/20. 157 lượt chấm, 0 lượt khác `completed`; trung vị 5,8 giây mỗi lượt.
- **Đối chiếu điều kiện đạt:** đạt đủ bốn điều kiện, ở máy này.
- **Ghi chú thực thi 37-1:** bản đăng ký ghi "các bản vá đã được chấm lại 448 lần". Con số 448 là của bốn file (224 bản vá × 2 lần, P26); hai file dùng ở K0b có 117 bản vá khác rỗng.
- **Chưa kết luận gì về Kaggle:** cổng chỉ mở khi `kaggle/notebooks/kaggle_stage0.ipynb` cho cùng kết quả trong Kaggle.

### §37: lần chạy đầu trên Kaggle (14/11/2026, do @thuthuy chạy; chép từ đầu ra của notebook)
- **K0a, phần môi trường:** "Docker daemon: KHONG" (xác nhận notebook Kaggle không có Docker daemon); `/kaggle/working` có 20 GB đĩa. Mã được clone từ nhánh mặc định ở commit `d6362c1`.
- **K0a, phần chạy image và K0b:** chưa chạy. Notebook dùng là bản cũ, đọc mã ở `scripts/` nên báo `No module named 'udocker_shim'` (mã đã chuyển sang `kaggle/scripts/`). Notebook bản mới tự tìm thư mục mã.
- **K0c (hạn mức, đọc ở trang Settings):** AI theo ngày 10,00 USD; theo tháng 100,00 USD; GPU 30 giờ/tuần; TPU 20 giờ/tuần; dataset riêng 214,75 GB. Số theo ngày và theo tháng khớp với con số người dùng báo trong kaggle-benchmarks#76.
- **K0c, K0d (gọi model):** chưa chạy được. Notebook thường không có `kaggle_benchmarks` và không có biến `MODEL_PROXY_*`.
- **Ghi chú thực thi 37-2:** K0c, K0d chạy trong notebook tạo từ https://www.kaggle.com/benchmarks/tasks/new (cách duy nhất mà quick start của thư viện mô tả), bằng một ô duy nhất `kaggle/notebooks/k0cd_benchmarks_cell.py`. Ô này thêm bước đọc chữ ký hàm `prompt`, `send`, `respond` để biết có đặt được nhiệt độ, seed hay system prompt không. Không đổi điều kiện đạt nào.
- **Hệ quả cần kiểm thêm:** nếu notebook Benchmarks không bật được Internet hoặc không chạy được udocker, agent và bộ chấm phải chạy ở hai notebook khác nhau. Khi đó cần một cách chuyển bản vá giữa hai notebook; sẽ quyết sau K0c, K0d.

### §37: lần chạy thứ hai và thứ ba trên Kaggle (14/11/2026), và ghi chú thực thi 37-3
- **Lần 2:** ô 4 báo lỗi vì `{CODE}` không được thay trong lệnh shell nhiều dòng. Đã đổi sang gọi bằng Python.
- **Lần 3:** ô 1 và ô 2 chạy đúng (clone commit `266b606`, tìm thấy thư mục mã). Ô 3 không in gì, và ô 4 báo `NameError: name 'CODE' is not defined`. Như vậy kernel đã khởi động lại trong lúc chạy ô 3.
- **Giả thuyết, chưa xác nhận:** udocker giải nén image (khoảng 4,7 GB, đo tại máy của phiên làm việc) vào `~/.udocker`, nằm trên đĩa hệ thống của Kaggle chứ không phải `/kaggle/working` (20 GB).
- **Ghi chú thực thi 37-3** (không đổi điều kiện đạt nào):
  - udocker đặt ở `/kaggle/working/udocker`;
  - mỗi ô tự đủ biến, nên kernel khởi động lại thì chỉ cần chạy lại ô 1;
  - K0a chạy trong tiến trình riêng (`kaggle/scripts/k0a_probe.py`), in tiến độ ngay và ghi `k0a.json` sau từng bước;
  - K0a thử lần lượt các cách chạy của udocker (P1, P2, F1, F2, R1, R2) và dùng cách đầu tiên chạy được test; ô 4 dùng đúng cách đó;
  - `k0a.json` ghi thêm: dung lượng trống của `/`, `~` và `/kaggle/working`, bộ nhớ, quyền (CapEff), user namespace, ptrace.
- **Đã kiểm tại máy của phiên làm việc:** ô 2–3 chạy hết; P1 chạy được test (33 test qua); `k0a.json` và `k0a_mode.txt` được ghi.

### §37: lần chạy thứ tư trên Kaggle (14/11/2026)
- **Đo được:** `/` và `~` còn 967 GB trống, `/kaggle/working` 19,4 GB; RAM 31 GB; chạy bằng root; ptrace_scope = 1; user namespace có (tối đa 128.361).
- **Giả thuyết của ghi chú 37-3 sai:** đĩa hệ thống không thiếu. Lý do kernel khởi động lại ở lần 3 vẫn chưa rõ; từ nay việc nặng chạy trong tiến trình riêng nên không còn phụ thuộc vào điều đó.
- **Lỗi lần này (K4):** tiến trình con không thấy lệnh `udocker` (`FileNotFoundError`). Đã sửa: udocker được gọi qua gói Python của chính trình thông dịch.
- **Kiểm tại máy của phiên làm việc, bỏ `udocker` khỏi PATH như trên Kaggle:** ô 2–4 chạy hết; K0a chọn P1; 4/4 bản vá trùng điểm; bản vá gốc 2/2; không vá 0/2; 0 lượt lỗi.

### §37: lần chạy thứ năm trên Kaggle (14/11/2026)
- Ô 1 cài được udocker 1.3.17 (udockertools 1.2.11) vào `/usr/bin/python3`; udocker có trên PATH.
- Ô 3 in thông tin môi trường rồi dừng sau "step 1/2: pull and unpack the image", không có mã thoát; ô 4 báo `k0a_mode.txt` rỗng. Như lần 3, kernel bị ngắt trong lúc kéo hoặc giải nén image, lần này kéo theo cả tiến trình con.
- **Ghi chú thực thi 37-4** (không đổi điều kiện đạt):
  - K0a và K0b chạy tách hẳn khỏi kernel, ghi `k0a.log`, `k0b.log`, in nhịp tiến độ mỗi 20 giây (dung lượng đã dùng, RAM còn trống);
  - tách bước kéo và bước giải nén để biết chỗ dừng;
  - xoá container dở dang của lần chạy bị ngắt trước khi giải nén lại.
- **Kiểm tại máy của phiên làm việc** (bỏ `udocker` khỏi PATH): kéo 64 s, giải nén 47 s; P1 chạy được 33 test; chạy lại ô 3 chỉ hiện log; ô 4 (rút gọn) 4/4 bản vá trùng, gốc 2/2, không vá 0/2, 0 lỗi.

### §37: lần chạy thứ sáu trên Kaggle (14/11/2026)
- Tiến trình nền khởi động (pid 215), in thông tin môi trường, vào bước kéo image; nhịp ở giây 20 cho thấy đã dùng 0,8 GB, RAM trống 30,1 GB. Ô 3 dừng ngay sau đó, không có mã thoát; ô 4 báo `k0a_mode.txt` rỗng. Không biết tiến trình nền có chạy tiếp hay không.
- **Ghi chú thực thi 37-5** (không đổi điều kiện đạt):
  - ô 3, ô 4 chỉ khởi động việc nền rồi trả về ngay;
  - ô 3b, 4b đọc log mỗi lần chạy, báo RUNNING, FINISHED hoặc STOPPED;
  - nhịp RAM và đĩa do chính tiến trình nền ghi vào log, không phụ thuộc kernel.
- **Kiểm tại máy của phiên làm việc** (bỏ `udocker` khỏi PATH): ô 3 trả về sau 0,02 s; ô 3b đọc được log khi đang chạy và khi xong; K0a chọn P1, 33 test qua; ô 4 (rút gọn) 4/4 trùng, gốc 2/2, không vá 0/2, 0 lỗi.

### §37: lần chạy thứ bảy trên Kaggle (14/11/2026)
- Phiên mới; ô 3 chạy khi chưa có mã (`CODE = None`), K0a dừng ngay với mã thoát 2; bấm lại ô 3 báo "already finished".
- Không có điểm chấm nào được tạo; không ảnh hưởng điều kiện đạt.
- Đã sửa (K7) và kiểm tại máy của phiên làm việc: ô 3 trên phiên trống dừng với thông báo "chạy ô 2 trước"; sau một lần chạy lỗi, bấm lại ô 3 khởi động lại và K0a chạy xong (P1, 33 test qua, mã thoát 0); bấm ô 3 lần nữa báo "already finished well".

### §37: lần chạy thứ tám trên Kaggle (14/11/2026) và phép thử chẩn đoán
- Ô 3b thấy K0a bắt đầu bước kéo image (1a). Khoảng một phút sau, ô 3b báo `k0a: not started`: file log không còn, nghĩa là `/kaggle/working` đã bị xoá và **cả phiên Kaggle đã khởi động lại**.
- Các lần 3, 5, 6 dừng cùng chỗ (bước kéo image), nên nhiều khả năng cùng nguyên nhân.
- **Chưa sửa.** Phép thử `kaggle/notebooks/k0_diag_download.py`:
  - tải lớp lớn nhất của image Jinja (445 MB) bằng `curl` thẳng từ Docker Hub, không dùng udocker;
  - in boot id, uptime và nội dung `/kaggle/working`.
- **Diễn giải đặt trước:**
  - phiên khởi động lại ở cả lần tải không giới hạn tốc độ → nguyên nhân là tải lớn hoặc tốc độ tải; thử lại với `--limit-rate 20M`;
  - phiên không khởi động lại → nguyên nhân nằm ở udocker (cách nó kéo hoặc ghi image); đổi sang tải lớp bằng `curl` rồi nạp vào udocker.
- Tại máy của phiên làm việc, phép thử tải 467 MB trong 24 giây và in đúng nhật ký.

### §37: kết quả phép thử chẩn đoán (14/11/2026) và ghi chú thực thi 37-6
- **Kết quả trên Kaggle:** `curl` tải lớp lớn nhất (466.932.925 byte) trong 1,8 s; boot id không đổi, uptime tăng (870 → 1073 s), `/kaggle/working` còn nguyên. Theo diễn giải đặt trước: **tải lớn không làm phiên khởi động lại; nguyên nhân nằm ở udocker.**
- **Ghi chú thực thi 37-6** (không đổi điều kiện đạt):
  - không dùng `udocker pull`: image được tải bằng `curl` từ Docker Hub vào dạng OCI, kiểm sha256 của từng blob, rồi nạp bằng mã `load` của chính udocker;
  - image Jinja có một lớp lặp lại hai lần trong danh sách lớp. `udocker load` di chuyển file lớp nên lần thứ hai thiếu file; lớp đã có được đăng ký lại thay vì di chuyển lần nữa. Byte và thứ tự lớp không đổi;
  - chờ và thử lại khi Docker Hub trả 429 (giới hạn tần suất theo IP).
- **Kiểm tại máy của phiên làm việc:** tải và nạp 59 s, giải nén 46 s, 33 test qua. Chấm lại một phần qua đường mới: 17/17 bản vá trùng điểm đã ghi, gốc 5/5, không vá 0/5, 0 lỗi.

### §37: lần chạy thứ mười (14/11/2026) và phép thử chẩn đoán thứ hai
- Bước tải và nạp image theo ghi chú 37-6 chạy xong (ô 3b thấy bước 1b). Sau đó ô 3b báo `k0a: not started`: phiên lại khởi động lại, lần này ở bước giải nén (`udocker create`).
- **Phép thử** `kaggle/notebooks/k0_diag_extract.py`: giải nén 12 lớp của image bằng `tar` thường (không dùng udocker), in số file và dung lượng sau mỗi lớp. Tại máy của phiên làm việc: 84.148 file, 3,3 GB.
- **Diễn giải đặt trước:**
  - giải nén vào `/tmp` không làm phiên khởi động lại, còn vào `/kaggle/working` thì có → nguyên nhân là ghi nhiều file vào thư mục đầu ra; đặt udocker ở ngoài `/kaggle/working`;
  - cả hai đều không làm khởi động lại → nguyên nhân nằm ở cách udocker giải nén; tự giải nén bằng `tar` (cùng quy tắc xoá file theo whiteout của OCI) rồi đưa vào udocker;
  - cả hai đều làm khởi động lại → Kaggle không chịu được việc giải nén image này; hướng udocker trên Kaggle dừng, cần cách khác (ví dụ chấm bài ở GitHub Actions như trước, chỉ gọi model ở Kaggle).

### §37: kết quả phép thử giải nén (14/11/2026) và ghi chú thực thi 37-7
- **Kết quả trên Kaggle:** `tar` thường giải nén 12 lớp vào `/tmp/rootfs` rồi vào `/kaggle/working/rootfs`; cả hai lần 84.148 file, 3,3 GB, mã thoát 0; boot id không đổi, uptime tăng (494 → 627 s). Theo diễn giải đặt trước: **lỗi nằm ở cách udocker giải nén**, không ở số file hay vị trí ghi.
- **Đo tại máy của phiên làm việc:** lệnh `find` sau mỗi lớp của udocker gọi tổng cộng 2 tiến trình `chmod`. Giả thuyết "một tiến trình cho mỗi file" bị bác bỏ; thay đổi theo giả thuyết đó đã bỏ.
- **Ghi chú thực thi 37-7** (không đổi điều kiện đạt): `udocker create` chạy nguyên văn, kèm ghi log từng lệnh và nhịp tài nguyên mỗi 5 giây; ô 3b tự cập nhật mỗi 5 giây. Mục đích: lần sau, nếu phiên khởi động lại, các dòng cuối trên trang cho biết lệnh nào đang chạy và tài nguyên lúc đó.
- **Hướng dự phòng, đặt trước khi có kết quả:** nếu log cho thấy phiên chết trong một lệnh `tar` của udocker, sẽ giải nén bằng chính lệnh `tar -xzf --no-same-owner` đã chạy được ở phép thử, rồi áp các file whiteout theo đúng mã `_apply_whiteouts` của udocker. Kết quả phải qua lại phép so cây thư mục với `udocker create` gốc (đường dẫn, quyền, nhóm, kích thước, loại).

### §37: K0a đạt trên Kaggle (14/11/2026, lần chạy thứ mười hai)
- Ô 3b: giải nén 46 s; còn 14,7 GB trống; cách chạy P1: setup và run mã thoát 0; `git log` thấy `83b7314 Initial commit`; Python 3.10.16; 33 test qua; mã thoát 0.
- **K0a đạt trên Kaggle:** image của task chạy được không cần Docker daemon (P1).
- Lần này `udocker create` chạy nguyên văn (chỉ thêm log) và không làm phiên khởi động lại. Các lần hỏng trước (K10) vì vậy chưa có lời giải thích; log từng lệnh và nhịp tài nguyên được giữ lại cho các bước sau.
- Ô 4b báo "not started" cho K0b: chưa rõ ô 4 chưa khởi động K0b hay phiên đã khởi động lại. Ô 4b nay tự in dòng mới mỗi 5 giây và cho biết log của K0a còn hay mất.

### §37: lần chạy thứ mười ba (14–15/11/2026) và ghi chú thực thi 37-8
- Log K0a trên Kaggle (`k0a.log`, `k0a.json` do @thuthuy gửi): tải và nạp 106 s; giải nén 66 s, mọi lệnh `tar` và `find` của udocker trả mã 0; RAM trống 28–30 GB; P1 chạy được 33 test.
- K0b khởi động; lượt chấm đầu (`f1_probe.json`, `func_basic__arv5rwp0`): ghi dưới Docker là giải được, Kaggle chấm giải được.
- Khoảng 2 giờ sau, cả hai log đều mất: phiên tương tác tự tắt khi không ai thao tác.
- **Ghi chú thực thi 37-8** (không đổi điều kiện đạt): K0a và K0b chạy bằng notebook chạy theo lô (`kaggle/notebooks/kaggle_stage0_batch.ipynb`, Save Version → Save & Run All), tiền cảnh, kết quả lưu cùng phiên bản. Đã kiểm tại máy của phiên làm việc (rút gọn): P1; 4/4 bản vá trùng; gốc 2/2; không vá 0/2; 0 lỗi; đủ 6 file kết quả.

### §37: lần chạy thứ mười bốn (15/11/2026): chạy theo lô bị hủy
- Phiên bản Save & Run All bị hủy: "Canceled by backend. Exit code: 137". Không có log, không có file kết quả.
- **Tình trạng các cổng:** K0a đạt trên Kaggle (lần 12). K0b chưa có kết quả trên Kaggle (lượt chấm đầu trùng điểm, rồi phiên tắt ở lần 13; lần 14 bị hủy). K0c, K0d chưa chạy.
- **Nhận định:** trong 14 lần chạy, Kaggle đã ngắt việc nhiều lần (phiên khởi động lại, ô bị ngắt, phiên tắt khi không ai thao tác, lần chạy theo lô bị hủy) mà phần lớn không cho biết lý do. Các thí nghiệm của giai đoạn 1–3 cần hàng nghìn lượt chạy container trong nhiều giờ, nên rủi ro bị ngắt sẽ lớn hơn nhiều. Chờ @thuthuy quyết.

### §37: lần chạy thứ mười lăm (15/11/2026): dừng việc chạy container trên Kaggle
- Cách B (chạy tương tác, @thuthuy giữ tab mở): log tự mất giữa chừng; phiên khởi động lại.
- **Kết luận giai đoạn 0, phần chấm bài (K0a, K0b):** K0a đạt một lần (lần 12). K0b không hoàn thành được trên Kaggle sau nhiều lần thử; Kaggle ngắt phiên hoặc hủy lần chạy mà không cho biết lý do (K3, K5, K6, K8, K10, K12–K14).
- **Theo điều kiện dừng đã nêu trước lần chạy này**, việc chạy container (udocker) trên Kaggle dừng tại đây. Các giai đoạn 1–3 cần chạy agent trong container trên Kaggle vì vậy không khả thi theo cách này.
- **Phần còn mở:** K0c, K0d (hạn mức gọi model trong notebook Benchmarks), dùng cho việc thuần văn bản (phương án 2), chờ @thuthuy quyết.
- Không có số liệu nào của paper phụ thuộc vào thư mục này; `main` không đổi.

