# Gatekeeper khác các công trình gần nhất ở đâu (nháp)

> **Nguồn:** chỉ abstract arXiv (`data/citations.json`, lấy tự động ngày 01/11/2026) và dữ liệu công khai của SWE-Skills-Bench. **Chưa đọc full paper.** Việc 👤 trong TODO Phase 0: đọc từng bài, sửa bảng này, rồi gửi người hướng dẫn góp ý.

## 1. Bảng so sánh

| | Học gì | Kiểm chứng thế nào | Bằng chứng lấy ở đâu | Bảo đảm thống kê | Ghép skill | Đánh giá trên |
| --- | --- | --- | --- | --- | --- | --- |
| **Gatekeeper** (đề xuất) | edit program + ⟨D, I, P, K⟩ | paired trial có/không skill + e-process | **repo đích** | FWER hữu hạn mẫu, theo scope (Theorem 4′) | footprint giao nhau → bài toán admission riêng | SWE-bench / Verified / Live (split theo repo) |
| **XRepoSkill** (2609.36807) | tập rule "làm gì, khi nào" + predicate thực thi | đối chiếu trajectory thành công/thất bại cùng issue; giữ rule khi liên quan tới thành công **và** lặp lại ở nhiều repo | trajectory leaderboard SWE-bench Verified (repo **nguồn**) | kiểm định liên hệ (Mantel–Haenszel theo TODO; cần xác nhận) | không nêu | SWE-bench Pro, DeepSWE |
| **GSE** (2608.06153) | skill + Skill Relation Graph | gom cụm + **replay verification** chống overfit/regression | repo nguồn | không nêu | quan hệ giữa skill (SRG), không phải kiểm tra ghép | **sinh test lộ bug, lọc false-positive bug report** (không phải sửa code) |
| **HSE** (2610.35616) | skill thủ tục, tổng hợp phân cấp task → repo → đa repo | vòng writer–evaluator bên ngoài | trajectory **SWE-Gym** | không nêu | không nêu | **SWE-bench Verified**, DeepSWE |
| **SWE-Skills-Bench** (2603.15401) | — (benchmark 98 skill có sẵn) | **paired** có/không skill, 10 requirement, kiểm định thống kê mỗi skill | repo gắn với skill | kiểm định mỗi skill (Golden / Ineffective / Harmful) | không | requirement + hidden test |
| **MemGovern** (2601.06789) | 135K experience card từ GitHub | governance + tìm kiếm agentic | lịch sử con người | không | không | SWE-bench Verified (+4,65%) |
| **CODESKILL** (2605.25430) | chính sách quản lý skill (RL) | phần thưởng rubric + thực thi | trajectory | không | không | EnvBench, Verified, Terminal-Bench 2 |
| **Formal verification [7]** (2605.23951) | — | capability containment (abstract interpretation, refinement type, SMT) | manifest của skill | chứng minh hình thức về **quyền** | không | demo trên một skill mẫu |

## 2. Điểm mới thật sự của Gatekeeper (cần bảo vệ)

1. **Câu hỏi khác:** "skill có nên chạy *ở repo này* không", không phải "skill có tốt nói chung không". Bằng chứng lấy trên repo đích. XRepoSkill, GSE và HSE đều kiểm chứng trên dữ liệu nguồn.
2. **Bảo đảm anytime-valid, kiểm soát toàn họ** (FWER theo scope, kể cả composite và re-admission). Không bài nào ở trên có bảo đảm dạng này.
3. **Composition là bài toán admission riêng**, kèm kết quả âm: rủi ro ghép không bị chặn bởi rủi ro riêng lẻ (Theorem 7′, có phản ví dụ chạy được).
4. **Retirement theo fingerprint** kèm alpha-spending khi re-admit.

## 3. Chỗ **không** mới (phải nói thẳng trong paper)

- **Paired có/không skill** đã có ở SWE-Skills-Bench (3.920 cặp). Gatekeeper dùng lại ý tưởng này như một thủ tục admission tuần tự, không phải như một benchmark một lần.
- **Kiểm chứng đa repo**: XRepoSkill đã giữ rule chỉ khi rule lặp lại ở nhiều repo. Khác biệt của Gatekeeper là kiểm chứng *trên repo đích* kèm bảo đảm thống kê, nhưng phải chứng minh khác biệt này có ích (RQ1).
- **Split SWE-Gym → SWE-bench Verified** trùng HSE. Đây là điểm cộng (so sánh được), nhưng phải trích dẫn HSE và cân nhắc HSE làm baseline nếu họ công bố code.
- Máy móc thống kê (betting e-process, Ville, union bound, cluster bootstrap) là **chuẩn**. Paper đã tự nhận điều này; giữ nguyên.

## 4. Rủi ro định vị do dữ liệu đã thấy

- SWE-Skills-Bench: 92/98 skill không có tác dụng đáng kể; SD thật của STR khoảng 0,03 (`results/sskb_analysis.json`). Nếu skill của Gatekeeper cũng nhỏ như vậy, câu trả lời của Gatekeeper gần như luôn là "quarantine". Kết quả đó **đúng về mặt thống kê nhưng không hữu ích**. Xem R15 trong `TODO.md`.
- Câu hỏi reviewer chắc chắn sẽ hỏi: "Nếu hầu hết skill không giúp gì, sao không bỏ hẳn skill (B1)?" Paper cần RQ3 (so với B9) và break-even (RQ4) để trả lời.

## 5. Việc tiếp theo (👤)

- [ ] Đọc full XRepoSkill: xác nhận thủ tục kiểm định (có thật là Mantel–Haenszel?) và họ có sửa cho kiểm định bội không.
- [ ] Đọc full HSE: có code không; nếu có, cân nhắc thêm làm baseline.
- [ ] Đọc full GSE: xác nhận lại tập đánh giá (TODO bản 1 ghi Multi-SWE-bench Java + IndustrialBugs Go; abstract nói về sinh test và lọc bug report).
- [ ] Gửi bản sửa của trang này cho người hướng dẫn.
