# Nguồn gốc của mọi con số (02/11/2026)

Tiêu chuẩn của @thuthuy: mỗi con số phải **(1) suy ra từ lý thuyết có sẵn**, hoặc **(2) là tham số phải chọn qua thử nghiệm, kèm lý do vì sao phải thử và một quy tắc chọn có thật**. Con số không đạt tiêu chuẩn thì **bị loại khỏi phương pháp**, không giữ lại kèm lời giải thích.

## 0. Giới hạn lý thuyết: những gì không thể suy ra

**Lý thuyết quyết định thống kê** (Wald 1950; định lý lớp đầy đủ): một quy tắc quyết định chỉ "tốt nhất" **đối với một hàm thiệt hại** cho trước. Không có hàm thiệt hại thì không quy tắc nào tốt hơn quy tắc nào. Vì vậy, mọi kiểm định đều cần đúng hai đầu vào giá trị, và **không thể suy ra hai đầu vào này từ dữ liệu**:

| Đầu vào giá trị | Ý nghĩa | Cách xác định có cơ sở |
| --- | --- | --- |
| **α** | Mức chấp nhận kết luận sai "skill giúp" | (a) Chuẩn được công nhận: ICH E9, **một phía 0,025** (≡ hai phía 0,05). Đây là chuẩn quản lý, không phải định lý. (b) Hoặc suy ra từ tỉ lệ chi phí của hai loại sai: α tối ưu là α làm nhỏ nhất tổng sai có trọng số (Mudge et al. 2012, *PLoS ONE*). Cần @thuthuy cho tỉ lệ đó |
| **θ** (thí nghiệm chính) | Mức có ích tối thiểu để admit một skill | Suy ra từ **chi phí–lợi ích đo được**: admit khi lợi ích kỳ vọng > chi phí. θ = (chi phí token tăng thêm của skill mỗi lần chạy) / (giá trị một task được giải). Giá trị một task được giải có thể quy ra **chi phí cơ hội**: chi phí trung bình để có thêm một lần giải bằng cách chạy lại agent, tức chi phí/lần chạy ÷ tỉ lệ giải. Cả hai vế **đo được** từ pilot (`results/pilot/*.json`) |

Mọi con số khác bên dưới đều được **suy ra từ α**, **suy ra từ ràng buộc**, **không ảnh hưởng kết quả** (có chứng minh), hoặc **bị loại**.

## 1. Phán quyết G1 (bản sửa của Bổ sung 3, áp dụng trước khi mở dữ liệu xác nhận)

| Con số cũ | Trạng thái | Thay bằng | Cơ sở |
| --- | --- | --- | --- |
| α một phía 0,025 | Đầu vào giá trị | Giữ | Chuẩn ICH E9 (mục 0) |
| Monte Carlo 200.000 lần, "liệt kê hết khi n ≤ 16" | ❌ Loại | **Kiểm định đổi dấu chính xác bằng tích chập.** Trung bình của m seed có giá trị dạng k/m, nên phân phối khi H₀ đúng tính được chính xác | Fisher 1935; Pitman 1937. Không còn sai số Monte Carlo, không còn con số nào |
| Bootstrap 10.000 lần, CI 95% | ❌ Loại | **Khoảng t**, mức = 1 − 2α = 95%, suy ra từ α | Định lý giới hạn trung tâm; khoảng tin cậy tương ứng với kiểm định |
| Power 80%, độ phủ Browne 90%, MDE | ❌ Loại khỏi phán quyết | **Hiệu ứng tới hạn** = t₁₋α′ · SE: hiệu ứng nhỏ nhất mà kiểm định có thể tuyên bố. Chỉ cần α | Định nghĩa của vùng bác bỏ. Không cần quy ước power |
| TOST với biên = MDE | ❌ Loại (biên là con số tự chọn) | **A/A bằng kiểm định đổi dấu chính xác hai phía** ở mức 2α = 0,05, trên hai nhánh không skill **mới** (seed 11 so với seed 21). Bác bỏ → "chưa kết luận: pipeline đáng ngờ" | A/A test (Kohavi et al. 2020): A/A không được bác bỏ ở mức α. Thêm khoảng t để báo độ lệch |
| Chọn skill "Z < 0" | ✅ Suy ra | Giữ | Với prior phẳng và likelihood đối xứng, P(hiệu ứng < 0 \| dữ liệu) > ½ ⇔ trung bình < 0. Chỉ xác nhận skill mà khả năng giúp lớn hơn khả năng không giúp. Tính hợp lệ không phụ thuộc quy tắc chọn, vì dữ liệu xác nhận độc lập với C (Cox 1975) |
| Số seed m = 3 | ✅ Suy ra | Giữ | Từ ràng buộc ngân sách: m = ⌊(trần − đã chi) / chi phí đo được của một seed⌋ |
| Trần 33,5 USD | ✅ Suy ra | Giữ | 35 USD (@thuthuy) − chi phí tối đa của các lô bị ngắt chưa ghi (4 × 3 × 0,10 + 1 × 2 × 0,20 = 1,6) → **33,4**. Sửa lại: dùng 33,4 |
| Seed 11, 21, 31 | ✅ Suy ra (không ảnh hưởng) | Giữ | Các lần lặp phải độc lập, nên seed phải khác mọi seed đã dùng và khác seed + 1 của đối chứng nhiễu. Giá trị cụ thể không ảnh hưởng tính hợp lệ (seed chỉ là chỉ số của lần lấy mẫu) |
| Endpoint resolved | ✅ Chuẩn | Giữ | SWE-bench (Jimenez et al. 2024) |
| w = 0,5 trong loss | ❌ Loại khỏi phán quyết | Chỉ báo loss như **đường cong theo w** (phân tích đa vũ trụ) | Steegen et al. 2016 (*multiverse analysis*); Simonsohn et al. 2020 (*specification curve*) |

## 2. Những gì đã xảy ra ở B1–B3 (không sửa được quá khứ, phải công khai)

| Con số | Vấn đề | Xử lý |
| --- | --- | --- |
| CI 90% để kiểm A/A ở B3 | Tự chọn; ở CI 80% thì B3 đã STOP (`review_thresholds.md` §5) | Kết luận "thước đo sạch" của B3 là **mong manh**. Được thay bằng A/A chính xác trên dữ liệu xác nhận mới (mục 1). Báo cáo nêu rõ |
| Ngưỡng −0,10 cho đối chứng dương ở B3 | Tự chọn | Kết luận vững trong khoảng 0–0,125 và ở mọi CI ≤ 95%; trên resolved, p = 0,0105. Báo cáo kèm đường cong độ nhạy |
| step_limit 30 → 60 → 100 | Chọn dần theo dữ liệu, không có quy tắc | Thí nghiệm chính: dùng **mặc định của harness, 250 bước** (chuẩn của tác giả công cụ). Chi phí tăng ít, vì chi phí theo số bước thực dùng và chỉ 1/39 lần chạy chạm trần 100. Pilot giữ 100 để nhất quán với C |
| Đối chứng dương v1 và các ngưỡng "mơ hồ −0,05", "2 skill", "2 seed", "0,15" | Tự chọn | Đã bỏ, không dùng trong phán quyết |

## 3. Thí nghiệm chính (sửa trước khi chạy)

| Con số | Trạng thái | Thay bằng | Quy tắc chọn |
| --- | --- | --- | --- |
| θ ∈ {0,02; 0,05} | Đầu vào giá trị | θ từ chi phí–lợi ích đo được (mục 0) | Phân tích quyết định |
| c = 0,5 (trần cược) | Tham số phải chọn: tính hợp lệ đúng với mọi c < 1, chỉ power thay đổi | Chọn c bằng **tối ưu tốc độ tăng trưởng** (GRO): c làm lớn nhất E[log Eₙ] khi H₁ đúng, tính bằng mô phỏng với phân phối Z **đo ở pilot** | Kelly 1956; Grünwald, de Heide & Koolen 2024 (*safe testing*, GRO). Mô phỏng không đụng dữ liệu thí nghiệm, nên được phép thử nhiều lần |
| Prior (0; 0,25; 1) | ⚠️ Nghi sai thang | Dùng mặc định của Waudby-Smith & Ramdas cho biến trong [0, 1] (trung bình ½, phương sai ¼) **đổi sang thang [−1, 1]** (trung bình 0, phương sai 1). Cần đối chiếu với bài gốc | Waudby-Smith & Ramdas 2024 |
| Chia α 70 / 20 / 10 | ❌ Tự chọn | **Trọng số bằng nhau cho mỗi giả thuyết**: α_i = α / K, với K = số giả thuyết dự kiến (từ kế hoạch thí nghiệm); phần chưa biết số lượng dùng dãy 6/(π²k²) | Bonferroni đều khi không có thông tin ưu tiên. Trọng số khác chỉ hợp lệ nếu suy từ power dự kiến (Spjøtvoll 1972; Rubin, Dudoit & van der Laan 2006) |
| Dãy 6/(π²k²) | ✅ Suy ra | Giữ | Tổng chuỗi Basel = π²/6 nên Σ ≤ phần được chia (định lý) |
| Kịch bản mô phỏng (p₊ = 0,10, STR, số ô, MAX_BUDGET) → "219 trial" | ❌ Tự chọn | Chạy lại mô phỏng với **phân phối đo ở pilot** (σ nhiễu 0,19; σ tương tác 0,25; tỉ lệ giải) | Mô phỏng dựa trên dữ liệu (plasmode, Franklin et al. 2014) |
| Số task mỗi ô | ❌ Tự chọn | **n = ngân sách / chi phí mỗi cặp**, rồi công bố hiệu ứng tới hạn tương ứng | Ràng buộc nguồn lực (Lakens 2022, *Sample size justification*) |
| ξ ∈ {0; 0,01; 0,025; 0,05} | Lưới hiển thị | Thay bằng **đường cong liên tục** theo ξ | Không có quyết định nào phụ thuộc |
| Margin "> 5 điểm" của paper | Số của paper | Giữ chỉ để kiểm tra tuyên bố của paper; kiểm định chính là ưu thế (> 0) | Kiểm tra đúng tuyên bố |
| Cluster bootstrap 2.000 lần | Sai số Monte Carlo | Chọn số lần lặp sao cho sai số Monte Carlo của cận CI < 1/10 độ rộng làm tròn khi báo cáo (Davison & Hinkley 1997, §2.5), hoặc dùng khoảng theo cụm giải tích | Lý thuyết sai số Monte Carlo |
| BH q = 0,05 | Đầu vào giá trị | = α | Cùng α |

## 4. Thuộc thiết kế can thiệp (định nghĩa skill là gì), không phải tham số thống kê

| Con số | Vì sao không cần suy ra | Điều kiện |
| --- | --- | --- |
| MIN_REPOS = 3; các mẫu regex I(x) | Chúng **định nghĩa** skill được kiểm. Đổi chúng là kiểm một skill khác. Tính hợp lệ của kiểm định không phụ thuộc | Phải chốt trên dữ liệu train trước khi đo (đã làm) và công bố. Không được chỉnh theo kết quả test |
| Nội dung guidance của từng skill | Như trên | Như trên |

## 5. Vận hành (chứng minh được là không ảnh hưởng số liệu)

| Con số | Bằng chứng không ảnh hưởng |
| --- | --- |
| cost_limit 0,20 USD | Không bao giờ chạm (chi phí lớn nhất mỗi lần chạy 0,129 USD); nếu chạm sẽ được ghi là kết quả bị cắt |
| Lô 4 task, 6 GB/task, dự phòng 4 GB, chờ 30 phút, 6 lần thử, 110 phút | Chỉ quyết định *khi nào* một lần chạy diễn ra, không quyết định *kết quả*. Lần chạy lỗi hạ tầng bị loại và chạy lại (A2, A3, A18) |
| Model Flash-Lite, `reasoning_effort` low | Không ảnh hưởng tính hợp lệ của phép so sánh (hai nhánh dùng cùng model). Có ảnh hưởng đến **phạm vi** kết luận → nêu trong giới hạn |
