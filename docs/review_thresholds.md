# Rà soát mọi chuẩn, ngưỡng và con số (02/11/2026)

Rà soát từ đầu dự án đến giờ: lý thuyết, kế hoạch, dữ liệu, pilot. Kết quả giai đoạn C **chưa được mở** khi viết tài liệu này.

## Cách phân loại

| Nhãn | Nghĩa | Có chấp nhận được không |
| --- | --- | --- |
| **S** | Chuẩn hoặc phương pháp đã công bố, được công nhận rộng rãi | ✅ |
| **M** | Suy ra bằng toán học (định nghĩa, chứng minh) | ✅ nếu chứng minh đúng (cần người rà, 👤) |
| **V** | Lựa chọn **không ảnh hưởng tính đúng đắn**: định lý đúng với *mọi* giá trị, chỉ ảnh hưởng power hoặc chi phí | ✅ nếu nêu rõ là vậy |
| **D** | Ước lượng từ dữ liệu bằng phương pháp chuẩn | ✅ nếu có biên bất định; đổi dữ liệu thì công thức giữ nguyên, ước lượng lại |
| **O** | Tham số vận hành (máy, đĩa, mạng), không vào số liệu | ✅ |
| **P** | Lấy từ paper gốc FSE-2027-13 | ⚠️ chỉ thuyết phục bằng paper |
| **J** | Phán đoán hoặc cảm tính, chưa có cơ sở được công nhận | ❌ phải sửa, hoặc chuyển thành V/S, hoặc nêu công khai là lựa chọn giá trị |

## 1. Lý thuyết và thiết kế thí nghiệm chính

| Con số / chuẩn | Ở đâu | Nhãn | Cơ sở | Đánh giá, việc cần làm |
| --- | --- | --- | --- | --- |
| F, R = tỉ lệ test FAIL_TO_PASS còn fail / PASS_TO_PASS bị hỏng | `loss.py` | **S** | Định nghĩa của SWE-bench (Jimenez et al., ICLR 2024) | ✅ |
| Chuẩn hoá ℓ = (F + wR)/(1 + w) ∈ [0,1] | `corrections.md` §1.1 | **M** | Bắt buộc: e-process cần Z bị chặn trong [−1, 1]. Loss của paper có thể vượt 1 | ✅ |
| **w = 0,5** | loss | **P** | Giữ tinh thần paper (0,5 điểm cho mỗi regression) | ⚠️ Không có chuẩn ngoài. **Đề xuất:** dùng chỉ số **resolved** của SWE-bench (F = 0 và R = 0), là chuẩn được công nhận, làm endpoint chính; loss có w chỉ là phụ, kèm sweep |
| Dải sweep w ∈ [0,2; 2,0] | prereg §3 | **J** | Chọn cho rộng | Chỉ là phân tích độ nhạy, giữ được nếu nêu rõ |
| Betting e-process, bất đẳng thức Ville | `eprocess.py` | **S** | Ville (1939); Waudby-Smith & Ramdas, *JRSSB* 2024 (ước lượng trung bình biến bị chặn bằng cá cược) | ✅ |
| aGRAPA plug-in | `eprocess.py` | **S** | Cùng tài liệu trên | ✅ |
| c = 0,5 (trần cược) | `eprocess.py` | **V** | Đúng với mọi c < 1; c chỉ ảnh hưởng power. Sai loại I đo được 3,0% ≤ 5% | ✅ ghi rõ là V |
| Prior (0; 0,25; 1) | `eprocess.py` | **V** | Như trên | ✅ ghi rõ là V |
| α họ = 0,05 | prereg §4 | **S** (quy ước) | Quy ước khoa học; ICH E9 cho thử nghiệm lâm sàng | ✅ |
| FWER, Bonferroni qua sổ α | `alpha_ledger.py` | **S** + **M** | Bonferroni/union bound; Theorem 4′ | ✅ |
| Chia α 70% / 20% / 10% (ô / composite / tái xét) | `alpha_ledger.py` | **V** | FWER đúng với mọi cách chia có tổng ≤ α | ⚠️ Hiện là J về power. **Đề xuất:** chia theo số giả thuyết dự kiến của mỗi loại (lấy từ kế hoạch thí nghiệm), hoặc ghi rõ là V |
| Dãy 6/(π²k²) | `alpha_ledger.py` | **M** | Tổng Basel = 1, nên tổng α không vượt mức đã chia dù có bao nhiêu yêu cầu | ✅ (dãy khác cũng đúng; đây là V) |
| **θ ∈ {0,02; 0,05}** | prereg §4 | **J** | Chưa chốt | ❌ Cùng bản chất với δ (mục 3): là "hiệu ứng nhỏ nhất đáng quan tâm" (SESOI), phải lý giải theo Lakens et al. 2018. Quyết định lớn nhất còn mở của paper |
| Lưới ξ {0; 0,01; 0,025; 0,05} | `corrections.md` §3 | **J** (báo cáo) | Lưới để báo cáo độ nhạy | Giữ được: không quyết định gì |
| "Margin có ý nghĩa nếu cận dưới CI > 5 điểm" | `corrections.md` §1.4 | **P** | Là tuyên bố của paper; ta kiểm tra đúng tuyên bố đó | ✅ (R14: power ~5% → đổi sang kiểm định ưu thế) |
| Power 80% | `design_table.py`, prereg | **S** (quy ước) | Cohen (1988) | ✅ |
| Kịch bản mô phỏng: p₊ = 0,10, budget 2.000, STR ∈ {−0,25; −0,15; −0,10}, số ô {10…1600}, MAX_BUDGET 3.000 | `simulate.py`, `design_table.py` | **J** (kịch bản) | Chọn để minh hoạ | ⚠️ **Con số "219 trial" (R2) phụ thuộc kịch bản này.** Phải ghi là "trong kịch bản …". Kết luận định tính (không scope nào đủ task cho trial không lặp) vẫn đứng: scope lớn nhất có 157 task |
| Cluster bootstrap theo repo, 2.000 lần lặp | prereg §6 | **S** | Bootstrap theo cụm (Field & Welsh 2007; Cameron, Gelbach & Miller 2008); ≥ 1.000 lần lặp cho CI (Efron & Tibshirani 1993) | ✅ |
| Benjamini–Hochberg q = 0,05 | prereg §6 | **S** | Benjamini & Hochberg 1995 | ✅ |
| Số liệu power endpoint (11,5% → 5,1%; 63 cặp) | prereg §6 | **P** | Số của paper | ✅ dùng để kiểm tra paper |
| Ước tính khối lượng pilot (10 skill × 2 scope, 30 cặp/ô, 270 cặp…) | prereg §8 | **J** | Ước lượng thô ban đầu | ⚠️ Đã lỗi thời, thay bằng số đo thật ở pilot |

## 2. Dữ liệu

| Con số / chuẩn | Nhãn | Cơ sở | Đánh giá |
| --- | --- | --- | --- |
| Benchmark: SWE-bench, Verified, SWE-Gym, SWE-bench-Live, SWE-smith, BugsInPy | **S** | Đã công bố và dùng rộng rãi (R13) | ✅ |
| Tách train/test theo repo | **S** (thực hành) | Tránh rò rỉ giữa train và test; đánh giá tổng quát hoá giữa các repo | ✅ |
| Kiểm định pool: gold resolve 2 lần, no-op cho F = 1 và R = 0 | **S** (thực hành) | Đúng cách harness SWE-bench xác định task hợp lệ; lặp 2 lần để loại test chập chờn | ✅ |
| N = 40, 6 task/repo, 30 task/skill, seed 2027 | **J** (cỡ mẫu theo ngân sách) | Chọn theo ngân sách ban đầu | ⚠️ Cỡ mẫu phải tính bằng công thức power (mục 3), không chọn tay. Seed chỉ để tái lập: ✅ |
| MIN_REPOS = 3 ("họ mẫu sửa lặp lại") | **J** | Định nghĩa vận hành | ⚠️ Nêu rõ là định nghĩa; kết quả khai thác phụ thuộc vào nó |
| Regex I(x): mẫu viết tay, chọn trên train theo lift | **D** + **J** | Chọn trên train, test không đụng (thực hành tốt); mẫu ứng viên do người viết | ⚠️ Lift chỉ 1,5–1,8 (R16). Đây là giới hạn đã báo cáo |
| Retries 2, chờ 90 giây (kiểm định pool) | **O** | Hạ tầng | ✅ |

## 3. Pilot (G1)

| Con số / chuẩn | Nhãn | Cơ sở | Đánh giá, việc cần làm |
| --- | --- | --- | --- |
| Model Flash-Lite, quy tắc "tỉ lệ giải 20–70%" | **J** | Ý đúng: phương sai p(1 − p) lớn nhất ở 50%, tránh trần và sàn. Hai mép 20/70 là tự đặt | ⚠️ Ghi lý do định tính; lựa chọn thực tế do chi phí (rẻ hơn 11×) |
| `reasoning_effort: low` | **O/J** | Chọn vì chi phí (thinking tốn ~11× token) | ⚠️ Ảnh hưởng năng lực model: phải ghi trong giới hạn |
| **step_limit 30 → 60 → 100** | **O** → ảnh hưởng số liệu | Mốc ngoài: cấu hình SWE-bench chính thức của mini-swe-agent là **250 bước, 3 USD**. Ta hạ xuống vì chi phí | ⚠️ 100 được chốt theo dữ liệu bão hoà (95% lần chạy ≤ 95 bước; chạm trần 1/39). Phải ghi rõ "lệch khỏi mặc định 250" |
| cost_limit 0,10 → 0,20 USD | **O** | Không bao giờ chạm (tối đa 0,129 USD) | ✅ không ảnh hưởng số liệu |
| Lô 4 task, 6 GB/task, dự phòng 4 GB, chờ 30 phút, 6 lần thử, 110 phút | **O** | Hạ tầng | ✅ |
| Đối chứng nhiễu (hai nhánh giống hệt) | **S** (khái niệm) | Đây là **A/A test** của thực nghiệm có đối chứng (Kohavi, Tang & Xu 2020, *Trustworthy Online Controlled Experiments*) | ✅ khái niệm. ❌ cách kiểm "CI 90% chứa 0" là J: sai báo động 10%, và "không bác bỏ" không chứng minh "không khác". **Chuẩn:** kiểm định tương đương TOST (Lakens et al. 2018) với biên đặt trước, hoặc kiểm phân phối p-value của nhiều A/A test |
| Đối chứng dương | **S** (khái niệm) | Thiết kế thí nghiệm có đối chứng dương | ✅ khái niệm |
| Đối chứng dương v1 chỉ xét task nhánh gốc thất bại | **J** (sai) | Hồi quy về trung bình | ❌ đã bỏ (D1) |
| min_unsolved = 5 | **J** | Tự đặt | ❌ đã bỏ ở v2 |
| **δ = 0,10** (hiệu ứng tối thiểu) | **J** | ≈ 15 điểm % tỉ lệ giải; gần đối chứng lộ đáp án (−0,125). Không có chuẩn ngoài | ❌ Theo Lakens et al. 2018: lý giải bằng lý thuyết, thực tiễn hoặc nguồn lực. **Đề xuất:** không dùng làm ngưỡng phán quyết; dùng để tính cỡ mẫu và công bố MDE "theo nguồn lực" |
| CI 90% cho sàng lọc | **J** | Tự đặt | ❌ Thay bằng α chuẩn (mục 4) |
| Mức nhóm 0,15 và CI 96,25% | **J** | Chỉ để khớp CI 90% | ❌ Bỏ |
| Mức "mơ hồ" −0,05, "tối đa 2 skill", "thêm 2 seed" | **J** | Cảm tính hoặc ước lượng bằng mắt | ❌ Bỏ |
| CI bootstrap (4.000 lần lặp) | **S** | Efron & Tibshirani | ✅, nhưng với n ≈ 30 nên dùng kiểm định hoán vị (chính xác) |
| Sign test ở rà soát B | **S** | Kiểm định dấu cổ điển | ✅ (chỉ dùng để chẩn đoán) |
| σ nhiễu = 0,19; σ tương tác = 0,25 | **D** | Tách thành phần phương sai từ B3 (38 task) | ⚠️ Ước lượng điểm từ mẫu nhỏ → dùng cận trên 90% (Browne 1995) |
| Chi phí/lần chạy (0,022–0,068 USD) | **D** | Token đo được × bảng giá LiteLLM | ⚠️ Bảng giá chưa đối chiếu hoá đơn Google (C5) |
| Trần 20 / 30 / 35 USD | — | Quyết định ngân sách của @thuthuy | ✅ không phải thống kê |
| Tách "1 USD dự phòng" | **D** | Chi phí tối đa của lô bị ngắt = 4 task × 3 nhánh × 0,10 USD | ✅ |

## 4. Tổng kết

- **Phần lõi đứng vững trên chuẩn được công nhận:** định nghĩa F/R của SWE-bench; e-process và Ville; Bonferroni/FWER; BH; cluster bootstrap; power 80%; benchmark và cách kiểm định pool. Các tham số chỉ ảnh hưởng power (c, prior, cách chia α, dãy chi tiêu) thuộc loại V: đúng với mọi giá trị.
- **Còn cảm tính hoặc chỉ dựa vào paper:**
  - w = 0,5, nên chuyển sang **resolved** làm endpoint chính.
  - **θ / δ (SESOI)**: quyết định lớn nhất, phải lý giải theo Lakens et al.
  - Kịch bản mô phỏng: phải ghi điều kiện khi trích con số 219.
  - Cỡ mẫu pool: nên tính bằng công thức power.
  - **Toàn bộ các ngưỡng của quy tắc G1** (CI 90%, 0,15, −0,05, "2 skill", "2 seed", "CI chứa 0"): thay hết.
- **Bộ thay thế đề xuất cho G1, toàn chuẩn đã công bố:**
  - Endpoint **resolved** (SWE-bench).
  - A/A test bằng **TOST** (Lakens 2018) cho đối chứng nhiễu.
  - **Kiểm định hoán vị đổi dấu** ghép cặp (Fisher 1935; Pitman 1937), một phía, α nhóm 0,025, **Holm** (1979).
  - **Tách dữ liệu chọn / xác nhận** (Cox 1975).
  - Cỡ mẫu bằng công thức chuẩn với **cận trên phương sai** (Browne 1995) và phương sai theo cụm (Miller 2024).
  - **δ chỉ để công bố MDE theo nguồn lực**, không làm ngưỡng phán quyết.
- **Không thể khử hết phán đoán:** SESOI (θ/δ), mức α, và các tham số vận hành (step_limit, model, `reasoning_effort`) là lựa chọn. Chuẩn khoa học (ICH E9; Lakens et al.) chỉ yêu cầu chúng được **lý giải, ghi trước, và kèm phân tích độ nhạy**, không yêu cầu chúng "đúng".

## Tài liệu

- Jimenez et al., *SWE-bench*, ICLR 2024.
- Ville 1939; Waudby-Smith & Ramdas, *Estimating means of bounded random variables by betting*, JRSSB 2024.
- Holm 1979, *Scand. J. Statist.*; Benjamini & Hochberg 1995, *JRSSB*.
- Fisher 1935; Pitman 1937 (kiểm định hoán vị); Cox 1975, *Biometrika* (tách dữ liệu).
- Efron & Tibshirani 1993; Field & Welsh 2007; Cameron, Gelbach & Miller 2008 (bootstrap theo cụm).
- Cohen 1988 (power).
- [Lakens, Scheel & Isager 2018, AMPPS](https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906) (SESOI, TOST).
- Browne 1995, *Stat. Med.* 14:1933 ([tóm tắt và nghiên cứu tiếp theo](https://uwe-repository.worktribe.com/OutputFile/11141516)).
- [Miller 2024, *Adding Error Bars to Evals*](https://arxiv.org/pdf/2411.00640).
- [ICH E9](https://www.ema.europa.eu/en/documents/scientific-guideline/ich-e-9-statistical-principles-clinical-trials-step-5_en.pdf).
- Kohavi, Tang & Xu 2020, *Trustworthy Online Controlled Experiments* (A/A test).
- Cấu hình SWE-bench mặc định của mini-swe-agent 2.4.6: `step_limit: 250`, `cost_limit: 3`.

Các tài liệu kinh điển không kèm link được trích theo hiểu biết, chưa mở bản gốc trong phiên này.
