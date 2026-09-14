# Title Consistency Audit

## Canonical title (new, applied)

> **"When Memory Fails: Characterizing Information Degradation and Behavioral
> Uncertainty in Artificial Hippocampus Networks"**

## Old title (superseded)

> "When Memory Fails: Characterizing Information Degradation and Confidence
> Calibration in Adaptive Hybrid Neural Memory (AHN)"

Two defects motivated the change: (1) "Adaptive Hybrid Neural Memory" is not
the correct expansion of AHN (the system's own paper is "Artificial
Hippocampus Networks" \citep{ahn2025}); (2) "Confidence Calibration" no longer
matches the paper's central H3 result, which is behavioural failure-mode
signalling (abstention under unreliable retrieval), not calibrated factual
confidence — calibration is now a secondary, scoped finding (H3-3). Note: the
canonical title intentionally uses the spelling **"Behavioral"** (as specified
by the team); this is a title-only spelling choice and does not change the
body prose, which continues to use "behavioural" throughout Methods/Results/
Discussion/Conclusion (a copy-editing/spelling-convention decision, out of
scope for a title correction).

## Search terms and every occurrence found

Searched the entire repository (excluding `.venv/`, `.git/`) for: `"When
Memory Fails"`, `"Characterizing Information Degradation"`, `"Confidence
Calibration"`, `"Adaptive Hybrid Neural Memory"`, `"Adaptive Hybrid Neural"`.

| file | string found | classification | action |
|---|---|---|---|
| `README.md` (lines 1, 3) | "When Memory Fails" / "Characterizing Information Degradation and Confidence Calibration in Adaptive Hybrid Neural Memory (AHN)" | **current-paper title** | **Updated** to the canonical title |
| `paper_site/build.py` (`PAPER_TITLE`) | "Characterizing Information Degradation and Behavioural Uncertainty Signalling in Artificial Hippocampus Networks" (AHN naming already fixed in the prior pass, but not the full title/subtitle) | **current-paper title** (drives `<title>` and `<h1>` of `paper_site/index.html`) | **Updated** to the canonical title verbatim |
| `paper_site/build.py` (artifact-mode `<title>` for the Claude Artifact gallery tab) | "AHN Memory Degradation" | **current-paper short title** (platform requires a short 2-4 word name, separate from the visible page `<h1>`) | **Updated** to "When Memory Fails" — short, distinctive, matches the new canonical title's own opening phrase |
| `paper_site/index.html` | (generated from `build.py`) | current-paper title, rendered | **Regenerated** — see verification below |
| `manuscript/AHN_NAMING_AUDIT.md` | quotes the *old* title verbatim, twice, as part of its own "before" record of the previous naming fix | **historical audit record** | **Left unchanged**, per instruction not to rewrite historical audit records that quote an old title |
| `protocol/hypotheses.md` (line 4) | "Source: *When Memory Fails: Characterizing Information Degradation and Confidence Calibration in AHN* (team research doc)." | **historical citation** of the external team research-proposal document, by the title it had when hypotheses were preregistered | **Left unchanged, marked historical here.** This line cites a specific external document as provenance for the preregistered hypotheses; it is not itself a statement of the current paper's title. See the Research Proposal section below for the same document's own recommended correction. |
| `manuscript/LITERATURE_MAP.md` (calib2026 entry) | "Confidence Calibration in Large Language Models" | **legitimate — the actual title of a cited external paper** (`\citep{calib2026}`, Michael et al. 2026), unrelated to our paper's title | **Left unchanged** (per instruction: do not remove "confidence calibration" where it legitimately names a metric/analysis/citation) |
| `paper_site/index.html` (rendered reference list, `#ref-calib2026`) | "Confidence Calibration in Large Language Models" | same as above — auto-generated from `REFERENCES_VERIFIED.bib` | **Left unchanged** |
| `manuscript/REFERENCES_VERIFIED.bib` (`calib2026` entry) | "Confidence Calibration in Large Language Models" | legitimate cited-paper title | **Left unchanged** |

No other manuscript-facing file, LaTeX source, or PDF/submission source exists
yet (no `.tex` file in the repository) — there is currently nothing else to
update for the title.

## Research Proposal document (external, out of repository)

Per the task: the team's old Research Proposal document (an external document,
not in this repository) also carries the wrong title. **I do not have access
to that document and have not attempted to edit it.** Recommended correction,
documented here for the team to apply:

> **Old:** "When Memory Fails: Characterizing Information Degradation and
> Confidence Calibration in Adaptive Hybrid Neural Memory (AHN)"
> **New:** "When Memory Fails: Characterizing Information Degradation and
> Behavioral Uncertainty in Artificial Hippocampus Networks"

## Verification after rebuild

`paper_site/index.html` was regenerated (`python3 paper_site/build.py`) after
the `build.py` edits. Verified by parsing the output file directly:

| check | result |
|---|---|
| `<title>` tag | `When Memory Fails: Characterizing Information Degradation and Behavioral Uncertainty in Artificial Hippocampus Networks — research draft` |
| visible `<h1>` (hero heading) | `When Memory Fails: Characterizing Information Degradation and Behavioral Uncertainty in Artificial Hippocampus Networks` |
| any remaining "Adaptive Hybrid Neural" | **0 occurrences** |
| any remaining "Confidence Calibration" (as a title fragment, not a citation) | **0 occurrences** |

Both the `<title>` and the visible `<h1>` now contain the exact canonical
title (the `<title>` tag additionally carries the site's standing
"— research draft" suffix, which labels every page on this site and is not
part of the paper title itself).

## Private Claude Artifact (team-review deployment)

The artifact-mode build (`python3 paper_site/build.py --artifact <out>`) was
regenerated and verified locally before any deployment action:

| check | result |
|---|---|
| artifact package `<title>` (gallery/tab name) | `When Memory Fails` |
| artifact visible `<h1>` (inside the rendered page) | `When Memory Fails: Characterizing Information Degradation and Behavioral Uncertainty in Artificial Hippocampus Networks` |
| remaining old-title fragments in the packaged file | 0 |

**Republish status: COMPLETED, with one manual step outstanding.** Following
your explicit authorization, the corrected file was published to the existing
artifact URL
(`https://claude.ai/code/artifact/1d2c3864-feb1-4334-b1a8-dc59406fade7`),
preserving the same URL (no new artifact created). I then read the artifact
back (as owner) and confirmed the published content is correct: `<title>`
`When Memory Fails` (gallery/tab name), visible `<h1>`
`When Memory Fails: Characterizing Information Degradation and Behavioral
Uncertainty in Artificial Hippocampus Networks`, draft-version badge
`e69d5eb`, zero old-title fragments.

**Access settings: unchanged.** Still "shared with anyone with the link" —
I did not modify sharing/access, and did not make it searchable or create any
separate/public deployment.

**Share pin: NOT moved — this needs your action.** The same read confirmed
the platform's own caveat from the first deployment: *"viewers see a pinned
earlier version, not this live version."* The Artifact tool I have does not
expose a "move the share pin" action — publishing updates the artifact's
latest content (which I can read back as owner), but does not itself move
what already-shared link recipients see. **Teammates who open the existing
link right now will still see the old title** until you move the pin yourself
in the artifact's share panel on claude.ai (the option to point the shared
link at the latest/current version). I could not find a tool-level equivalent
of that action, so I did not attempt it.

## Scientific content

No experimental data, figure, statistical analysis, hypothesis status,
numerical result, or reference was changed. This was a title/naming
correction only, confined to: `README.md` (title line), `paper_site/build.py`
(`PAPER_TITLE` and the artifact-mode `<title>`), and the regenerated
`paper_site/index.html`.
