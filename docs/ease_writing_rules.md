# Quy tắc viết bài cho EASE 2027 (chuẩn mực bắt buộc khi sửa `paper/`)

Lập ngày 25/11/2026 (R-98) theo yêu cầu của @thuthuy: "tìm tất cả thông báo liên quan tới EASE và đọc sau đó tạo thành 1 rule chuẩn mực để follow viết report".

**Cách dùng.** Trước mỗi lần sửa `paper/main.tex` và trước khi nộp: đọc lại bảng §9 và chạy hai lệnh sau.

- `python scripts/preflight.py` chạy kiểm tra [ease], phần kiểm được trên mã nguồn.
- `python scripts/ease_pdf_check.py paper/main.pdf` kiểm phần chỉ đo được trên PDF.

Một quy tắc mới, hay một quy tắc bị vi phạm, được ghi vào bảng §9 trong cùng commit.

**Nguồn.** Mọi câu trích dưới đây là nguyên văn từ bản gốc. Các bản gốc được tải bằng workflow `sources` và lưu trên nhánh `sources-snapshots`; khóa nguồn nằm trong `configs/sources.json`. Không có quy tắc nào lấy từ trí nhớ hay từ một bài review do AI viết. Bài review chỉ được dùng để tìm chỗ cần kiểm, rồi đối chiếu với nguồn.

| Khóa nguồn | Nội dung |
| --- | --- |
| `ease_2027_research_cfp` | Call for Papers, track Research Papers của EASE 2027 (track ta nộp) |
| `ease_2027_home` | Trang chủ EASE 2027 |
| `ease_2027_rnr_track` | Track Reproducibility and Negative Results. Không phải track ta nộp, nhưng cùng hội nghị và nêu rõ hơn yêu cầu tái lập với nghiên cứu dùng LLM |
| `sigsoft_open_science_policy` | Chính sách Open Science của SIGSOFT, được CFP dẫn tới |
| `sigsoft_general_standard` | Chuẩn chung của ACM SIGSOFT Empirical Standards |
| `sigsoft_benchmarking_standard` | Chuẩn Benchmarking |
| `sigsoft_metascience_standard` | Chuẩn Methodological Guidelines and Meta-Science |
| `sigsoft_simulation_standard` | Chuẩn Simulation (Quantitative) |
| `sigsoft_open_science_supplement` | Phụ lục Open Science |
| `sigsoft_infovis_supplement` | Phụ lục Information Visualization |
| `sigsoft_irr_supplement` | Phụ lục Inter-Rater Reliability and Agreement |
| `sigsoft_registered_reports_supplement` | Phụ lục Registered Reports |
| `acm_authorship_ai_policy` | Chính sách ACM về tác giả và AI. **Bản gốc trả về 403** (cả `acm_publications_faq`) |
| `sigcse_2027_ai_policy` | Trang của SIGCSE TS 2027 (một hội nghị ACM), **trích nguyên văn** chính sách ACM hiện hành. Đây là nguồn thứ cấp cho E-AI1 |
| `sigchi_acm_ai_policy_guidance` | Blog SIGCHI (07/2023) về bản chính sách cũ hơn. Chỉ dùng để thấy chính sách đã đổi |
| `disclose_data_dbr_howto` | Hướng dẫn mà chính sách Open Science dẫn tới: chia sẻ hiện vật cho review ẩn danh, rồi mở khi bài được nhận |
| `continuous_skill_eval_2026` | Bài cùng chủ đề trình bày theo mẫu ACM. Là nguồn bên thứ ba cho tên khái niệm CCS, vì trang CCS của ACM (`acm_ccs2012`) trả về 403 |

**Chuẩn nào áp dụng.** Mỗi chuẩn tự nêu phạm vi của nó trong mục "Application". Ta xét bài theo đúng câu đó, không theo cảm nhận.

- **General Standard: áp dụng.** "applies to all software engineering studies that collect and analyze data".
- **Benchmarking: áp dụng.** Chuẩn này dành cho nghiên cứu "investigates software systems within a defined context with an automated, repeatable procedure" và "studies the software system's quality of service under a specific workload or usage profile". Agent cộng skill chạy trên bộ task SWE-smith khớp với mô tả đó.
- **Meta-Science: áp dụng.** Chuẩn dành cho bài "provide analysis of one or more methodological issues, or advice concerning some aspect of research", và nêu "may simultaneously be a methodology paper and an empirical study". Bài khớp ở hai chỗ: mục "What is certified" và các khuyến nghị đánh giá skill.
- **Simulation: áp dụng cho các kiểm tra phương pháp bằng mô phỏng.** Phạm vi của chuẩn là "studies that use simulation to understand, assess or improve a system or process".
- **Experiments (with Human Participants): không áp dụng.** Không có người tham gia. Chuẩn Benchmarking viết: "For experiments with human participants, see the Experiments (with Human Participants) Standard".
- **Phụ lục IRR: áp dụng cho X3′.** Phạm vi là "studies in which one or more human raters ... rate ... one or more properties of one or more research objects". Ở X3′, tác giả gán nhãn trace.
- **Phụ lục Registered Reports: chỉ dùng phần RR2 làm tham chiếu.** Bài không nộp theo hình thức registered report hai pha. Tuy vậy, bài có bản đăng ký trước, nên các mục RR2 về sai lệch và phân tích post hoc là chuẩn hợp lý để reviewer đối chiếu.

---

## 1. Định dạng và nộp bài (E-F)

| Mã | Quy tắc | Nguyên văn | Nguồn | Kiểm |
| --- | --- | --- | --- | --- |
| E-F1 | Nộp file PDF qua EasyChair | "All papers must be submitted in PDF format through the web-based submission system EasyChair" | `ease_2027_research_cfp` | người |
| E-F2 | Tối đa 10 trang cho phần chính, **tính cả hình, bảng và phụ lục**; thêm tối đa 2 trang **chỉ chứa** tài liệu tham khảo | "Submissions must not exceed 10 pages for the main text, including all figures, tables, appendices, etc. Up to two additional pages containing ONLY references are permitted." | `ease_2027_research_cfp` | `ease_pdf_check.py` |
| E-F3 | Dùng ACM Primary Article Template; lệch định dạng có thể bị loại ngay từ vòng đầu | "All submissions should use the official ACM Primary Article Template. Deviating from the ACM formatting instructions may lead to a desk rejection." | `ease_2027_research_cfp` | preflight [ease] |
| E-F4 | Dòng `\documentclass` phải đúng nguyên văn | "\documentclass[sigconf,review,anonymous]{acmart}" | `ease_2027_research_cfp` | preflight [ease] |
| E-F5 | Dòng `\acmConference` phải đúng nguyên văn; `--` trong LaTeX in ra dấu "–" | "\acmConference[EASE 2027]{The 31st International Conference on Evaluation and Assessment in Software Engineering}{15–18 June, 2027}{Hanoi, Vietnam}" | `ease_2027_research_cfp` | preflight [ease] |
| E-F6 | Hạn nộp, giờ AoE (UTC−12): tóm tắt 15/01/2027, bài 22/01/2027; thông báo kết quả 12/03/2027 | "Abstract Submission deadline: 15 January 2027, AoE Submission deadline: 22 January 2027, AoE Notification: 12 March 2027, AoE" | `ease_2027_research_cfp` | người (lịch) |
| E-F7 | Nếu bài được nhận, ít nhất một tác giả phải đăng ký và trình bày | "at least one author of the paper is required to register for the conference and present the paper" | `ease_2027_research_cfp` | @thuthuy |
| E-F9 | Không còn cảnh báo nào của acmart gọi một phần tử là "mandatory" (ACM reference format, CCS concepts, keywords). Không tắt các phần tử mặc định của mẫu (`printacmref=false`, `\setcopyright{none}`). Mỗi hình có `\Description` | acmart: "CCS concepts are mandatory for papers over two pages", "ACM reference format is mandatory for papers over one page", "Some images may lack descriptions" | `acmart.cls` (TeX Live) | `ease_pdf_check.py` đọc log |
| E-F8 | Bài được nhận xuất bản open access trong ICPS và có thể phải trả APC | "this may require payment of an ACM Article Processing Charge (APC)" | `ease_2027_research_cfp` | @thuthuy |

CFP **không** nhắc tới vòng rebuttal hay tỉ lệ nhận bài. Một review nói có các thứ đó là sai so với nguồn (R-97).

## 2. Ẩn danh hai chiều (E-A)

| Mã | Quy tắc | Nguyên văn | Nguồn | Kiểm |
| --- | --- | --- | --- | --- |
| E-A1 | Không có tên hay đơn vị của tác giả | "Do not include author names or affiliations in submissions." | `ease_2027_research_cfp` | preflight [ease]: không có `\author`, `\affiliation`, `\email`, `acks`; không có tên chủ repo. `ease_pdf_check.py`: metadata Author của PDF rỗng |
| E-A2 | Nhắc tới công trình cũ của chính mình ở ngôi thứ ba | "All references to the author's prior work should be in the third person." | `ease_2027_research_cfp` | preflight [ease]: chặn các cụm như "our previous work", "our prior work", "our earlier paper" |
| E-A3 | Gói tái lập và tài liệu bổ sung cũng phải ẩn danh | "Any online supplements, replication packages, etc., referred to in the work should also be anonymized." | `ease_2027_research_cfp` | preflight [ease]: không có URL chứa tên chủ repo; gói thì dựng bằng `scripts/build_replication_package.py` và quét bằng `scripts/check_anonymity.py` (A4) |
| E-A4 | Cách chia sẻ ẩn danh: chuẩn bị bản ẩn danh cho vòng review, rồi công bố bản mở khi bài được nhận | "A step-by-step approach to disclosing artifacts for (double-blind) peer review and make it open data upon acceptance is available at: https://github.com/dgraziotin/disclose-data-dbr-first-then-opendata" | `sigsoft_open_science_policy` | @thuthuy (Q6) |

Hệ quả cho cách viết: không viết "the author" ở số ít, vì như vậy lộ số tác giả. Dùng "an author" hoặc "the authors".

## 3. Open Science (E-O)

| Mã | Quy tắc | Nguyên văn | Nguồn | Kiểm |
| --- | --- | --- | --- | --- |
| E-O1 | Tuân thủ chính sách Open Science của SIGSOFT | "Authors must comply with the SIGSOFT Open Science Policy." | `ease_2027_research_cfp` | các mục dưới |
| E-O2 | Có mục **Data Availability** đặt **sau** Conclusion | "We ask authors to provide a supporting statement on the data availability (or lack thereof) in their submitted papers in a section named _Data Availability_ after the _Conclusion_ section." | `sigsoft_open_science_policy` | preflight [ease] |
| E-O3 | Lưu trữ trên kho có bảo tồn. GitHub không được coi là lưu trữ | "Archived on preserved digital repositories such as zenodo.org, figshare.com, www.softwareheritage.org, osf.io, or institutional repositories." và "GitHub, GitLab, and similar services for version control systems do not offer properly archived and preserved data." | `sigsoft_open_science_policy` | @thuthuy (Q6) |
| E-O4 | Giấy phép mở cho dữ liệu, ví dụ CC0 hay CC-BY 4.0; mã nguồn dùng giấy phép nguồn mở | "Released under a proper open data license such as the CC0 dedication or the CC-BY 4.0 license" và "Software can be released under an open source license." | `sigsoft_open_science_policy` | @thuthuy (chọn giấy phép) |
| E-O5 | Phần nào không công bố được thì nói rõ lý do | "Authors who cannot disclose data for the reasons stated in the principles of the policies should provide a short statement" | `sigsoft_open_science_policy` | người |
| E-O6 | Việc công bố là khuyến khích, không phải điều kiện nhận bài | "all submissions will undergo the same review process independent of whether they disclose their analysis code or data" | `sigsoft_open_science_policy` | (thông tin) |
| E-O7 | Với nghiên cứu dùng LLM, báo phiên bản model và công cụ, prompt, seed và các nguồn không tất định, cùng gói tái lập có liên kết lưu trữ lâu dài. Đây là danh sách của track RNR; ta dùng làm chuẩn tối thiểu vì nó cụ thể hơn CFP | "and tool versions Prompts and relevant interaction information for LLM-based studies Random seeds and other sources of nondeterminism Replication packages and persistent archival links" | `ease_2027_rnr_track` | người |
| E-O8 | Hiện vật bị hạn chế công bố: nêu rõ hạn chế và cung cấp thông tin thay thế | "Where artifacts cannot be publicly released because of licensing, privacy, security, proprietary, or other legitimate restrictions, authors should clearly explain the limitation and provide as much alternative information as possible to support verification." | `ease_2027_rnr_track` | người |

## 4. Nội dung do AI tạo (E-AI)

| Mã | Quy tắc | Nguyên văn | Nguồn | Kiểm |
| --- | --- | --- | --- | --- |
| E-AI1 | Theo chính sách của ACM về tác giả | "Concerning AI Generated content, authors should adopt the ACM Policy: https://www.acm.org/publications/policies/new-acm-policy-on-authorship" | `ease_2027_research_cfp` | người |
| E-AI1a | AI dùng để **làm nghiên cứu** (viết mã, chạy mô phỏng, phân tích dữ liệu, kiểm thử, lưu trữ mã và dữ liệu, tạo hình) phải được mô tả chi tiết **trong phần phương pháp** | "When using Artificial Intelligence to conduct research, including ... coding, implementing models, running simulations, data analysis, testing, validating results, deploying software, archiving data and code for reproducibility ... the specific use(s) of AI tools must be described in detail in the methods section of the Work. This includes the creation of artifacts that are directly relevant to the conclusions of the research, such as code, datasets, and charts or figures that rely on the AI tools." | `sigcse_2027_ai_policy` (trích chính sách ACM) | người: đoạn "AI tools used in this research" ở mục Setting |
| E-AI1b | AI hỗ trợ **viết** không còn bắt buộc khai báo. Ta vẫn khai báo, vì việc đó không bị trừ điểm dưới bản chính sách nào | "When using Artificial Intelligence to assist with writing an ACM submission, ACM no longer requires the disclosure of information regarding the use of AI" | như trên | người |
| E-AI1c | Mọi tác giả chịu trách nhiệm về nội dung, bất kể nguồn gốc; ACM có quyền từ chối bài | "All named authors on an ACM submission will be held responsible and accountable for any problematic content contained in the submission regardless of the source of that problematic content" | như trên | người |
| E-AI2 | Khai báo phù hợp về nội dung do AI tạo hay hỗ trợ; tác giả chịu trách nhiệm về độ chính xác và tính nguyên bản | "Appropriate disclosure of any AI-generated or AI-assisted content" | `ease_2027_rnr_track` | người: mục "Use of AI Tools" |

Bản gốc của ACM vẫn bị chặn (403). Câu trích ở E-AI1a đến E-AI1c lấy từ trang của một hội nghị ACM khác, nơi chính sách được trích nguyên văn. Blog SIGCHI năm 2023 mô tả bản cũ, bắt buộc khai báo cả việc AI hỗ trợ viết. Cách viết hiện tại của bài đúng với cả hai bản: mô tả việc AI làm trong nghiên cứu ở phần phương pháp, và khai báo luôn việc hỗ trợ viết. Bài nêu tên công cụ (Claude Code). Tên model hay phiên bản của các agent được nghiên cứu chỉ ghi trong gói tái lập, theo quy tắc của repo.

## 5. Tiêu chí reviewer chấm (E-C)

CFP viết: "The reviewers will be encouraged to do a standards-based review." Ngoài các chuẩn, reviewer chấm năm tiêu chí sau. Ta chuyển mỗi tiêu chí thành một điều phải làm được, kiểm bằng người.

| Mã | Tiêu chí (nguyên văn) | Điều bài phải làm được |
| --- | --- | --- |
| E-C1 | "Soundness: The extent to which the paper's contributions and innovations address its research questions and are supported by rigorous application of appropriate research methods" | Mỗi đóng góp ở phần mở đầu trỏ tới đúng mục và đúng phép kiểm hỗ trợ nó. Không có đóng góp nào chỉ dựa trên phân tích post hoc mà không được ghi là thăm dò |
| E-C2 | "Significance: ... and under which assumptions (if any)" | Nêu giả định mà ý nghĩa của kết quả phụ thuộc vào, ví dụ Assumption 1 và bộ task kiểu SWE-smith |
| E-C3 | "Novelty: ... sufficiently original with respect to the state-of-the-art" | Nói rõ cái gì đã được công bố trước (rò rỉ lịch sử git) và cái gì là mới (learner biến rò rỉ thành lời khuyên, và phần gain phụ thuộc vào nó) |
| E-C4 | "Verifiability and Transparency: ... how data was obtained, analyzed, and interpreted, and how the paper supports independent verification or replication" | Mọi con số sinh bằng script; gói tái lập; ghi rõ cái gì đã đăng ký và cái gì là post hoc |
| E-C5 | "Presentation: ... absence of significant ambiguity, clearly readable figures and tables, and adherence to the formatting instructions provided above" | §1, §8, và [terms] của preflight |

## 6. Chuẩn chung, General Standard (E-G)

Chỉ liệt kê các mục **Essential**. Thiếu một mục Essential là một lỗi phải sửa. Các mục Desirable ở cuối bảng thì làm khi còn chỗ.

| Mã | Mục (nguyên văn, `sigsoft_general_standard`) | Cách đáp ứng trong bài |
| --- | --- | --- |
| E-G1 | "states a purpose, problem, objective, or research question" | Phần mở đầu: câu hỏi có thể tách được phần gain không thuộc về skill hay không |
| E-G2 | "explains why the purpose, problem, etc. is important (motivation)" | Đoạn đầu: một con số gain duy nhất được dùng làm bằng chứng |
| E-G3 | "defines jargon, acronyms and key concepts" | Định nghĩa skill, scope, $S$, $L$, T1–T3 trước khi dùng (`docs/glossary.md` §7) |
| E-G4 | "names the methodology or methodologies used" | Gọi tên phương pháp theo đúng tên của Empirical Standards: benchmarking có can thiệp, mô phỏng định lượng, meta-science |
| E-G5 | "methodology is appropriate (not necessarily optimal) for stated purpose" | Các đối chứng trong đó nguyên nhân được cho là vắng mặt |
| E-G6 | "describes in detail what, where, when and how data were collected" | Mục Setting, bảng inventory, hình chronology |
| E-G7 | "describes in detail how the data were analyzed" | Mục "What is certified" và các phép kiểm đã đăng ký |
| E-G8 | "visualizations/graphs are not misleading" | §8 |
| E-G9 | "complies with all applicable empirical standards" | §7 |
| E-G10 | "presents results" và "results directly address research questions" | Mục Results theo thứ tự gain → cơ chế → can thiệp → phần còn lại → phạm vi |
| E-G11 | "enumerates and validates assumptions of statistical tests used (if any)" | **Nêu giả định của từng phép kiểm** (e-process, sign test, end-of-pool) và cách kiểm mỗi giả định (chẩn đoán thứ tự, Kendall τ) |
| E-G12 | "discusses implications of the results" | Mục Discussion |
| E-G13 | "discloses all major limitations" | Mục Threats to Validity |
| E-G14 | "states clear conclusions which are linked to research question (or purpose, etc.) and supported by explicit evidence (data/observations) or arguments" | Mỗi câu trong Conclusion phải khớp với một kết quả ở thân bài, **không mạnh hơn** cách thân bài đã nói. Ví dụ: "phần gain còn lại" là gain còn lại khi không có hai commit đó, không phải gain đã chứng minh đến từ skill |
| E-G15 | "contributes in some way to the collective body of knowledge" | Phần đóng góp |
| E-G16 | "language is not misleading" | Giống E-G14, áp dụng cho tiêu đề và tóm tắt |
| E-G17 | "acknowledges and mitigates potential risks, harms, burdens or unintended consequences of the research" | Không có người tham gia. Rủi ro: hướng dẫn khai thác rò rỉ, và việc nêu tên các hệ thống bên thứ ba. Bài không quy kết gì về các con số đã công bố (`docs/reviewer_fidelity.md`) |
| Desirable | "demonstrates appropriate statistical power"; "discusses study's realism, assumptions and sensitivity"; "clarifies the roles and responsibilities of the researchers (i.e. who did what?)"; "uses multiple raters, where philosophically appropriate"; "publishes the study in two phases" | Power của các phép kiểm đã nêu ở mục 3; vai trò nêu ở mục Use of AI Tools; một người gán nhãn, xem E-I |

**Phản phương pháp khi viết** (Research and Reporting Antipatterns, nguyên văn):
- "Hypothesizing After Results are Known (HARKing)";
- "Reporting only the subset of statistical tests that produce significant results (p-hacking)";
- "Reporting---together in one paper---several immature or disjointed studies instead of one fully-developed study";
- "Overreaching conclusions".

Mục thứ ba là rủi ro thật của bài: hai review đã nói bài "quá nhiều paper trong một". Cách đáp: mọi thí nghiệm phụ phải nối vào chuỗi gain → cơ chế → can thiệp → phần còn lại → phạm vi, và bảng inventory nêu câu hỏi mà mỗi thí nghiệm trả lời.

**Phê bình không hợp lệ** (Invalid Criticisms, nguyên văn). Dùng khi phản biện review, không dùng để bỏ qua một lỗi thật:
- "Setting arbitrary minimum sample sizes or other data requirements, based on neither power analysis nor theoretical saturation";
- "lacks detail without enumerating missing details";
- "is not new without providing citations to published studies that make **practically identical** contributions";
- "Criticizing a study for limitations intrinsic to that kind of study";
- "Rejecting a study because the reviewer would have used a different methodology or design";
- "Rejecting a study because it reports negative results".

## 7. Các chuẩn cụ thể (E-B, E-M, E-S, E-I, E-R)

| Mã | Mục (nguyên văn) | Nguồn | Cách đáp ứng |
| --- | --- | --- | --- |
| E-B1 | "justifies the selection of an existing, publicly available or standard benchmark (in terms of relevance, timeliness, etc.)" | `sigsoft_benchmarking_standard` | Nêu vì sao chọn SWE-smith, Jinja, Bleve và Pygments, có trích nguồn |
| E-B2 | "describes the experimental setup for the benchmark in sufficient detail to support independent replication" | như trên | Mục Setting, cùng commit của gskill và phiên bản harness |
| E-B3 | "specifies the workload or usage profile in sufficient detail" | như trên | Cách chia task, seed, giới hạn bước, trần chi phí |
| E-B4 | "allows different configurations of a system under test to compete on their merits without artificial limitations" | như trên | Cùng trần chi phí ở cả hai nhánh; báo số run chạm trần |
| E-B5 | "assesses stability or reliability using sufficient experiment repetitions" | như trên | Seed thứ hai (S1–S3), học lại (R2), lượt xác nhận C. Ghi rõ đó là bằng chứng mô tả về độ ổn định |
| E-B6 | "discusses the construct validity of the benchmark; that is, does the benchmark measure what it is supposed to measure?" | như trên | Threats, đoạn Measurement: $S$ là các test của benchmark, không phải một phép kiểm ngữ nghĩa độc lập |
| E-B7 (Desirable) | "transparently reports on problems with executing benchmark runs, if any" | như trên | Crash do rate limit, run chạm trần, lượt C10 dừng vì trần |
| E-M1 | "presents information that is useful for other researchers"; "makes recommendations for future research"; "presents clear, valid arguments supporting recommendations" | `sigsoft_metascience_standard` | Discussion: đối chứng một commit cho benchmark xây kiểu SWE-smith; chứng nhận có giá trị tới đâu |
| E-M2 (Antipattern) | "overreaching"; "attacking individual studies or researchers" | như trên | Không quy kết các con số gskill đã công bố (`docs/reviewer_fidelity.md`) |
| E-S1 | "justifies that simulation is a suitable method" | `sigsoft_simulation_standard` | Mô phỏng dùng để đo tỉ lệ sai và power, những thứ không đo được trên dữ liệu thật |
| E-S2 | "describes the simulation model ..., including input parameters and response variables" | như trên | Tỉ lệ giải được đo theo từng task, các pool null, tỉ lệ chứng nhận sai |
| E-S3 | "describes simulation packages or tools used ..., including version numbers, and computational environments" | như trên | Python và NumPy cùng phiên bản được ghi trong `results/method_check.json` (trường `environment`); bài trỏ tới gói |
| E-S4 | "describes the study protocol, including ... number of runs per scenario" | như trên | Số lần lặp trên mỗi pool (`\neopValidReps`) |
| E-S5 | "clearly explicates the assumptions of the simulation model" | như trên | Task độc lập khi biết trạng thái; trạng thái chung có hai giá trị |
| E-I1 | "clearly states what properties were rated"; "clearly states how many raters rated each property" | `sigsoft_irr_supplement` | X3′: Q1–Q4, một người gán nhãn |
| E-I2 | "provides reasonable justification for using a single rater" | như trên | Q1–Q3 là nhãn danh nghĩa, khớp với bộ dò trên 104/104 trace. Q4 là phán đoán, nên ghi là giới hạn |
| E-R1 | "clearly designates as exploratory any unregistered post hoc analyses" | `sigsoft_registered_reports_supplement` | Chú thích bảng inventory ghi rõ phân tích post hoc là thăm dò |
| E-R2 | "EITHER: adheres precisely to the registered procedures OR: thoroughly justifies all deviations"; "deviations, if any, are _not_ justified based on the data" | như trên | Sai lệch D# và ghi chú thực thi có ngày trong bản đăng ký (R5) |
| E-R3 (Antipattern) | "Pre-registrations that are not verifiably committed prior to data collection, e.g. not time-stamped." | như trên | Thời điểm commit của từng bản đăng ký nằm trong gói (Data Availability) |

## 8. Hình và bảng (E-V, `sigsoft_infovis_supplement`)

Phạm vi: hình mã hóa giá trị định lượng. Phụ lục ghi rõ nó không áp dụng cho "Diagrams not encoding quantitative values" và "Tables that encode data in textual format".

| Mã | Quy tắc (nguyên văn) |
| --- | --- |
| E-V1 | "the ratio of two values is equal to the geometrical ratio on paper"; "diagrams are rendered in 2D" |
| E-V2 | "the title (or figure caption) concisely conveys what is the content of the visualization and the intended message": chú thích phải nói cả **thông điệp**, không chỉ mô tả hình |
| E-V3 | "axes and the relative tick marks are labelled"; "the size of text is large enough to make it readable" |
| E-V4 | "use of logarithmic scales is explicitly highlighted" |
| E-V5 | "color encoding of categorical measures is limited to at most 5 distinct levels"; "the design is colorblind-friendly" |
| E-V6 | "image format is preferably vectorial" (TikZ/pgfplots đã là vector) |

## 9. Tình trạng của bài so với quy tắc (cập nhật trong cùng commit khi sửa)

Ký hiệu: **đạt**; **sửa R-98** (sửa trong lượt này); **chờ** (thuộc quyền @thuthuy hoặc bị chặn).

| Mã | Tình trạng | Ghi chú |
| --- | --- | --- |
| E-F2 | đạt | Phần chính tới trang 9, tức dưới giới hạn 10; đo lại bằng `ease_pdf_check.py` sau mỗi lần build |
| E-F9 | sửa R-99 | Bỏ `printacmref=false`, `\setcopyright{none}` và lệnh ẩn ô bản quyền. Thêm CCS và `\Description` cho ba hình. Log không còn cảnh báo "mandatory" |
| E-F4, E-F5 | đạt | preflight [ease] |
| E-A1–E-A3 | sửa R-98 | Sửa "reviewed by the author" (lộ số tác giả) thành "an author". preflight [ease] kiểm tên chủ repo, `\author`, `acks` và cụm ngôi thứ nhất |
| E-A4, E-O3, E-O4 | sửa R-99; **còn bước tải lên** | Chọn (R-99) figshare với link riêng tư ẩn danh. Theo `disclose_data_dbr_howto`, Zenodo buộc công bố công khai ngay ("the file will be publicly accessible and indexed in Zenodo"), còn figshare cho link riêng tư trong lúc review và công bố khi bài được nhận. Giấy phép: CC-BY 4.0 cho dữ liệu và tài liệu, MIT cho mã (file `LICENSE`, `LICENSE-DATA.md` trong gói). Còn lại: @thuthuy tải gói lên figshare bằng tài khoản của mình (việc ra bên ngoài), rồi thay macro `\anonpackage`. `ease_pdf_check.py` báo lỗi khi macro còn là ANON-LINK-PENDING |
| E-O2 | đạt | preflight [ease] |
| E-O5, E-O8 | sửa R-98 | Data Availability nêu lý do không phân phối lại: các văn bản bên thứ ba không có giấy phép, và khóa truy cập |
| E-O7 | sửa R-98 | Data Availability liệt kê phiên bản model và công cụ, prompt, seed trong gói |
| E-AI1 | sửa R-99 | Chuyển phần khai báo vào mục Setting (phần phương pháp), nêu chi tiết việc AI làm; bỏ mục riêng ở cuối bài |
| E-AI2 | sửa R-98 | Use of AI Tools: thêm câu tác giả chịu trách nhiệm, và tác giả gán nhãn X3′ |
| E-C1, E-G14, E-G16 | sửa R-98 | Tóm tắt, phần mở đầu và kết luận viết lại cho khớp mục 4.5: phần gain còn lại là gain khi không có hai commit, được các phép kiểm đã đăng ký nhận; phép end-of-pool là đọc lại post hoc |
| E-G4 | sửa R-98 | Gọi tên phương pháp theo Empirical Standards. Không thêm mục trích dẫn cho từng chuẩn: bản gốc không ghi năm, và nhiều mục không năm cùng nhãn "sig" làm hỏng kiểu ACM (`make_bib.py` dừng). Theo R1 không tự điền năm |
| E-G11 | sửa R-98 | Nêu giả định của sign test và trỏ tới chẩn đoán thứ tự |
| E-B1 | sửa R-98 | Lý do chọn Jinja, Bleve (bài công bố gskill) và Pygments (ví dụ trong script học của gskill) |
| E-S3 | sửa R-98 | `verify_methods.py` ghi phiên bản; bài nêu NumPy, seed cố định |
| E-R1 | sửa R-98 | Chú thích bảng inventory |
| E-V2 | sửa R-98 | Chú thích Hình 3 (paired gains) nêu thông điệp |
| E-A3 (tên riêng) | sửa R-100 | Bỏ tên "Gatekeeper" (trùng tên repo công khai `-gatekeeper-p6` của tác giả); preflight [ease] chặn tên repo; gói đổi sang `evalgate`. **Khuyến nghị @thuthuy:** để `-gatekeeper-p6` ở chế độ private tới khi có kết quả (12/03/2027) |
| E-G1 (câu hỏi nghiên cứu) | sửa R-100 | Bốn RQ tường minh ở phần mở đầu, mỗi RQ trỏ tới mục trả lời nó |
| Năm trên trang 1 | sửa R-100 | `\acmYear{2027}`, `\copyrightyear{2027}` |
| E-I2 | đạt | Câu "One rater sufficed" và giới hạn Q4 trong Threats |
| CCS Concepts | sửa R-99 | "Software and its engineering → Software verification and validation" và "Computing methodologies → Artificial intelligence". Hai khái niệm này được dùng nguyên văn trong `continuous_skill_eval_2026`, một bài cùng chủ đề theo mẫu ACM. Trang CCS của ACM bị 403; khi đọc được thì đối chiếu lại |
| Tiêu đề | sửa R-99 | "A Published Skill Learner Found the Leak: Controls for Evaluating Learned Coding-Agent Skills". "A published skill learner" chỉ đúng một learner, khớp Threats (E-G16). Bỏ "Certifying" vì chứng nhận không còn là đóng góp chính (Q3) |
