# Rà tài liệu về tính mới (05/11/2026; bản gốc lưu ở `sources-snapshots`, id trong ngoặc)

| Công trình | Làm gì (câu gốc) | Trùng với Gatekeeper ở đâu |
| --- | --- | --- |
| Propose, Don't Judge (`anytime_referee_2026`, arXiv 2609.27051, 22/09/2026) | "a frozen statistical referee … by betting, so its false-discovery guarantee holds at every stopping time for any proposal policy". Admit bằng "online e-BH"; thu hồi bằng "an e-detector" với ngưỡng "viability threshold δ … the edge that just pays" | **Trùng phần lõi:** nhận và thu hồi các thứ do LLM agent đề xuất bằng e-process, chống dừng tùy ý và đa giả thuyết, có ngưỡng chi phí. Khác: lĩnh vực tài chính; kiểm soát FDR (không phải FWER); không có scope; không có ghép skill |
| Library Drift (`library_drift_2026`) | Thu hồi skill theo kết quả, với "Evidence floor N_min … 100" và cận Hoeffding (ε ≈ 0,20) | Trùng phần thu hồi skill cho coding agent; quy tắc cỡ mẫu cố định, không anytime-valid |
| HDSO (`hdso_2026`) | "a skill is not accepted because it sounds plausible, but because a falsifiable hypothesis survives prospective validation" | Trùng ý tưởng nhận skill bằng kiểm định ghép cặp; không có bảo đảm sai số hình thức |
| EvoUndo (`evoundo_2026`) | Cổng nhận đột biến của harness dựa trên tập phát triển và tập giữ lại; tỉ lệ dương tính giả quan sát được | Cổng nhận có tỉ lệ sai đo được, không có bảo đảm |
| CELEUS (`celeus_2026`); Efficient Sequential Evaluation (`seq_eval_llm_2026`) | Đánh giá LLM có chứng nhận bằng e-process | Trùng phần "chi phí chứng nhận / đánh giá tuần tự" |
| Online FWER / alpha-spending (Tian & Ramdas 2021, qua tài liệu onlineFDR) | Phiên bản online của Bonferroni | Trùng phần sổ α |

**Còn lại có vẻ mới (phải kiểm thêm khi viết bài):**
1. FWER (không phải FDR) cho cả thư viện skill, theo từng (skill, scope).
2. Bảo đảm cho skill ghép (Định lý 4′, hệ số TV).
3. Đo trên khoảng 2.000 lần chạy ghép cặp của coding agent thật, kèm so sánh trực tiếp với các quy tắc đã công bố ở trên.

## Thu hồi hai bước (§15): rà tính mới (05/11/2026)

- **Universality of e-detectors** (`universality_edetectors_2026`): bài lý thuyết. Có các phụ lục "Residual criteria and restartable detector fields", "Repeated alarms and counting e-detectors", "Local-window control". Cách hai bước của mình (báo động, cách ly, xác nhận với α chia nhỏ, dùng lại) rất có thể là **một trường hợp riêng** của khung này.
  → **Không** tuyên bố tính mới về lý thuyết.
  → Đóng góp, nếu có, là **cách xây dựng cụ thể cho việc thu hồi skill**, cùng phép đo đánh đổi trên lần chạy agent thật, so với e-SR (Qu et al.) và Library Drift.
- **Sequential Control of False Positives in Online CPD** (`seq_fp_cpd_2026`): hiệu chỉnh ngưỡng bằng mô phỏng, FWER theo cửa sổ thời gian, dữ liệu điện thoại. Khác lĩnh vực; không có bước xác nhận.
