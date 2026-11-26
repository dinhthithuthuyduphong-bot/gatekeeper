// R-105: reader companion for reviewers (tables and notation as text). Data: scripts/reviewer_guide_data.py
// Reader's companion for the paper: tables and notation as text (R-105).
// Input: tables.json from scripts/reviewer_guide_data.py (values = the paper's generated macros).
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType,
  HeadingLevel, AlignmentType, LevelFormat, BorderStyle, PageNumber, Footer,
} = require("docx");

// usage: node scripts/reviewer_guide.js <dir holding tables.json>; writes reader_companion.docx there
const dir = process.argv[2];
if (!dir) throw new Error("usage: node scripts/reviewer_guide.js <dir>");
const data = JSON.parse(fs.readFileSync(path.join(dir, "tables.json"), "utf8"));
const M = data.macros;
const mv = (k) => {
  const v = M[k];
  if (v === undefined) throw new Error("missing macro " + k);
  return v.replace(/\\ensuremath\{([^}]*)\}/, "$1").replace(/\\times10\^\{(-?\d+)\}/, " × 10^$1");
};
const T = Object.fromEntries(data.tables.map((t) => [t.label, t]));

const FONT = "Arial";
const PAGE_W = 11906, MARGIN = 1134; // A4, 2 cm margins
const CONTENT_W = PAGE_W - 2 * MARGIN;
const border = { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" };
const borders = { top: border, bottom: border, left: border, right: border };

const p = (text, opts = {}) =>
  new Paragraph({ spacing: { after: 100 }, ...opts, children: runs(text, opts.size) });
function runs(text, size) {
  // **bold** segments
  return String(text).split(/(\*\*[^*]+\*\*)/).filter(Boolean).map((s) =>
    s.startsWith("**")
      ? new TextRun({ text: s.slice(2, -2), bold: true, font: FONT, size: size || 21 })
      : new TextRun({ text: s, font: FONT, size: size || 21 }));
}
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] });
const bullet = (t) => new Paragraph({ numbering: { reference: "b", level: 0 }, spacing: { after: 60 }, children: runs(t) });

function table(header, rows, widths, size = 17) {
  const sum = widths.reduce((a, b) => a + b, 0);
  const w = widths.map((x) => Math.floor((x / sum) * CONTENT_W));
  w[w.length - 1] += CONTENT_W - w.reduce((a, b) => a + b, 0);
  const cell = (txt, i, head) => new TableCell({
    borders, width: { size: w[i], type: WidthType.DXA },
    shading: head ? { fill: "E8EEF4", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ children: [new TextRun({ text: String(txt), font: FONT, size, bold: !!head })] })],
  });
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: w,
    rows: [new TableRow({ tableHeader: true, children: header.map((c, i) => cell(c, i, true)) }),
      ...rows.map((r) => new TableRow({ children: r.map((c, i) => cell(c, i, false)) }))],
  });
}
function paperTable(label, title, widths) {
  const t = T[label];
  const out = [h2(title), p(t.caption, { size: 19 })];
  // pad rows with a merged cell (e.g. S3, C in Table 2) so every row has the header's width
  const n = t.header.length;
  const rows = t.rows.map((r) => {
    if (r.length === n) return r;
    // a contrast row: the PDF spans None, Skill and Gain with one text; show it under Gain
    const k = n - r.length;
    return [...r.slice(0, 3), ...Array(k).fill("–"), r[3], ...r.slice(4)].slice(0, n);
  });
  out.push(table(t.header, rows, widths));
  if (t.notes) out.push(p("Notes under the table: " + t.notes, { size: 19 }));
  if (label === "tab:decisions") out.push(p("Rows S3 and C are contrasts between environments: the PDF prints one text across the None, Skill and Gain columns; it is shown here under Gain.", { size: 19 }));
  return out;
}

const children = [
  new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("Reader’s companion: tables, notation and checked facts")] }),
  p("For: “A Published Skill Learner Found the Leak: Controls for Evaluating Learned Coding-Agent Skills” (EASE 2027 submission, anonymous)."),
  p("**Purpose.** Several automated reviews read the PDF through text extraction and reported errors that the printed PDF does not contain (inverted columns, missing symbols, shifted cells). This note gives every table and the notation as plain text. Each value is the same generated macro that the PDF prints; nothing here is typed by hand. **When this note and an extracted text disagree, read the rendered PDF page.** This note is an internal aid; it is not part of the submission and adds no result."),

  h1("1. Extraction artifacts already checked against the rendered PDF"),
  table(["Reported by text extraction", "What the PDF prints"], [
    ["Table 2: columns None and Skill inverted (e.g. J1 read as 53/15)", "J1 None 15, Skill 53. In all twelve rows None ≤ Skill; for P the “None” column is the placebo arm (24), as the table note says."],
    ["Table 2: no header over the E column", "The header row reads: ID, Comparison, Arms, None, Skill, Gain [95% CI], E, ≥40, fam., Seq."],
    ["Table 2/3 notes read as “a82”, “b79”, “cran”", "Superscript note marks a, b, c followed by text: “a 82 of 100 tasks…”, “b 79 of 100…”, “c ran in a different run…”."],
    ["Table 3: “5/34” for the learned skill, seed 41", "15/34."],
    ["Table 5: 0.0032 on the sign-test row", "0.0032 is on the “Registered e-process” row; the sign-test row reads “–” and 0.7%."],
    ["Table 1: “same job (79/100)” on row G", "Row G reads “same job”; “(79/100)” belongs to row X (Pygments). Rows H, X3 and L2 read “–”."],
    ["“Rungit log -n 5”", "“Run git log -n 5” (typewriter font; extraction drops the space at the font change)."],
    ["Expectation printed as 𝔹[Z_i | C]", "𝔼[Z_i | C] (blackboard E; some extractors map the glyph to B)."],
    ["“Kendall’s  between position and Z_i” (τ missing)", "“Kendall’s τ between position and Z_i”."],
    ["PACE first cited only in Section 5", "Cited in Section 3, at the end-of-pool statistic."],
    ["“URL.” orphan on page 10 makes the paper too long", `Main text ends on page ${data.layout.main_to}, within the 10-page limit; the ${data.layout.ref_only_after} page(s) after it hold references only, as the call allows.`],
  ], [5, 7]),

  h1("2. Notation (one meaning each)"),
  table(["Symbol", "Meaning"], [
    ["S", "Scorer: the benchmark’s notion of resolved (every FAIL_TO_PASS and PASS_TO_PASS test passes). Every gain in the paper is under S."],
    ["L", "Scorer in gskill’s public code (verify_with_patch), which the learning loop optimises; audited in Section 4.7. Not the experiment L2."],
    ["ℓ_i, Z_i", "ℓ = 1 − 1[resolved under S]; Z_i = ℓ_i(skill) − ℓ_i(none) ∈ {−1, 0, 1}; Z_i < 0 means the skill helped."],
    ["D_i", "Contrast between environments: D_i = (Z_i shipped − Z_i one commit)/2 (S3, C, C10, V1–V3)."],
    ["C", "State of the run: everything the tasks of a run share (served model version, harness, provider state over time)."],
    ["T1, T2, T3", "T1: mean effect over the fixed pool within the run (certified). T2: its mean over runs. T3: effect on future tasks."],
    ["E", "End-of-pool statistic Π(1 + λ(−θ − Z_i)), θ = 0, λ = 0.5 (half the maximal safe bet). With Z_i ∈ {−1, 0, 1}: E = 1.5^b · 0.5^c, b and c the tasks resolved only with / only without the skill."],
    ["Thresholds", "Certified: E ≥ 40 (α = 0.025, one-sided). Twelve decisions read as one family: E ≥ 480. V1–V3: one family of three, E ≥ 120. C10: one test, E ≥ 40."],
    ["Experiment IDs", "S1–S3 = second agent seed (not the scorer S); L2 = second learner XRepoSkill (not the scorer L); A = skill without its history line, C = confirmatory contrast (neither is the run state C); see Table 1."],
    ["C10 histories", "H_ship (shipped), H_neutral (same diff, neutral message), H_empty (empty “Bug Patch” commit), H_none (no bug commit)."],
    ["b/c (Table 2)", "Tasks resolved only with / only without the skill; E = 1.5^b · 0.5^c."],
  ], [2, 9]),

  h1("3. The tables as text"),
  ...paperTable("tab:inventory", "Table 1 — Experiment inventory", [3, 2, 9, 7, 7, 6, 5]),
  ...paperTable("tab:decisions", "Table 2 — The twelve registered decisions", [2, 7, 3, 2.5, 2.5, 6.5, 2.5, 4, 2, 2, 2]),
  ...paperTable("tab:nops", "Table 3 — Jinja tasks without an issue description", [5, 4, 6, 3]),
  ...paperTable("tab:vendors", "Table 4 — Agents of other vendors", [5, 3, 3, 6, 3, 2]),
  ...paperTable("tab:rules", "Table 5 — Decision rules", [6, 4, 2.5, 3, 3, 3]),

  h1("4. Key results, with where each is in the paper"),
  bullet(`Confirmatory test C (preregistered; both environments in one job; 70 tasks without description): the skill’s gain is larger with the commits on ${mv("ncfFor")} tasks, smaller on ${mv("ncfAgainst")}, ties ${mv("ncfTies")}; E = ${mv("neopL")} (Section 4.4).`),
  bullet(`C10 (registered; eight arms in one job, ${mv("nctrACN")} tasks): with the skill, ${mv("nctrASkill")} resolved in H_ship (shipped history), ${mv("nctrBSkill")} in H_neutral (diff under a neutral message), ${mv("nctrCSkill")} in H_empty (empty “Bug Patch” commit), ${mv("nctrDSkill")} in H_none (no bug commit); H_ship − H_empty mean D = ${mv("nctrACMean")}, E = ${mv("nctrACE")} (Section 4.3).`),
  bullet(`All 100 Jinja test tasks: gain ${mv("njinjaGain")} as shipped vs ${mv("njinjaLFGain")} with one commit; difference ${mv("nleak")} [${mv("nleakLo")}, ${mv("nleakHi")}], arms in different runs. Second seed, one job: ${mv("nsdLeak")} [${mv("nsdLeakLo")}, ${mv("nsdLeakHi")}], not certified on 100 tasks (E = ${mv("neopK")}).`),
  bullet(`Scorer L accepts a no-op patch on ${mv("nfzeroLNoop")} of ${mv("nfzeroN")} tasks; S passes ${mv("nfzeroSNoop")} of them (Section 4.7).`),
  bullet(`Trace labels (X3): one author labelled all ${mv("nxhN")} runs blind; agreement with the audit on the three nominal labels: ${mv("nxhAgreeMin")} of ${mv("nxhN")}. The reliance judgment (${mv("nxhUse")} of ${mv("nxhDiff")}; unclear ${mv("nxhUnclear")}) has one rater and is stated as a limitation.`),
  bullet(`Simulations (Section 3): false certification at most ${mv("neopTypeMax")} on three null pools; ${mv("neopShared")} for a state shared by the run (T2, not certified). Dependence between tasks: at most ${mv("ndepEopMild")} for the end-of-pool test and ${mv("ndepEpMild")} for the registered e-process unless a strong link (correlation 0.8) sits inside one arm (${mv("ndepEopStrong")} and ${mv("ndepEpStrong")}; sign test ${mv("ndepSignStrong")}).`),

  h1("5. Registered and post hoc"),
  bullet("Registered before the data: every comparison of Table 2 (sign test with Holm where registered, and the sequential e-process), C, C10, V1–V3, R2, K, W, L2, G, X3. Table 1, column Analysis."),
  bullet("Post hoc (labelled in the text, exploratory): the end-of-pool reading of the twelve decisions of Table 2 (it was registered as primary only for C10 and V1–V3); the trace audit H; the exact sign test on C’s new cohort; the content reading of L2."),
  bullet("Families: C10 one test (40); V1–V3 three tests (120); the twelve decisions also read as one family (480). No correction spans experiments; each conclusion names its test."),

  h1("6. What the paper does not claim"),
  bullet("That the git-history leak is new (Section 1 cites the reports), or that the numbers announced for gskill came from the code tested."),
  bullet("That the gain left without the two commits comes from the skill alone: it is the gain without these two channels, under the benchmark’s tests S, not an independent semantic check."),
  bullet("That any learner writes such an instruction: the claim is for gskill’s learner and writer; a second learner and other writers did not separate the leak from habit."),
  bullet("That a certification covers other runs or tasks: it covers T1 only."),

  h1("7. Venue facts, checked against the EASE 2027 call"),
  bullet(`Main text ≤ 10 pages including figures, tables and appendices, plus up to two pages containing only references. This PDF (${data.layout.pages} pages): main text ends on page ${data.layout.main_to}, where the references begin; ${data.layout.ref_only_after} page(s) after it hold references only.`),
  bullet("Template \\documentclass[sigconf,review,anonymous]{acmart} and the call’s \\acmConference line; double-anonymous review; SIGSOFT Open Science Policy (Data Availability after the Conclusion)."),
  bullet("Dates (AoE): abstract 15 January 2027, paper 22 January 2027, notification 12 March 2027. The call names five criteria: Soundness, Significance, Novelty, Verifiability and Transparency, Presentation."),
  bullet("Not in the call (do not rely on it): an acceptance rate, a rebuttal phase or its absence, a numeric scoring scale."),
  bullet("The anonymous replication package is on figshare (private link in Data Availability); it will be published with a DOI on acceptance."),
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { font: FONT, size: 34, bold: true }, paragraph: { spacing: { before: 0, after: 160 }, keepNext: true } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 27, bold: true, color: "1F3864" }, paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 23, bold: true }, paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync(path.join(dir, "reader_companion.docx"), b);
  console.log("written");
});
