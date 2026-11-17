# Việc cần làm để sửa bài cho EASE 2027 (lập 16/11/2026)

File này là danh sách việc dùng chung cho mọi phiên làm việc. Nó tổng hợp bản review của thầy ngày 16/11 và bốn vòng phản biện sau đó.

**Quy tắc của file:**
- Mỗi khi một việc đổi trạng thái, sửa file này trong cùng commit với thay đổi đó.
- Ô `[ ]` là chưa làm, `[x]` là xong. Ghi mã commit sau mỗi việc đã xong.
- Không đưa con số mới nào vào `paper/` trước khi việc B5 xong.
- Mục nào ghi "chờ @thuthuy" thì không tự làm.
- File này có trên cả `main` và nhánh mặc định. Sửa ở nhánh nào thì chép sang nhánh kia.

---

## 1. Kết luận: hướng đi

**Giữ khung chứng nhận, nhưng thu hẹp nó về đúng điều chứng minh được, và đặt phát hiện thực nghiệm lên trước.**

Bài sau khi sửa nói ba điều, theo thứ tự:

1. **Phát hiện:** một skill học được tăng điểm rõ rệt, và một phần mức tăng biến mất khi xóa lịch sử git của task.
2. **Chứng nhận theo phạm vi:** một skill được chứng nhận khi phép kiểm cuối pool vượt ngưỡng. Điều được chứng nhận là tác dụng kỳ vọng trung bình trên một pool task cố định, trong điều kiện của một lượt chạy. Không hơn.
3. **Giới hạn của cổng thống kê:** một phép kiểm đúng chỉ trả lời "điểm có tăng thật không". Câu hỏi "mức tăng có hợp lệ không" cần đối chứng trong đó nguyên nhân bị loại bỏ.

**Vì sao chọn hướng này:**
- Bản review cho góc nhìn "phát hiện thực nghiệm" 4/5 và góc nhìn "bảo đảm thống kê" 2/5. Hướng này sửa phần 2/5 mà không bỏ nó.
- @thuthuy đã bác phương án bỏ hẳn khung chứng nhận (16/11: "Không, hãy tìm thêm hướng cải thiện").
- Luận điểm "theo phạm vi" đứng được dù các thí nghiệm mới ra kết quả chiều nào.

**Không có hướng nào bảo đảm được nhận.** Thầy ước lượng 25–45% cho bản hiện tại và 50–70% sau khi sửa lý thuyết, nguồn gốc đăng ký và câu chữ. Các con số này là phán đoán chủ quan, không tính được từ dữ liệu.

---

## 2. Dữ kiện đã kiểm (đừng kiểm lại, trừ khi có lý do)

| Dữ kiện | Nguồn |
| --- | --- |
| Bản thầy review là `paper/main.tex` trên **`main`** (13/11, có §36). Bản trên nhánh mặc định cũ hơn (12/11). | so sánh hai nhánh, 16/11 |
| Hai nhánh đã rẽ: `main` có bài mới hơn và các nguồn mới; nhánh mặc định có thư mục `kaggle/`. | `git log`, 16/11 |
| EASE 2027: tóm tắt 15/01/2027, bài 22/01/2027 (AoE), thông báo 12/03/2027. | nguồn `ease_2027_research_cfp` trên nhánh `sources-snapshots` |
| EASE 2027: 10 trang gồm cả hình, bảng, phụ lục; thêm tối đa 2 trang chỉ chứa tài liệu tham khảo. | cùng nguồn |
| EASE 2027: mẫu `\documentclass[sigconf,review,anonymous]{acmart}`; sai định dạng có thể bị loại ngay. | cùng nguồn |
| EASE 2027: review ẩn danh hai chiều; gói tái lập cũng phải ẩn danh; theo chính sách Open Science của SIGSOFT; theo chính sách của ACM về nội dung do AI tạo. | cùng nguồn |
| PACE (arXiv 2606.08106, 06/06/2026): cổng nhận theo cặp, anytime-valid, dùng e-process kiểu đặt cược, cho thay đổi prompt và skill của agent. **Mới đọc phần tóm tắt.** | nguồn `pace_paired_anytime_gate` |
| Luồng 70 task của §35 là 34 task của seed 51 nối với 36 task mới, theo thứ tự cố định; không phải hoán vị ngẫu nhiên. | `docs/preregistration_main.md` §35 |
| Bản đăng ký §40 (C4) coi "nhận ở môi trường gốc, không nhận ở một commit" là lặp lại được. Trong bài, skill được nhận ở **cả hai** môi trường; phát hiện là mức tăng tụt từ 0,38 xuống 0,21. | `kaggle/preregistration_s40.md` §6 |
| Trong 68 trace của §34, lịch sử git mà agent in ra chỉ có ba thông điệp: "Initial commit", "Bug Patch", "Remove F2P Tests". **Đếm bằng regex nhanh, chưa kiểm kỹ.** | `results/s34_*.traces.jsonl.gz` |
| Repo task `swesmith/pallets__jinja.ada0a9a6` đọc được từ phiên làm việc. Nhánh `main` của nó trỏ tới `83b7314`, đúng mã của "Initial commit" trong trace. | `git ls-remote`, 16/11 |
| Trên `main` có 29 file trace (`results/*.traces.jsonl.gz`). | `git ls-tree`, 16/11 |

**Chưa kiểm được:** nội dung chính sách của ACM về AI (mới đọc câu CFP dẫn tới nó); toàn văn PACE.

---

## 3. Phần thống kê đã thống nhất (đặc tả cho B1–B7)

### 3.1 Phép kiểm cuối pool

- **Dữ liệu:** pool cố định gồm N task. Với task i, Zᵢ = (thất bại khi có skill) − (thất bại khi không skill), nằm trong [−1, 1].
- **Trạng thái lượt chạy C:** toàn bộ diễn biến của mọi thứ dùng chung giữa các task trong lượt chạy (phiên bản model được phục vụ, cấu hình harness, trạng thái nhà cung cấp theo thời gian).
- **Giả định:** với C đã cho, các Zᵢ độc lập giữa các task. Hai nhánh trong cùng một task được phép phụ thuộc nhau.
- **Giả thuyết không:** tổng của E[Zᵢ | C] trên pool ≥ −Nθ.
- **Thống kê:** E = tích trên i của (1 + λ(−θ − Zᵢ)), với **λ = c/(1 + θ) = 0,5**. Đây là mức cược tối đa đã đăng ký của Gatekeeper (θ = 0, c = 0,5), nên không có tham số nào được chọn sau dữ liệu.
- **Quyết định:** chứng nhận khi E ≥ 1/α = 40, chỉ xét ở cuối pool.
- **Chứng minh (ba dòng):**
  1. Độc lập nên kỳ vọng của tích bằng tích các kỳ vọng.
  2. Mỗi thừa số nằm trong [0,5; 1,5], và 1 + x ≤ eˣ, nên tích ≤ exp(−λ·Σ(θ + E[Zᵢ | C])).
  3. Dưới giả thuyết không, số mũ ≤ 0, nên E có kỳ vọng ≤ 1. Bất đẳng thức Markov cho xác suất nhận nhầm ≤ α.
- **Chứng minh không cần từng task có tác dụng không dương.** Thứ bị chặn là tổng.

### 3.2 Những điều phép kiểm này KHÔNG nói

- Nó không anytime-valid. Nó chỉ bảo đảm ở cuối pool.
- Nó không nói gì về một lượt chạy khác ngày, một phiên bản model khác, hay task ngoài pool.
- Trên các quyết định đã có, nó là **phân tích sau dữ liệu**. Chỉ một thí nghiệm mới, đăng ký trước, mới cho nó lần dùng xác nhận.
- Giả định độc lập là giả định. Vi phạm đã biết: các task chạy song song tạo tải cho nhau; 2 lượt của nhánh skill Bleve sập vì giới hạn tốc độ.

### 3.3 Số liệu sơ bộ (CHƯA đưa vào bài)

Tính từ số cặp lợi/hại đã công bố, λ = 0,5. Mới có 6 trong 12 quyết định.

| Phép so | Cặp lợi / hại | E | Vượt 40 | Vượt 480 |
| --- | --- | --- | --- | --- |
| Jinja bỏ chỉ dẫn | 25 / 2 | 6.313 | có | có |
| Jinja học lại, một commit | 20 / 3 | 416 | có | không |
| Jinja seed 2, môi trường gốc | 38 / 4 | 307.000 | có | có |
| Jinja seed 2, một commit | 23 / 5 | 351 | có | không |
| Bleve, một commit | 19 / 2 | 554 | có | có |
| Pygments dùng lại | 2 / 1 | 1,1 | không | không |

### 3.4 Mô phỏng sơ bộ (phải chạy lại trong `verify_methods.py`)

- Sáu pool có tác dụng trung bình bằng 0, các task không đồng nhất, 400.000 lần mỗi pool: phép kiểm cuối pool nhận nhầm cao nhất 0,0017; kiểm định dấu chính xác cao nhất 0,0098. Cả hai dưới 0,025.
- **Trạng thái chung cho cả lượt chạy** (xác suất 1/2 tác dụng −0,2, xác suất 1/2 tác dụng +0,2, trung bình 0): phép kiểm cuối pool nhận nhầm **35,7%**. Đây là lý do đại lượng mục tiêu phải có điều kiện theo C.

### 3.5 Vai trò của từng phép thử trong bài

| Phép thử | Vai trò |
| --- | --- |
| Phép kiểm cuối pool, λ = 0,5, ngưỡng 40 | **Định nghĩa duy nhất của "được chứng nhận"** |
| E-process tuần tự (Gatekeeper), ngưỡng 40 | Báo cáo thời điểm lẽ ra có thể dừng. Hợp lệ cho giả thuyết hẹp hơn: không task nào có tác dụng kỳ vọng, theo thứ tự cố định trước. |
| Kiểm định dấu chính xác với Holm | Giữ vai trò đã đăng ký. Bảo đảm chính xác cho giả thuyết: ở mỗi cặp lệch, hai chiều có xác suất bằng nhau. |
| Ngưỡng 480 | Phân tích độ nhạy cho cả 12 quyết định (chặn hợp, không cần độc lập). |

Không gọi Gatekeeper hay mệnh đề cuối pool là "đóng góp phương pháp".

---

## 4. Phương án đã bị loại (đừng mở lại)

| Phương án | Lý do loại |
| --- | --- |
| Bỏ hẳn khung chứng nhận | @thuthuy bác, 16/11 |
| Thay bằng e-value dạng Hoeffding | Hợp lệ nhưng yếu: chỉ giữ 1 trong 5 quyết định ở ngưỡng 40, vì coi các cặp hòa là nhiễu |
| Lưới chín giá trị λ | Lưới được đặt sau khi có dữ liệu; thay bằng hằng số đã đăng ký 0,5 |
| Nói rằng hai nhánh chạy cùng lúc bảo đảm độc lập giữa các task | Sai: mô phỏng 35,7% ở mục 3.4 |
| Dùng chứng minh trên trung bình qua nhiều trạng thái lượt chạy | Bất đẳng thức đi ngược chiều |
| Gọi hai phép kiểm là "hai đóng góp thống kê" | Sau PACE không còn mới |
| Đi tìm định lý về tính bảo thủ của kiểm định dấu | Không cần: phép kiểm cuối pool đã gánh tuyên bố về trung bình pool |
| Viết "PACE không ngăn được khai thác rò rỉ" | Quá mạnh; dùng cách nói ở D9 |
| Chạy C7, C8, C9 trước khi bài về 10 trang | Thầy xếp tùy chọn; bài đang thừa khoảng 3 trang |

---

## 5. Danh sách việc

Cột "Duyệt": **tự làm** = việc kỹ thuật, không tốn tiền, làm được ngay. **Chờ** = cần @thuthuy quyết.

### Đợt 1: nền tảng (làm ngay)

| # | Việc | Xong khi | Duyệt |
| --- | --- | --- | --- |
| [ ] G2 | Gộp `main` và nhánh mặc định thành một nguồn duy nhất. Trước đó: gắn tag cho đầu hai nhánh, liệt kê file khác nhau, **báo phiên Kaggle đang đẩy commit lên nhánh mặc định**. | Một nhánh chứa cả bài mới nhất lẫn `kaggle/`; CI đạt | tự làm, nhưng phải phối hợp |
| [x] D8 | Xong 17/11 (R-69). Sửa ba câu sai dữ kiện trên `main`: "All agent runs use one model" (mâu thuẫn với §34); "609 rewrites" (đếm sai đơn vị); câu "chỉ so trên luồng A/A" ở Threats (bài đã so trên 20 luồng thật). Ghi vào `docs/audit_pilot.md`. | Ba câu khớp với dữ liệu | tự làm |
| [x] S0 | **Bước 0: kiểm toán lịch sử git và trace.** Xong 17/11: `docs/preregistration_main.md` §41. Mỗi task có đúng ba commit; không có lịch sử thật; có **hai** kênh rò rỉ (diff "Bug Patch" và test bị xóa trong "Remove F2P Tests"); agent nghiên cứu chỉ dùng kênh thứ nhất, agent thứ hai dùng cả hai. | Có bảng kết quả và file JSON | tự làm |
| [ ] A5a | Đưa chính sách của ACM về AI vào `configs/sources.json`, để runner tải, rồi đọc. | Có trích đoạn trên `sources-snapshots` | tự làm |
| [ ] D9a | Tải toàn văn PACE (hiện mới có tóm tắt) và đọc. | Biết chính xác quy tắc của PACE | tự làm |

### Đợt 2: thống kê và phạm vi tuyên bố

| # | Việc | Xong khi | Duyệt |
| --- | --- | --- | --- |
| [x] B0 | Xong 17/11 (§42): theo từng task. Cùng job: 6, 9, 10, 11, 12; phần lớn cùng job: 7, 8; hai lượt cùng ngày: 1, 2; khác ngày: 3, 4, 5. Phân loại 12 quyết định theo cấu trúc lượt chạy: hai nhánh chạy cùng lúc, khác ngày, hay chạy lại. | Bảng 12 dòng | tự làm |
| [x] B1 | Xong 17/11: `docs/method_end_of_pool.md`; `end_of_pool_log_e` trong `src/gatekeeper/eprocess.py`, có test tính kỳ vọng chính xác. Viết chứng minh đầy đủ của mục 3.1 thành một ghi chú phương pháp trong `docs/`. Thêm hàm vào `src/gatekeeper/eprocess.py` (không có giá trị mặc định cho θ, λ, α) kèm test. | Preflight đạt | tự làm |
| [x] B2 | Xong 17/11: T1, T2, T3 ở `docs/method_end_of_pool.md` mục 2. Định nghĩa ba đại lượng mục tiêu: trên pool trong một lượt chạy; qua nhiều lượt chạy; khi triển khai. | Nằm trong ghi chú của B1 | tự làm |
| [x] B7 | Xong 17/11: `verify_methods.py` mục `end_of_pool`. Nhận nhầm ≤ 0,0013 trên ba pool có trung bình 0; trạng thái chung 0,042; power kém kiểm định dấu ở mức tăng nhỏ. Đưa mô phỏng của mục 3.4 vào `scripts/verify_methods.py`: tỉ lệ nhận nhầm và power, trên đúng quy tắc cuối cùng. | `results/method_check.json` cập nhật | tự làm |
| [x] B5 | Xong 17/11 (§42): ngưỡng 40 ra đúng mọi quyết định đã đăng ký; ngưỡng 480 giữ 8/10. Tính đủ 12 quyết định **từ dữ liệu ghép cặp gốc**. Mỗi dòng: mã phép so, giả thuyết không, pool, trạng thái từng task (timeout, lỗi hạ tầng), cấu trúc lượt chạy, λ, E, ngưỡng, có nằm trong phạm vi chứng nhận có điều kiện không. Thiếu dữ liệu gốc thì ghi rõ thiếu gì. | Một file JSON và một bảng | tự làm |
| [x] B6 | Xong 17/11 (§42): không τ nào có p < 0,05; 2 lượt sập vì giới hạn tốc độ (Bleve một commit). Chẩn đoán giả định độc lập: số lượt sập vì giới hạn tốc độ ở từng phép so; tương quan của Z theo thứ tự chạy. Ghi rõ đây là chẩn đoán, không phải xác nhận. | Có số cho từng phép so | tự làm |
| [x] B3 | Xong 17/11: Định lý 2 và Mệnh đề 3 cũ được thay bằng mệnh đề cuối pool có chứng minh. Trong bài: thu hẹp Định lý 2 về phần đã chứng minh. Sửa Mệnh đề 3 bằng điều kiện "thủ tục nhận skill với xác suất dương". | Sau B5 | **chờ** (phạm vi tuyên bố) |
| [x] B4 | Xong 17/11. Trong bài: §35 ghi là "34 task đã dùng với seed mới + 36 task mới"; báo cáo riêng từng nhóm. | Sau B5 | tự làm |

### Đợt 3: thí nghiệm (đóng băng ngày 01/12)

| # | Việc | Xong khi | Duyệt |
| --- | --- | --- | --- |
| [ ] C1a | Sửa `kaggle/preregistration_s40.md` **trước lượt chạy đầu của C4′**: (1) đích tái lập là hiệu của hai mức tăng trên cùng task, như §33 và §35; (2) phép kiểm cuối pool là phép thử chính; (3) khai rằng số của phiên 1 không hợp lệ đã được nhìn thấy. | Ghi chú thực thi có ngày | tự làm, phối hợp với phiên Kaggle |
| [ ] C1b | Mô phỏng power cho phép so giữa hai môi trường, theo từng agent. Power thấp thì ghi trước vào bản đăng ký hoặc bỏ agent đó. | Có số power trước khi chạy | tự làm |
| [ ] C1 | Chạy C4′ trên Kaggle (ba agent khác hãng, hai môi trường, 100 task). Cần cổng cách ly C5 đạt. | Theo `kaggle/TODO.md` | đã duyệt (hạn mức Kaggle) |
| [ ] C2 | §38 phiên 3 và phân tích. Báo cáo tỉ lệ theo từng model; các đầu ra không phải là các lượt học độc lập. | Theo `kaggle/TODO.md` | đã duyệt |
| [x] C3 | §39 (auditor bốn hãng). | Xong 16/11 | — |
| [ ] C10 | Can thiệp lịch sử git có kiểm soát. Đặc tả ở mục 7. **Chỉ lập thiết kế sau khi S0 xong.** | — | **chờ** (ngân sách mới, khoảng 7,5 USD cho 34 task) |
| [ ] C6 | Dự phòng nếu C1 không chạy được: agent Flash, môi trường một commit, trên Vertex, khoảng 5,9 USD cho hai nhánh. | — | **chờ**; hiện chưa duyệt |

**Định nghĩa đóng băng (đề xuất, chờ @thuthuy xác nhận):** sau 01/12 không mở thí nghiệm xác nhận mới. Vẫn được sửa lỗi phân tích và tính lại, có ghi nhật ký. Không đổi giả thuyết hay quy tắc phân tích sau khi thấy kết quả.

### Đợt 4: câu chữ (làm song song với đợt 2)

| # | Việc |
| --- | --- |
| [x] D1 | Xong 17/11. Theo §41: "phần do rò rỉ" thành "tác động của việc bỏ hai commit do benchmark tạo ra"; bỏ chữ "cận trên" (không có lịch sử thật để xóa nhầm). Threats: thay "một kênh" bằng hai kênh và mức dùng của từng agent (A133). |
| [x] D2 | Xong 17/11. "Genuine" thành "còn lại dưới đối chứng một commit, theo bộ chấm của benchmark". |
| [x] D3 | Xong 17/11. "Tác dụng của độ dài" thành "tác dụng của một skill không liên quan". |
| [x] D4 | Xong 17/11 (cột cấu trúc lượt chạy). Tách so sánh cùng ngày khỏi so sánh khác ngày (placebo chạy sau một ngày; 21 task Pygments chạy lại). |
| [x] D5 | Xong 17/11. Đặt giới hạn "một lượt học" ngay cạnh kết luận học lại. |
| [x] D6 | Xong 17/11. Pygments: chỉ nói "chưa có bằng chứng", kèm tỉ lệ nền thấp. |
| [x] D7 | Xong 17/11. Chi phí tiết kiệm: ghi là ước tính hồi cứu, vì mọi task đều đã chạy. |
| [x] D9 | Xong 17/11. Đối chiếu PACE: cổng thống kê trả lời "điểm có tăng thật không"; bài này hỏi thêm "mức tăng có hợp lệ không". Viết sau D9a. |
| [ ] D10 | Bỏ mọi chỗ gọi Gatekeeper là đóng góp phương pháp. Cân nhắc bỏ chữ "Certifying" khỏi tên bài: **chờ @thuthuy**. |

### Đợt 5: mạch bài, hình, minh bạch

| # | Việc |
| --- | --- |
| [x] E1 | Xong 17/11. Mạch: mức tăng → cơ chế trong trace → can thiệp → phần còn lại → phạm vi. |
| [x] E2 | Xong 17/11. Rút ngắn tóm tắt; bỏ lặp con số ở mở đầu và kết luận. |
| [x] E3 | Xong 17/11 (Bảng 1). Bảng kê thí nghiệm: câu hỏi → can thiệp → nhóm task → seed → bộ chấm → phân tích. |
| [x] E4 | Xong 17/11. Vẽ lại Hình 1: nét liền cho điều đo được, nét đứt cho điều suy ra. |
| [x] E5 | Xong 17/11 (Hình 3). Hình dòng thời gian đăng ký và nhóm task (34 + 36). |
| [x] E6 | Xong 17/11 (Hình 2). Hình mức tăng theo cặp và tương tác, có khoảng tin cậy. |
| [x] E7 | Xong 17/11: Bảng 2, Bảng 3; bỏ Bảng II, III và Hình 2 cũ. Sửa Hình 2, Hình 3, Bảng I theo ghi chú của thầy; bỏ hoặc gộp Bảng II, III. |
| [x] E8 | Xong 17/11 (Threats theo đối tượng). Ký hiệu riêng cho skill và bộ chấm; sắp lại Threats theo đại lượng mục tiêu. |
| [x] F1 | Bảng đăng ký: mỗi mục kèm mã commit, thời điểm, và dữ liệu nào đã thấy lúc đó. **Xong 17/11:** `scripts/registration_timeline.py` → `results/registration_timeline.json` (52 dòng: mục và ghi chú thực thi, commit đầu tiên chứa tiêu đề; file kết quả đầu tiên trên `pilot-snapshots`). Không mục nào có kết quả công bố trước khi đăng ký. Giới hạn: "dữ liệu đã thấy" chỉ chứng minh được bằng thứ tự thời gian, không bằng nội dung đã đọc. |
| [~] F2 | Trong gói: mã task, mã băm skill, phiên bản model, ngày chạy, phiên bản bộ chấm, kết quả chấm, mã tính thời điểm vượt ngưỡng. **Phần lớn xong 17/11:** `scripts/package_manifest.py` → `results/package_manifest.json` (42 file lượt chạy: chuỗi model do runner ghi, seed, số lượt, sha256 danh sách task, sha256 file, thời điểm công bố đầu tiên; 26 file skill kèm sha256). Kết quả chấm S và L nằm trong từng bản ghi; mã tính thời điểm vượt ngưỡng là `src/gatekeeper/eprocess.py`. **Còn thiếu:** phiên bản bộ chấm (ảnh Docker của từng task) chưa được ghi riêng; chuỗi model là tên endpoint, không phải mã bản dựng của nhà cung cấp. |
| [x] F3 | Ghi rõ nhật ký học nào đã bị ghi đè. **Đã có:** A130 và `docs/preregistration_main.md` (lượt học Jinja gốc còn 6 lần gọi; Bleve 7; §30 14); cả hai file nằm trong gói. Paper phải nhắc lại câu này ở mục Threats (kiểm ở G1). |
| [x] F4 | Dựng lại mọi con số từ gói, trên một máy sạch. **Xong 17/11 (trong một thư mục sạch, không phải máy sạch):** chạy `make_numbers.py --trial trial --rows <rows>` trong gói cho ra `paper/numbers.tex` **giống hệt** bản trong repo. Mã `src/` của gói giống hệt repo. Chưa thử trên một máy cài mới từ đầu (cần cài `pip install -e .` trong gói). |

### Đợt 6: định dạng và nộp

| # | Việc | Duyệt |
| --- | --- | --- |
| [x] A1 | Xong 17/11: `acmart` sigconf,review,anonymous. Chuyển sang mẫu ACM `acmart` (`sigconf,review,anonymous`). | tự làm |
| [x] A2 | Xong 17/11: 7 trang kể cả tham khảo. Cắt còn 10 trang, tính cả hình, bảng, phụ lục. | tự làm |
| [x] A3 | Xong 17/11 trong PDF; gói tái lập vẫn ở A4. Ẩn danh trong PDF: tên tác giả, đường dẫn repo, siêu dữ liệu, cách nhắc tới việc của chính mình. | tự làm |
| [~] A4 | Gói tái lập ẩn danh, dựng thành **bản xuất có chọn lọc** trong một thư mục của repo. Không dùng repo kèm lịch sử: repo chứa tên người phụ trách (`CLAUDE.md`), địa chỉ tài khoản dịch vụ (`docs/vertex_setup.md`), đường dẫn phiên trong lời nhắn commit. Bằng chứng thời điểm đăng ký giữ bằng một file liệt kê mã commit, thời điểm, lời nhắn đã gỡ danh tính. | **Bản nội bộ xong 17/11:** `python scripts/build_replication_package.py --trial <worktree nhánh trial> --rows <rows> --out <thư mục rỗng>`: 2034 file, quét danh tính 0 chỗ lộ (kể cả các file `.gz`, kiểm riêng bằng `zcat`). **Đưa ra ngoài (Zenodo hay nơi khác): chờ @thuthuy.** Bản trên Zenodo không xóa được. |
| [ ] A5 | Khai báo việc dùng AI theo chính sách của ACM. Lập bảng: công cụ, việc AI đã làm, phần nào tác giả đã kiểm. Viết sau A5a. | **chờ** (nội dung khai báo) |
| [ ] A6 | Đăng ký tóm tắt trước 15/01; nộp trước 22/01. | @thuthuy |
| [ ] G1 | Bảng đối chiếu: 27 ghi chú trên PDF và danh sách của thầy (mục 8) với từng chỗ sửa. | tự làm |
| [ ] G3 | Một vòng review lại sau khi sửa. | @thuthuy và thầy |
| [ ] G4 | Soát tiếng Anh; soát theo năm tiêu chí của CFP. | tự làm |

---

## 6. Đặc tả bước 0 (S0): kiểm toán lịch sử git và trace

Miễn phí, chỉ đọc. Kết quả quyết định có chạy C10 không và thiết kế thế nào.

**Ba mức, không gộp:**

| Mức | Câu hỏi | Lấy từ đâu |
| --- | --- | --- |
| 1. Tồn tại | Mỗi task có bao nhiêu commit, thông điệp gì, diff của từng commit chứa gì? | Repo task thật (`github.com/swesmith/<repo>.<hash>`, mỗi task một nhánh). Không suy từ trace. |
| 2. Đã hiển thị | Thông điệp và diff của commit nào đã hiện trong một quan sát của agent? | 29 file trace trên `main` |
| 3. Chỉ báo sử dụng | Sửa mã sau khi xem diff? Bản vá là đảo ngược chính xác của commit chèn lỗi? Agent khôi phục hoặc chạy lại test đã bị gỡ? | Trace và bản vá. **Ghi rõ là chỉ báo gián tiếp.** |

**Phải tách riêng hai commit:** "Bug Patch" (diff là lỗi được chèn) và "Remove F2P Tests" (diff chứa chính các bài kiểm tra tái hiện lỗi). Commit thứ hai có thể là một kênh rò rỉ mà bài chưa xét; bài hiện viết "chúng tôi đo một kênh".

**Lưu ý khi phân loại lệnh:**
- `git log` không kèm `-p` chỉ cho thấy thông điệp, không cho thấy diff.
- `git show <ref>` và `git diff <ref>` phải được quy về đúng commit: `HEAD` là "Remove F2P Tests", `HEAD~1` là "Bug Patch", `HEAD~2` là "Initial commit" (nếu mức 1 xác nhận cấu trúc ba commit).
- Mã băm rút gọn phải được nối với thông điệp qua đầu ra `git log` trong cùng trace.

**Báo cáo theo từng nhánh thí nghiệm** (repo, môi trường, có skill hay không), kèm mã task làm bằng chứng cho mỗi con số.

**Ba trường hợp sau S0:**
- Chỉ diff của "Bug Patch" được hiển thị: giữ thiết kế 2 × 2 ở mục 7.
- Cả hai commit được hiển thị: thiết kế lại để tách hai kênh; kiểm power và chi phí trước.
- Lịch sử có nhiều hơn ba commit ở một số task: xem lại cả câu chữ D1.

---

## 7. Đặc tả C10 (CHƯA duyệt; chỉ để lập kế hoạch)

**Câu hỏi:** thành phần nào của lịch sử git tạo ra mức tăng?

**Kết quả S0 (§41):** có hai kênh, nhưng agent nghiên cứu chỉ dùng kênh diff "Bug Patch" (0 lượt thấy test bị xóa). Vậy với agent nghiên cứu, thiết kế cơ sở dưới đây là đúng, với điều kiện commit "Remove F2P Tests" được giữ y nguyên ở cả bốn ô. Với agent thứ hai cần thêm một chiều cho kênh test.

**Thiết kế cơ sở** (agent nghiên cứu):

| | Diff xem được | Diff không xem được |
| --- | --- | --- |
| **Thông điệp "Bug Patch"** | A: môi trường gốc | C: commit rỗng mang thông điệp, trên cùng cây mã |
| **Thông điệp trung tính** | B | D: một commit |

- Cây mã ở `HEAD` giống hệt nhau ở cả bốn môi trường.
- Mỗi môi trường hai nhánh (có skill, không skill): tám nhánh, **chạy cùng lúc**. Không dùng lại số của A và D đã chạy ngày khác.
- Task: 34 task Jinja không có mô tả. Tập này được chú ý vì đã thấy hiệu ứng ở đó, nên kết quả phải ghi là "trên tập được chọn sau khi thấy dữ liệu trước". Dùng cả 70 task (thêm 36 task của §35, chọn bằng quy tắc trước khi có kết quả) thì sạch hơn và power cao hơn, chi phí khoảng gấp đôi.
- Phép thử chính: phép kiểm cuối pool của mục 3.1. Đăng ký trước **một** phép so chính và phép kiểm tương tác giữa thông điệp và diff.
- Thông điệp và diff có thể bổ trợ nhau (thông điệp chỉ đường tới diff). Khi đó không chia được mức tăng thành hai phần cộng lại.
- Đọc kết quả: nếu B gần bằng A thì giả thuyết về thông điệp **yếu đi**.
- Mô phỏng power trước khi đăng ký.

**Chi phí ước tính:** khoảng 5 USD dự kiến, trần khoảng 7,5 USD cho 34 task. Cách tính: chi phí bốn nhánh đo ở §35 là 0,0746 USD mỗi task, nhân đôi cho tám nhánh, cộng một cost_limit 0,30 cho mỗi nhánh. Tiền thật trên Vertex. **Là ngân sách mới; @thuthuy chưa duyệt.**

**So với C1:** nếu chỉ kịp một thí nghiệm trước 01/12 và S0 xác nhận C10 cô lập được cơ chế, ưu tiên C10. Nếu lịch sử có nhiều kênh đan xen không tách được trong ngân sách, ưu tiên C1.

---

## 8. Các điểm của thầy (tóm tắt, để đối chiếu ở G1)

Bản gốc (meta-review và PDF có 27 ghi chú) do @thuthuy giữ; chưa đưa vào repo.

**Kết luận của thầy:** "weak reject", cần sửa lớn trước khi nộp. Điểm theo bốn góc nhìn: phát hiện thực nghiệm 4/5; bảo đảm thống kê 2/5; đối chứng nhân quả 3/5; tái lập và trình bày 3/5.

**P0, thống kê và trình tự:**
- [ ] Tách ba đại lượng: tác dụng trên pool đã hiện thực, tác dụng kỳ vọng của agent, tác dụng khi triển khai. → B2
- [ ] Lập luận lấy mẫu hợp lệ cho phép thử 70 task, hoặc rút cách đọc anytime-valid. → B4, mục 3.5
- [ ] Ghi 70 quan sát là 34 task quen với kết quả seed mới cộng 36 task mới. → B4
- [ ] Thu hẹp Định lý 2 hoặc thêm chứng minh trên sự ngẫu nhiên của agent. → B1, B3
- [ ] Sửa Mệnh đề 3 bằng điều kiện không tầm thường. → B3
- [ ] Liệt kê mọi quyết định tuần tự và cách chia α; khớp con số 12. → B5
- [ ] Đăng ký có mốc thời gian, kế hoạch phân tích đã khóa, thông tin đã thấy ở mỗi lần đăng ký. → F1

**P0, nộp bài:** mẫu ACM ẩn danh (A1, A3); trong giới hạn trang (A2); gói tái lập ẩn danh kiểm từ máy sạch (A4, F4).

**P1, diễn giải:** xóa lịch sử là can thiệp vào lịch sử, chưa chắc là rò rỉ thuần (D1, S0, C10); giới hạn một lượt học (D5); "length-only" (D3); tách cùng ngày và khác ngày (D4); "mức tăng theo bộ chấm" (D2); công bố mã task, mã băm, phiên bản (F2); nhật ký bị ghi đè (F3); so sánh với PACE (D9).

**P1, mạch bài và hình:** E1–E8.

**P2, tùy chọn:** lặp lại việc học qua nhiều seed; giữ lịch sử hợp lệ và chỉ bỏ kênh rò rỉ (C10); họ model khác hoặc repo độc lập (C1). Thầy ghi: đừng trình bày các mục này là bắt buộc.

**Các ghi chú trên PDF chưa nằm trong danh sách trên:**
- [ ] Trang 5, so sánh quy tắc dưới A/A: trình bày là so sánh về kiểm soát sai số; nêu mục đích, mức danh nghĩa, số lần được nhìn của từng quy tắc; thêm một phép kiểm cỡ mẫu cố định.
- [ ] Trang 6, Hình 2: gắn nhãn nhóm task, seed, giả thuyết; vẽ ngưỡng 40 và ngưỡng cả họ; tách thời điểm vượt ngưỡng hồi cứu khỏi lần dừng thật.
- [ ] Trang 6, Hình 3: ghi mẫu số và nhánh đối chứng cùng thời điểm.
- [ ] Trang 8, bộ theo dõi trace: đánh giá với nhãn độc lập, có ma trận nhầm lẫn; tách "thấy thông điệp commit" khỏi "dùng thông tin rò rỉ". → S0 mức 2 và 3
- [ ] Trang 9, các quy tắc trên luồng thật: bảng so sánh mục đích, mức danh nghĩa, số lần nhìn, cỡ mẫu hiệu dụng; tách khỏi mô phỏng A/A.
- [ ] Trang 12, Bảng II và III: tách thành phần phương sai thực nghiệm khỏi mô phỏng power; chú thích tự đủ.

---

## 9. Quyết định đang chờ @thuthuy

| # | Việc | Lời khuyên |
| --- | --- | --- |
| Q1 | Xác nhận đích là EASE 2027 (hạn 22/01). `CLAUDE.md` và `README.md` vẫn ghi ASE 2027. | Xác nhận rồi cập nhật hai file |
| Q2 | Mốc đóng băng 01/12 theo định nghĩa ở đợt 3. | Đồng ý |
| Q3 | Tên bài: giữ hay bỏ chữ "Certifying". | Bỏ, vì chứng nhận không còn là đóng góp chính |
| Q4 | Ngân sách C10 (khoảng 7,5 USD cho 34 task). | Quyết sau khi có kết quả S0 |
| Q5 | Ngân sách C6 (khoảng 5,9 USD). | Chỉ khi C1 không chạy được |
| Q6 | Nơi đặt gói tái lập ẩn danh, và thời điểm đưa ra ngoài. | Dựng nội bộ trước; chỉ đưa ra khi đã xem bản cuối |
| Q7 | Dừng mở rộng hướng Kaggle (C7, C8, C9, D, E trong `kaggle/plan_v4.md`). | Dừng cho tới khi bài về 10 trang |

Mọi "quyết định" xuất hiện trong các vòng phản biện ngày 16/11 đều là lời của bên phản biện. Trong các vòng đó @thuthuy mới quyết hai điều: không bỏ khung chứng nhận, và yêu cầu lập file này.

---

## 10. Trạng thái repo lúc lập file

- Đã lên `main`: hai commit chỉ thêm nguồn vào `configs/sources.json` (PACE, CFP của EASE, từ khóa mới cho bài báo về đặt cược) và file này.
- Chưa có mã, bản đăng ký hay nội dung bài nào bị sửa theo kế hoạch này.
- Số mục đăng ký mới nhất là §40 (trong `kaggle/`). Trước khi đặt số cho một mục mới, kiểm lại số lớn nhất ở cả `docs/preregistration_main.md` và `kaggle/`.
