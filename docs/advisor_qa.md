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

## 5. Đối chiếu bản gốc (03/11/2026) và hướng giải quyết từng điểm yếu

Nguồn tải qua `.github/workflows/sources.yml`; trích đoạn ở nhánh `sources-snapshots`.

### 5.1 Xác nhận các nguồn đã trích

| Nguồn | Câu trích (bản gốc) | Kết luận |
| --- | --- | --- |
| Voyager (arXiv 2305.16291) | "an ever-growing skill library of executable code for storing and retrieving complex behaviors … reusable, interpretable, and generalizable to novel tasks" | ✅ khái niệm skill library |
| Agent Skills (`anthropics/skills`) | "Skills are folders of instructions, scripts, and resources that Claude loads dynamically … Each skill is self-contained in its own folder with a SKILL.md file" | ✅ |
| XRepoSkill (arXiv 2609.36807) | "a skill as a collection of rules, each specifying what action to take and when to take it"; rule giữ lại theo "resolution gain … the Mantel–Haenszel estimator" kèm "z score … (Sato et al., 1989)"; "we have released the source code, data, and skill corpus" | ✅ **có bộ skill công khai và quy tắc admit được mô tả bằng công thức** |
| Repo XRepoSkill (README) | "Two calls to the backbone LLM select at most three rules per issue; the rules' title and body are placed above the issue description in the first message of an unchanged mini-SWE-agent" | ✅ **cùng harness với chúng tôi (mini-swe-agent)**, nên dùng được trực tiếp |
| SWE-Skills-Bench (arXiv 2603.15401) | "We start from 98 public SWE skills"; "92 of 98 skills are Ineffective, and the mean pass ratio changes only from 76.6% without skills to 76.9%" | ✅ khớp kết quả G1 |
| SWE-bench Verified (swebench.com) | "Human annotators reviewed each instance to ensure the problem descriptions are clear, the test patches are correct, and the tasks are solvable" | ✅ |
| SWE-bench-Live (arXiv 2505.23419; repo) | "1,319 tasks derived from real GitHub issues created since 2024, spanning 93 repositories. Each task is accompanied by a dedicated Docker image"; "contamination-free"; bản Python dùng thư viện `swebench` để chấm | ✅ chống nhiễm dữ liệu, tương thích harness |
| Mutation testing (Wikipedia; DeMillo, Lipton & Sayward 1978) | "Mutation testing involves making small changes to the program … A test detects, and therefore rejects, a mutant"; dựa trên giả thuyết "competent programmer" và "coupling effect" | ✅ là cơ sở của việc dùng lỗi nhân tạo để đánh giá khả năng phát hiện |
| Cohen's κ (McHugh 2012, PMC3900052) | thang của Cohen "0.61–0.80 as substantial … this interpretation allows for very little agreement among raters to be described as 'substantial'" | ⚠️ **Ngưỡng κ ≥ 0,7 tôi đặt không có cơ sở.** Thay bằng báo cáo κ kèm CI, và theo khuyến nghị chặt hơn của McHugh (κ ≥ 0,80 mới là đồng thuận mạnh; cần đối chiếu đúng câu trong bài trước khi chốt) |
| Jia & Harman 2011 (khảo sát mutation testing) | bản gốc chưa tải được | ⚠️ chỉ dùng DeMillo et al. qua nguồn thứ cấp |

### 5.2 Hướng giải quyết

| Điểm yếu | Hướng giải quyết (có cơ sở) | Làm khi nào |
| --- | --- | --- |
| **(a) Skill do chúng tôi tự viết, có bậc tự do của người nghiên cứu** | Thí nghiệm chính dùng **bộ skill công khai của XRepoSkill** (học tự động từ trajectory công khai của SWE-bench Verified, chọn rule theo issue bằng chính code của họ, chèn vào cùng mini-swe-agent). Chúng tôi không viết hay chọn skill nào | Thí nghiệm chính (E2) |
| **(b) Rò rỉ và nhiễm dữ liệu** | XRepoSkill học từ repo của **Verified**, nên phải đánh giá trên **SWE-bench-Live** (93 repo, issue từ 2024, image riêng từng task, tương thích `swebench`). Repo trùng sẽ bị loại. Cách này loại cả rò rỉ skill lẫn nhiễm dữ liệu huấn luyện model | E2 |
| **(c) Skill không đại diện** | Hai nguồn skill bên ngoài: XRepoSkill (cho SWE-bench) và 98 skill công khai của SWE-Skills-Bench (dữ liệu đã công bố) | E2 cùng phân tích ngoài đã có |
| **(d) Skill có hại chỉ là "người rơm"** | Hại **thật**: skill của XRepoSkill áp sang repo mới có thể chuyển giao âm, và được đo trên Live. Skill có hại theo thiết kế chỉ là **đối chứng dương** (như mutant trong mutation testing), báo cáo riêng | E1 (đối chứng) và E2 (hại thật) |
| **(e) Nhãn có hại / có ích không chắc chắn** | **Nhãn 3 lớp theo kiểm định trên dữ liệu độc lập** (có hại đã xác lập, có ích đã xác lập, chưa xác định), báo cáo cả lớp chưa xác định. Code: thêm vào `rq1_mini.py` **trước khi có kết quả E1** | Ngay bây giờ |
| **(f) Test chỉ đo tính đúng chức năng** | Đọc tay một mẫu bản sửa (2 người, báo κ kèm CI, ngưỡng theo McHugh 2012), ước lượng tỉ lệ "qua test nhưng sai". Ghi rõ estimand là "đúng chức năng theo test của SWE-bench" | Thí nghiệm chính (👤) |
| **(g) Quy tắc admit của baseline** | Cài **đúng công thức đã công bố** của XRepoSkill (gain Mantel–Haenszel + z Sato, trên trajectory) **chỉ để so sánh quy tắc quyết định**, và vẫn chạy code gốc của họ cho bước học và chọn skill | E2 |

### 5.3 Chuẩn bị E2: skill của bên thứ ba (03/11/2026)

- Repo XRepoSkill tại commit `26fd70345698108c0fdce2d8904293a38b9cd42f` công bố `data/general_strategies_36.md`: **36 chiến lược** học từ trajectory SWE-bench Verified của 11 repo Python. Mỗi chiến lược có *Trigger* và *Action*.
- Bước chọn skill (`src/xreposkill/retrieval.py`): 2 lần gọi LLM cho mỗi issue (phân tích, rồi chọn tối đa `top_n` rule); chỉ chèn tiêu đề và nội dung của rule được chọn lên đầu đề bài.
- **Repo không có file LICENSE**, nên không phân phối lại nội dung skill. E2 tải nội dung tại đúng commit trên khi chạy và chỉ ghi lại mã commit vào kết quả.
- **Tập đánh giá:** SWE-bench-Live (Python), loại 11 repo học skill (`data/verified_submissions.txt` cùng danh sách repo của SWE-bench Verified). Pool được chọn ngẫu nhiên và kiểm định như E1.
- **Việc còn lại:** đọc `llm.py`, `config.py`; chạy bước chọn bằng Gemini Flash-Lite (cùng backbone với agent); đăng ký trước E2; chọn và kiểm định pool trên Actions.
