# Thuật ngữ của dự án Gatekeeper và pilot G1

Mỗi mục có ba phần: **định nghĩa** (chính xác), **vì sao cần**, và **cơ sở**. Thứ tự đi từ đối tượng, sang phép đo, sang phán quyết.

## 1. Đối tượng được nghiên cứu

| Khái niệm | Định nghĩa | Vì sao cần |
| --- | --- | --- |
| **Task** | Một bug thật trong SWE-bench: repo tại một commit, mô tả issue, và bộ test | Đơn vị độc lập để đo. Mỗi task là một "bệnh nhân" |
| **Agent** | Chương trình dùng LLM để đọc repo, chạy lệnh và nộp bản sửa (mini-swe-agent + Gemini Flash-Lite) | Đối tượng mà skill tác động vào |
| **Skill** | Một đoạn hướng dẫn tái sử dụng được, rút ra từ các bản sửa ở repo *khác*, được chèn vào đề bài cho agent (ví dụ `validation-error`: "kiểm tra đầu vào sai và báo lỗi rõ ràng…") | Đây là thứ Gatekeeper quyết định cho dùng hay chặn. Paper gọi là π |
| **Điều kiện kích hoạt I(x)** | Biểu thức regex trên nội dung issue, cho biết skill có áp dụng cho task x không | Skill chỉ có ý nghĩa ở nơi nó được dùng. Đo trên mọi task sẽ pha loãng hiệu ứng (`corrections.md` §1.2). Chọn trên dữ liệu train để test không bị rò rỉ |
| **P_s** | Tập task mà I(x) đúng | Phân phối mà hiệu ứng của skill được định nghĩa trên đó |
| **Nhánh (arm)** | Một cấu hình chạy: `none` (không skill), skill s, đối chứng nhiễu, đối chứng dương | So sánh luôn giữa các nhánh trên cùng task |
| **Seed** | Số khởi tạo cho việc lấy mẫu ngẫu nhiên của LLM | LLM có tính ngẫu nhiên. Seed khác nhau cho ra các lần chạy khác nhau, dùng để đo nhiễu và lặp lại |

## 2. Phép đo

| Khái niệm | Định nghĩa | Vì sao cần | Cơ sở |
| --- | --- | --- | --- |
| **F** | Tỉ lệ test FAIL_TO_PASS (test chứng minh bug đã được sửa) **vẫn còn fail** | Đo xem bug đã được sửa chưa | SWE-bench (Jimenez et al. 2024) |
| **R** | Tỉ lệ test PASS_TO_PASS (test vốn đang chạy đúng) **bị làm hỏng** | Đo tác dụng phụ: sửa một chỗ, hỏng chỗ khác | Như trên |
| **Resolved** | F = 0 **và** R = 0: sửa được bug mà không làm hỏng gì | Endpoint chuẩn, được công nhận rộng nhất. Chỉ số chính từ Bổ sung 3 | Như trên |
| **Loss ℓ** | (F + 0,5·R) / 1,5 ∈ [0, 1]. Không giải được: 0,667; giải được: 0 | Thang liên tục, phân biệt "sửa được nhưng làm hỏng 1 test" với "không sửa được". Bị chặn trong [0, 1] để e-process hợp lệ | Paper, đã chuẩn hoá (`corrections.md` §1.1); trọng số 0,5 là của paper |
| **Cặp (pair) / trial** | Một task được chạy ở cả hai nhánh, có skill và không skill | Ghép cặp triệt tiêu độ khó riêng của task | Neyman–Rubin |
| **Z** | ℓ(có skill) − ℓ(không skill) trên cùng task. **Z < 0: skill giúp; Z > 0: skill hại** | Đại lượng cơ bản của mọi phân tích | Như trên |
| **Z_resolved** | 1[không resolved, có skill] − 1[không resolved, không skill] ∈ {−1, 0, 1} | Z theo endpoint chuẩn: −1 là skill cứu được task, +1 là skill làm hỏng task | |
| **STR** (selective transfer risk) | E_{x∼P_s}[Z], tức Z kỳ vọng trên các task skill áp dụng | **Hiệu ứng thật** của skill: con số Gatekeeper muốn biết nhưng không quan sát trực tiếp được, chỉ ước lượng được | Hiệu ứng nhân quả trung bình (ATE) |

## 3. Skill "có hiệu ứng", "trung tính", "gây hại"

Theo định nghĩa của paper (đã sửa, `corrections.md` §1.4), với **θ** là mức có ích nhỏ nhất đáng quan tâm:

| Nhãn | Điều kiện | Ý nghĩa thực tế |
| --- | --- | --- |
| **Có ích (beneficial)** | STR ≤ −θ | Trung bình làm agent tốt hơn ít nhất θ. Ví dụ θ = 0,05 ≈ giải thêm khoảng 7–8% task |
| **Trung tính (neutral)** | −θ < STR ≤ 0 | Không hại, nhưng cũng không giúp đủ để đáng dùng |
| **Gây hại (harmful)** | STR > 0 | Trung bình làm agent **tệ hơn**: hỏng task mà không skill thì giải được, hoặc làm hỏng test cũ (R tăng) |

**Vì sao có ba nhãn:**
- Gatekeeper phải **chặn skill gây hại** (an toàn) và **cho dùng skill có ích** (lợi ích).
- Skill trung tính là vùng xám. Cho dùng nó không có lợi, mà vẫn tốn context và chi phí.
- Phân biệt "hại" với "không giúp" là cốt lõi của paper. Một skill rút ra từ repo khác có thể **chuyển giao âm** (negative transfer): đúng ở repo gốc nhưng sai ở repo mới.

**"Có hiệu ứng" trong pilot G1.** Đây khác với nhãn "có ích" của paper: pilot hỏi *có phát hiện được* hay không.
- Quy tắc chuẩn (Bổ sung 3): skill "có hiệu ứng" nếu bác bỏ được H₀ "skill không giúp" (E[Z_resolved] ≥ 0) bằng kiểm định hoán vị, Holm, α = 0,025, trên dữ liệu xác nhận.
- Kèm theo là MDE: hiệu ứng nhỏ hơn MDE thì pilot không đủ sức phát hiện.

**"Gây hại" trong pilot.** Pilot không kiểm định chính thức điều này. Bảng C chỉ **mô tả** số task bị hại (Z_res = +1). Ví dụ type-guard có 3 task bị hại và 0 task được giúp. Kiểm định có hại hay không là việc của thí nghiệm chính, với e-process.

**Vì sao gọi là hiệu ứng "chọn lọc" (selective):** STR được đo trên P_s, chỉ các task mà skill được kích hoạt, chứ không phải trên mọi task. Đo trên mọi task thì hiệu ứng bị pha loãng; ví dụ skill liên quan 10% task thì hiệu ứng bị chia khoảng 10 lần.

## 4. Đối chứng và B3 (quy tắc v2)

| Khái niệm | Định nghĩa trong pilot | Vì sao cần | Cơ sở |
| --- | --- | --- | --- |
| **Đối chứng nhiễu / A/A** | Nhánh `control-none-seed1`: **giống hệt** nhánh `none`, chỉ khác seed (seed gốc + 1). Hiệu ứng thật **bằng 0 theo thiết kế** | Nếu A/A khác 0 thì lỗi nằm ở thước đo (ghép cặp, seed, hạ tầng), không ở skill. Nó cũng đo độ lớn của nhiễu | A/A test (Kohavi, Tang & Xu 2020) |
| **Đối chứng dương** | Can thiệp **chắc chắn có tác dụng**: lộ đáp án. v1: tên file cần sửa. **v2 (B3): file + hàm cần sửa + tên test cần qua + test patch** | Nếu ngay cả lộ đáp án mà không thấy hiệu ứng, thước đo quá kém nhạy, và mọi kết luận "skill không giúp" đều vô nghĩa | Thiết kế thí nghiệm |
| **Quy tắc v2, kiểm nhiễu** | Z_nhiễu = ℓ(seed 2) − ℓ(seed 1), nhánh không skill, trên **mọi** 38 task. Đạt nếu CI 90% chứa 0 | Kiểm thước đo sạch | (Sau này thay bằng TOST, xem bên dưới) |
| **Quy tắc v2, kiểm độ nhạy** | Z_dương = ℓ(đối chứng dương) − ℓ(nhánh nhiễu) trên **mọi** task. Đạt nếu trung bình ≤ −0,10 **và** cận trên CI 90% < 0 | Kiểm thước đo đủ nhạy với hiệu ứng lớn | |
| **Vì sao v2 so dương với nhiễu, không so với `none`** | Hai nhánh này **chạy độc lập**, không nhánh nào được dùng để chọn task | v1 chọn task theo kết quả xấu của `none` rồi so với `none` → **hồi quy về trung bình** làm mọi nhánh trông có ích. Ở B2, chính đối chứng nhiễu đạt −0,17 trên các task đó | Galton; Cox 1975 |
| **Kết quả B3** | Nhiễu +0,062, CI [−0,001; +0,135] (chứa 0, sát mép); dương −0,125, CI [−0,22; −0,03] | Thước đo sạch và đủ nhạy với hiệu ứng ≥ khoảng 0,1 | |

Giới hạn của v2: ngưỡng −0,10 và CI 90% là **lựa chọn chưa có chuẩn ngoài** (`review_thresholds.md`). Chúng được dùng cho B3 vì đã đăng ký trước khi chạy B3. Quy tắc cuối cùng của G1 (Bổ sung 3) thay chúng bằng các phương pháp chuẩn.

## 5. Thống kê dùng để phán quyết

| Khái niệm | Định nghĩa | Vì sao cần | Cơ sở |
| --- | --- | --- | --- |
| **H₀ (giả thuyết không)** | "Skill không giúp": E[Z] ≥ 0 | Mặc định là hoài nghi; chỉ kết luận "giúp" khi dữ liệu đủ mạnh | Neyman–Pearson 1933 |
| **α** | Xác suất tối đa kết luận "giúp" khi thực ra không giúp (sai lầm loại I) | Kiểm soát kết luận sai. 0,025 một phía ≡ 0,05 hai phía | Quy ước; ICH E9 |
| **Power** | Xác suất phát hiện được khi skill thật sự giúp | Thí nghiệm power thấp thì "không thấy" không nói lên gì | Cohen 1988 |
| **CI (khoảng tin cậy)** | Khoảng chứa giá trị thật với tần suất (ví dụ 95%) nếu lặp lại thí nghiệm nhiều lần | Cho thấy độ bất định, không chỉ một con số | Neyman 1937 |
| **Bootstrap** | Lấy mẫu lại các task có hoàn lại để ước lượng CI | Không cần công thức phân phối | Efron 1979 |
| **Kiểm định hoán vị đổi dấu** | Nếu H₀ đúng (skill không có tác dụng với task nào) thì đổi dấu Z của mỗi task không làm đổi phân phối. Đổi dấu ngẫu nhiên nhiều lần cho ra phân phối khi H₀ đúng | Chính xác với mẫu nhỏ và dữ liệu rời rạc; không cần giả định phân phối chuẩn | Fisher 1935; Pitman 1937 |
| **FWER và Holm** | FWER = xác suất ít nhất một skill "đạt" sai. Holm: xếp p-value tăng dần, so lần lượt với α/k, α/(k − 1), … | Thử nhiều skill thì xác suất "đạt do may" tăng; phải kiểm soát cho cả nhóm | Holm 1979 |
| **Tách dữ liệu** | Chọn skill trên C, kết luận chỉ trên dữ liệu xác nhận (seed mới) | Tránh "lời nguyền người thắng": chọn cái tốt nhất rồi kiểm trên cùng dữ liệu thì kết quả bị thổi phồng | Cox 1975 |
| **TOST** | Hai kiểm định một phía để khẳng định \|hiệu ứng\| < biên | "Không bác bỏ khác 0" không chứng minh "bằng 0". TOST chứng minh "gần như bằng 0" | Schuirmann 1987; Lakens 2018 |
| **MDE** | Hiệu ứng nhỏ nhất mà thí nghiệm có power 80% để phát hiện | Diễn giải đúng kết quả "không thấy": nó chỉ có nghĩa là không có hiệu ứng ≥ MDE | Lakens 2018; Browne 1995 |
| **Phương sai theo cụm** | Nhiều seed trên cùng task không độc lập; đơn vị là task | Không thổi phồng cỡ mẫu (128 lần chạy ≠ 128 quan sát độc lập) | Miller 2024 |
| **Hồi quy về trung bình** | Giá trị cực trị ở lần đo đầu thường gần trung bình hơn ở lần sau | Lý do quy tắc v1 sai | Galton |
| **Đăng ký trước** | Ghi quy tắc phân tích trước khi thấy dữ liệu | Chống "khu vườn lối rẽ" | ICH E9; Nosek et al. 2018 |

## 6. Các cổng và quyết định

| Khái niệm | Định nghĩa | Vì sao cần |
| --- | --- | --- |
| **G1** | Cổng pilot: có skill nào có hiệu ứng **phát hiện được** không, và thước đo có tốt không | Không tiêu hàng nghìn USD cho thí nghiệm chính nếu không có gì để đo |
| **θ** (thí nghiệm chính) | Mức có ích tối thiểu để admit: Gatekeeper admit skill khi chứng minh được STR ≤ −θ | Quyết định quan trọng nhất còn mở. θ nhỏ thì cần nhiều trial; θ lớn thì ít skill đạt |
| **E-process** (thí nghiệm chính) | Thống kê cá cược, tăng khi dữ liệu cho thấy skill giúp; admit khi vượt 1/α | Cho phép quyết định **trong lúc** đang chạy mà vẫn giữ được α (Ville 1939) |
| **Sổ α (alpha ledger)** | Chia tổng α cho các ô (skill, scope), các skill kết hợp, và các lần xét lại | Gatekeeper ra rất nhiều quyết định; tổng sai lầm vẫn phải ≤ α |
