# Baselines

Nguyên tắc (TODO.md mục 5): chỉ dùng baseline có code công khai, **không tự cài lại** phương pháp của người khác. Mọi hệ thống chạy trên **cùng một harness** (đề xuất: mini-swe-agent) và cùng model, sampling, budget.

## Điều kiện đối chứng (cài trong `src/gatekeeper/baselines.py`)

| Baseline | Lớp | Quyết định | Chi phí thêm mỗi lần reuse | Khác bản trong paper |
| --- | --- | --- | --- | --- |
| B1 No skills | `NoSkills` | Không bao giờ dùng skill | 0 | Không |
| B2 Unrestricted reuse | `UnrestrictedReuse` | Luôn dùng skill | 0 | Harmful acceptance của B2 = 100% theo định nghĩa đã sửa (paper ghi 22,7%) |
| B8 Always-retest | `AlwaysRetest` | Chạy task có/không skill trên target trước mỗi lần reuse; giữ skill nếu không tệ hơn | 2 lần chạy | Không |
| B9 Budget-matched retries | `BudgetMatchedRetries` | Không dùng skill; dùng đúng budget admission của Gatekeeper cho các lần sửa thêm | bằng Gatekeeper | Budget tính theo số lần chạy agent + test, cùng đơn vị với Gatekeeper |

Cách chạy: mỗi lớp nhận một hàm chạy thật (`paired_run` cho B8, `attempt` cho B9) do trial runner cung cấp. Kết quả ghi qua `gatekeeper.runlog.ResumableLog`.

## Baseline của bên thứ ba (chạy từ repo gốc)

Phải ghi commit khi clone (Phase 2). Chỉ được viết **adapter** chuyển định dạng skill/task, không sửa thuật toán.

| Baseline | Repo | Commit | Lệnh chạy | Adapter | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| XRepoSkill (quyết định) | [XREPOSKILL/XRepoSkill](https://github.com/XREPOSKILL/XRepoSkill) | _chưa clone_ | _theo README của repo_ | skill → `Skill` JSON | Chưa chạy (cần LLM 💰) |
| MemGovern | [QuantaAlpha/MemGovern](https://github.com/QuantaAlpha/MemGovern) | _chưa clone_ | | experience card → `Skill` | Chưa chạy 💰 |
| gskill (GEPA) | [gepa-ai/gepa](https://github.com/gepa-ai/gepa) | _chưa clone_ | | `SKILL.md` → `Skill` | Chưa chạy 💰 |
| ASI (tuỳ chọn) | [zorazrw/agent-skill-induction](https://github.com/zorazrw/agent-skill-induction) | | | cần port sang coding | Chưa quyết định |

Tiêu chí tái hiện (R5): so trên **đúng tập task** paper gốc đã dùng; đạt nếu số của paper nằm trong CI 95% của mình.
