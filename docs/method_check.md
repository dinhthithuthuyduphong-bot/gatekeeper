# Kiểm định phương pháp bằng số (03/11/2026)

Câu hỏi của @thuthuy: các con số có **đáng tin** (tỉ lệ kết luận sai đúng như lý thuyết hứa) và có **tác dụng** (đủ sức phát hiện hiệu ứng có thật) không?

- **Mã:** `scripts/verify_methods.py`. **Kết quả:** `results/method_check.json`.
- **Phương pháp:** mô phỏng plasmode (Franklin et al. 2014). Tỉ lệ giải của từng task lấy từ nhánh không skill **đã đo** ở G1 (32 task × 3 seed). **Không dùng dữ liệu E1** (R5).
- **Hiệu ứng thử:** các mốc của SWE-Skills-Bench (0,02; 0,05; 0,109) và lớn hơn. Skill dịch tỉ lệ giải của mỗi task thêm δ, cắt trong [0, 1]. Hiệu ứng thực hiện được (`eff` trong bảng) nhỏ hơn δ, vì task đã giải chắc chắn thì không thể cải thiện.
- **Số lần lặp:** R = 12.000 cho kiểm tính hợp lệ (sai số Monte Carlo < α/10), R = 2.500 cho power (sai số ≤ 0,01). Công thức sai số √(p(1−p)/R) theo Morris, White & Crowther 2019. Nguồn này **đang chờ lấy bản gốc**.
- **Kiểm plasmode:** tỉ lệ bất đồng P(Z = +1) trong mô phỏng là 0,055, nằm trong khoảng đã đo 0,04–0,08.
- **Kiểm phép tính:** kiểm định chính xác bằng tích chập trùng khớp với liệt kê đủ 2¹² cách đổi dấu, trên 50 bộ dữ liệu.
- **Lỗi tìm được trong chính script kiểm định khi review:** `rng.random((n, s)) < q` với q có dạng (n,) âm thầm tạo ra ma trận n × n khi s = 1. Đã sửa và thêm assert về kích thước (review R-6).

## 1. Đáng tin: tỉ lệ sai khi H₀ đúng (δ = 0)

| Thiết kế | Mức danh nghĩa | Kiểm định chính | Kết luận "vững" (chính + S1 + S2) | Đạt? |
| --- | --- | --- | --- | --- |
| E1 (n = 40, 3 seed, 8 repo, mức Holm đầu 0,025/3) | 0,0083 | 0,0012 | 0,0001 | ✅ (bảo thủ) |
| E2 (n = 119, 3 seed, 65 repo) | 0,025 | 0,0162 | 0,0135 | ✅ |
| A/A E1 (n = 40) | 0,05 | 0,0055 | – | ✅ nhưng **rất bảo thủ** |
| A/A E2 (n = 119) | 0,05 | 0,0233 | – | ✅ |
| Gatekeeper RQ1 (40 trial, α = 0,05/7) với skill trung tính hoặc có hại (δ ≤ 0) | 0,0071 | 0 / 12.000 | – | ✅ |

**Kết luận:** mọi phương pháp đều **hợp lệ**: tỉ lệ sai ≤ mức danh nghĩa. Chúng bảo thủ vì dữ liệu rời rạc (nhiều cặp Z = 0).

## 2. Tác dụng: power

| δ (hiệu ứng thực hiện được) | E1 chính | E1 vững | E2 chính | E2 vững |
| --- | --- | --- | --- | --- |
| 0,02 (0,013) | 0,010 | 0,000 | 0,083 | 0,070 |
| 0,05 (0,031) | 0,044 | 0,001 | 0,360 | 0,317 |
| 0,109 (0,068) | 0,255 | 0,016 | **0,924** | **0,899** |
| 0,15 (0,094) | 0,475 | 0,050 | 0,993 | 0,992 |
| 0,20 (0,125) | 0,753 | 0,114 | 1,000 | 1,000 |
| 0,30 (0,187) | 0,980 | 0,307 | 1,000 | 1,000 |

**RQ1 (40 trial sàng lọc, 1 seed):** tỉ lệ được admit theo δ.

| δ | −0,20 | −0,10 | −0,05 | 0 | 0,05 | 0,109 | 0,20 | 0,30 | 0,40 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gatekeeper (α = 0,05/7) | 0 | 0 | 0 | 0 | 0 | 0 | 0,001 | 0,012 | 0,091 |
| Plug-in (trung bình < 0) | 0,014 | **0,100** | **0,211** | **0,402** | 0,624 | 0,849 | 0,963 | 0,996 | 1,000 |
| Gatekeeper, ô E2 (α = 0,05) | | | | 0 | | 0,007 | 0,072 | 0,317 | |
| Kiểm định chính xác, cỡ mẫu cố định, cùng dữ liệu, α = 0,05 (để so sánh) | | | | 0,009 | | 0,145 | 0,450 | 0,810 | |

## 3. Phát hiện

| # | Phát hiện | Mức độ | Xử lý đề xuất (kèm cơ sở) |
| --- | --- | --- | --- |
| **A38** | **Power của E1 bị tính sai trong bản đăng ký trước.** n = 40 ra từ (z₁₋α′ + z₁₋β)²·V/δ² với α′ = 0,025. Nhưng phân tích của E1 dùng Holm trên 3 skill (mức đầu 0,0083) và đòi S2 cùng bác bỏ. Với α′ = 0,0083 thì công thức cho n ≈ 53. Plasmode: ở hiệu ứng thực hiện 0,094–0,125, power của kiểm định chính là 0,48–0,75, power của kết luận "vững" chỉ 0,05–0,11 | Cao: tuyên bố "power 80%" sai | **Giữ thiết kế E1** (R5: dữ liệu đang được thu, và tôi đã lỡ thấy 1 cặp). Báo cáo power đã sửa. Lý do không tăng n: dù n = 53, điều kiện S2 với 8 repo vẫn giới hạn kết luận "vững" (xem C7). Tăng n tốn thêm khoảng 30% chi phí E1 mà không gỡ được nút thắt. **E2 (65 repo, power 0,90 ở 0,068) là phép kiểm mạnh của paper** |
| **C8** | **RQ1 thu nhỏ không thể cho thấy độ phủ.** Với 40 trial, Gatekeeper gần như không bao giờ admit, kể cả khi δ = 0,3. Điều này đã biết từ trước: bảng plasmode (`results/design_table_plasmode.json`) cho thấy cần 186–413 trial ở δ = 0,109. Vì vậy RQ1 thu nhỏ chỉ kiểm được **một vế**: harmful acceptance (Gatekeeper 0 so với plug-in 10–21% ở δ = −0,10/−0,05). Vế clean-reuse coverage chắc chắn ≈ 0 | Cao cho paper: đây chính là rủi ro "an toàn nhưng gần như vô dụng" | (1) Báo cáo RQ1 thu nhỏ đúng phạm vi: chỉ vế an toàn. (2) Vế độ phủ cần ngân sách mỗi ô theo bảng plasmode; đó là việc của thí nghiệm chính. (3) Chi phí của tính hợp lệ mọi lúc so với kiểm định cỡ mẫu cố định (0,007 so với 0,145 ở δ = 0,109) là một **kết quả đo** cần báo cáo, không phải lỗi. Lý thuyết của đánh đổi này nằm trong Waudby-Smith & Ramdas 2024 và Grünwald et al. 2024 (GRO; c đã chọn bằng GRO, `results/gro_c.json`) |
| **C9** | A/A của E1 bảo thủ: tỉ lệ báo động 0,0055 ở mức 0,05. A/A đạt **gần như không chứng minh** pipeline sạch | Trung bình | Đã có trong bản đăng ký trước: không bác bỏ ≠ tương đương (ICH E9). Báo cáo A/A kèm CI, không dùng như bằng chứng sạch |
| C7 | S2 với 8 repo (E1) | (đã ghi) | Như A38 |
| N3, N6, N7 | **Ba nguồn chưa xác nhận được từ bản gốc:** mốc cắt dữ liệu của Gemini (cả hai trang của Google tải được nhưng không ghi mốc); Steegen et al. 2016 (đa vũ trụ) và McHugh 2012 (κ): chưa tải được | Trung bình | Không dùng cho tới khi xác nhận (R1). Steegen chỉ dùng để báo loss dạng đường cong, không quyết định nào phụ thuộc. McHugh chỉ dùng cho bước gán nhãn hai người, chưa làm. Mốc cắt: phân tích nhiễm dữ liệu E2 bị treo |
| **C10** | **Nhãn "có hại đã xác lập" của RQ1** (2 seed giữ lại, 40 task, α = 0,05/7) chỉ đạt khi skill hại mạnh: tỉ lệ gán nhãn 0,013 / 0,088 / 0,419 / 0,820 ở δ = −0,05 / −0,109 / −0,20 / −0,30. Gán nhãn sai chiều: 0 | Trung bình | Skill có hại yếu sẽ thành "chưa xác định", được báo cáo riêng (§6.1 bản đăng ký trước E1). Harmful acceptance chỉ tính trên các ô đã xác lập, nên số ô có thể rất ít. Phải nêu rõ khi báo cáo |
| – | Plasmode của E2 dùng tỉ lệ giải đo trên Verified; Live có thể khác | Thấp | Sau seed đầu, đo lại tỉ lệ giải của Live và tính lại bảng E2 (không nhìn hiệu ứng) |

## 4. Tóm lại

- **Đáng tin:** mọi phép kiểm định đều giữ đúng tỉ lệ sai danh nghĩa trên dữ liệu mô phỏng từ số đo thật. Phép tính chính xác khớp với liệt kê đầy đủ.
- **Có tác dụng:**
  - **E2: có.** Power 0,90 ở hiệu ứng 0,068.
  - **E1: yếu.** Kết luận "vững" có power ≤ 0,11 ở hiệu ứng thực tế. Kiểm định chính có power 0,98 khi δ = 0,30, nhưng chỉ 0,26 ở δ = 0,109.
  - **RQ1 thu nhỏ: chỉ đo được vế an toàn**, không đo được độ phủ. Vế an toàn cũng chỉ đo được trên các skill có hại mạnh (C10).
