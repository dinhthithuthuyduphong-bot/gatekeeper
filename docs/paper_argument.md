# Chuỗi luận điểm của paper (05/11/2026): mọi số liệu đều có trong `results/`

| # | Luận điểm | Bằng chứng (file) | Số liệu chính | Loại bằng chứng | Giới hạn phải nêu |
| --- | --- | --- | --- | --- | --- |
| C1 | Tác dụng của skill cho coding agent thường rất nhỏ, ở cả skill tự viết lẫn skill của hệ thống đã công bố | `e1_final.json`, `e2_final.json`; SWE-Skills-Bench (`sskb_paper`) | E1: Z̄ ∈ [−0,019; +0,013], mọi CI chứa 0. E2: mức tăng +2,1 điểm, CI [−1,0; +5,3]. A/A sạch (p = 0,82; 0,75) | Đăng ký trước, xác nhận | Một model (Gemini 3.1 Flash-Lite), một harness |
| C2 | Mức tăng mà XRepoSkill công bố không chuyển sang được các repo mới trong thiết lập này | `xreposkill_replication.json` | Sau Holm, bác bỏ 4/6 mức tăng họ công bố (+6,2 tới +12,4 điểm, mọi p ≤ 0,0052). **Không** bác bỏ được mức nhỏ nhất +4,0 (p = 0,12) | Phân tích thêm sau khi có kết quả; quy tắc SESOI ghi trước khi đọc bảng của họ | Khác model, khác benchmark; không kết luận "kết quả của họ sai" |
| C3 | Cổng ngây thơ nhận nhầm trên dữ liệu thật | `rq1_mini.json`; `plasmode_extra.json` P3 | E1: plug-in admit 2/6 ô, Gatekeeper 0/6. SWE-Skills-Bench: các ô do plug-in hay GEPA chọn có 43–44% là có hại trên dữ liệu giữ lại; hiệu ứng của chúng không khác chọn ngẫu nhiên | E1 đăng ký trước; P3 thăm dò | Nhãn trên các ô thật chưa được xác lập bằng kiểm định |
| C4 | Gatekeeper giữ đúng mức sai và vẫn mở khi skill có ích (nhiễu thật, đáp án biết trước) | `plasmode_real.json` | FWER 0,000 (mức 0,025). Độ phủ 0,58 (109 trial) và 0,78 (200 trial); δ = 0,3 được admit 98% | Plasmode đăng ký trước | Cơ chế hiệu ứng được cấy là giả lập |
| C5 | Theo dõi liên tục phá vỡ cổng cỡ mẫu cố định, nhưng không phá được Gatekeeper | `plasmode_extra.json` P1 | Thống kê của XRepoSkill: FWER 0,075 → 0,343. Plug-in/GEPA: 0,997. Gatekeeper: 0,000 | Plasmode đăng ký trước | Như C4 |
| C6 | Với hiệu ứng ở mức thực tế, không quy tắc hợp lệ nào chứng nhận được với ≤ 200 trial; cổng ngây thơ thì nhận khoảng 10–12 ô có hại hoặc vô dụng trên 100 ô | `plasmode_extra.json` P2 | Trên 100 ô: Gatekeeper 0 ô có hại hoặc trung tính, 0,2 ô có ích; B-X2 0,5 / 7,0; plug-in 11,6 / 36,4 | Plasmode đăng ký trước | Thang đo của SWE-Skills-Bench khác thang "resolved" |
| C7 | Độ vững của C2 | `e2_final.json` (`hypothetical`) | Bỏ các trial bị cắt ngang (truncated): mức tăng +1,4 điểm, CI [−2,3; +5,2]; cận trên gần như không đổi | Độ nhạy đã đăng ký | — |

**Không thể kiểm từ bài gốc:** mức tăng của XRepoSkill trên riêng các task Python so với "không skill". Table 2 của họ chỉ so với STAIR và Trace2Skill.
