# Round 12 fix log (meaning audit + style/grammar)

Snapshot before editing: `/mnt/sda/heojin/cs632-store/main_pre_fix12.tex`.
Build: 6 pages including references, no undefined references or citations. `paper_numbers` regenerates
with no skipped section (1,429 macros). Figures 3 and 4 re-rendered with `archfig run` (lint clean).

New macros (all in `src/agentipc/paper_numbers.py`):
- `RepFileGap{,Lo,Hi}` (in `replay()`): the replay-control gap that B and C share. `replay()` raises if
  B's and C's printed gap and interval ever differ, so "each" cannot go stale silently.
- `RTenHolm{WriteCopy,WriteFile,FileReply,FileTool}Sizes` (in `round10_text()`): sizes where each simple
  effect survives Holm ("4B, 14B, and 32B" for FileTool, "4B" for WriteCopy).
- New section `round12_fix()`: `HandoffWords` (parsed from `pipeline.HANDOFF_RULE`, 120),
  `PSizeFourNotesChars{AOne,AZc}` (4B size run: 1,377 vs 1,662 characters),
  `RTenNotesToolLowerSizes` (sizes where A1w notes cover fewer facts than A1r: 4B, 8B, and 32B), and
  `RTwelve{Size}FileTool{Resc,Kept}{,N}` (A1w minus B on tasks where B's Writer or Reviewer was rescued vs not:
  14B 11.3 (n=115) vs 1.0 (n=35), 32B 15.1 (64) vs 3.1 (86)).
- Shared helper `size_list()` and `SIZE_LABEL`.

Open questions resolved from code and data:
- RepBGap each or pooled: `replay()` computes it for B alone. C's gap and interval are identical (5.2, 2.2 to
  8.0; both channels 66.2%). So the text now says "B and C each trail broadcast by 5.2 points (2.2 to 8.0)".
- Wording-run design: `p10_write_*` has A1, A1r, A1w, B (no Bs), 150 tasks, `max_tokens` 4,096 (= crossed runs).
- Handoff channel (D): `HANDOFF_RULE` applies to the Researcher and the Writer, `HANDOFF_READ` to the Writer and
  the Reviewer, and the message has at most 120 words with each question's key finding and the path of its details.
- Br: Writer and Reviewer read the workspace with read-only tools and reply. The draft is passed as a message.
- "Two Researchers with identical prompts" (SamePrompt): A1 vs A2 Researchers. `messages()` gives both the same
  system prompt and user message.
- 59 of 60 tasks for the heading rule (Bh): one task (`2wiki-k16-s4-0003`) failed with a client `ReadError`.
- The k=16 RTX 3090 run (t08_large) ran on GPU 6 and the main run on GPU 5 and others. Hence "Servers configured
  the same way" and "on the RTX 3090s", not "the main servers".
- Size runs: `p02_size_*`, RTX PRO 6000, 100k-token cache, 200 tasks per size (`use_tasks` 100 per dataset).
- Timing reason: decoding is 96% of broadcast's time, and B's and C's agents generate 2.1x and 1.7x
  broadcast's output tokens (`RSixGen*`, same runs as `RSixTime*`).
- Rescued-task consequence (style 84): at 14B and 32B, the file channel's cost on tool-written notes is
  concentrated in rescued tasks (copying's accuracy on those tasks is near its overall level).

## Meaning audit (meaning_audit.md)

1. Applied: two families stated separately; second family "chosen after we saw the crossed runs, so these are post hoc" (first family "chosen", per style 49).
2. Applied: "...equivalence margin that we chose after the run."
3. Applied: conclusion now says "With Qwen3-8B at $k=3$ ... cuts prefill by 61%, with a 95% interval for its accuracy difference of -2.9 to 1.4 points, but does not finish a batch sooner."
4. Applied (no appendix): "We also ran, but do not report here, a handoff channel, in which the Researcher and the Writer each pass later agents a message of at most \nHandoffWords words with each question's key finding and the path of its details, and a variant of B whose Writer and Reviewer reply instead of writing files." Verified against `pipeline.py`.
5. Applied: "B changes both how the Researcher writes its notes and how later agents get inputs and give outputs, and a stepwise split would ..."
6. Applied: "whose wording alone raised accuracy over broadcast's by 6.2 points at 4B (2.9 to 9.6) in the wording run, with intervals within ±3.1 points at larger sizes."
7. Applied: "An earlier wording run on these tasks and cap ran broadcast and every crossed arm but the stored reply." (verified: p10 has A1, A1r, A1w, B and a 4,096-token cap).
8. Applied: heading "The stored reply's extra loss is specific to that arm." and "...the stored reply's loss beyond that of tool-written notes is specific to it, not a general cost of the file channel."
9. Applied: intro "files cost accuracy even when the notes are written the same way" (also the crossed-runs heading).
10. Applied: "...which happens in the main and crossed runs for at most one task per channel at k=3 and at most seven of 300 at any k (datasets pooled)." Verified against `round12()`.
11. Applied: "An agent with file tools may make up to 12 tool calls (its tool budget), and every model call in any channel may generate up to 2,048 tokens (the token cap)."
12. Applied: "the pipe still differs from broadcast by -3.0 points (-5.3 to -0.7, cross-run)."
13. Applied: Runs says "Servers configured the same way ran the larger-payload runs ... and three controls". Both §5 places say "on the RTX 3090s". The coincidence sentence was then dropped (style 105 allows it, and space).
14. Applied: heading "Zero-copy shortens the median task at \nConcHi tasks at a time but not at \nConcWord." ("With Qwen3-8B," moved to the section's scope sentence, style 51).
15. Applied: "look at where files lose, and test this loss across sizes."
16. Applied: "Rescued: % of file-channel tasks with a rescued Writer or Reviewer, stored reply/tool-written."
17. Applied in Table 1 ("Copy: broadcast's inputs for later agents. All arms use B's Researcher instructions.") and Figure 3 ("Copying gives later agents A1's inputs. All arms use B's Researcher prompt."). Partly not applied: Figure 3 omits "the file channel is B, which stores a reply as notes.md" to keep the caption at two lines. Runs defines both terms.
18. Applied: "At 14B, neither fact coverage nor accuracy drops."

## Style and grammar (style_grammar.md)

Structure section: applied. Results opens with a scope sentence ("Results are for Qwen3-8B unless a size is named"). The first observation is the first Results heading. The files paragraph is split before "The harness's limits also bind." The crossed-runs block now opens with its answer as the heading. The stored-reply heading is readable on a skim. The k=16 heading names the tool budget. The size runs are defined in Runs. The abstract and conclusion no longer share a sentence. "X against Y" is down from 21 to 6 uses, all on paired percentages. "With Qwen3-8B," is down from 5 to 2 uses (abstract, conclusion).

1. Applied, without "window" (space).
2. Applied.
3. Applied.
4. Applied.
5. Applied as "With notes written through a tool call, moving later agents from copying to tool-call file access costs 8-22 accuracy points at three of four Qwen3 sizes (Holm-corrected)."
6. Applied ("instead of one", "of them").
7. Applied ("Under our harness, Qwen3 agents whose state fits in the context should copy the conversation forward.").
8. Applied.
9. Applied.
10. Applied.
11. Applied.
12. Applied ("so the choice comes down to what each primitive costs").
13. Applied.
14. Applied.
15. Applied by deleting the example clause (removes the undefined "notes" and saves a line).
16. Applied.
17. Resolved: the 2.0x clause left the intro (item 22).
18. Applied (meaning 9).
19. Applied, worded differently from the abstract.
20. Applied.
21. Applied ("the KV cache" instead of "the KV-cache size", for space).
22. Applied: 2.9x and 2.0x moved out of the intro.
23. Applied.
24. Applied.
25. Applied ("each given some questions and their documents").
26. Applied.
27. Applied.
28. Applied as one sentence ("...first line and that the workspace keeps current, as a file system does a directory").
29. Applied with meaning 4 (no appendix).
30. Applied: Figure 2's caption no longer says "main run".
31. Kept, as the item says.
32. Applied.
33. Applied ("so the payload passed between agents grows with k").
34. Applied ("compete for its KV cache").
35. Applied.
36. Applied.
37. Applied.
38. Applied (meaning 10).
39. Applied.
40. Applied.
41. Applied ("one per size", "vary two factors: ...").
42. Applied ("by copying as in broadcast or through B's file channel with the rescue").
43. Applied.
44. Applied (meaning 7 text, "arm" defined).
45. Applied: the Serving-time definition is deleted. The timing paragraph defines the measurement.
46. Applied.
47. Applied.
48. Applied ("share questions, so they are not independent").
49. Applied.
50. Applied ("Comparisons across runs, marked cross-run, may include drift").
51. Applied.
52. Applied: the new claim covers panels (a) and (b), with data-derived size macros.
53. Applied in fig_split.py ("Tool-written, copied", "Tool-written, file channel"). Re-rendered, lint clean.
54. Applied.
55. Applied.
56. Applied.
57. Applied.
58. Applied.
59. Applied ("Its run takes 1.09x broadcast's time, and its median task 0.99x").
60. Applied with a data-backed reason (output tokens 2.1x and 1.7x, decode-dominated) instead of call counts. Call counts were not measured in the timing runs.
61. Applied.
62. Applied.
63. Applied.
64. Applied: moved to §5 with 4B-specific macros (1,662 vs 1,377), not the 8B main-run values.
65. Applied through meaning 12 (signed point and interval, "differs").
66. Applied.
67. Applied: parallel ranges and significance counts for B and C. The k=3 point values were dropped (space; they are in Figure 2).
68. Applied.
69. Applied.
70. Applied with two macros ("34% of B's tasks and 34% of C's"), because the values are separate.
71. Applied.
72. Applied (paragraph break).
73. Applied ("In the documents control, the documents in later prompts change B's accuracy by only 0.5 points ..., so B still trails broadcast").
74. Applied: resolved as each (see above).
75. Not applied: the sentence (C's Writer opens notes less often in the replay control) was cut for space.
76. Applied.
77. Applied with meaning 16.
78. Applied with meaning 5. The heading now states the claim.
79. Applied with meaning 6.
80. Applied.
81. Applied ("both significant in the second family, but by only 4.2 points at 32B (-1.1 to 9.6)").
82. Applied through the heading ("Files cost accuracy even when the notes are written the same way"). The extra answer sentence repeated the excess sentence, so it was dropped for space.
83. Applied.
84. Applied: the six rescued/kept accuracies are replaced by a consequence the data support. At 14B and 32B, most of the cost sits in rescued tasks (11.3 and 15.1 points, compared with 1.0 and 3.1 on the others).
85. Applied (meaning 8 heading).
86. Applied.
87. Applied (meaning 8).
88. Applied.
89. Applied.
90. Not applied: the `% TODO p17` comment is kept because a run is pending.
91. Applied in modified form: "On copied notes, the tool-call write lowers accuracy significantly only at 4B." The suggested "lowers fact coverage" is not tested and does not hold at 14B.
92. Not applied: the 8B exact-match sentence was cut for space. The heading already says only 4B survives Holm.
93. Applied ("from -8.7 to -6.6 points").
94. Applied.
95. Applied in fig_scaling.py: the panel (a) title drops the cache size ("(a) Prefill: savings fade as payloads grow"). The caption gives 34,864. Re-rendered, lint clean.
96. Applied ("as payload and Researchers change", shortened to pass lint).
97. Applied.
98. Applied.
99. Applied.
100. Applied.
101. Applied ("an interval that allows a small residual loss").
102. Applied as "Separate folders also change the paths the Writer sees, which confounds this arm."
103. Applied ("..., but a larger tool budget does not.").
104. Applied ("on the 59 tasks that completed"). One task failed with a client error.
105. Applied, and the coincidence clause was dropped.
106. Applied.
107. Applied, shortened ("At 32B, B and C come from a rerun that fixes a harness bug (cross-run)").
108. Applied.
109. Applied.
110. Applied: resolved as the Researchers of broadcast and the pipe.
111. Applied ("against 7.8 originally").
112. Applied.
113. Applied.
114. Applied as "including ignored input, as in our unopened notes".
115. Applied.
116. Applied.
117. Applied.
118. Applied: the conclusion's recommendation is worded differently from the abstract's.
119. Applied.
120. Applied.
121. Applied (21 to 6 uses).
122. Applied (5 to 2 uses).
123. Applied: the legend now says "Tool-written". The prose uses "tool-written notes" for the level and "the tool-call write" for the effect.
124. Applied in prose ("File-based channels" in Figure 1, "An agent with file tools", "file-based channels' gaps", Related Work). Not applied in the Figure 2 legend ("File channels"), which is a figure label the item did not cover.
125. Applied in Serving and Runs (past tense for what was run).

## Other cuts for the 6-page limit (not requested by either review)

- Intro: "such as replaying one agent's notes into every channel" was removed (also fixes style 15).
- §4 cost paragraph: "It still sends about broadcast's tokens" was removed (Figure 2a shows it).
- Figure 2 caption: "Gray labels: cached share of prompt tokens" was removed. The panel labels say "% cached".
- Table 1 caption: "Files: the file channel." was removed.
- Replay control: C's Writer opening rate (63% vs 76%) was removed (style 75).
- Write-copy paragraph: the 8B exact-match interval was removed (style 92).
- k=16 paragraph: the coincidence sentence and "RTX PRO 6000" for the budget runs were removed (the PRO 6000 is the stated default).
- 32B rerun sentence: "with broadcast from the first run" was removed ("cross-run" carries it).
- Noise paragraph: "(all intervals within -3.6 to 3.1)" was removed.
- Several one-to-three-word trims that pull short last lines up. None of them changes a claim.
