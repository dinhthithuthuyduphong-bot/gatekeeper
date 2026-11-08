# Chuỗi luận điểm của paper (05/11/2026): mọi số liệu đều có trong `results/`

| # | Luận điểm | Bằng chứng (file) | Số liệu chính | Loại bằng chứng | Giới hạn phải nêu |
| --- | --- | --- | --- | --- | --- |
| C1 | Tác dụng của skill cho coding agent thường rất nhỏ, ở cả skill tự viết lẫn skill của hệ thống đã công bố | `e1_final.json`, `e2_final.json`; SWE-Skills-Bench (`sskb_paper`) | E1: Z̄ ∈ [−0,019; +0,013], mọi CI chứa 0. E2: mức tăng +2,1 điểm, CI [−1,0; +5,3]. A/A sạch (p = 0,82; 0,75) | Đăng ký trước, xác nhận | Một model (Gemini 3.1 Flash-Lite), một harness |
| C2 | Mức tăng mà XRepoSkill công bố không chuyển sang được các repo mới trong thiết lập này | `xreposkill_replication.json` | Sau Holm, bác bỏ 4/6 mức tăng họ công bố (+6,2 tới +12,4 điểm, mọi p ≤ 0,0052). **Không** bác bỏ được mức nhỏ nhất +4,0 (p = 0,12) | Phân tích thêm sau khi có kết quả; quy tắc SESOI ghi trước khi đọc bảng của họ | Khác model, khác benchmark; không kết luận "kết quả của họ sai" |
| C3 | Cổng ngây thơ nhận nhầm trên dữ liệu thật | `rq1_mini.json`; `plasmode_extra.json` P3 | E1: plug-in admit 2/6 ô, Gatekeeper 0/6. SWE-Skills-Bench: trong các ô do plug-in hay GEPA chọn, 43–44% có hại trên dữ liệu giữ lại, **so với tỉ lệ nền 38,5% (151/392) khi chọn hết**; hiệu ứng trên dữ liệu giữ lại không khác chọn ngẫu nhiên (CI chồng lên nhau) | E1 đăng ký trước; P3 thăm dò | Nhãn trên các ô thật chưa được xác lập bằng kiểm định |
| C4 | Gatekeeper giữ đúng mức sai và vẫn mở khi skill có ích (nhiễu thật, đáp án biết trước) | `plasmode_real.json` | FWER 0,000 (mức 0,025). Độ phủ 0,58 (109 trial) và 0,78 (200 trial); δ = 0,3 được admit 98% | Plasmode đăng ký trước | Cơ chế hiệu ứng được cấy là giả lập |
| C5 | Theo dõi liên tục phá vỡ cổng cỡ mẫu cố định, nhưng không phá được Gatekeeper | `plasmode_extra.json` P1 | Thống kê của XRepoSkill: FWER 0,075 → 0,343. Plug-in/GEPA: 0,997. Gatekeeper: 0,000 | Plasmode đăng ký trước | Như C4 |
| C6 | Với hiệu ứng ở mức thực tế, không quy tắc hợp lệ nào chứng nhận được với ≤ 200 trial; cổng ngây thơ thì nhận khoảng 10–12 ô có hại hoặc vô dụng trên 100 ô | `plasmode_extra.json` P2 | Trên 100 ô: Gatekeeper 0 ô có hại hoặc trung tính, 0,2 ô có ích; B-X2 0,5 / 7,0; plug-in 11,6 / 36,4 | Plasmode đăng ký trước | Thang đo của SWE-Skills-Bench khác thang "resolved" |
| C7 | Độ vững của C2 | `e2_final.json` (`hypothetical`) | Bỏ các trial bị cắt ngang (truncated): mức tăng +1,4 điểm, CI [−2,3; +5,2]; cận trên gần như không đổi | Độ nhạy đã đăng ký | — |

**Không thể kiểm từ bài gốc:** mức tăng của XRepoSkill trên riêng các task Python so với "không skill". Table 2 của họ chỉ so với STAIR và Trace2Skill.

## Sửa sau khi rà tính trung thực (05/11/2026)

1. **C4:** FWER cao của B-X2 ở một lần nhìn (0,065–0,075) một phần là do **không hiệu chỉnh đa giả thuyết**, chứ không chỉ do thống kê của nó. Một kiểm định cỡ mẫu cố định có hiệu chỉnh Bonferroni có thể giữ được FWER ở một lần nhìn. Vì vậy không được trình bày C4 là "B-X2 sai". Lợi thế riêng của Gatekeeper là **C5**: cùng quy tắc B-X2, chỉ đổi số lần nhìn, FWER tăng từ 0,075 lên 0,343.
2. **C3:** phải nêu tỉ lệ nền 38,5% bên cạnh con số 43–44%.
3. **Ghi chú thực thi 1 của §9:** cách ước lượng được chọn khi viết mã, nhưng chỉ được ghi lại **sau khi** đã thấy kết quả. Lời ghi cũ ("trước khi đọc kết quả P2") không chính xác và đã được sửa.
4. **FWER 0 của Gatekeeper trong plasmode:** với 1.000 lần lặp, cận trên khoảng tin cậy 95% của FWER là khoảng 0,003 (quy tắc 3/n), không phải đúng bằng 0.

## C8. Mức nhiễu nền và đối chiếu (bản đăng ký §12, đăng ký trước khi đối chiếu; `results/noise_floor_audit.json`)

- **Ngưỡng nhiễu F(n)** (chỉ do chạy lại, phân vị 97,5%, lấy từ 257 task thật): 8,0 điểm (n = 113), 6,0 điểm (n = 200), 3,8 điểm (n = 500).
- **7/13 mức tăng đã công bố nằm trong mức nhiễu này:**
  - XRepoSkill: 3/6 (Pro/DeepSeek +4,0; Pro/GPT +5,5; DeepSWE/MiMo +6,2);
  - MemGovern: 4/7 (+2,4; +3,0; +3,2; +3,2).
- **6/13 vượt mức nhiễu:** XRepoSkill +8,5 / +12,4 / +12,4; MemGovern +8,0 / +8,2 / +9,4.
- **Bằng chứng từ chính bài XRepoSkill:** Pass@4 89,4% và All@4 32,7%, tức 56,7% số task cho kết quả khác nhau giữa 4 lần chạy của họ.
- **Giới hạn:** nhiễu đo trên một model với tỉ lệ nền 0,37. Ở tỉ lệ gần 0,5 phương sai lớn hơn, nên F(n) của mình có thể thấp hơn nhiễu thật của họ. Quy tắc này vì vậy **có lợi cho các tuyên bố**. "Nằm trong nhiễu" không có nghĩa là "không có tác dụng": nó chỉ có nghĩa là một lần chạy không đủ để phân biệt với việc chạy lại.

## Sửa theo A76 (05/11/2026): chạy lại với định nghĩa đã đăng ký (loss = 0); tỉ lệ giải nền 0,27

| | Trước | Sau |
| --- | --- | --- |
| C4, 109 trial | Gatekeeper FWER 0,000, độ phủ 0,58 | FWER 0,000, độ phủ 0,59; δ = 0,3 được admit 99% |
| C4, 200 trial | FWER 0,000, độ phủ 0,78 | FWER 0,002, độ phủ 0,80 |
| C4, B-X2 ở một lần nhìn | 0,065–0,075 | 0,082–0,089 |
| C5 | B-X2 0,343; Gatekeeper 0,000 | B-X2 **0,303**; Gatekeeper **0,002** |
| C6, 109 trial, trên 100 ô (có hại hoặc trung tính / có ích) | plug-in 11,6 / 36,4; Gatekeeper 0 / 0,2 | plug-in **10,5 / 38,6**; Gatekeeper **0 / 0,1** |
| C8 | F = 8,0 / 6,0 / 3,8 điểm; 6/13 vượt mức nhiễu | F = **7,1 / 5,5 / 3,4** điểm; **6/13** vượt mức nhiễu (Pro/GPT +5,5 đúng bằng F) |

## Rà tính trung thực của luận điểm bác bỏ (05/11/2026)

1. **B-X2 là cổng do ta dựng.** XRepoSkill không dùng thống kê của họ làm cổng; câu gốc: "The gain and z score are not used as thresholds for retaining rules". Bác bỏ B-X2 **không** bác bỏ thực hành của XRepoSkill. Thực hành thật của họ là không có cổng (B-X1), và họ không tuyên bố kiểm soát sai số.
2. **Tiêu chí của GEPA không được thiết kế để kiểm soát sai số.** Nó dùng để nhận ứng viên trong vòng tối ưu, trên minibatch 3 task. Việc nó nhận nhầm ở ô trung tính là điều dễ đoán, nên chỉ được trình bày như vậy. Điểm có nguồn: vòng tối ưu của gskill áp tiêu chí này **lặp lại nhiều lần** (`max_metric_calls` mặc định 600, minibatch 3). Đó là một trường hợp đã công bố của việc áp một tiêu chí nhiều lần.
3. **"Kiểm định một lần nhìn sai khi bị nhìn nhiều lần" là kiến thức thống kê đã biết,** không phải phát hiện của paper. Đóng góp chỉ là đo mức độ trên lần chạy agent thật (0,026 tăng lên 0,103).
4. **Câu "người dùng theo dõi kết quả, như cách vẫn làm trong thực tế" không có nguồn.** Bỏ câu này, hoặc tìm nguồn trước khi dùng.
5. **Kết luận:** các con số của luận điểm bác bỏ là đúng, nhưng giá trị của nó là **động cơ và minh họa**, không phải đóng góp chính.

## Phát hiện từ T4, mục 1.4 (05/11/2026; thăm dò)

- Ở nhánh có gợi ý bản vá, 7/17 task không được tính là giải được. Trong đó **4/7 có loss trong (0; 0,01)**.
- Ví dụ conan-15705: bản agent nộp **giống hệt** bản vá gốc mà vẫn không được tính là giải được.
- Giả thuyết: một số test PASS_TO_PASS chập chờn hoặc nhạy với môi trường, nên endpoint "resolved" (đòi mọi PASS_TO_PASS phải qua) có nhiễu đo.
- **Cần kiểm (miễn phí):** chấm lại bản vá gốc của các task này nhiều lần; tính lại với endpoint chỉ xét FAIL_TO_PASS làm phân tích độ nhạy.
- Đưa vào phần threats to validity.

## Phân loại luận điểm: xác nhận và thăm dò; điều chỉnh (06/11/2026)

**Vì sao:** reviewer sẽ hỏi luận điểm nào đã đăng ký trước. Paper chia phần kết quả thành hai tiểu mục: **Pre-registered confirmatory** và **Exploratory**. Luận điểm thăm dò không được dùng làm đóng góp chính.

| Luận điểm | Loại | Neo đăng ký | Vai trò trong paper |
| --- | --- | --- | --- |
| C1 (E1, E2 null) | Xác nhận | `preregistration_e1.md`, `_e2.md` | Chính. §26m: vững với lỗi bộ chấm (F, B không đổi kết luận) |
| C2 (XRepoSkill: bác bỏ 4/6) | Thăm dò; quy tắc SESOI ghi trước khi đọc bảng của họ | §10 | Phụ, ghi rõ là phân tích thêm |
| C3 (cổng ngây thơ nhận nhầm trên dữ liệu thật) | E1 đăng ký trước; phần SSKB thăm dò | §9 | **Hạ xuống ghi chú** trong phần thảo luận A/A. Lý do: 43–44% so với nền 38,5%, CI chồng nhau |
| C4–C6 (plasmode) | Xác nhận (plasmode) | §9, §14 | Chính, kèm giới hạn "hiệu ứng được cấy là giả lập" |
| C7 (độ nhạy truncation) | Độ nhạy đã đăng ký | `_e2.md` | Phụ |
| C8 (7/13 mức tăng nằm trong nhiễu chạy lại) | Xác nhận | §12 | Chính |
| §18 (placebo cho quy lỗi) | Xác nhận | §18 | Chính |
| §19 (bảng placebo cho quy tắc đã công bố) | Xác nhận | §19 | Chính |
| §20 S3 (đối chứng dương phía "giúp") | Xác nhận | §20 | Chính |
| §20 S4 (cơ chế đổ lỗi) | Thăm dò | §20 | Phụ |
| §21 (hoán vị chính xác; bootstrap theo task) | Xác nhận | §21 | Chính |
| §13 (ô trung tính) | Thăm dò, làm sau khi thấy dữ liệu | §13 | Phụ |
| §22, §23a (SSKB trên Flash-Lite và Pro) | Đăng ký trước, n nhỏ | §22, §23 | **Nghiên cứu tình huống mô tả**, không phải kiểm định: tác dụng công bố không xuất hiện; trên Pro, 8/8 cặp giống hệt (hiệu ứng trần) |
| §23b (Flash) | Dừng theo cổng chi phí | §23 | Chỉ nêu ở phần chi phí |
| §26m (kiểm bộ chấm) | Độ nhạy đã đăng ký | §26m | Threats to validity; T4 bị S đo thấp khoảng 0,10 |

**Threats to validity, thêm từ §26m:**
- Endpoint resolved đòi mọi PASS_TO_PASS qua. Một số test hỏng do môi trường của mình, ví dụ `conan-15705`: FAIL_TO_PASS 1/1 qua, PASS_TO_PASS 5/3.650 trượt.
- Lỗi này làm task không giải được ở **cả hai nhánh**. Nó pha loãng tác dụng nhưng không tạo ra tác dụng.
- Kết luận của E1 và E2 không đổi khi chỉ xét FAIL_TO_PASS (F) hoặc khi bỏ test hỏng (B).
- Kết quả chấm lại bản vá gốc 3 lần: `results/harness_gold.json`. Số liệu sẽ được ghi vào đây khi xong.
