# Pilot G1: kiểm chứng điều gì, bằng lý thuyết nào, lý thuyết đó dựa trên cơ sở nào

Viết cho người mới làm nghiên cứu (02/11/2026).

## 1. Vì sao phải có pilot

Paper Gatekeeper (FSE-2027-13) đề xuất một "người gác cổng" cho **skill tái sử dụng** của agent sửa code. Skill là một đoạn hướng dẫn hay quy trình rút ra từ repo này để dùng ở repo khác. Gatekeeper chỉ cho một skill được dùng (admit) khi có **bằng chứng thống kê** rằng nó giúp, và chặn skill có hại.

Paper chỉ có ý nghĩa nếu hai điều sau đúng:

1. **Có tồn tại skill tạo ra hiệu ứng đo được.** Nếu mọi skill đều có hiệu ứng ≈ 0, Gatekeeper sẽ không bao giờ admit gì, và paper không có gì để chứng minh. Đây là rủi ro R15 trong `TODO.md`.
2. **Phép đo hiệu ứng là đáng tin**: không lệch, không quá nhiễu, chi phí chịu được.

Thí nghiệm chính tốn hàng nghìn USD. Pilot (≤ 35 USD) trả lời hai câu trên **trước** khi tiêu số tiền đó. Đây là **cổng G1**: đạt thì đi tiếp, trượt thì thu hẹp hoặc đổi hướng.

## 2. Mỗi giai đoạn kiểm chứng điều gì

| Giai đoạn | Câu hỏi | Cách kiểm | Kết quả |
| --- | --- | --- | --- |
| **A** (2,12 USD) | Một lần chạy agent tốn bao nhiêu? Model nào đủ rẻ mà vẫn giải được task? | Chạy 4 task với Flash và Flash-Lite | Flash-Lite rẻ hơn 11 lần, giải được như Flash → chọn Flash-Lite |
| **B1, B2** | Phép đo có lỗi không? | **Đối chứng nhiễu** (A/A): hai nhánh giống hệt nhau, chỉ khác seed, nên hiệu ứng thật phải là 0. **Đối chứng dương**: lộ đáp án, nên phải giúp rõ rệt | Tìm ra lỗi seed = 0 (A14) và lỗi thiết kế đối chứng (D1, D2) → làm lại |
| **B3** | Sau khi sửa, phép đo có sạch và đủ nhạy không? | A/A + đối chứng dương mạnh (file + hàm + test) | **Đạt**: A/A ≈ 0; đối chứng dương −0,125. Pipeline phát hiện được hiệu ứng lớn |
| **C** (sàng lọc) | 4 skill thật có giúp không? | Mỗi skill chạy trên task mà nó được kích hoạt, so với nhánh không skill | Chỉ validation-error đi đúng hướng (−0,06) |
| **Xác nhận** (đang chạy) | Tín hiệu của validation-error có thật hay chỉ là may? | Chạy lại trên **dữ liệu mới** với 4 seed, kiểm định đã khóa trước | Chờ |

Ý tưởng cốt lõi: **trước khi đo thứ mình muốn biết (C), phải chứng minh cái thước đo tốt (B)**. Giống như cân phải được hiệu chỉnh bằng quả cân chuẩn trước khi cân hàng.

## 3. Các lý thuyết được dùng và cơ sở của chúng

### 3.1 Đo hiệu ứng nhân quả bằng thiết kế ghép cặp

- **Đại lượng cần đo:** STR = E[ℓ(có skill) − ℓ(không skill)] trên các task mà skill áp dụng. Đây là **hiệu ứng nhân quả trung bình** (average treatment effect).
- **Cơ sở: mô hình kết cục tiềm năng (potential outcomes)** của Neyman (1923) và Rubin (1974). Mỗi task có hai kết cục tiềm năng, "nếu dùng skill" và "nếu không dùng". Ta không quan sát được cả hai trên cùng một lần chạy, nhưng có thể chạy **cùng một task hai lần**, mỗi nhánh một lần.
- **Vì sao ghép cặp:** hai nhánh chạy trên cùng task, cùng image Docker, cùng model. Độ khó riêng của từng task bị triệt tiêu khi lấy hiệu Z. Pilot ngoài trên SWE-Skills-Bench cho thấy ghép cặp giảm phương sai khoảng 4,3 lần (R15).
- **Giả định cần có:** hai nhánh chỉ khác nhau ở skill (không lẫn biến khác). Lỗi seed = 0 ở B1 vi phạm đúng giả định này. Ta phát hiện được nó nhờ đối chứng A/A.

### 3.2 Thước đo: test của SWE-bench

- **Resolved** = mọi test FAIL_TO_PASS chuyển sang pass và không test PASS_TO_PASS nào bị hỏng (Jimenez et al., ICLR 2024).
- **Cơ sở:** test là **đặc tả có thể chạy được** (executable specification), một ý tưởng nền tảng của kiểm thử phần mềm. Bản *Verified* được con người kiểm tra lại để loại task có test sai hoặc mơ hồ.
- **Giới hạn:** test chỉ là xấp xỉ của tính đúng. Một bản sửa có thể qua test mà vẫn sai ở chỗ khác.

### 3.3 Đối chứng nhiễu (A/A) và đối chứng dương

- **A/A test** (Kohavi, Tang & Xu 2020, thực nghiệm trực tuyến): chạy hai nhánh giống hệt nhau để phát hiện lỗi của chính hệ thống đo. Nếu A/A cho hiệu ứng khác 0, lỗi nằm ở thước đo chứ không ở thứ được đo.
- **Đối chứng dương:** khái niệm cơ bản của thiết kế thí nghiệm (sinh học, y học). Dùng một can thiệp **chắc chắn có tác dụng**; nếu không thấy tác dụng thì phép đo không đủ nhạy.
- **Kiểm định tương đương TOST** (Schuirmann 1987; Lakens et al. 2018): để khẳng định "gần như bằng 0", cần chứng minh hiệu ứng nằm **trong một biên**. Chỉ "không bác bỏ được H₀" thì chưa đủ.

### 3.4 Kiểm định giả thuyết

- **Khung Neyman–Pearson** (1933): đặt H₀ ("skill không giúp"), chọn mức sai lầm loại I α (xác suất kết luận "giúp" khi thực ra không giúp), và power (xác suất phát hiện khi thật sự giúp).
- **Kiểm định hoán vị đổi dấu** (Fisher 1935; Pitman 1937).
  - **Cơ sở:** suy luận dựa trên phép ngẫu nhiên hoá. Nếu skill không có tác dụng với task nào, nhãn "có skill / không skill" của mỗi cặp có thể **đổi chỗ** mà phân phối không đổi. Vì thế đổi dấu ngẫu nhiên các Z cho ra phân phối của thống kê khi H₀ đúng.
  - Kiểm định này **chính xác** và không cần giả định phân phối chuẩn, nên hợp với mẫu nhỏ (~30 task) và dữ liệu rời rạc {−1, 0, 1}.
- **Holm (1979):** khi kiểm nhiều skill, xác suất "ít nhất một skill đạt do may" tăng lên. Holm kiểm soát xác suất này cho cả nhóm (FWER). Holm được chứng minh bằng bất đẳng thức hợp (Bonferroni) và đúng với mọi kiểu phụ thuộc giữa các skill.
- **Tách dữ liệu chọn / xác nhận** (Cox 1975): nếu dùng cùng dữ liệu để chọn skill tốt nhất rồi kiểm định nó, kết quả sẽ bị thổi phồng ("lời nguyền người thắng"). Dùng dữ liệu C để chọn và dữ liệu mới để kiểm thì loại bỏ được thiên lệch này.
- **Hồi quy về trung bình** (Galton, thế kỷ 19): lý do quy tắc đối chứng dương v1 sai. Chọn task theo kết quả xấu của một lần chạy thì lần chạy sau tự nhiên trông tốt hơn.

### 3.5 Cỡ mẫu và power

- **Công thức** n = (z₁₋α + z₁₋β)² σ² / δ², dựa trên định lý giới hạn trung tâm (phân phối của trung bình gần chuẩn khi n đủ lớn); xem Cohen (1988).
- **Phương sai theo cụm:** nhiều seed trên một task không độc lập. Chạy lặp chỉ giảm nhiễu *trong* task, không giảm khác biệt *giữa* các task (Miller 2024, áp dụng cho đánh giá LLM).
- **Browne (1995):** phương sai đo từ pilot nhỏ thường bị đánh giá thấp, nên dùng **cận trên tin cậy** để không thiếu power.
- **MDE theo nguồn lực** (Lakens et al. 2018): với ngân sách có hạn, công bố hiệu ứng nhỏ nhất mà thí nghiệm phát hiện được. Nhờ vậy "không thấy hiệu ứng" được đọc đúng nghĩa là "không có hiệu ứng lớn hơn MDE".

### 3.6 Đăng ký trước (pre-registration)

- **Cơ sở:** hướng dẫn thử nghiệm lâm sàng (ICH E9) và phong trào khoa học mở (Nosek et al. 2018). Quy tắc phân tích phải được ghi **trước** khi thấy dữ liệu. Nếu không, người phân tích (kể cả vô tình) chọn cách phân tích cho ra kết quả mình muốn ("khu vườn lối rẽ", Gelman & Loken 2013).
- Trong pilot này, mỗi quy tắc đều được commit lên git **trước** khi có dữ liệu tương ứng. Thời điểm commit chính là bằng chứng.

### 3.7 Lý thuyết của thí nghiệm chính (chưa dùng ở pilot)

- **E-process / martingale kiểm định** (Ville 1939; Waudby-Smith & Ramdas 2024; Ramdas et al. 2023):
  - Cho phép xem dữ liệu **liên tục** và dừng bất cứ lúc nào mà vẫn giữ được α. Đây là điều Gatekeeper cần, vì nó quyết định admit trong lúc trial vẫn đang chạy.
  - **Cơ sở:** lý thuyết martingale và bất đẳng thức Ville, tức xác suất một martingale không âm từng vượt 1/α là ≤ α.
- Pilot dùng kiểm định cổ điển vì là sàng lọc có cỡ mẫu cố định. E-process dành cho thí nghiệm xác nhận.

## 4. Chuỗi cơ sở, từ nền móng lên

```
Lý thuyết xác suất (Kolmogorov)
├─ Định lý giới hạn trung tâm ──────────── công thức cỡ mẫu, power, CI
├─ Martingale, bất đẳng thức Ville ─────── e-process (thí nghiệm chính)
├─ Bất đẳng thức hợp (Bonferroni) ──────── Holm, sổ α (FWER)
└─ Suy luận ngẫu nhiên hoá (Fisher) ────── kiểm định hoán vị đổi dấu
Suy luận nhân quả (Neyman–Rubin) ───────── STR = hiệu ứng nhân quả; thiết kế ghép cặp
Thiết kế thí nghiệm ────────────────────── A/A, đối chứng dương, tách dữ liệu, đăng ký trước
Kiểm thử phần mềm ──────────────────────── test là đặc tả → resolved của SWE-bench
```

## 5. Pilot chứng minh được gì và không chứng minh được gì

- **Chứng minh được:**
  - Pipeline đo sạch (A/A ≈ 0) và đủ nhạy với hiệu ứng lớn (đối chứng dương −0,125).
  - Chi phí thật khoảng 0,04 USD/lần chạy với Flash-Lite.
  - Phương sai thật, dùng để tính cỡ mẫu cho thí nghiệm chính.
- **Đang kiểm:** 4 skill theo họ mẫu sửa có hiệu ứng lớn (≥ MDE, khoảng 0,1–0,2) hay không.
- **Không chứng minh được:**
  - Skill có hiệu ứng nhỏ (< MDE) hay không. Ngân sách không đủ.
  - Kết quả có còn đúng với model khác hay benchmark khác không.
  - Kết quả có còn đúng với skill dạng khác không, ví dụ skill là chương trình sửa code thay vì đoạn hướng dẫn.

## Tài liệu

Neyman 1923; Rubin 1974; Fisher 1935; Pitman 1937; Neyman & Pearson 1933; Holm 1979; Cox 1975; Schuirmann 1987; Cohen 1988; Browne 1995; Ville 1939; Gelman & Loken 2013; Nosek et al. 2018 (*PNAS*); Kohavi, Tang & Xu 2020; Jimenez et al. 2024 (SWE-bench); Waudby-Smith & Ramdas 2024 (*JRSSB*); Ramdas et al. 2023 (*Statistical Science*, game-theoretic statistics); Lakens et al. 2018; Miller 2024; ICH E9. Các tài liệu kinh điển được trích theo hiểu biết; xem thêm `docs/review_thresholds.md`.
