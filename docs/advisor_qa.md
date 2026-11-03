# Trả lời phản biện: skill, nhãn có hại / có ích, dataset, skill tự sinh (03/11/2026)

## 1. Skill là gì?

**Định nghĩa vận hành (paper, `docs/theory/corrections.md`):** skill là bộ 5 thành phần ⟨π, D, I, P, K⟩:
- **π:** quy trình tái sử dụng. Ở pilot, π là **đoạn hướng dẫn bằng ngôn ngữ tự nhiên** chèn vào đề bài. Trong paper gốc π còn có thể là chương trình sửa code (edit program).
- **D:** dấu vân tay môi trường áp dụng được (ngôn ngữ, phiên bản…).
- **I(x):** điều kiện kích hoạt trên task x. Ở pilot, I là regex trên nội dung issue.
- **P:** hậu điều kiện cần kiểm.
- **K:** phạm vi tác động (file, quyền).

**Liên hệ với khái niệm đã công bố:**
- *skill library* của agent (Voyager, Wang et al. 2023);
- *Agent Skills* dạng `SKILL.md`, được SWE-Skills-Bench đánh giá (98 skill công khai);
- skill tái sử dụng giữa các repo (XRepoSkill, gskill).

Điểm chung: tri thức thủ tục rút ra từ lần giải trước, đem dùng lại cho task mới.

**Skill trong pilot cụ thể là gì:** 4 skill "theo họ mẫu sửa" (null-guard, type-guard, exception-handling, validation-error).
- Họ mẫu sửa được **khai thác tự động** từ gold patch của SWE-Gym train: mẫu xuất hiện ở ≥ 3 repo (`scripts/mine_skills.py`).
- I(x) được **chọn trên train** theo lift (`scripts/activation_check.py`).
- **Đoạn hướng dẫn π do chúng tôi (LLM) viết**, không được trích tự động. Đây là điểm yếu, xem mục 4.

## 2. Làm sao biết skill có hại, không hại, có ích hay không có ích?

**Không dựa vào ý định hay phán đoán của người viết, mà dựa vào phép đo nhân quả có đối chứng.**

- **Đại lượng:** STR(s) = E[ℓ(có skill) − ℓ(không skill)] trên các task mà I(x) đúng. Đây là hiệu ứng nhân quả trung bình theo mô hình kết cục tiềm năng (Neyman 1923; Rubin 1974). Đo bằng **cặp lần chạy trên cùng task**: cùng image Docker, cùng model, cùng seed. Kết quả lấy từ **test của harness SWE-bench chính thức**.
- **Nhãn** (`corrections.md` §1.4):
  - **có hại:** STR > 0;
  - **có ích:** STR ≤ −θ;
  - **trung tính:** ở giữa.
- **Vì STR chỉ ước lượng được, nhãn phải kèm độ bất định.** Đề xuất thay nhãn 3 lớp theo ước lượng điểm bằng **nhãn theo kiểm định trên dữ liệu độc lập**:
  - *có hại đã xác lập* nếu kiểm định chiều hại bác bỏ;
  - *có ích đã xác lập* nếu kiểm định chiều ích bác bỏ;
  - **chưa xác định** nếu không bác bỏ chiều nào.

  Lớp "chưa xác định" phải được báo cáo, không được gộp vào lớp nào. Pilot cho thấy hầu hết skill rơi vào lớp này (G1, A23).
- **Dữ liệu dùng để gán nhãn tách khỏi dữ liệu dùng để quyết định** (Cox 1975). RQ1 thu nhỏ: quyết định trên seed 41, nhãn trên seed 51 và 61.
- **Giới hạn phải thừa nhận:**
  - Test chỉ đo **tính đúng chức năng**. Skill có thể "có hại" theo cách test không bắt được (bảo mật, khả năng bảo trì, sửa quá rộng). Nhãn của chúng tôi là **"có hại về chức năng, theo test của SWE-bench"**.
  - Test của SWE-bench không đầy đủ: một bản sửa qua test vẫn có thể sai.

## 3. Dataset là gì, và tại sao dùng nó?

| Dataset | Là gì | Dùng để |
| --- | --- | --- |
| **SWE-bench** (Jimenez et al., ICLR 2024) | 2.294 issue GitHub thật từ 12 repo Python, mỗi task có test FAIL_TO_PASS / PASS_TO_PASS lấy từ PR thật | Task để đo skill |
| **SWE-bench Verified** (OpenAI 2024) | 500 task đã được người kiểm lại: đề rõ, test đúng | Pilot G1 |
| **SWE-Gym** (Pan et al. 2024) | Task từ **các repo khác** | Khai thác họ mẫu sửa và chọn I(x) (train), không bao giờ dùng để đo |
| **SWE-Skills-Bench** (arXiv 2603.15401) | 98 skill công khai × 4 cấu hình agent × 10 requirement | Bằng chứng ngoài về hiệu ứng skill |

**Vì sao dùng:**
- Được dùng rộng rãi nhất trong đánh giá agent sửa code.
- Là issue thật chứ không phải bài tập tự chế.
- **Nhãn khách quan:** test chạy được, harness chính thức, image Docker tái lập được.
- Tách theo repo nên tránh rò rỉ giữa train và test.

**Giới hạn:**
- Chỉ có Python.
- Model có thể đã thấy repo hoặc PR khi huấn luyện (nhiễm dữ liệu). SWE-bench-Live (task sau ngày cắt dữ liệu huấn luyện) dùng để giảm rủi ro này.
- SWE-bench đầy đủ có nhiều task đề không rõ (lý do OpenAI làm bản Verified). Chúng tôi lọc bằng điều kiện "gold resolve 2 lần, no-op thất bại". Bước lọc này loại task có test hỏng, **nhưng không loại task có đề mơ hồ**. Các task đó làm tăng nhiễu, không gây lệch, vì cả hai nhánh cùng chịu.

## 4. Skill tự sinh có minh bạch và đáng tham khảo không?

**Phần lo ngại là đúng:**
- (a) Người nghiên cứu tự viết skill tạo ra **bậc tự do của người nghiên cứu**: có thể vô tình viết skill dễ hoặc khó.
- (b) Skill tự sinh **không đại diện** cho skill ngoài thực tế.
- (c) Skill có hại theo thiết kế có thể bị coi là **"người rơm"**: hại rõ ràng nên dễ phát hiện hơn hại thật.

**Những gì đã làm để minh bạch:**
- Mọi nội dung skill, code khai thác, I(x) đều nằm trong git và được **commit trước khi đo**. Đăng ký trước có dấu thời gian.
- I(x) được chọn trên train, không chạm dữ liệu test.
- Nhãn có hại hay có ích **được đo**, không được giả định.

**Mức độ đáng tham khảo của từng loại số liệu:**

| Loại số liệu | Có phụ thuộc vào việc skill là tự sinh? | Đáng tham khảo? |
| --- | --- | --- |
| Độ đúng và nhạy của thước đo (A/A, đối chứng dương, khớp harness) | Không | ✅ |
| Nhiễu và phương sai của agent, cỡ mẫu cần thiết | Gần như không (đo trên nhánh không skill và hiệu số) | ✅ |
| "Lời nguyền người thắng" của sàng lọc ngây thơ | Không riêng cho skill tự sinh: **lặp lại trên 98 skill công khai** của SWE-Skills-Bench | ✅ |
| Độ lớn hiệu ứng của 4 skill họ mẫu sửa | **Có** | ⚠️ chỉ mang tính minh hoạ, không suy rộng |
| Gatekeeper chặn skill có hại theo thiết kế (RQ1 thu nhỏ) | **Có** | ⚠️ chứng minh **cơ chế**, không chứng minh **tỉ lệ** ngoài thực tế |

**Cách khắc phục cho thí nghiệm chính (đề xuất):**
1. **Dùng skill của bên thứ ba thay cho skill tự viết:** 98 skill công khai của SWE-Skills-Bench; skill do chính XRepoSkill hay gskill khai thác ra (chạy code gốc của họ); thư viện skill công khai. Cách này loại bỏ bậc tự do của người nghiên cứu.
2. **Skill có hại thật thay vì chỉ có hại theo thiết kế:** skill **lỗi thời** khi đổi phiên bản thư viện (Regime A trong TODO), và skill đúng ở repo gốc nhưng sai ở repo mới (chuyển giao âm). Skill có hại theo thiết kế chỉ giữ vai trò **đối chứng dương cho claim an toàn**. Cách làm này tương tự **mutation testing**: dùng lỗi nhân tạo để đánh giá khả năng phát hiện (DeMillo, Lipton & Sayward 1978; Jia & Harman 2011), và được báo cáo tách riêng.
3. **Nhãn 3 lớp theo kiểm định** (mục 2), báo cáo cả lớp "chưa xác định".
4. **Mở rộng đo lường ngoài test:** đọc tay một mẫu bản sửa (2 người, Cohen's κ ≥ 0,7, đã có trong TODO) để ước lượng tỉ lệ "qua test nhưng sai".

Các tài liệu Voyager, mutation testing và OpenAI Verified được trích theo hiểu biết; chưa đối chiếu bản gốc trong phiên này.
