# Round 10 fix log

Snapshot before this pass: `cs632-store/main_pre_fix10.tex`. Build: 6 pages including references, no undefined
references, no overfull boxes. Every number is a macro from `paper/numbers.tex`; `python -m agentipc.paper_numbers`
reports no skipped section. Figure 2, Figure 3 and Table 1 sit on separate pages from Figure 4. Fig. 4 re-rendered
(archfig lint clean). Fig. 3 re-rendered after a docstring fix (lint clean).

Macros added (`src/agentipc/paper_numbers.py`): ConcWord (round10_text), KEightPerSet, KSixteenPerSet, ScaleNMain,
ScaleNEight, ScaleNSixteen (scaling), PSizeGapBMin, PSizeGapBMax, PSizeGapCMin, PSizeGapCMax (pro6000). Precision
changes (same values, one decimal now): Gap{ch}Min/Max, Gap{ch}K{k}, ZcEmGapMax, PSize{size}Gap{ch}(Lo/Hi),
Rep{ch}Gap(Lo/Hi).

## Meaning audit

- MA1 applied. Merged with A3: "Writing the Researcher's notes through a tool call costs accuracy at three of four model sizes when the notes are copied forward (at one after Holm correction)".
- MA2 applied ("cost plain files").
- MA3 applied in the abstract and the conclusion.
- MA4 applied. Merged with I7 into one sentence ("..., but not through files, where a plain reply stored as a file does no better than tool-written notes").
- MA5 applied. Kept "when work fans out" and merged I8's numbers.
- MA6 applied.
- MA7 applied ("we run each channel alone ... at six tasks at a time, and broadcast, zero-copy, and B also at 32"). Checked against `p11_c32_{A1,A1zc,B}` configs.
- MA8 applied. Checked `p10_write_*` and `p16_*` configs (max_tokens 4096).
- MA9 applied. Checked in fig_tradeoff.py (the "% cached" labels are gray5, in (b) only).
- MA10 applied with a correction. Data show copied tool writes at 14B are 74.4% against copied replies' 74.2%, so the caption says "Copied replies are the most accurate arm at every size, tied with copied tool writes at 14B". fig_split.py docstring updated to match.
- MA11 applied (heading).
- MA12 applied.
- MA13 applied, in present tense per R23.
- MA14 applied.
- MA15 applied. Fig. 4b retitled "(b) Accuracy: B drops at k=16, where three Researchers share a folder". To keep it on the canvas, both panel titles went from 7.5 to 7.3 pt and (b) moved 1.5 pt left. Lint clean.
- MA16 applied.
- MA17 applied.
- MA18 applied, in present tense per K3.
- MA19 applied ("Splitting the loss between them step by step gives each a share that depends on the order, so the crossed runs vary both at once").

## Coverage

- C-1 applied. Tasks: "We also draw 100 (k=8) and 30 (k=16) tasks per dataset". Fig. 4 caption: 300/200/60 tasks. New macros come from configs `t08_k8` and `t08_large` and from fig4 data n.
- C-2 applied (fan-out sentence at the end of §2's first paragraph). No reason is given. The code records it only as a design choice ("as in an orchestrator-worker fan-out").
- C-3 applied (same as MA6).
- C-4 applied in part. Added the repairs list to Runs. Named the earlier run in §5 ("an earlier all-channel run on these tasks on the RTX PRO 6000"). The wording run is named where used. "Smaller controls are described where used" was added and then cut for the page budget.
- C-5 applied (Runs defines the crossed runs and their arms).
- C-6 not applied (author decision). There is no mention of a local vLLM build, and "vLLM v0.33.0" is unchanged.
- C-7 applied ("its KV cache capped at 100k tokens at every size unless stated otherwise"; "35k (the RTX 3090's)"). Checked in queue_pro6000.sh (6,250 blocks for every size; 2,179 blocks = 34,864).
- C-8 applied (§5 reports zero-copy at 100k and 400k: 0.36x and 0.36x).
- C-9 applied (Runs now lists serving time, crossed runs, cache, parallel writers, then model size).
- C-10 applied. The pipe/B/C times now come before the 32-at-a-time result, and Methods states which channels ran at 32.
- C-11 applied as "(main run with Qwen3-8B, k=3, ...)". "On the RTX 3090 servers" was dropped for space, because the main run is defined as the RTX 3090 run.
- C-12 applied ("uses the main run (Qwen3-8B, k=3, datasets pooled) except where noted").
- C-13 applied (Harness: "Table 1 adds paired permutation tests with Holm correction over its 16 simple effects"). The caption explanation was dropped.
- C-14 applied ("so that fewer tool-call writes of the notes are cut off"). The reason comes from the round-5 methods review W1 (truncated A1w writes at 2,048) and the p10 commit that raised the cap.
- C-15 applied ("tasks" for rescues and concurrency).
- C-16 applied. Adds "fact coverage", "Cohen's κ", and "a prediction at most four words longer" (taken from metrics.py: `len(pred) <= len(gold) + 4`).
- C-17 applied (Sensitivity opener mentions noise, and Harness points to §5).
- C-18 applied ("The Researchers of broadcast and the pipe, whose prompts are identical"). Checked in pipeline.py: both use OUTPUT_MSG and the same user message.
- C-19 applied ("larger payloads of §5").
- C-20 no change needed (35k is defined in Runs by C-7).
- C-21 applied. The notes-length result moved to §4's zero-copy accuracy paragraph, where it now says "on average".
- C-22 not applied (optional reorder). The page budget and float placement were already at the limit.

## Style and grammar

- T1 applied ("in inter-process communication (IPC)").
- A1 applied ("We vary only this choice, the channel, ... served by vLLM, using ...").
- A2 applied ("At three questions, its accuracy difference from broadcast has a 95% interval of ...").
- A3 applied (merged with MA1).
- A4 applied with MA2's "plain files" ("against one Researcher, and separate folders recover 19.8").
- I1 applied. I2 applied. I3 applied.
- I4 applied as "The serving engine must prefill ..." and "The engine's prefix cache changes both costs". The suggested "Its" would have pointed back to the tool call.
- I5 applied. I6 applied.
- I7 applied (merged with MA4). I8 applied (merged with MA5). I9 applied.
- F1 applied.
- C1 applied. C2 applied.
- C3 applied as "which A1 puts in the system prompt". "First" was dropped because A1's system prompt starts with the shared team text (pipeline.py).
- C4 applied (moved per C-21, with "on average"). C5 applied.
- C6 applied. Checked in workspace.py (refresh_index after each write).
- F2 applied, then the caption sentence was compressed for space ("Broadcast is the most accurate channel, files are the most expensive (a), and zero-copy computes about the pipe's prefill (b)"). The arrow label in the figure still says "no significant loss".
- M1 applied. M2 applied ("with its supporting sentences marked"). M3 applied.
- M4 applied (new macro \nConcWord = six). 32 stays a numeral.
- M5 applied. M6 applied with MA6's parenthetical. M7 applied (reworded).
- M8 applied (declarative sentences, no rhetorical questions).
- M9 applied. M10 applied.
- M11 applied. "Crossed runs" is defined once in Runs and used in Harness, the Table 1 caption, the Fig. 3 caption and §4.
- M12 applied. M13 applied (\nAccB, \nAccC). M14 applied. M15 applied. M16 applied.
- M17 applied by naming the runs in place (R18, S7).
- R1 applied for the first sentence. The roadmap sentence was cut for the page budget (the assessment also flags opener lists).
- R2 applied.
- R3 applied in corrected form: "Broadcast puts each role's instruction in the system prompt, ahead of the shared history, so consecutive prompts share almost no prefix." The prompts start with the shared team text, not the role instruction.
- R4 applied. R5 applied. R6 applied (deleted).
- R7 applied. The setup (Qwen3-8B, RTX PRO 6000, six at a time) is now stated once in Runs and not repeated here, for space.
- R8 applied. R9 applied (range deleted). R10 applied.
- R11 applied as "Zero-copy thus pays off mainly where prefill is billed". "We turn to accuracy" was deleted.
- R12 applied. R13 applied. R14 applied.
- R15 applied with a tag in the interval parentheses: "(3.5 to 10.2, cross-run), but its difference from broadcast is still −3.0 points (−5.3 to −0.7)".
- R16 applied (deleted).
- TB1 applied ("Each effect: the arm right of the arrow minus the one left"). The arms are defined in Runs and in the Fig. 3 caption.
- TB2 applied ("Interaction (untested)").
- F3 applied as "(a) Fact coverage of the notes (AlignScore)", using the C-16 term.
- F3b superseded by MA10.
- F3c superseded. The caption no longer names an agent for the save ("as notes.md for a reply"), and Runs says "a reply saved as notes.md".
- R17 superseded by MA19.
- R18 applied with a correction. RSixWordingNullBound is the widest interval end, not an estimate, so the text reads "these instructions raised accuracy over broadcast's by 6.2 points (2.9 to 9.6) at 4B, and their intervals at 8B to 32B lay within ±3.1 points". Direction checked: RSixFourWording = A1r − A1.
- R19 applied ("though only 4B survives Holm correction. At these three sizes, its notes state fewer supporting facts ...").
- R20 applied.
- R21 superseded by MA12 (sentence kept with the corrected qualifier).
- R22 applied. R23 applied.
- R24 applied ("the Writer" plus the clause "so the open rates leave the stored reply's deficit at 14B unexplained").
- F4 applied (the caption now also says "relative to A1" to save space).
- R25 applied. R26 applied. R27 applied. R28 applied. R29 applied.
- S1 applied ("This section varies payload and cache size, the number of Researchers, and model size, and measures run-to-run noise").
- S2 applied. S3 applied (checked: PKvAccShiftMax is the largest per-channel range across the three caches).
- S4 applied ("at 0.37x broadcast's prefill"). S5 applied.
- S6 applied with a correction. The guard recovers 15.1 of 30.4 (49.7%), so "half or more" would overstate it. The heading says "about half of B's loss or more".
- S7 applied, with the C-4 naming.
- S8 applied with a correction plus MA14. The text says "missed the final answer file", because rescue.py counts final.md files written under workspace/.
- S9 applied.
- S10 applied (one decimal through the generator).
- S11 applied by cutting the 14B C-versus-B sentence, since no reason is supported by the data.
- S12 applied (same as C-18). S13 applied.
- W1 applied by cutting the sentence. The intro already says prior work keeps the channel fixed.
- W2 not applied. The suggested tie ("which the file channels' many calls would need") claims a need we did not measure.
- K1 applied. K2 applied. K3 applied (present tense for findings).
- K4 applied. The restating sentence was removed, and the MA18 sentence was kept.
- K5 applied. K6 applied.
- G1 applied ("across runs" / "(cross-run)" only where a paired reading is possible, plus MA14's tag).
- G2 applied.
- G3 applied in part. The lead-in closers were deleted, but the zero-copy paragraphs were not merged, so the claim headings stay.
- G4 applied. The generator emits one decimal for setting gaps, k-scaling gaps, the exact-match gap, model-size gaps and replay gaps. The model-size ranges are now computed (PSizeGap{B,C}{Min,Max}) over 4B, 8B, 14B and the 32B rerun. With decimals, the old hard-coded endpoints would be wrong: C's minimum is the 32B rerun's 8.2.

## Cuts made only for the page budget (content kept elsewhere or restated)

- Results roadmap sentence. "So a loss of up to 2.9 points is not excluded" (restates the interval).
- §2 "Every token is still sent ..." (§4 says zero-copy sends broadcast's tokens). Intro "For LLM agents, the costs look different."
- Runs "Smaller controls are described where used." Related Work "All of these keep the channel fixed" and the vLLM/SGLang clause (both cited in the intro).
- Conclusion: the "Through files ..." restatement.
- Fig. 3 caption: "one interleaved run each" and "with 95% intervals" (the panel title states it).
- Many word-level trims that keep each number, interval, condition and sample size.
