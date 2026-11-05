# Rà soát 4 việc và hướng đi cho paper (bản 2, 05/11/2026; chờ @thuthuy và thầy duyệt)

**Nguồn và quy ước:**
- Bản gốc đọc lại: paper gốc, bản tóm tắt, to-do bản 2 (commit `22159ef`).
- Mọi file trong `results/`.
- Dữ liệu thô của p6 (chỉ Study T/T2; số đếm **tính lại từ từng dòng, khớp file kết quả**).
- Bản gốc tài liệu lưu ở nhánh `sources-snapshots`, lấy qua run 42017123630 và lần tải lại lúc 11:28 UTC.
- Mỗi rủi ro ở mục 4 ghi rõ **đã kiểm bằng gì** và **trạng thái**.

---

## 1. Paper gốc và kỳ vọng gốc: khả thi hay không

| Kỳ vọng gốc | Khả thi? | Bằng chứng |
| --- | --- | --- |
| Tiền đề: skill có hiệu ứng lớn, khác nhau theo ngữ cảnh; hại ở 20–58% số cặp | ❌ sai với skill mức agent | E1: Z̄ ∈ [−0,019; +0,013]. E2: +2,1 điểm [−1,0; +5,3]. SWE-Skills-Bench: "92 of 98 skills are Ineffective … 76.6% … 76.9%" |
| RQ1: nhận nhầm 11,5% → 5,1% so với replay + fingerprint, tại cùng độ phủ | ❌ trên skill agent, vì không gán được nhãn có hại. ⚠️ Phần động cơ "replay không đủ" có bằng chứng thật | Nhãn cần hơn 100 trial mỗi ô. §16: không có lợi thế khi so ở cùng độ phủ. p6 T/T2: replay + fingerprint nhận 9/11 và 17/20 ô Ruff có hại |
| RQ2: bắt 41/46 cặp ghép có hại | ❌ trên dữ liệu thật; ✅ trên plasmode và lý thuyết | T3: ghép ngây thơ 98,8%, Gatekeeper 0% |
| RQ3: regime A/B/C; B9 thử lại cùng ngân sách | ❌ | Cần nhãn hại |
| RQ4: thu hồi; điểm hòa vốn | ✅ | T2/T2b; chi phí đo được |
| Lý thuyết: admission, ghép, Prop. 9 | ✅ nếu viết gọn | Prop. 9 đo được: 3,3–4,6× (repo này) và **3,2–4,4× trên 4 cấu hình của SWE-Skills-Bench** |
| SkillShift-SE 180 cặp | ❌ | Khoảng 5.800 USD |

## 2. To-do gốc: khả thi hay không

| Phase | Trạng thái | Khả thi cho paper |
| --- | --- | --- |
| H, 0, 5a | Xong | — |
| 1: sửa lý thuyết | Mới có ghi chú | ✅ miễn phí (F1) |
| 2: môi trường, baseline | Một model; XRepoSkill, GEPA, Library Drift đã có nguồn | Model thứ hai còn mở (P2) |
| 3: pilot và go/no-go **theo power** | Đã trả lời "không đủ power" từ G1 (03/11) | Đây là dữ liệu cho hướng mới |
| 4: SkillShift-SE | ❌ | Bỏ; thay bằng plasmode trên nhiễu thật, đối chứng dương T4, dữ liệu công khai của SWE-Skills-Bench |
| 5b: Gatekeeper đầy đủ | Một phần | Chỉ giữ admission, sổ α, thu hồi |
| 6: 8 hệ thống × 2 backend | ❌ | Bỏ |
| 7: phân tích, viết | ⏳ | ✅ |

## 3. Kết quả từ giai đoạn 0 tới nay

| Mức | Kết quả | Vì sao |
| --- | --- | --- |
| **Dùng chính** | Khoảng 2.000 lần chạy ghép cặp; A/A; F(n); 7/13 mức tăng đã công bố nằm trong nhiễu | Dữ liệu nhiễu thật của **phép so có/không skill**. Các bài đã công bố chỉ đo nhiễu khi so model hoặc agent |
| **Dùng chính** | Null thật B-X2 0,026 → 0,103; P1 0,075 → 0,303; Gatekeeper ≤ 0,002; T1 | RQ2 |
| **Dùng chính** | T4: admit ở trial 20, khớp dự đoán đăng ký 21–25 | Kiểm chứng trên agent thật |
| **Dùng chính** | T2/T2b (thu hồi) | RQ4 |
| **Dùng chính** | Dữ liệu SWE-Skills-Bench: 3.920 cặp, 4 cấu hình, MIT | Bằng chứng ngoài, nhiều model |
| Dùng có giới hạn | C2, C3, §16 (kết quả âm), dư địa (thăm dò) | Động cơ; định phạm vi tuyên bố |
| Dùng có giới hạn | p6 T/T2 | Chỉ ở phần thảo luận phạm vi, trình bày riêng (định nghĩa draw khác) |
| Không dùng | G1-B, A76 rerun, ô MemGovern, kiểm "model không đổi", 2.1, p6 Study Q (trùng PatchDiff), lý thuyết p6, mock review | Lỗi, trùng, hoặc không phải bằng chứng |

## 4. Hướng đi và mọi rủi ro, mỗi rủi ro đã kiểm bằng gì

**Hướng:** *Testing a Skill Before You Install It* (kiểm tra skill trước khi cài).
- Câu hỏi của SWE-Skills-Bench, nguyên văn: "no standard procedure tests an individual skill before installation".
- Trả lời bằng ba phép đo trên dữ liệu thật:
  1. RQ1: nhiễu của phép so có/không skill;
  2. RQ2: các tiêu chí nhận và thu hồi **đã công bố** khi gặp nhiễu và bị xem nhiều lần;
  3. RQ3/RQ4: một thủ tục anytime-valid giữ được sai số, có đối chứng dương trên agent thật.
- Không tuyên bố công cụ thống kê mới.

| # | Rủi ro | Đã kiểm bằng | Kết quả | Trạng thái |
| --- | --- | --- | --- | --- |
| R1 | "Đo nhiễu đã có người làm" | Bản gốc 2602.07150, 2609.17394 | Đúng: họ đo nhiễu khi so model, agent hoặc leaderboard. Không đoạn trích nào chứa "skill", "paired", "sequential" (2602.07150) | ✅ **Xử lý:** trích họ; đóng góp của mình là nhiễu của **phép so có/không skill** và hệ quả cho việc nhận skill |
| R2 | "Xem nhiều lần làm hỏng kiểm định là kiến thức cũ" | Bản gốc gskill/GEPA, Library Drift | gskill: tiêu chí "strictly greater" trên minibatch 3, `max-metric-calls` mặc định 600. Library Drift chạy 100 vòng và tự viết "skills … are prematurely retired on unlucky draws, while genuinely harmful skills may survive early rounds" | ✅ **Xử lý:** đóng góp là **độ lớn đo được trên các tiêu chí đã công bố**, vốn được áp lặp lại theo thiết kế. Bỏ câu "người dùng hay theo dõi" vì không có nguồn |
| R3 | Trùng công cụ với Qu et al. | `anytime_referee_2026` | Họ dùng betting, FDR, ở lĩnh vực tài chính | ⚠️ Rủi ro do reviewer đánh giá. **Xử lý:** nói thẳng là áp dụng; tách các phần khác (FWER theo scope, thu hồi có xác nhận, dữ liệu coding agent) |
| R4 | Một model | `results/sskb_analysis.json` | Ghép cặp giảm phương sai 3,2–4,4× ở cả 4 cấu hình. Hiệu ứng skill gần 0 ở cả 4 (mean Z từ −0,008 tới +0,003) | ⚠️ Một phần. RQ1-pairing và RQ2 có dữ liệu 4 model. A/A chỉ có một model, cần P2 (khoảng 48 USD, @thuthuy quyết) |
| R5 | Hiệu ứng trong plasmode là giả lập | T4 | Agent thật admit ở trial 20, khớp dự đoán 21–25 | ✅ một điểm kiểm chứng. Nêu giới hạn |
| R6 | "Không chứng nhận được skill thật nào" | Dư địa (thăm dò), SWE-Skills-Bench | 48,5% số lần chạy thất bại vì "sửa đúng file nhưng sai cách sửa". SWE-Skills-Bench: 92/98 skill không có hiệu ứng có ý nghĩa thống kê | ✅ Đây là kết quả của RQ1. Phải đăng ký lại phân tích dư địa (F2) |
| R7 | §16: không có lợi thế khi so ở cùng độ phủ | `harm_coverage.json` | Đúng | ✅ **Xử lý:** chỉ tuyên bố "hợp lệ khi không có đáp án để chỉnh ngưỡng và khi bị xem nhiều lần" |
| R8 | Định lý lộn xộn (bài học của p6) | `PAPER_EXPECTATION_AUDIT.md` của p6; R12 trong to-do gốc | Ba lỗi đã biết: hệ số TV, Định lý 7, sổ α với 1/C(N, m) | ⏳ **Xử lý:** F1 chỉ 3 mệnh đề (admission theo Ville + sổ α; ghép có thứ tự; thu hồi Σα_k ≤ α). Bỏ cận dịch phân phối. Mỗi ký hiệu một nghĩa. 👤 người biết thống kê đọc |
| R9 | Endpoint "resolved" có nhiễu (A76; PASS_TO_PASS chập chờn) | T4: 4/9 task không giải được có loss trong (0; 0,01) | Nghi chập chờn | ⏳ F2: chấm lại bản vá gốc 5 lần (chỉ Docker, 0 USD); thêm độ nhạy chỉ xét FAIL_TO_PASS |
| R10 | Trộn dữ liệu p6 | Tính lại từ dữ liệu thô | Khớp. **Sửa một nhận định sai của mình:** tác hại ở các ô Ruff **không** tất định (10/20 ô T2 có tỉ lệ 0,067–0,20); smoke test bỏ sót ít vì ô có hại hiếm | ✅ **Xử lý:** chỉ ở phần thảo luận phạm vi, không gộp với dữ liệu agent |
| R11 | F8 có thể không ra điều gì mới | Bản gốc SWE-Skills-Bench (Table 4) | Kiểm định của họ là "Exact sign-flip (primary)", hợp lệ khi xem một lần. **Tính trước:** σ_S² = 0,040, n = 10, nên nửa độ rộng CI 90% khoảng 9–12 điểm tùy cấu hình | ✅ **Đổi nội dung F8:** không nói "sai", mà đo **power và tính tương đương**. Dự đoán: gần như không skill "Ineffective" nào được chứng minh là có hiệu ứng dưới ±5 điểm, nếu tính theo từng cấu hình. **Còn mở:** họ gộp 4 cấu hình (40 cặp, khoảng ±5 điểm) hay tách? Phải đọc lại bản gốc trước khi đăng ký |
| R12 | Thu hồi hai bước bị trùng | `universality_edetectors_2026` | Có thể là trường hợp riêng | ✅ Chỉ tuyên bố cách xây dựng và phép đo |
| R13 | Con số "7/13 nằm trong nhiễu" | `noise_floor_audit.json` | Nhiễu đo trên một model, ở tỉ lệ giải nền thấp hơn của họ | ✅ Đã ghi: quy tắc **có lợi cho các tuyên bố** |
| R14 | Tái lập | `raw-archive`; không tất định 21,5% | — | ✅ Công bố dữ liệu thô và mã |

## 5. To-do cuối (không có việc nào đặt cược vào giả thuyết "skill có tác dụng")

| # | Việc | Chi phí | Kết quả chắc chắn có | Phụ thuộc |
| --- | --- | --- | --- | --- |
| F0 | Đọc lại bản gốc SWE-Skills-Bench để biết họ gộp hay tách 4 cấu hình, và mức α | 0 | Có | — |
| F2 | Đăng ký §18, rồi đo: dư địa, F(n), A/A trên E1 + E2; chấm lại bản vá gốc nghi chập chờn | 0 | Có | — |
| F8 | Đăng ký §19 (power và tương đương của thủ tục kiểu SWE-Skills-Bench), rồi chạy trên dữ liệu của họ và trên plasmode | 0 | Có (đã tính trước bằng σ_S²) | F0 |
| F3 | Bảng số trial cần cho các mức tăng đã công bố | 0 | Có | F2 |
| F1 | 3 mệnh đề + 👤 người đọc | 0 | Có | — |
| F5 | Viết paper; `number_provenance`, `glossary`, `refs.bib` | 0 | Có | F1–F8 |
| P2 | *(tùy chọn)* A/A trên model thứ hai | khoảng 48 USD | Có (phép đo) | @thuthuy |

**Còn lại không xử lý được bằng dữ liệu** (phải nói thẳng):
- (a) Reviewer có thể coi đây là "áp dụng thống kê đã biết" (R3).
- (b) A/A chỉ trên một model, nếu không làm P2 (R4).
- Mức cạnh tranh (định tính):
  - không có P2: **ranh giới, nhưng cạnh tranh được**;
  - có P2: **cạnh tranh được**.
