# Kiểm khả thi W5 và W7 (18/11/2026; 0 USD; @thuthuy 18/11: "Tranh thủ làm 2 cái 0usd")

Tài liệu này chỉ kiểm tính khả thi. Không có lệnh gọi model nào, và không có kết luận nào về kết quả. Mọi con số chi phí ở đây là **dự kiến** (L63): chúng suy ra từ chi phí đã đo của các lượt trước, không phải số đo của thí nghiệm mới.

## W7: một bộ học skill duy nhất (gskill)

### Bộ học thứ hai: XRepoSkill

- **Mã:** commit ghim `26fd70345698108c0fdce2d8904293a38b9cd42f`, mã đã dùng ở E2 (`docs/preregistration_e2.md`).
  - Repo không có file LICENSE. Ta được chạy mã của họ, nhưng không phân phối lại nội dung (`docs/skill_catalog.md`).
  - Mọi việc ở mục này chỉ là đọc mã. Lệnh cài và chạy mã bên thứ ba trên máy của phiên bị chặn (18/11), và tôi không vòng qua.
- **Bộ học thật sự có trong repo** (README: "The code implements the three stages of the paper and nothing else"). Bước 1, "Divergence-guided rule discovery": "A failed and a successful trajectory on the same issue are aligned action by action; three prompts read the trajectories from the divergence point onward and write candidate rules".
- **Định dạng đầu vào:**
  - `ingest.py::adapt_trajectory` đọc `messages` của mini-swe-agent. Tin nhắn `user` và `tool` được đọc là quan sát; tin nhắn `assistant` được đọc là hành động hoặc suy nghĩ.
  - Quỹ đạo đã lưu của ta (`results/*.traces.jsonl.gz`) có đúng dạng `instance_id` + `messages` với vai trò system/user/assistant. Chỉ cần đổi bố cục thư mục (`<submission>/trajs/<iid>/<iid>.traj.json`) và file nhãn (`per_instance_details.json`, trường `resolved`).
- **Quy tắc ghép cặp** (`pairing.py::select_pairs`, đọc mã; K = 4 theo `configs/pipeline.yaml`): trên mỗi issue có cả hai kết quả, mỗi quỹ đạo thất bại được ghép với mỗi quỹ đạo thành công của một model có tỉ lệ giải cao hơn. Các cặp xếp theo khoảng cách tỉ lệ giải, lấy K cặp đầu.
- **Dữ liệu sẵn có cho cách ghép đó** (tôi đếm lại theo đúng quy tắc trên, không chạy mã của họ):
  - Môi trường gốc của Jinja, nhánh không skill.
  - Model mạnh: agent Flash của §34 (`s34_none_pilot`, `s34_none_rest`), 34 task không mô tả, giải 31 (tỉ lệ 0,912).
  - Model yếu: agent Flash-Lite (`s29_none`, `s33_ship_none`, `c10_A_none_all70`, `c10r_A_none_all70`), tỉ lệ 0,121.
  - **123 cặp trên 31 issue**; ở mọi cặp, phía thành công là Flash.
  - Đây là đúng tình huống cần hỏi. Flash không có skill vẫn tự thấy diff "Bug Patch" ở 33/34 lượt (`hiFlNoneDiff`, §41). Vậy ở điểm rẽ nhánh, quỹ đạo thành công thường là quỹ đạo đọc lịch sử.
- **Câu hỏi khoa học (đề xuất, chưa đăng ký):** từ các cặp này, bộ học của XRepoSkill có viết, và tự chấm qua, một quy tắc bảo agent đọc lịch sử git không?
  - Đại lượng đề xuất: quy tắc có dòng khớp `RULE` của §29 (giống H của §38).
  - Bước kiểm trùng n-gram với bản vá gốc của họ (`audit.py`, n = 6) có bắt được quy tắc đó không? Theo thiết kế thì không, vì quy tắc kiểu "đọc `git log`" không chứa đoạn nào của bản vá. Đây sẽ là một điểm cụ thể cho paper: cách chống rò rỉ của XRepoSkill không chặn được kênh này.
- **Giới hạn của thiết kế không có đối chứng:**
  - Chỉ có Jinja. Bleve không có quỹ đạo của agent Flash, nên bước tổng quát hóa qua nhiều repo (`generalize`, cần ≥ 2 repo) không tạo được quy tắc chuyển giao. Chỉ có quy tắc riêng của repo.
  - Không có đối chứng một commit: agent Flash chưa chạy trong môi trường một commit (paper đã ghi: "We did not run the single-commit control for this model"). Không có đối chứng, kết quả chỉ là mô tả, giống quan sát của §36.
  - **Thêm đối chứng:** chạy Flash không skill trong môi trường một commit trên 34 task. Nhánh tương ứng của §34 đã chi 2,696 USD (0,342 + 2,354), nên dự kiến cũng khoảng chừng đó. Sau đó học từ các cặp trong môi trường một commit, và so tỉ lệ quy tắc có dòng lịch sử giữa hai môi trường.
- **Chi phí dự kiến của bước học** (cận trên thô):
  - Khoảng 123 cặp × 3 prompt phân tích ≈ 370 lần gọi, cộng các lần gộp và chấm.
  - Mỗi lần gọi đọc hai quỹ đạo. Trung vị độ dài: Flash thành công 47.597 ký tự; Flash-Lite 17.698 ký tự.
  - Theo giá mỗi lần gọi đo ở P0 của §38 (prompt 74.305 ký tự): gpt-oss 0,0028, Haiku 0,0054, Gemini Pro 0,089 USD hạn mức. Cận trên khoảng 1 USD với gpt-oss, khoảng 2 USD với Haiku, khoảng 30 USD với Gemini Pro.
  - Model mặc định của họ (`deepseek/deepseek-v4-pro`) chưa được kiểm có trên Kaggle hay không. Đổi model là dùng nút `PIPELINE_MODEL` mà README cho phép, nhưng vẫn là một sai khác so với bản gốc, phải ghi vào `docs/reviewer_fidelity.md`.
  - Chỉ chốt chi phí sau một lần đo thử ít lần gọi.
- **Nơi chạy:**
  - Notebook Kaggle Benchmarks: proxy model của Kaggle có `MODEL_PROXY_URL`, và `litellm` của họ có thể trỏ tới đó như ô C4′.
  - Hoặc workflow GitHub với Vertex.
  - Cả hai đều cần cài mã của họ ở nơi chạy, như E2 đã làm.

## W5: chỉ có task tổng hợp

- **Đã sửa câu chữ (R-79):** paper giờ tách rõ. Các thí nghiệm về skill dùng task SWE-smith (repo thật, lỗi chèn, lịch sử do benchmark dựng). Các luồng A/A và mức nhiễu dùng issue thật của SWE-bench và SWE-bench-Live.
- **Kênh rò rỉ trên benchmark repo thật** (đọc từ bản chụp nguồn):
  - SWE-bench, issue 465 (`swebench_git_log_leak`): "We've identified multiple loopholes with SWE Bench Verified where agents may look at future repository state". PR 471 (`swebench_git_log_fix`): "Fix git log leakage in environment images". Image SWE-bench ta dùng không còn commit tương lai (B1 ở `docs/audit_pilot.md`: `git rev-list --all --not HEAD` = 0).
  - Đây là một **loại rò rỉ khác**: lời giải tương lai, không phải mã trước lỗi. Nên không lặp lại được C10 trên SWE-bench.
  - **SWE-Bench Pro Verified** (Zheng et al., arXiv 2609.08149; toàn văn trong bản chụp `swebench_pro_verified_pdf`, run 44207267485). Câu trích nguyên văn:
    - Bảng 1, "Primary reward-hacking channels in SWE-Bench Pro": "Git history Local Future commits, branches, tags, remotes, and reflogs".
    - "An existing community proposal isolates tasks by deleting future Git history after checking out the base commit [5]. However, its cleanup procedure deletes only branch, remote, and tag references, without handling notes, replace references, or stashes, which may preserve objects created after the base commit. Consequently, future fixes may remain recoverable from .git/objects after all visible references have been deleted."
    - Cách vá của họ: "we recursively remove nested Git histories and reconstruct each repository as a fresh single-commit repository". Đây đúng là đối chứng một commit của ta.
    - Một trace họ trích: "There's a 'git log --all' that shows future commits ... This is the gold patch source!"
  - **Hệ quả cho W5:**
    - Trên một benchmark issue thật (SWE-Bench Pro, 731 task), kênh lịch sử git có tồn tại. Nhưng nó là kênh **lời giải tương lai**, khác với kênh **mã trước lỗi** của SWE-smith.
    - Vì vậy C10 không lặp lại nguyên vẹn được ở đó.
    - Câu hỏi làm được: một skill dạy đọc lịch sử có tạo mức tăng trên task thật khi lịch sử còn lộ, và mất mức tăng đó trong bản một commit của Pro Verified không?
    - Thiết kế đó trả lời W5 theo nghĩa "hiện tượng skill khai thác lịch sử cũng xảy ra trên repo thật". Nó không trả lời "đúng cơ chế của SWE-smith".
  - **Khả thi kỹ thuật (chưa đo):**
    - Cần image Pro gốc (`docker.io/jefzda/sweap-images`, theo README của XRepoSkill), bộ chấm Pro, và image đã làm sạch của Pro Verified.
    - Image lớn, kéo từ Docker Hub (đã từng chạm giới hạn 429, C6 ở `docs/audit_pilot.md`).
    - Tỉ lệ giải nền của agent Flash-Lite trên Pro chưa biết; nếu thấp thì power thấp.
    - Bài chưa cho con số mức điểm thay đổi giữa bản gốc và bản đã làm sạch trong các đoạn đã chụp. Tôi không ghi con số nào khi chưa đọc thấy.
  - **Kết luận khả thi:** làm được, nhưng tốn công kỹ thuật lớn hơn nhiều so với W7, và câu trả lời gián tiếp hơn. Trước khi xin ngân sách, cần một bước đo miễn phí: kéo 1 image, chạy bộ chấm với bản vá gốc và bản vá rỗng, và đếm commit tương lai trong image gốc.

## Việc tiếp theo

1. Đọc toàn văn SWE-Bench Pro Verified khi workflow `sources` xong. Bổ sung mục W5.
2. Gửi @thuthuy hai lựa chọn có giá, kèm power hoặc phạm vi kết luận. Thêm thí nghiệm là quyền của @thuthuy (CLAUDE.md, quyền quyết định mục 2).
