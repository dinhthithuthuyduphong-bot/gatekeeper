# Rà hướng đi của paper từ đầu tới cuối, đối chiếu dữ liệu (05/11/2026)

**Luận điểm của paper:** đánh giá skill cho coding agent, gồm nhận skill, quy lỗi cho skill và audit, phải qua được **placebo A/A**. Nhiều quy tắc đã công bố không qua. Phép trừ placebo (Mệnh đề P) cho cách làm đúng, có chứng minh.

Quy ước: **ĐK** = đã đăng ký trước; **TD** = thăm dò.

## 1. Đối chiếu từng luận điểm với dữ liệu

| # | Luận điểm | Bằng chứng (file) | Loại | Độ chắc | Vấn đề phát hiện khi rà |
| --- | --- | --- | --- | --- | --- |
| L1 | Bước tạo ứng viên "lỗi do skill" của Dong et al. cho số ca placebo bằng số ca có skill | `replicate_attribution.json`: E2 13 so với 14, R = 1,08 [0,68; 1,75]; E1 mọi skill có CI của R chứa 1 | ĐK §18 | Chắc, nhưng CI rộng | Một model, một loại tác vụ |
| L2 | Phép trừ placebo ước lượng đúng số ca do skill (Mệnh đề P) | `docs/theory/proofs.md`; test mô phỏng | Chứng minh | Chắc | (b) cần giả thiết "chỉ gây hại". (c) D2 chỉ xấp xỉ, do các cặp dùng chung lần chạy không skill |
| L3 | Phương pháp phân biệt được khi tác dụng có thật | S3: T4 × placebo E2, R_help = 0,09, p = 4·10⁻⁵ | ĐK §20 | Chắc ở chiều "giúp" | T4 chỉ có 20 task, 1 seed; cost-limit 0,5 so với 1,0; **chiều "hại" chưa có đối chứng thật** (S5 dừng) |
| L4 | Auditor LLM đổ lỗi sai | Đổ lỗi cho skill giả: 100% / 12% / 20% (Lite / Flash / Pro). Cận dưới đổ lỗi sai (S2): 0,64 / 0,04 / 0,21 | ĐK §19, §20 | **Vừa** | **LỖI MỚI:** S2 gộp E1 theo đơn vị (skill, task), nhưng 45/112 task thuộc ≥ 2 skill, nên cặp placebo bị đếm lặp. Bootstrap coi các đơn vị độc lập, nên **U có thể bị đánh giá thấp và cận dưới có thể bị phóng đại**. Phải tính lại bằng bootstrap theo task |
| L5 | Cơ chế: auditor đổ lỗi theo dấu vết của skill | S4: Pro 18/25 so với 11/27, p = 0,029 | TD | Yếu–vừa | Mẫu nhỏ; đặc trưng thô |
| L6 | Các quy tắc đã công bố nhận nhầm dưới placebo | Bảng A: so một lần 0,46 / 0,80; GEPA 0,14 mỗi đề xuất; MH 0,025 / 0,111; e-SR 1,0; Library Drift 0,003; Gatekeeper 0,003 | ĐK §19 | Chắc (10.000 luồng) | B-X2 là cổng do mình dựng theo công bố. e-SR "1,0" là đúng lý thuyết, phải giải thích rõ để không bị đọc thành phê bình sai |
| L7 | SWE-Skills-Bench không khác may rủi | 6/392 ô (ĐK); 8/98 skill so với 4,9 (TD) | ĐK + TD | Vừa | Bản gộp chưa tái lập được đúng 4/2/92 (mình ra 4/4/90) |
| L8 | Quy tắc hiệu chỉnh D2 dùng được | Dương tính giả 0,006; độ nhạy 0,41 / 0,77 | ĐK §19 (plasmode) | Vừa | Chỉ trên mô phỏng; D2 là xấp xỉ (xem L2 c) |
| L9 | Độ không đồng nhất theo task nhỏ | Bác được τ ≥ 0,20 | ĐK §18 + D-M8 | Yếu (chỉ là cận) | Phép thử H18-1 không có power |
| L10 | Admission và thu hồi có kiểm soát (Gatekeeper) | T4 admit ở trial 20; T2b không thu hồi nhầm lần nào trong 1.000 | ĐK §14, §15 | Chắc | Thu hồi chỉ có trên plasmode |

## 2. Điểm yếu tổng hợp, theo mức nguy hiểm

1. **Một model agent** cho mọi phép đo A/A (L1, L3, L4, L6).
2. **L4 vừa có lỗi tính (đếm lặp) vừa có sắc thái** theo auditor.
3. **Chiều "hại" chưa có đối chứng dương thật** (L3).
4. **D2 chỉ xấp xỉ** (L2 c) và chỉ được kiểm trên plasmode (L8).
5. **Mẫu nhỏ, CI rộng** (L1: [0,68; 1,75]).
6. Một loại tác vụ.

## 3. Phương án tăng sức mạnh (theo L38)

| # | Phương án | Vá | Chi phí | Dự đoán |
| --- | --- | --- | --- | --- |
| **P-A** | **Sửa L4:** bootstrap theo **task** (mỗi lần lấy một task thì lấy mọi đơn vị (skill, task) của nó). Báo cáo cả bản cũ | Điểm yếu 2 (tính đúng) | 0 | Chắc chắn ra số; cận dưới có thể giảm |
| **P-B** | **Nâng D2 thành kiểm định hoán vị chính xác:** khi không có hiệu ứng, trong từng task, nhãn "có skill / không skill" của 2k lần chạy hoán đổi được. Hoán vị nhãn trong từng task cho mức **đúng α** (định lý hoán vị cổ điển; phải lấy nguồn công bố trước khi dùng, R1). Kèm công thức phương sai cho S − P | Điểm yếu 4; làm Mệnh đề P chặt hơn | 0 | Chắc chắn |
| **P-C** | **Lặp lại trên model khác hãng** (gpt-oss-120b hoặc Qwen3 trên Vertex): §18 (1 skill E1 × 40 task × 3 seed × 2 nhánh), bảng A (A/A), và một đối chứng dương nhỏ kiểu T4 | Điểm yếu 1 | Khoảng 10–25 USD (giá chưa xác minh); có bước thử dưới 0,1 USD | Phép đo luôn ra số. Rủi ro: model chưa được bật, hoặc không tương thích với mini-swe-agent |
| **P-D** | **Áp phép trừ placebo lên dữ liệu ngoài có chạy lặp,** nếu có công bố: SkillJuror (5 trial mỗi điều kiện), ACES. Kiểm câu "the benefit is task-dependent" | Điểm yếu 1, 6 (dữ liệu ngoài, nhiều model, tác vụ khác) | 0 nếu dữ liệu công khai | Chưa biết dữ liệu có công khai không; phải kiểm |
| **P-E** | **Audit bởi người** trên khoảng 20 cặp (10 có skill thật, 10 skill giả), làm mù điều kiện | Điểm yếu 2 (giới hạn "auditor là LLM") | Thời gian của người (👤) | Không dự đoán; kết quả nào cũng có giá trị |
| **P-F** | **Thêm seed cho E2:** 2 seed không skill nữa cho 109 task | Điểm yếu 5 (CI hẹp hơn; cho phép phân tích k = 5) | Khoảng 218 lần chạy × khoảng 0,08 USD ≈ 17 USD | Chắc chắn ra số |
| P-G | Đối chứng dương phía "hại": skill gợi ý bản vá sai, chạy thử 3 task | Điểm yếu 3 | Thử khoảng 0,15 USD | Đặt cược nhỏ (phải xem agent có làm theo không) |

**Đề xuất thứ tự:**
- P-A và P-B ngay, 0 USD, vì sửa chỗ sai và làm lý thuyết chặt hơn.
- P-D (0 USD, kiểm dữ liệu có công khai không).
- Rồi P-C, giá trị cao nhất trên mỗi USD, cần @thuthuy duyệt và cho biết tình trạng Model Garden.
- P-E nếu có người đọc.
- P-F và P-G tùy ngân sách.
