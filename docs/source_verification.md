# Đối chiếu với bản gốc (02/11/2026)

Bản gốc được tải bằng GitHub Actions (`.github/workflows/sources.yml`), vì container phát triển không truy cập được các host này. Trích đoạn được lưu ở nhánh `sources-snapshots` (`data/sources/<id>.json`), kèm URL và sha256 của tệp đã tải. Kết quả giai đoạn xác nhận **chưa mở** khi viết tài liệu này.

## 1. Đã đối chiếu, khớp với cách dùng

| Phương pháp / con số | Nguồn gốc (đã mở) | Câu trích nguyên văn | Kết luận |
| --- | --- | --- | --- |
| α một phía 0,025 | **ICH E9** (EMA, §5.5) | "The approach of setting type I errors for one-sided tests at half the conventional type I error used in two-sided tests is preferable in regulatory settings." | ✅ Khớp |
| Phải lý giải trước việc dùng kiểm định một phía | ICH E9 §5.5 | "It is important to clarify whether one- or two-sided tests of statistical significance will be used, and in particular to justify prospectively the use of one-sided tests." | ✅ Lý giải: quyết định admit chỉ có một chiều (chỉ admit khi skill giúp); gây hại được báo cáo riêng. Đã ghi trước |
| Endpoint resolved | **SWE-bench**, Jimenez et al., ICLR 2024; **mã nguồn harness `swebench` 5.0.2** (`harness/grading.py`, `get_resolution_status`) | "If fail-to-pass (Resolution) = 1 and pass-to-pass (Maintenance) = 1 -> FULL"; test F2P bị skip được tính là **fail** (ghi chú dòng 107) | ✅ Định nghĩa của ta (F = 0 và R = 0) **khớp 100%** với trường `resolved` của harness trên 567 report thật (369 resolved / 198 không; 0 chỗ lệch) |
| Kiểm định đổi dấu là chính xác | **Hemerik & Goeman 2018**, *Exact testing with random permutations* (Định nghĩa 1) | Kiểm định chính xác khi H₀ "implies that the joint distribution … is invariant under all transformations in G"; G có thể gồm các phép "multiply part of the data by −1" | ✅, kèm **sửa cách phát biểu H₀** (mục 2) |
| Holm kiểm soát FWER không cần giả định | Holm 1979, qua Wikipedia (bản gốc trên JSTOR, không truy cập được) | "Holm–Bonferroni can be applied without such assumptions" [về tính độc lập]; "uniformly more powerful than the Bonferroni correction" | ✅ (nguồn thứ cấp; chứng minh dựa trên bất đẳng thức Boole) |
| Tách dữ liệu chọn / xác nhận | **Rinaldo, Wasserman, G'Sell & Lei** (Annals of Statistics 2019; bản arXiv) | "The oldest method for inference after model selection is sample splitting … The earliest references … are Barnard (1974), Cox (1975)…" | ✅ (Cox 1975 qua nguồn thứ cấp) |
| A/A test | **Kohavi, Henne & Sommerfield**, *Practical guide to controlled experiments on the web* | "A/A Test. Sometimes called a Null Test … exercise the experimentation system … but expose them to exactly the same experience. An A/A test can be used to (i) collect data and assess its variability for power calculations, and (ii) …" | ✅ |
| Không suy ra được α nếu không có hàm thiệt hại | Lý thuyết quyết định (Wald), qua Wikipedia *Admissible decision rule* | "According to the complete class theorems, under mild conditions every admissible rule is a (generalized) Bayes rule"; quy tắc quyết định được định nghĩa theo một "loss function L : Θ × A → ℝ" | ✅ (nguồn thứ cấp) |
| α suy ra từ chi phí sai lầm | **Mudge et al. 2012**, *PLoS ONE* | "calculating the α associated with the minimum average of α and β at the critical effect size … incorporate … relative costs of Type I and Type II errors, if known" | ✅ |
| c = 0,5 (trần cược) | **Waudby-Smith & Ramdas**, JRSSB 2024, Định lý 2–3 | "for some c ∈ (0,1) (a reasonable default being 1/2 or 3/4)" | ✅ **c = 0,5 là mặc định của tác giả**, có cơ sở |
| Prior của bettor | Như trên, (15) | "σ̂²_t := (1/4 + Σ(X_i − μ̂_i)²)/(t + 1), μ̂_t := (1/2 + Σ X_i)/(t + 1)" cho X ∈ [0, 1] | ❌ **Code dùng 0,25 trên thang Z ∈ [−1, 1]; đúng ra phải là 1.** Đã sửa (mục 2) |
| GRO (chọn c bằng tăng trưởng log) | **Grünwald, de Heide & Koolen**, *Safe Testing* (JRSSB 2024); **Kelly 1956** | "We define growth-rate optimality (GRO) as an analogue of power"; Kelly: "G = lim (1/N) log(V_N/V_0)" | ✅ |
| Đánh giá LLM như thí nghiệm | **Miller 2024**, *Adding Error Bars to Evals* | "1. Computing standard errors of the mean using the Central Limit Theorem 2. … clustered standard errors 3. Reducing variance by resampling answers … 4. … question-level paired differences … 5. Using power analysis" | ✅ Khớp với thiết kế: ghép cặp theo task, cụm theo task, lặp seed |
| Ville | Wikipedia *Ville's inequality* | "provides an upper bound on the probability that a supermartingale exceeds a certain value" | ✅ (nguồn thứ cấp) |
| step_limit mặc định 250, cost_limit 3 USD | Cấu hình đi kèm `mini-swe-agent` 2.4.6 (`config/benchmarks/swebench.yaml`) | `step_limit: 250`, `cost_limit: 3.` | ✅ |

## 2. Đối chiếu bản gốc phát hiện ra, và đã sửa

1. **Phát biểu H₀ của kiểm định đổi dấu** (Hemerik & Goeman, Định nghĩa 1).
   - Trước: "H₀: E[Z] ≥ 0". Chưa chính xác: kiểm định đổi dấu không kiểm định một giả thuyết về trung bình.
   - **Sửa:** H₀ là "**skill không có tác dụng**: trên mỗi task, hai nhánh hoán đổi được, nên Z_i có phân phối đối xứng quanh 0 và độc lập giữa các task". Dưới H₀ này, phép đổi dấu giữ nguyên phân phối, nên kiểm định chính xác. Bác bỏ một phía nghĩa là có bằng chứng skill **làm lệch** kết quả theo hướng có ích.
2. **Prior của bettor sai thang đo** (Waudby-Smith & Ramdas, (15)): 0,25 là phương sai mặc định cho biến trong [0, 1]. Với Z ∈ [−1, 1] (Z = 2X − 1) thì phải là 1. Đã sửa `eprocess.py` và `simulate.py`. Tính hợp lệ không đổi (định lý đúng với mọi prior); mô phỏng chạy lại: trung vị 219 → 221 trial; sai loại I 3,0% → 2,88% ≤ 5%.
3. **Hiệu ứng tới hạn không nhất quán với kiểm định**: bản trước tính theo phân phối t, trong khi kiểm định là đổi dấu. Đã sửa để hiệu ứng tới hạn được lấy **từ chính phân phối chính xác** mà kiểm định dùng. Có test kiểm tra: quan sát đúng bằng hiệu ứng tới hạn thì có ý nghĩa, kém đi một task thì không.
4. **"Không bác bỏ" ≠ "tương đương"** (ICH E9: "Concluding equivalence … based on observing a non-significant test result … is inappropriate"). Vì vậy, nếu A/A ở bước xác nhận **không** bác bỏ, ta **không** được viết "pipeline sạch". Chỉ được viết: "A/A không phát hiện lệch; độ lệch ước lượng [khoảng t]". Đây cũng là cách Kohavi dùng A/A: để phát hiện vấn đề, không phải để chứng minh không có vấn đề.

## 3. Chưa mở được bản gốc

| Nguồn | Tình trạng | Ảnh hưởng |
| --- | --- | --- |
| Lakens, Scheel & Isager 2018 (TOST, SESOI) | Lượt tải đầu thất bại; đang thử lại qua mirror | TOST và biên đã bị **bỏ** khỏi phán quyết G1; chỉ còn dùng để lý giải θ cho thí nghiệm chính |
| Lakens 2022 (*Sample size justification*) | Như trên | Chỉ dùng cho kế hoạch thí nghiệm chính |
| Nosek et al. 2018; Steegen et al. 2016 | Như trên | Không ảnh hưởng phép tính nào |
| Holm 1979, Cox 1975, Fisher 1935, Pitman 1937, Wald 1950 | Sách hoặc bài sau tường phí | Đã xác nhận qua nguồn thứ cấp uy tín (mục 1) |
| ICH E9 về mức 2,5% | ✅ đã mở bản gốc | — |

## 4. Những gì không phụ thuộc vào nguồn nào

- Tổng chuỗi Basel Σ 6/(π²k²) = 1: định lý toán học, đã kiểm bằng số trong `tests/`.
- Kiểm định đổi dấu chính xác bằng tích chập: test so khớp với liệt kê vét cạn 2⁸ dấu (`test_sign_flip_is_exact`).
- Số seed m, trần ngân sách: phép tính trên ràng buộc, xem `docs/number_provenance.md`.
