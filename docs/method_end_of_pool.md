# Phép kiểm cuối pool: phát biểu, chứng minh và phạm vi (B1, B2 của `docs/todo_ease_revision.md`)

Lập 17/11/2026. Mã: `end_of_pool_log_e` trong `src/gatekeeper/eprocess.py`. Kiểm bằng số: `scripts/verify_methods.py` (mục `end_of_pool`). Áp dụng: `docs/preregistration_main.md` §42.

## 1. Vì sao cần

Bản review ngày 16/11 chỉ ra hai lỗ hổng của bản cũ:

- **Mệnh đề 1** chỉ xét các kết quả đã xảy ra, lấy trung bình trên thứ tự task.
- **Định lý 2** lại phát biểu về tác dụng kỳ vọng, và không có chứng minh nối hai thứ này.

Mọi thí nghiệm của bài đều chạy hết pool, nên một phép kiểm chỉ quyết định ở cuối pool là đủ, và có chứng minh trọn vẹn.

## 2. Ba đại lượng mục tiêu (B2)

Ký hiệu:
- Pool cố định gồm N task, chọn trước khi có kết quả.
- Với task i: Zᵢ = 1[thất bại khi có skill] − 1[thất bại khi không skill], nằm trong [−1, 1]. Zᵢ < 0 nghĩa là skill có lợi ở task đó.
- C là **trạng thái của lượt chạy**: toàn bộ diễn biến của mọi thứ dùng chung giữa các task trong lượt chạy (phiên bản model được phục vụ, cấu hình harness, trạng thái nhà cung cấp theo thời gian). Một phép so có hai nhánh chạy ở hai lượt khác nhau thì C gồm trạng thái của cả hai lượt.

| Đại lượng | Định nghĩa | Bài chứng nhận được không |
| --- | --- | --- |
| **T1. Trên pool, trong lượt chạy** | μ(C) = (1/N) Σᵢ E[Zᵢ \| C] | **Có**: phép kiểm ở mục 3 |
| T2. Trên pool, qua nhiều lượt chạy | E_C[μ(C)] | Không. Lượt lặp với seed 51 là bằng chứng mô tả về độ ổn định, không phải bảo đảm |
| T3. Khi triển khai | tác dụng trên task tương lai của repo | Không |

T1 lấy kỳ vọng trên **sự ngẫu nhiên của agent** (nhiễu lấy mẫu của model ở từng lần gọi), với pool và trạng thái lượt chạy cố định.

## 3. Phát biểu

**Giả định A (độc lập có điều kiện).** Với C cho trước, Z₁, …, Z_N độc lập. Hai nhánh trong cùng một task được phép phụ thuộc nhau, vì chúng đã được gộp thành một biến Zᵢ.

**Giả thuyết không:** H₀(C): Σᵢ E[Zᵢ | C] ≥ −Nθ, tức skill không giúp trung bình ít nhất θ trên pool trong lượt chạy đó.

**Thống kê:** E = Πᵢ (1 + λ(−θ − Zᵢ)), với λ cố định trước dữ liệu, 0 ≤ λ < 1/(1 + θ).

**Mệnh đề.** Dưới giả định A và H₀(C): E[E | C] ≤ 1. Do đó Pr[E ≥ 1/α | C] ≤ α.

**Chứng minh.**
1. Mỗi thừa số 1 + λ(−θ − Zᵢ) ≥ 1 − λ(1 + θ) > 0, vì Zᵢ ≤ 1 và λ < 1/(1 + θ).
2. Theo giả định A, kỳ vọng của tích bằng tích các kỳ vọng: E[E | C] = Πᵢ (1 + λ(−θ − μᵢ)), với μᵢ = E[Zᵢ | C].
3. Mỗi thừa số dương, và 1 + x ≤ eˣ với mọi x, nên E[E | C] ≤ exp(−λ Σᵢ (θ + μᵢ)).
4. Dưới H₀(C), Σᵢ (θ + μᵢ) ≥ 0, nên số mũ ≤ 0 và E[E | C] ≤ 1.
5. Bất đẳng thức Markov: Pr[E ≥ 1/α | C] ≤ α · E[E | C] ≤ α. ∎

**Điều chứng minh không cần:** từng task có μᵢ ≥ −θ. Một task được lợi nhiều làm thừa số của nó lớn hơn 1, các task bị hại làm thừa số nhỏ hơn 1; thứ bị chặn là tổng, và tổng chính là giả thuyết trên trung bình pool. `tests/test_eprocess.py::test_end_of_pool_expectation_is_exactly_bounded_on_a_heterogeneous_null` kiểm điều này bằng phép tính chính xác.

## 4. Tham số

| Tham số | Giá trị | Nhóm (R2) | Căn cứ |
| --- | --- | --- | --- |
| θ | 0 | chuẩn công bố của thiết kế | đã đăng ký cho mọi phép nhận (§25) |
| λ | 0,5 | suy ra từ thiết kế đã đăng ký | bằng mức cược tối đa c/(1 + θ) của Gatekeeper, với c = 0,5 đã đăng ký từ §25. Không tham số nào được chọn sau khi thấy dữ liệu |
| α | 0,025 cho mỗi quyết định; ngưỡng 1/α = 40 | đã đăng ký | §25 |
| Ngưỡng cả họ | 12/α = 480 | suy ra | chặn hợp trên 12 quyết định của §36a; không cần các quyết định độc lập nhau |

## 5. Những điều phép kiểm KHÔNG nói

- **Không anytime-valid.** Nó chỉ bảo đảm khi đọc ở cuối pool. Đọc giữa chừng rồi dừng sẽ làm mất bảo đảm.
- **Không nói về T2 hay T3.** Khi có một trạng thái chung cho cả lượt chạy, tỉ lệ nhận nhầm đối với T2 vượt mức danh nghĩa. Hai con số:
  - `verify_methods.py` (mục `end_of_pool`), trên 100 task Jinja với tỉ lệ giải nền đo được, hai trạng thái đồng xác suất có tác dụng ngược chiều, trung bình qua hai trạng thái đúng bằng 0: phép kiểm cuối pool nhận nhầm **4,2%**, kiểm định dấu **11,2%**, so với mức 2,5%.
  - Ví dụ đơn giản ngày 16/11 (mọi task có xác suất lợi/hại 0,30/0,10 hoặc 0,10/0,30 tùy trạng thái): **35,7%**.
  - Bảo đảm chỉ đúng khi điều kiện hóa trên C.
- **Trên các quyết định đã có, nó là phân tích sau dữ liệu.** Phép kiểm được nghĩ ra sau khi đã thấy kết quả, dù λ là hằng số đã đăng ký. Lần dùng xác nhận đầu tiên phải là một thí nghiệm mới, đăng ký trước.

## 6. Giả định A đứng đến đâu

- **Hai nhánh chạy song song** khử mọi biến động tác động như nhau lên cả hai nhánh của cùng một task. Điều đó không làm các Zᵢ độc lập với nhau, nhưng C đã chứa mọi trạng thái dùng chung, nên giả định chỉ còn là: các task không tác động trực tiếp lên nhau.
- **Vi phạm đã biết:** các task chạy song song tạo tải cho nhau qua giới hạn tốc độ gọi model. Số lượt sập vì lý do này được đếm cho từng quyết định ở §42.
- **Chẩn đoán (không phải xác nhận):** tương quan của Zᵢ theo thứ tự chạy, ở §42. Chẩn đoán chỉ bác bỏ được giả định, không chứng minh được nó.
- **Phép so có hai nhánh ở hai lượt chạy khác nhau:** chứng minh vẫn đúng với C gồm cả hai lượt. Nhưng đại lượng T1 khi đó trộn tác dụng của skill với khác biệt giữa hai lượt chạy. Bài phải tách các phép so này ra (D4).

## 7. Quan hệ với các phép thử khác của bài

| Phép thử | Giả thuyết không mà nó bảo đảm | Vai trò |
| --- | --- | --- |
| **Phép kiểm cuối pool** (mục 3) | H₀(C) trên trung bình pool | **Định nghĩa duy nhất của "được chứng nhận"** |
| E-process tuần tự (Gatekeeper, §25) | mỗi task có E[Zᵢ \| quá khứ] ≥ −θ theo thứ tự cố định trước; giả thuyết hẹp hơn | báo cáo thời điểm lẽ ra có thể dừng |
| Kiểm định dấu chính xác, Holm (§25) | ở mỗi cặp lệch, hai chiều có xác suất bằng nhau | giữ nguyên vai trò đã đăng ký |
| Cổng của PACE (arXiv 2606.08106) | như kiểm định dấu, dạng anytime-valid | công trình liên quan; cùng thống kê |

**Về PACE.** Với θ = 0 và Zᵢ ∈ {−1, 0, 1}, E = (1 + λ)^b (1 − λ)^c, trong đó b là số cặp skill thắng và c là số cặp skill thua. Đây đúng là thống kê của cổng PACE trên các cặp lệch (công thức (2) của PACE: E ← E·(1 + λ(2wᵢ − 1))). PACE chứng minh tính hợp lệ dưới giả thuyết "mỗi cặp lệch là một lần tung đồng xu cân bằng". Mệnh đề ở mục 3 cho thấy **cùng thống kê đó, đọc ở cuối pool, vẫn hợp lệ dưới giả thuyết yếu hơn: trung bình pool không dương, các task không đồng nhất.** Bài trích PACE là nơi đã công bố thống kê này; mệnh đề không phải đóng góp phương pháp.
