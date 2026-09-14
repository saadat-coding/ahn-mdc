# W vs K Feedback Audit (Teammate Feedback Item 4)

**Feedback:** "W = 256 is NOT a hard failure point; degradation begins before
the target necessarily leaves the window; W must remain distinct from K."

**Verdict: ALREADY ADDRESSED — NO EDIT NEEDED.**

## Search scope

`manuscript/ABSTRACT.md`, `INTRODUCTION.md`, `METHODS.md`, `METHODS_EXTENDED.md`,
`RESULTS.md`, `DISCUSSION.md`, `CONCLUSION.md`,
`outputs/publication_exhibits/CAPTIONS.md`.

## Findings

**W is never presented as a hard failure point.** Grep for "compression
threshold," "hard failure," "failure point," "collapse occurs at W," "K = W"
across all seven manuscript sections returns exactly one hit, and it is the
required disavowal itself:

> Methods §2.3: "We do not describe the collapse as occurring 'at' a
> compression threshold or compression as 'beginning at K'."

**W and K are kept distinct everywhere both are mentioned:**

| location | text |
|---|---|
| Methods §2.3 | "K is a descriptive per-run quantity and is not W" |
| Results [R17] | "Every K lies **below** the exact-attention window W = 256." |
| Results [R25] | "The knee is not the window and the transition is not a clean inside/outside switch: every K (208-240) lies below W (256)…" |
| Discussion §4.5 (title) | "Why K < W matters" |
| Discussion §4.5 | "K is an observed per-run quantity, not an architectural constant, and it does not mark the onset of compression." |
| Conclusion | "The empirical performance knee does not coincide with the exact-attention window — for every architecture it sits below the window…" |

**Degradation beginning before the target leaves the window is explicitly
acknowledged** via the residual exact-attention-eligible failure result
(VAL-4), present in Methods (§2.3, §2.6), Results ([R25], [R46]-[R48], §3.6),
Discussion (§4.5), and Conclusion:

> Results [R25]: "…about 32% of trials whose target span is exact-attention
> eligible throughout the trial still fail (§3.6), so deterioration begins
> before that boundary alone can explain it."
> Conclusion: "…a substantial fraction of trials fail while the target is still
> exact-attention eligible, so the transition is not a clean inside/outside
> boundary."

The publication figure captions (`outputs/publication_exhibits/CAPTIONS.md`)
already state, for fig2: "W = 256 is the architectural sliding-window
reference… The diamonds … are the empirical performance knee K per
architecture … a descriptive location, not a threshold, and distinct from W.
Every K (208-240) lies below W."

## Conclusion

Every element of this feedback item — W is not a hard failure boundary, K is
distinct from W, degradation begins before the window boundary — is already
stated in the current manuscript, consistently, in Methods, Results,
Discussion, Conclusion, and the exhibit captions. No prohibited phrasing
("compression begins at K," "collapse occurs at W," "K = W") was found
anywhere.

**Classification: A — already addressed in the current manuscript.**
**Edit needed: none.**
