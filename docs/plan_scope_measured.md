# Kế hoạch: "Scope before Reuse, Measured" (bản 1, 05/11/2026; chờ @thuthuy duyệt, trần 60 USD)

## 1. Định vị

**Tên làm việc:** *Scope before Reuse, Measured: Replicating, Certifying and Attributing Published Agent Skills under Placebo Control.*

**Paper trả lời câu hỏi của paper gốc** ("một skill có nên được dùng ở đây không?") **bằng skill thật, đã được người khác công bố là có lợi hoặc có hại**, với các công cụ đã xây trong dự án này:
- Gatekeeper (admission và thu hồi có bảo đảm);
- placebo A/A;
- Mệnh đề P (phép trừ placebo);
- kiểm định hoán vị chính xác.

Thống kê là **công cụ**. Đóng góp chính là **bằng chứng thực nghiệm về việc dùng lại skill**: lặp lại được không, chứng nhận được không, quy lỗi đúng không, phụ thuộc scope không.

**Mục đích:**
1. **Lặp lại:** tác dụng đã công bố của skill (SWE-Skills-Bench: `viper-configuration` +17,7 điểm; `asyncio-patterns` −17,0 điểm) có còn không khi đổi scope (agent và model khác), chạy lặp có đối chứng placebo?
2. **Chứng nhận:** lần đầu admit hoặc từ chối một **skill thật** trong một scope, có bảo đảm, kèm số trial và chi phí. Paper gốc và pilot 2.1 chưa làm được việc này.
3. **Quy lỗi:** phép trừ placebo bắt được lỗi do skill thật gây ra (chiều "hại"); auditor có quy lỗi đúng không.
4. **Kiểm tra phương pháp:** bảng placebo cho các quy tắc đã công bố (đã có ở §18–§21).

## 2. Đóng góp dự kiến

| # | Đóng góp | Trạng thái |
| --- | --- | --- |
| C1 | Nghiên cứu **lặp lại** đầu tiên của tác dụng skill đã công bố, qua 6 cấu hình agent–model: 4 của SWE-Skills-Bench và 2 của mình, có chạy lặp và placebo | Cần chạy (phần 4, giai đoạn 1–2) |
| C2 | **Chứng nhận có bảo đảm cho skill thật theo scope** (admit hoặc từ chối), kèm số trial và chi phí đo thật | Cần chạy |
| C3 | **Quy lỗi có hiệu chỉnh placebo**, có chứng minh (Mệnh đề P; kiểm định hoán vị: mức 0,042, độ nhạy 0,72–0,93), có **đối chứng dương ở cả hai chiều**: giúp (T4, có rồi) và hại (`asyncio-patterns`, cần chạy) | Lý thuyết và chiều "giúp" đã có |
| C4 | Bảng placebo cho 8 quy tắc đã công bố; giới hạn của audit bằng LLM; bộ dữ liệu chạy lặp có A/A | Đã có (§18–§21) |

## 3. Điểm mạnh và điểm yếu

**Điểm mạnh:**
- **Đúng luận điểm của paper gốc**, nhưng với **skill thật có tác dụng thật**, thay cho số liệu dự phóng của paper gốc.
- **Kết quả nào cũng báo cáo được:**
  - lặp lại được: có chứng nhận skill thật và đối chứng dương phía "hại";
  - không lặp lại được: có bằng chứng scope (tác dụng không chuyển sang agent và model khác).
- **Nhiều model:** 4 cấu hình của SWE-Skills-Bench, cộng 2 của mình (một hãng khác Google).
- **Phương pháp đã kiểm sẵn:** Gatekeeper (T4), placebo (§18), hoán vị (§21), cùng toàn bộ quy trình đăng ký trước.
- **Dữ liệu và hạ tầng công khai:** image, test ẩn và skill của SWE-Skills-Bench (repo MIT; `SKILL.md` của `asyncio-patterns` ghi MIT).

**Điểm yếu và rủi ro:**

| Rủi ro | Mức | Xử lý |
| --- | --- | --- |
| Adapter (mini-swe-agent + Vertex trong image của họ) **khác cách họ chạy**: Claude Code hoặc Codex nạp skill bằng lệnh `/skill-id`, còn mình chèn nội dung `SKILL.md` vào prompt | Cao | Nêu là thay đổi scope (agent khác), đúng câu hỏi RQ1. Chạy thử miễn phí để chắc điểm số tính đúng |
| Mỗi skill chỉ có **10 yêu cầu**, nên số trial bị giới hạn | Vừa | 3 seed × 10 = 30 cặp mỗi skill mỗi model. Điểm là tỉ lệ test qua (liên tục), phương sai thấp hơn kết quả 0/1. Tính power trước khi chạy (L38) |
| Tác dụng có thể không lặp lại trên Flash-Lite | Vừa | Vẫn là kết quả (bằng chứng scope); đã đăng ký trước cả hai chiều diễn giải |
| Model khác hãng chưa được bật hoặc không tương thích | Vừa | Hỏi @thuthuy hoặc gọi thử dưới 0,01 USD; chạy thử 1 yêu cầu trước |
| Image Docker lớn (Go) | Thấp–vừa | Kiểm kích thước trước; xóa image sau mỗi skill |
| Chọn skill đối chứng | Thấp | Quy tắc chọn cố định trước (phần 4, 0.6), không chọn theo ý |

## 4. To-do cụ thể

### Giai đoạn 0: miễn phí, khoảng 1 ngày

| # | Việc | Đầu ra | Cổng dừng |
| --- | --- | --- | --- |
| 0.1 | Rà tính mới (R1): đã có ai lặp lại tác dụng skill của SWE-Skills-Bench, hoặc chứng nhận skill thật chưa? Đọc lại bản gốc phần skill Harmful ("version-mismatched guidance") | Mục trong `docs/novelty_review.md`, kèm câu trích | Có bài làm trùng thì báo @thuthuy |
| 0.2 | Model thứ hai: gpt-oss-120b hoặc Qwen3 trên Vertex. **Hỏi @thuthuy tình trạng Model Garden (L21)**, rồi gọi thử 1 lời gọi | Model ID và giá đã xác minh | Không có model dùng được thì dùng Gemini Flash (đắt hơn) và báo |
| 0.3 | Kéo image `swe-skills-bench-python` và `-golang`; ghi kích thước; kiểm đĩa | Bảng kích thước | Không đủ đĩa thì chạy lần lượt từng skill |
| 0.4 | **Adapter** `scripts/sskb_adapter.py`: clone repo ở đúng commit, chạy `setup_commands`, chèn `SKILL.md` vào prompt (nhánh skill), chạy mini-swe-agent với Docker env trong image của họ, chạy `test_command` của họ để lấy tỉ lệ pass. Có test | Mã + test | — |
| 0.5 | **Chạy thử miễn phí** (model giả lập) trên 1 yêu cầu của mỗi skill: kiểm cả hai nhánh chạy hết, điểm số đọc đúng, nhánh không skill không chứa `SKILL.md` | Review R-42 | Điểm sai hoặc hạ tầng lỗi thì sửa trước, không chạy có phí |
| 0.6 | **Đăng ký trước §22:** 4 skill = `viper-configuration`, `asyncio-patterns` + 2 đối chứng chọn bằng quy tắc cố định (2 skill Python có \|trung bình\| nhỏ nhất trong SWE-Skills-Bench); 10 yêu cầu × seed 41/51/61 × 2 nhánh; endpoint = tỉ lệ pass; giả thuyết RQ1–RQ3 kèm cả hai chiều diễn giải; quy tắc Gatekeeper (α, θ, scope = skill × repo × model); placebo và hoán vị; số trial dự kiến (L38); trần từng giai đoạn | §22 + commit | — |

### Giai đoạn 1: có trả phí, Flash-Lite, trần 25 USD

| # | Việc | Cổng |
| --- | --- | --- |
| 1.1 | Chạy thử: 1 yêu cầu × 4 skill × 1 seed × 2 nhánh (8 lần chạy), đo chi phí thật | Lỗi hạ tầng > 1/8, hoặc chi phí mỗi lần chạy > 2 lần ước tính, thì dừng và báo |
| 1.2 | Đủ: 4 × 10 × 3 × 2 = 240 lần chạy | Driver dừng khi "đã chi + lô xấu nhất > trần". Lỗi hạ tầng > 10% thì dừng |
| 1.3 | Lưu trữ thô (`archive_raw.py`); kiểm `infra_failures` | — |

### Giai đoạn 2: có trả phí, model khác hãng, trần 25 USD

| # | Việc | Cổng |
| --- | --- | --- |
| 2.1 | Như 1.1 trên model thứ hai | Như 1.1; thêm: agent không đúng định dạng của mini-swe-agent ở > 1/8 lần chạy thì dừng |
| 2.2 | Như 1.2 | Như 1.2 |

### Giai đoạn 3: phân tích, 0 USD (cộng khoảng 1 USD audit, trong dự phòng)

| # | Việc | Gắn với |
| --- | --- | --- |
| 3.1 | Tác dụng mỗi skill × model kèm CI; so với 4 cấu hình của SWE-Skills-Bench | RQ1, C1 |
| 3.2 | Gatekeeper trên từng scope: admit hoặc từ chối, số trial lúc dừng, chi phí | RQ2, C2 |
| 3.3 | Phép trừ placebo và kiểm định hoán vị theo chiều "hại" (`asyncio-patterns`) | RQ3, C3 |
| 3.4 | Audit (Flash, Pro) trên ứng viên của `asyncio-patterns` và skill đối chứng | RQ3, C3 |
| 3.5 | Bảng scope: tác dụng qua 6 cấu hình | RQ1, C1 |

### Giai đoạn 4: viết, 0 USD

| # | Việc |
| --- | --- |
| 4.1 | Viết lại `paper/main.tex` theo định vị này. Paper gốc là khung (scope, admission, thu hồi); §18–§21 là phần phương pháp và kiểm tra |
| 4.2 | Bảng và hình sinh tự động; `refs.bib` chỉ dùng bản gốc đã đọc; `number_provenance`, `glossary` |
| 4.3 | 👤 Người biết thống kê đọc phần lý thuyết; 👤 thầy duyệt |
| 4.4 | Artifact: adapter, dữ liệu chạy lặp, bản đăng ký trước |

## 5. Ngân sách

| Giai đoạn | Trần |
| --- | --- |
| 1 (Flash-Lite) | 25 USD |
| 2 (model khác hãng) | 25 USD |
| Dự phòng (audit, chạy lại do lỗi hạ tầng) | 10 USD |
| **Tổng** | **60 USD** |

Mọi khoản nằm trong mức @thuthuy đưa ra. Mỗi giai đoạn có cổng dừng riêng.
