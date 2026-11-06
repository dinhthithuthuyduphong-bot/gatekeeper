# Kế hoạch gộp: tái hiện các mức tăng nhờ skill đã công bố (bản 1, 06/11/2026; chờ @thuthuy duyệt, trần 60 USD)

## 1. Hướng này có hợp lý không

**Câu hỏi:** các mức tăng (hoặc giảm) nhờ skill **đã công bố** có đứng vững khi đánh giá có chạy lặp, có placebo A/A và có chứng nhận theo scope không?

| Kiểm tra | Kết quả |
| --- | --- |
| **Khớp to-do gốc** (bản 2, 01/11) | Có. To-do gốc đặt XRepoSkill, MemGovern, gskill làm baseline "có code", và yêu cầu tái hiện chúng "trên tập task của paper" (Phase 2, R5). Paper gốc hỏi "skill có nên được dùng ở đây không" (scope, admission) |
| **Khớp những gì đã làm** | Có. XRepoSkill đã chạy (E2). MemGovern đã qua đủ kiểm tra miễn phí (lần thử 7: F1–F6 và F4b đạt; §11e, `preregistration_main_draft.md`). Có sẵn công cụ: placebo (§18), Mệnh đề P và hoán vị (§20–§21), Gatekeeper (T4), thu hồi (T2b) |
| **Có tác dụng thật để chứng nhận không** | Có. SWE-Skills-Bench: `viper-configuration` +17,7 điểm, `asyncio-patterns` −17,0 điểm; ổn định qua 4 cấu hình (−0,16 tới −0,19; +0,10 tới +0,22) |
| **Không đặt cược** | Mỗi phần đều là phép đo. Mỗi kết quả, tích cực hay tiêu cực, đều có diễn giải đã viết trước (phần 5) |

**Kết luận:** hợp lý. Đây là hướng gần to-do gốc nhất mà vẫn khả thi trong 60 USD.

## 2. Định vị

**Tên làm việc:** *Do Published Skill Gains Survive? Replicated, Placebo-Controlled Evaluation and Certification of Agent Skills.*

**Ba đối tượng đã công bố**, ba loại "skill":

| Đối tượng | Loại | Mức công bố | Vai trò trong paper |
| --- | --- | --- | --- |
| XRepoSkill | Rule chuyển giữa repo | +4,0 tới +12,4 điểm (6 mức) | Mức tăng nhỏ đến vừa, kiểm "có lặp lại không" (đã có E2) |
| MemGovern | Thẻ kinh nghiệm từ lịch sử phát triển | +2,4 tới +9,4 điểm (7 mức) | Như trên; benchmark gốc của họ là SWE-bench Verified |
| SWE-Skills-Bench | Tài liệu `SKILL.md` | +17,7 / −17,0 điểm | Tác dụng lớn: kiểm "lặp lại" và **chứng nhận** (admit / từ chối) |

**Đóng góp:**
- **C1:** tái hiện có lặp lại và placebo cho ba hệ thống.
- **C2:** chứng nhận skill thật theo scope.
- **C3:** quy lỗi có hiệu chỉnh placebo (lý thuyết và đối chứng dương ở hai chiều).
- **C4:** bảng placebo cho 8 quy tắc; giới hạn của audit; bộ dữ liệu.

## 3. To-do và quan hệ phụ thuộc

```
W0 (đăng ký §22, sổ chi) ──┬──> C0 (adapter SWE-Skills-Bench) ──> C1 (chạy thử 8) ──> C2 (Flash-Lite, đủ) ──┐
                           │                                                     └──> D1 (model 2, thử) ──> D2 (model 2) ──┤
                           ├──> B0 (F1 trên task của B) ──> B1 (10 trial đầu) ──> B2 (MemGovern, đủ) ─────────┤
                           └──> A1 (XRepoSKill: phân tích lại, 0 USD) ──────────────────────────────────────┤
Q0 (hỏi Model Garden) ─────────────> D1                                                                    v
                                                                                                    E (phân tích, viết)
```

| # | Việc | Phụ thuộc | Chi phí | Đầu ra / cổng |
| --- | --- | --- | --- | --- |
| **W0** | Đăng ký trước §22: đối tượng, n, seed, endpoint, quy tắc Gatekeeper, placebo, hoán vị, Holm, diễn giải cho từng kết quả, trần từng track | — | 0 | Commit trước mọi lần chạy có phí |
| **Q0** | Hỏi @thuthuy tình trạng Model Garden (gpt-oss-120b / Qwen3) theo L21; nếu được phép thì gọi thử 1 lần | — | dưới 0,01 USD | Model ID và giá đã xác minh |
| **A1** | XRepoSkill (E2): Gatekeeper theo scope (repo); kiểm định hoán vị; so với 6 mức công bố | — | 0 | Phần lớn đã có (§18, §21, C2) |
| **B0** | MemGovern: chọn task (phần 4); chạy lại F1 trên đúng các task này (miễn phí, GitHub Actions) | W0 | 0 | F1 đạt |
| **B1** | MemGovern: 10 trial đầu, đo chi phí (quy tắc §11e) | B0 | khoảng 1,3 USD | Dự kiến cả ô vượt trần B thì dừng và hỏi |
| **B2** | MemGovern: đủ, dùng lại nhánh không skill (`--reuse-none`) | B1 | trần 18 USD | — |
| **C0** | Adapter SWE-Skills-Bench (`scripts/sskb_adapter.py`): clone repo ở commit, `setup_commands`, chèn `SKILL.md`, mini-swe-agent trong image của họ, chấm bằng `test_command` của họ. Test; chạy thử bằng model giả lập; kiểm kéo image | W0 | 0 | Review R-42; điểm số đọc đúng |
| **C1** | 8 lần chạy thử (4 skill × 1 yêu cầu × 2 nhánh) | C0 | khoảng 0,7 USD | Lỗi hạ tầng > 1/8, hoặc chi phí > 2 lần ước tính, thì dừng |
| **C2** | Flash-Lite: 2 skill chính × 10 yêu cầu × **6 seed** × 2 nhánh, cộng 2 skill đối chứng × 10 × 3 × 2 = 360 lần chạy | C1 | trần 28 USD | Lỗi hạ tầng > 10% thì dừng |
| **D1** | Model khác hãng: thử 4 lần chạy | Q0, C0 | dưới 0,5 USD | Agent không đúng định dạng ở > 1/4 lần chạy thì dừng D |
| **D2** | Model khác hãng: 2 skill chính × 10 × 3 seed × 2 = 120 lần chạy | D1 | trần 10 USD | — |
| **E** | Phân tích (C1–C4); audit Flash/Pro trên ứng viên của `asyncio-patterns` (khoảng 1 USD, trong dự phòng); viết paper | A1, B2, C2, D2 | 0–1 USD | — |

**Thứ tự để có kết quả tích cực sớm** (trước khi gửi thầy):
1. W0 → C0 → C1 → C2, vì tác dụng lớn nên khả năng ra kết quả rõ cao nhất;
2. rồi B;
3. rồi D.

## 4. Lựa chọn thiết kế cần chốt ở W0

- **MemGovern trên task nào:**
  - **Verified** (40 task E1, dùng lại nhánh không skill 3 seed): kiểm thẳng mức họ công bố, vì cùng benchmark.
  - **Live** (task E2): thêm chiều scope (repo và thời gian mới).
  - **Đề xuất Verified**, vì so được với số của họ. Ước chi khoảng 120 lần chạy × khoảng 0,13 USD ≈ 16 USD; F1 phải chạy lại trên task E1.
- **Cách đưa skill SWE-Skills-Bench vào prompt:** chèn nội dung `SKILL.md` vào prompt, thay cho lệnh `/skill-id` của họ. Nêu đây là thay đổi scope (agent khác).
- **Hai skill đối chứng:** chọn bằng quy tắc cố định: hai skill Python có |trung bình| nhỏ nhất trong dữ liệu SWE-Skills-Bench, có đủ 40 hiệu số.

## 5. Rủi ro và cách sửa

| # | Rủi ro | Mức | Cách sửa |
| --- | --- | --- | --- |
| R1 | Adapter chấm điểm sai hoặc khác cách của họ | Cao | Chạy `test_command` trên repo **chưa sửa** để kiểm đọc điểm; chạy thử bằng model giả lập; kiểm nhánh không skill **không** chứa `SKILL.md`; test cho từng bước |
| R2 | Không đủ power để chứng nhận (30 cặp: 0,5% và 1,5%) | Cao, **đã sửa** | 6 seed cho 2 skill chính: 60 cặp, chứng nhận khoảng 83% (`viper`) và 49% (`asyncio`) theo bootstrap từ hiệu số thật. **Lỗi thời (06/11, A83):** hai con số này lấy tác dụng công bố của SSKB làm giá trị thật; §22 cho thấy trên agent của mình `viper` +1,5 điểm, `asyncio` −11,3 điểm (10 cặp), và phần chuyển giao giữa các agent chỉ có sd 1,83 điểm, nên không dùng được nữa. Báo cáo thêm kiểm định hoán vị cỡ mẫu cố định làm phân tích phụ |
| R3 | Cách đưa skill khác họ | Vừa | Đặt câu hỏi rõ: "tác dụng có chuyển sang agent khác không" là một câu hỏi về scope. Có thể thêm: cài `SKILL.md` vào container và bảo agent đọc (gần cách của họ hơn) |
| R4 | Chi phí MemGovern chưa đo (prompt dài, gọi công cụ) | Vừa | Quy tắc §11e: đo trên 10 trial đầu, vượt trần dự kiến thì dừng và hỏi |
| R5 | Model khác hãng chưa được bật hoặc không tương thích | Vừa | Q0 hỏi trước; D1 thử 4 lần. Không được thì dùng Gemini Flash (cùng hãng, đắt hơn) với số seed ít hơn, và báo cáo giới hạn |
| R6 | Image Go lớn, thiếu đĩa | Thấp–vừa | Chạy lần lượt từng skill; xóa image sau mỗi skill; kiểm đĩa trước mỗi lô |
| R7 | Nhiều phép kiểm (nhiều skill × model) | Thấp | Holm trên từng họ phép kiểm, ghi trước |
| R8 | License | Thấp | Kiểm `license` của từng `SKILL.md`. MemGovern và XRepoSkill không có LICENSE nên không phân phối lại nội dung; chỉ công bố mã và kết quả |
| R9 | Kết quả "không lặp lại" bị đọc là bài bác bỏ | Vừa | Viết theo khung scope và chứng nhận. Đối chứng dương (T4, và `asyncio` nếu lặp lại) cho thấy phương pháp không mù |
| R10 | Tác dụng lặp lại, nên phần "phụ thuộc scope" yếu | Vừa | Chấp nhận. Paper không cần scope có ảnh hưởng; nó cần đo được scope có ảnh hưởng hay không. MemGovern và XRepoSkill (mức tăng nhỏ) bổ sung chiều này |

## 6. Ngân sách

| Track | Trần |
| --- | --- |
| B MemGovern (gồm 20 USD đã duyệt ngày 04/11) | 18 + 1,3 (thử) |
| C SWE-Skills-Bench, Flash-Lite | 28 + 0,7 (thử) |
| D Model khác hãng | 10 + 0,5 (thử) |
| Dự phòng (audit, chạy lại do lỗi hạ tầng) | 1,5 |
| **Tổng** | **60 USD** |

## 7. Điểm mạnh và tính cạnh tranh (định tính; không có số để tính xác suất được nhận)

**Điểm mạnh:**
1. **Ba hệ thống đã công bố**, ba loại skill, đúng các baseline của paper gốc.
2. **Skill thật có tác dụng thật** nên có thể chứng nhận được. ~~Xác suất chứng nhận đã tính trước: khoảng 83% và 49%.~~ Lỗi thời, xem A83 và R2.
3. **Phương pháp đã kiểm sẵn:** placebo, Mệnh đề P, hoán vị (mức 0,042), Gatekeeper (T4).
4. **Nhiều model:** 4 cấu hình của SWE-Skills-Bench, cộng 2 cấu hình của mình.
5. **Kết quả nào cũng diễn giải được**, đã viết trước.

**Điểm yếu còn lại:**
- Agent và cách nạp skill khác các bài gốc (R3).
- MemGovern và SWE-Skills-Bench có ít task (40 và 10 yêu cầu mỗi skill).
- Chiều "scope = repo và phiên bản" chưa được kiểm trực tiếp với skill có tác dụng lớn, vì cần tự viết yêu cầu mới (ngoài 60 USD).

**Tính cạnh tranh theo kịch bản:**

| Kịch bản | Mức |
| --- | --- |
| Chứng nhận được ≥ 1 skill thật, tác dụng lặp lại trên 2 model, các mức tăng nhỏ không qua placebo | **Cạnh tranh tốt** |
| Tác dụng lặp lại nhưng chưa chứng nhận được | Cạnh tranh được |
| Tác dụng lớn không lặp lại trên agent của mình | Cạnh tranh được (bằng chứng scope), cần giải thích kỹ |
| Adapter không chạy được | Quay về hướng placebo (§18–§21) và MemGovern |
