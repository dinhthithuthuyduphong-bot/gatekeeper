# Pilot G1 theo từng giai đoạn: lý thuyết áp vào ra sao, kỳ vọng, kết quả thật

Cập nhật 02/11/2026. Lý thuyết nền: `docs/explainer_pilot.md`. Số liệu: `results/pilot/*.json`.

Ký hiệu chung:
- Với mỗi task x, chạy agent hai lần: có skill và không skill.
- Loss ℓ = (F + 0,5R)/1,5. Task không giải được có ℓ = 0,667; task giải được có ℓ = 0.
- **Z = ℓ(có) − ℓ(không)**. Z < 0 nghĩa là skill giúp.
- Endpoint chuẩn **resolved**: Z_res = 1[không resolved | có] − 1[không resolved | không] ∈ {−1, 0, 1}.

---

## Giai đoạn 0 (miễn phí): thử pipeline với model giả

| | |
| --- | --- |
| **Lý thuyết** | Kiểm thử phần mềm: harness chính thức của SWE-bench là "thước đo". Phải chắc thước đo đúng trước khi đo agent |
| **Áp dụng** | (1) Bản sửa gold của từng task phải được chấm *resolved* hai lần → task hợp lệ. (2) Bản sửa no-op phải cho F = 1, R = 0 → nhánh "không làm gì" được đo thật |
| **Kỳ vọng** | Gold resolve 100%; no-op có F = 1 và R = 0 |
| **Kết quả** | Đúng như kỳ vọng. Pool default dùng được **38/40** task, pool g1 dùng được **86/89**. Lần kiểm đầu loại nhầm 18 task do lỗi tải image; tách riêng lỗi hạ tầng xong thì chạy lại đúng (A1 trong `docs/audit_pilot.md`) |

## Giai đoạn A (16 lần chạy; 8,4M token input, 0,17M output): đo lượng tính toán và chọn model

| | |
| --- | --- |
| **Lý thuyết** | Lập kế hoạch thí nghiệm: cỡ mẫu = ngân sách / chi phí mỗi lần chạy, nên phải **đo** chi phí thật. Chọn model có tỉ lệ giải không quá cao, không quá thấp, vì phương sai p(1 − p) lớn nhất ở 50%: quá dễ thì skill không còn gì để giúp (trần), quá khó thì skill không cứu được (sàn) |
| **Áp dụng** | 4 task × 2 nhánh × 2 model (Flash, Flash-Lite), 60 bước |
| **Kỳ vọng** (từ bài thử 2 lần chạy) | Khoảng 475k token input mỗi lần chạy với Flash; tỉ lệ giải 20–70% |
| **Kết quả** | Mỗi lần chạy: Flash-Lite **247k input / 2,7k output**, Flash 808k input / 18,4k output (cache 79% ở cả hai). Cả hai giải 3/4 task (75%, hơi trên dải, chỉ 4 task). → Chọn Flash-Lite: ít hơn 3,3× token input và 6,7× token output (rẻ hơn khoảng 11× theo bảng giá) |
| **Phát hiện** | Lượt A1 đầu tiên **không hợp lệ**: 3/8 container không khởi động (image chưa tải) bị chấm nhầm là "không giải" → Z = −0,33 giả. Đây là lỗi của thước đo, đúng loại lỗi pilot cần bắt. Đã sửa, cách ly kết quả và chạy lại |

## Giai đoạn B1 (38 task, 113 lần chạy; 51,8M token input, 0,59M output): kiểm thước đo lần 1

| | |
| --- | --- |
| **Lý thuyết** | **A/A test:** nhánh nhiễu giống hệt nhánh gốc, chỉ khác seed, nên hiệu ứng thật bằng 0 theo thiết kế. **Đối chứng dương:** một can thiệp chắc chắn có tác dụng (gợi ý đúng file cần sửa). **CI bootstrap 90%:** lấy mẫu lại 38 task 4.000 lần để ước lượng độ bất định của Z trung bình |
| **Quy tắc đặt trước** | CI của nhiễu phải chứa 0; đối chứng dương phải cho Z ≤ −0,10 trên các task nhánh gốc thất bại |
| **Kỳ vọng** | Nhiễu ≈ 0. Lưu ý: quy tắc này có 10% xác suất báo động giả ngay cả khi pipeline hoàn hảo. Đối chứng dương giúp rõ |
| **Kết quả** | Nhiễu **−0,104, CI [−0,19; −0,02] → STOP**. Đối chứng dương −0,25 trên 23 task |
| **Chẩn đoán** | Vertex coi seed = 0 là "không đặt seed", nên nhánh gốc lấy mẫu ngẫu nhiên còn nhánh nhiễu lấy mẫu tất định: hai nhánh không giống nhau về cách lấy mẫu. Đây là vi phạm giả định ghép cặp, và A/A đã bắt được. Rà lại sau: sign test cho 8 cặp lật một chiều so với 2 cặp chiều kia, **p = 0,11**, nên ngẫu nhiên cũng giải thích được. Vì vậy, nguyên nhân B1 STOP chưa được chứng minh là lỗi seed (D3) |

## Giai đoạn B2 (38 task, 114 lần chạy; 51,3M token input, 0,59M output): kiểm thước đo lần 2, đã sửa seed

| | |
| --- | --- |
| **Lý thuyết, quy tắc** | Như B1 |
| **Kỳ vọng** | Nhiễu ≈ 0; đối chứng dương ≤ −0,10 |
| **Kết quả** | Nhiễu **−0,021, CI [−0,11; +0,08] ✅**. Đối chứng dương **−0,066, CI [−0,13; +0,0002] ❌** → STOP |
| **Chẩn đoán bằng lý thuyết** | (1) **Hồi quy về trung bình:** trên đúng 20 task mà nhánh gốc thất bại, chính nhánh *nhiễu* đạt −0,17, tốt hơn đối chứng dương. Chọn task theo kết quả xấu của một lần chạy thì lần chạy khác tự nhiên trông tốt hơn, nên quy tắc v1 sai về logic (D1). (2) **Đối chứng dương quá yếu:** mọi bản nộp đã chạm đúng file gold (sai file 0 lần), nên gợi ý tên file là thừa (D2). (3) **Phân tích phương sai:** cùng một cấu hình vẫn lật kết quả ở 8/37 task; SD của Z = 0,36 mỗi cặp; 30% lần chạy chạm trần 60 bước mà không nộp gì (D4, D5) |

## Giai đoạn B3 (38 task, 117 lần chạy; 73,6M token input, 0,76M output): kiểm thước đo lần 3, quy tắc v2

| | |
| --- | --- |
| **Lý thuyết** | Sửa D1: so đối chứng dương với nhánh nhiễu, hai nhánh **chạy độc lập** trên mọi task, không chọn lọc. Sửa D2: **đối chứng dương mạnh** (file + hàm + test cần qua + test patch). Sửa D5: 100 bước |
| **Quy tắc v2** (đăng ký trước) | Nhiễu: CI 90% chứa 0. Độ nhạy: Z(dương − nhiễu) ≤ −0,10 **và** cận trên CI < 0 |
| **Kỳ vọng** | Nhiễu ≈ 0; đối chứng dương mạnh giúp rõ rệt |
| **Kết quả** | Nhiễu **+0,062, CI [−0,001; +0,135] ✅** (sát mép). Đối chứng dương **−0,125, CI [−0,22; −0,03] ✅**. Resolved: không skill 22/39, nhiễu 20/39, **đối chứng dương 28/38**. Có 9 task chỉ đối chứng dương giải được, 1 task chỉ nhánh nhiễu giải được. Chạm trần 100 bước: 1/39 |
| **Ý nghĩa** | Thước đo **sạch** và **đủ nhạy với hiệu ứng lớn**. Tách phương sai: nhiễu giữa các lần chạy σ ≈ 0,19; khác biệt hiệu ứng giữa các task σ ≈ 0,25. Hai số này dùng để tính cỡ mẫu và MDE |

## Giai đoạn C (86 task, 204 lần chạy; 97,2M token input, 1,10M output): sàng lọc 4 skill thật

| | |
| --- | --- |
| **Lý thuyết** | **Kết cục tiềm năng / ghép cặp:** mỗi skill chỉ chạy trên các task mà điều kiện kích hoạt I(x) của nó đúng (P_s trong `corrections.md` §1.2). Nhánh không skill chạy một lần trên hợp các task đó và dùng chung cho 4 skill |
| **Vai trò trong quy tắc đã khóa** | **Chỉ để chọn**, không để kết luận (tách dữ liệu, Cox 1975): skill có Z_res trung bình < 0 được vào vòng xác nhận |
| **Kỳ vọng** | Theo dữ liệu ngoài (SWE-Skills-Bench, R15: SD của hiệu ứng skill ≈ 0,03) và R16 (I(x) chỉ có lift 1,5–1,8): **hiệu ứng nhỏ**. Với 1 seed và khoảng 30 task, MDE ≈ 0,16–0,28, nên khó thấy được gì |
| **Kết quả** | Xem bảng dưới. Chỉ **validation-error** đi đúng hướng (−0,062) → được chọn |

| Skill | n | Z resolved | Resolved (có / không) | Giúp / hại | Z loss |
| --- | --- | --- | --- | --- | --- |
| null-guard | 25 | 0,000 | 20 / 20 | 1 / 1 | +0,027 |
| type-guard | 32 | **+0,094** | 22 / 25 | 0 / **3** | +0,062 |
| exception-handling | 25 | 0,000 | 13 / 13 | 1 / 1 | −0,019 |
| validation-error | 32 | −0,062 | 19 / 17 | 2 / 0 | +0,009 |

Nhận xét:
- Hiệu ứng nhỏ, đúng như kỳ vọng.
- **type-guard có dấu hiệu gây hại**: 3 task bị hỏng, 0 task được giúp. Đây chưa phải kiểm định, nhưng chính là loại skill mà Gatekeeper phải chặn.
- Ở validation-error, hai endpoint lệch nhau: resolved giúp (−0,062) nhưng loss hơi xấu đi (+0,009). Cần xem xác nhận.

## Giai đoạn xác nhận (32 task × 3 seed, 192 lần chạy; 122,5M token input, 1,15M output): kiểm validation-error trên dữ liệu mới

| | |
| --- | --- |
| **Lý thuyết** | **Tách dữ liệu:** chỉ dùng 4 seed mới (11, 21, 31, 41), C không được dùng để kết luận. **Phương sai theo cụm:** lấy trung bình 4 seed của mỗi task rồi coi *task* là đơn vị (32 quan sát, không phải 128). **Kiểm định hoán vị đổi dấu** một phía: đổi dấu ngẫu nhiên 32 giá trị 200.000 lần để có phân phối khi H₀ đúng. **Holm** với 1 skill: α = 0,025. **A/A bằng TOST:** nhánh không skill seed 11 so với seed 21 phải tương đương trong biên MDE. **MDE theo Browne:** dùng cận trên 90% của phương sai |
| **Kỳ vọng** (nói trước) | Ở C, validation-error chỉ giúp 2/32 task (−0,06), trong khi MDE khoảng 0,1–0,2. **Khả năng cao là G1 FAIL**, tức không phát hiện hiệu ứng ≥ MDE. Muốn PASS, skill phải có hiệu ứng thật lớn hơn nhiều so với những gì C cho thấy |
| **Kết quả** | **G1 FAIL**: Ẑ = +0,031, CI 95% [−0,057; +0,120]; p chính 0,83, S1 0,76, S2 0,69; A/A 0,000 (p = 1,0). Xem `docs/g1_verdict.md` |

---

## Tổng kết: kỳ vọng và kết quả

| Câu hỏi của G1 | Kỳ vọng | Kết quả |
| --- | --- | --- |
| Thước đo có lỗi không? | Có thể có lỗi ẩn | **Có, 20 lỗi đã tìm và sửa** (A1–A20); lỗi nghiêm trọng nhất là container không chạy và seed = 0 |
| Thước đo sạch chưa? | A/A ≈ 0 | ✅ B3: +0,06, CI chứa 0 (sát mép) |
| Thước đo đủ nhạy chưa? | Đối chứng dương ≤ −0,10 | ✅ B3: −0,125, CI < 0 |
| Lượng tính toán một lần chạy? | ~475k token input (Flash, 30 bước) | **450k–640k token input, 5–6,5k output** (Flash-Lite, 60–100 bước; cache 85–87%) |
| Skill thật có hiệu ứng lớn? | Có lẽ không (R15, R16) | C: các hiệu ứng ≤ 0,1; chờ xác nhận |
| Có skill gây hại không? | Có thể | type-guard: 3 hại / 0 giúp (mô tả, chưa kiểm định) |

**Bài học quan trọng nhất cho thí nghiệm chính:**
- Nhiễu giữa các lần chạy rất lớn: cùng cấu hình mà khoảng 1/4 số cặp lật kết quả.
- Hiệu ứng khác nhau nhiều giữa các task (σ ≈ 0,25).
- Vì vậy, thí nghiệm chính cần **nhiều task hơn** chứ không chỉ nhiều seed hơn. Nó cũng phải chọn θ (SESOI) phù hợp với mức hiệu ứng thật mà skill có thể đạt.
