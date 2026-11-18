# Related work: "Pipes, Files, or Handles? Revisiting IPC for LLM Multi-Agent Pipelines"

Compiled 2026-11-18.

**How entries were checked.** Every arXiv ID below was resolved through the arXiv API (`export.arxiv.org/api/query?id_list=...`), and the returned title, first author, and submission date were matched. Classic papers were resolved by DOI through the Crossref API. Venues come from the arXiv comment field, the ACL Anthology, USENIX pages, Crossref, or Semantic Scholar's venue field.

- **†** means the paper exists, but the exact venue/track is from Semantic Scholar or my own knowledge and was not confirmed on the venue's own page. Check it before camera-ready.
- **UNVERIFIED** means I could not confirm the item at all.
- Nothing in this list is fully UNVERIFIED. The one non-peer-reviewed item (TOAP, Zenodo) is labelled as such.

---

## 1. Multi-agent LLM frameworks and their communication styles

| Short name | Title | Authors | Venue / year | ID | URL |
| --- | --- | --- | --- | --- | --- |
| AutoGen | AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation | Q. Wu et al. | COLM 2024 (per Microsoft Research and AG2 publication pages) | arXiv:2308.08155 | https://arxiv.org/abs/2308.08155 |
| MetaGPT | MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework | S. Hong et al. | ICLR 2024 | arXiv:2308.00352 | https://arxiv.org/abs/2308.00352 |
| CAMEL | CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society | G. Li et al. | NeurIPS 2023 | arXiv:2303.17760 | https://arxiv.org/abs/2303.17760 |
| ChatDev | ChatDev: Communicative Agents for Software Development | C. Qian et al. | ACL 2024 | arXiv:2307.07924 | https://arxiv.org/abs/2307.07924 |
| AgentVerse | AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors | W. Chen et al. | ICLR 2024 | arXiv:2308.10848 | https://arxiv.org/abs/2308.10848 |
| MacNet | Scaling Large Language Model-based Multi-Agent Collaboration | C. Qian et al. | ICLR 2025 | arXiv:2406.07155 | https://arxiv.org/abs/2406.07155 |
| MegaAgent | MegaAgent: A Large-Scale Autonomous LLM-based Multi-Agent System Without Predefined SOPs | Q. Wang et al. | Findings of ACL 2025 | arXiv:2408.09955; DOI 10.18653/v1/2025.findings-acl.259 | https://arxiv.org/abs/2408.09955 |
| Multiagent debate | Improving Factuality and Reasoning in Language Models through Multiagent Debate | Y. Du et al. | ICML 2024 | arXiv:2305.14325 | https://arxiv.org/abs/2305.14325 |
| Generative Agents | Generative Agents: Interactive Simulacra of Human Behavior | J. S. Park et al. | UIST 2023 | arXiv:2304.03442; DOI 10.1145/3586183.3606763 | https://arxiv.org/abs/2304.03442 |
| LangGraph | LangGraph (documentation; no paper) | LangChain, Inc. | Software docs, accessed 2026-11 | none | https://docs.langchain.com/oss/python/langgraph/overview |
| MAS survey | Large Language Model based Multi-Agents: A Survey of Progress and Challenges | T. Guo et al. | IJCAI 2024 survey track† | arXiv:2402.01680 | https://arxiv.org/abs/2402.01680 |
| Protocol survey | A Survey of AI Agent Protocols | Y. Yang et al. | arXiv 2025 | arXiv:2504.16736 | https://arxiv.org/abs/2504.16736 |
| MCP/A2A survey | A survey of agent interoperability protocols: MCP, ACP, A2A, and ANP | A. Ehtesham et al. | arXiv 2025 | arXiv:2505.02279 | https://arxiv.org/abs/2505.02279 |

### Notes on each entry
- **AutoGen.** Agents talk through "conversable agents", and GroupChat broadcasts every message to all participants. This is our **A1 broadcast** channel. AutoGen treats the conversation as the only channel and does not measure its token or prefill cost. The GroupChat docs are at https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/design-patterns/group-chat.html.
- **MetaGPT.** Agents publish structured documents (PRDs, designs) to a shared message pool and subscribe by role. It is the closest framework analogue to publish/subscribe IPC, and it sits between our B (files) and D (handles). MetaGPT argues for structured artifacts on quality grounds, without a cost or prefill analysis.
- **CAMEL.** Two agents in a role-play hand messages back and forth, which is a point-to-point dialogue (pipe-like, but bidirectional). It is a classic example of pure message passing with no shared state.
- **ChatDev.** A waterfall of role-pair "chat chains" in which only phase outputs and summaries carry forward. It is effectively our **A2 pipe** with summaries. ChatDev reports cost but does not isolate the channel as a variable.
- **AgentVerse.** Dynamic expert recruitment with horizontal (shared discussion) and vertical (solver/reviewer) structures. It shows that the topology choice matters, but the channel stays full-text messages.
- **MacNet.** Agents are organized as DAGs, and only artifacts, not full dialogues, propagate along edges. It scales to more than 1,000 agents. It supports the "pass outputs, not transcripts" design (A2/D) at scale, without measuring prefill.
- **MegaAgent.** A large-scale MAS with shared files plus version-control-style merging of file changes. It is an early example of file-workspace coordination (our B/C), studied for autonomy rather than IPC cost.
- **Multiagent debate.** Every agent reads all other agents' answers each round (all-to-all broadcast). It is the canonical broadcast workload that later prefix-sharing systems (TokenDance, KVCOMM) target.
- **Generative Agents.** Agents keep a memory stream with retrieval and reflection. It is an early instance of "store in memory, retrieve on demand", the pull side of our D handles.
- **LangGraph.** Agents read and write a typed, shared graph state object with reducers. This is shared memory with structured fields, close to our C/D, and is useful as an industry reference point.
- **MAS survey (Guo et al.).** Categorizes communication paradigms (cooperative/debate/competitive) and structures (layered, decentralized, centralized, shared message pool). Use it as a taxonomy citation.
- **Protocol surveys.** Cover MCP, A2A, ACP, and ANP. They are relevant because A2A "artifacts" and MCP "resources" are handle-like references. These are protocol-level surveys with no cost measurements.

---

## 2. Communication efficiency, token cost, and failure studies

| Short name | Title | Authors | Venue / year | ID | URL |
| --- | --- | --- | --- | --- | --- |
| AgentPrune | Cut the Crap: An Economical Communication Pipeline for LLM-based Multi-Agent Systems | G. Zhang et al. | ICLR 2025 | arXiv:2410.02506 | https://arxiv.org/abs/2410.02506 |
| Optima | Optima: Optimizing Effectiveness and Efficiency for LLM-Based Multi-Agent System | W. Chen et al. | Findings of ACL 2025† | arXiv:2410.08115 | https://arxiv.org/abs/2410.08115 |
| G-Designer | G-Designer: Architecting Multi-agent Communication Topologies via Graph Neural Networks | G. Zhang et al. | ICML 2025 | arXiv:2410.11782 | https://arxiv.org/abs/2410.11782 |
| GPTSwarm | Language Agents as Optimizable Graphs | M. Zhuge et al. | ICML 2024 | arXiv:2402.16823 | https://arxiv.org/abs/2402.16823 |
| AgentDropout | AgentDropout: Dynamic Agent Elimination for Token-Efficient and High-Performance LLM-Based Multi-Agent Collaboration | Z. Wang et al. | ACL 2025 (long) | arXiv:2503.18891; DOI 10.18653/v1/2025.acl-long.1170 | https://aclanthology.org/2025.acl-long.1170/ |
| PACT | What Should Agents Say? Action-state Communication for Efficient Multi-Agent Systems | C. Huang et al. | arXiv, Jun 2026 | arXiv:2606.05304 | https://arxiv.org/abs/2606.05304 |
| TOAP | TOAP: The Token-Optimized Agent Protocol — Reference, Summary, or KV Cache? Measuring How Multi-Agent Systems Should Share Context | T. Sharma (single author) | Zenodo preprint, Jun 2026 (**not peer reviewed**) | DOI 10.5281/zenodo.20671083 | https://zenodo.org/records/20671083 |
| Cache-to-Cache (C2C) | Cache-to-Cache: Direct Semantic Communication Between Large Language Models | T. Fu et al. | ICLR 2026 | arXiv:2510.03215 | https://arxiv.org/abs/2510.03215 |
| LatentMAS | Latent Collaboration in Multi-Agent Systems | J. Zou et al. | ICML 2026 (spotlight, per arXiv comment) | arXiv:2511.20639 | https://arxiv.org/abs/2511.20639 |
| MAST | Why Do Multi-Agent LLM Systems Fail? | M. Cemri et al. | NeurIPS 2025 (Datasets & Benchmarks†) | arXiv:2503.13657 | https://arxiv.org/abs/2503.13657 |
| Complexity Trap | The Complexity Trap: Simple Observation Masking Is as Efficient as LLM Summarization for Agent Context Management | T. Lindenbauer et al. | DL4C workshop @ NeurIPS 2025 | arXiv:2508.21433 | https://arxiv.org/abs/2508.21433 |
| Robot-team orchestration | Persistent LLM Orchestration of Heterogeneous Robot Teams via Partial Delegation to Multi-Agent Protocols | M. G. Mendoza et al. | arXiv, Oct 2026 | arXiv:2610.15224 | https://arxiv.org/abs/2610.15224 |
| Lost in the Middle | Lost in the Middle: How Language Models Use Long Contexts | N. F. Liu et al. | TACL 2024 | arXiv:2307.03172 | https://arxiv.org/abs/2307.03172 |
| Anthropic MAS blog | How we built our multi-agent research system | Anthropic Engineering | Blog, Jun 2025 | none | https://www.anthropic.com/engineering/multi-agent-research-system |

### Notes on each entry
- **AgentPrune.** Identifies "communication redundancy" in spatio-temporal message graphs and prunes edges with a one-shot graph mask, cutting tokens at similar accuracy. This is the closest "channel cost" ML paper. It changes *who talks to whom*; we change *how* content moves (copy, file, or handle) and also count post-cache prefill.
- **Optima.** Trains agents (iterative SFT/DPO) to produce shorter, more effective messages. It compresses message *content* through training, while our setup is training-free and varies the channel only.
- **G-Designer.** Uses a GNN to generate a task-adaptive communication topology, reducing tokens. It is a topology-level optimization, orthogonal to our channel axis.
- **GPTSwarm.** Treats agents as optimizable computation graphs, with edges optimized for performance. It is a foundational "MAS as graph" work behind AgentPrune and G-Designer.
- **AgentDropout.** Drops redundant agents and edges per round (21.6% fewer prompt tokens than baselines). Another topology-pruning baseline for the "tokens" axis.
- **PACT ("What Should Agents Say?").** Compares five message-content strategies (full output, conclusion-only, brief summary, and others) on two topologies, and proposes compact action-state records. This is very close to our A1-vs-A2 question about message content. It measures tokens and accuracy but not file/handle channels or engine-level prefix-cache effects.
- **TOAP.** Compares passing a *reference* vs a *summary* vs a *transferred KV cache* between agents. It finds that summaries drop facts while references do not, and that same-model KV reuse speeds up prefill. This is conceptually the closest work to our handles (D) and zero-copy angle. It is a small-n, single-author, non-peer-reviewed Zenodo record, so cite it as concurrent work with that caveat.
- **Cache-to-Cache.** Agents communicate by projecting and fusing one model's KV cache into another's instead of text. It is the "true shared memory" extreme, which needs a learned fuser and changes model semantics; our zero-copy is exact prefix reuse with plain text.
- **LatentMAS.** Training-free latent-space collaboration through a shared latent working memory. Like C2C, it bypasses text, while we stay in text and exploit the serving engine.
- **MAST.** A taxonomy of 14 failure modes from 150+ traces. It includes inter-agent misalignment such as information withholding and ignoring other agents' input. It motivates our "information delivery/loss" metric, and our results can be mapped onto MAST's inter-agent categories.
- **Complexity Trap.** Simple observation masking matches LLM summarization for single-agent context management at lower cost. It supports the claim that cheap channel choices can match expensive summarization.
- **Robot-team orchestration (Mendoza et al.).** Full-history prompting (about 1.16M tokens) is replaced by a Markovian state summary (about 0.41M tokens) with *higher* success. It is a non-QA data point that broadcast history is costly and can hurt.
- **Lost in the Middle.** Accuracy drops for information placed mid-context. This is a mechanism for why broadcast (A1) can *lose* information despite delivering all tokens.
- **Anthropic blog.** An industry report that multi-agent systems consume many more tokens than chat; subagents write outputs to external storage and pass lightweight references. This is a practitioner instance of our D handles. It is a blog, so cite it as a footnote or URL. Secondary sources quote "~15x chat tokens", which I did not confirm on the page itself.

---

## 3. Shared memory, blackboard, and file-based coordination

| Short name | Title | Authors | Venue / year | ID | URL |
| --- | --- | --- | --- | --- | --- |
| bMAS / LbMAS | Exploring Advanced LLM Multi-Agent Systems Based on Blackboard Architecture | B. Han and S. Zhang | arXiv, Jul 2025 | arXiv:2507.01701 | https://arxiv.org/abs/2507.01701 |
| Blackboard for data discovery | LLM-Based Multi-Agent Blackboard System for Information Discovery in Data Science | A. Salemi et al. | arXiv, Sep 2025 | arXiv:2510.01285 | https://arxiv.org/abs/2510.01285 |
| STORM | Multi-agent Collaboration with State Management | M. Liu et al. | arXiv, May 2026 | arXiv:2605.20563 | https://arxiv.org/abs/2605.20563 |
| GVS5H (ledger) | GVS5H: Zero-Shot Self-Orchestration with Ledger-Based Control for Improved LLM Coding Performance | V. Gao et al. | arXiv, Aug 2026 | arXiv:2608.26480 | https://arxiv.org/abs/2608.26480 |
| Agentic File System | Everything is Context: Agentic File System Abstraction for Context Engineering | X. Xu et al. | arXiv, Dec 2025 | arXiv:2512.05470 | https://arxiv.org/abs/2512.05470 |
| File-native context | Structured Context Engineering for File-Native Agentic Systems: Evaluating Schema Accuracy, Format Effectiveness, and Multi-File Navigation at Scale | D. McMillan (single author) | arXiv, Feb 2026 | arXiv:2602.05447 | https://arxiv.org/abs/2602.05447 |
| MemGPT / Letta | MemGPT: Towards LLMs as Operating Systems | C. Packer et al. | arXiv 2023 | arXiv:2310.08560 | https://arxiv.org/abs/2310.08560 (Letta: https://www.letta.com/) |
| AIOS | AIOS: LLM Agent Operating System | K. Mei et al. | COLM 2025 | arXiv:2403.16971 | https://arxiv.org/abs/2403.16971 |
| LLM as OS | LLM as OS, Agents as Apps: Envisioning AIOS, Agents and the AIOS-Agent Ecosystem | Y. Ge et al. | arXiv 2023 | arXiv:2312.03815 | https://arxiv.org/abs/2312.03815 |
| Collaborative Memory | Collaborative Memory: Multi-User Memory Sharing in LLM Agents with Dynamic Access Control | A. Rezazadeh et al. | arXiv 2025 | arXiv:2505.18279 | https://arxiv.org/abs/2505.18279 |
| Intrinsic Memory Agents | Intrinsic Memory Agents: Heterogeneous Multi-Agent LLM Systems through Structured Contextual Memory | S. Yuen et al. | arXiv 2025 | arXiv:2508.08997 | https://arxiv.org/abs/2508.08997 |
| A-MEM | A-MEM: Agentic Memory for LLM Agents | W. Xu et al. | NeurIPS 2025 | arXiv:2502.12110 | https://arxiv.org/abs/2502.12110 |
| SWE-agent | SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering | J. Yang et al. | NeurIPS 2024† | arXiv:2405.15793 | https://arxiv.org/abs/2405.15793 |
| OpenHands | OpenHands: An Open Platform for AI Software Developers as Generalist Agents | X. Wang et al. | ICLR 2025 | arXiv:2407.16741 | https://arxiv.org/abs/2407.16741 |
| CoALA | Cognitive Architectures for Language Agents | T. R. Sumers et al. | TMLR 2024 | arXiv:2309.02427 | https://arxiv.org/abs/2309.02427 |
| Hearsay-II (classic) | The Hearsay-II Speech-Understanding System: Integrating Knowledge to Resolve Uncertainty | L. D. Erman et al. | ACM Computing Surveys 12(2), 1980 | DOI 10.1145/356810.356816 | https://doi.org/10.1145/356810.356816 |
| Blackboard model (classic) | The Blackboard Model of Problem Solving and the Evolution of Blackboard Architectures | H. P. Nii (single author) | AI Magazine 7(2), 1986 | DOI 10.1609/aimag.v7i2.537 | https://ojs.aaai.org/index.php/aimagazine/article/view/537 |
| Linda (classic) | Generative Communication in Linda | D. Gelernter (single author) | ACM TOPLAS 7(1), 1985 | DOI 10.1145/2363.2433 | https://doi.org/10.1145/2363.2433 |

### Notes on each entry
- **bMAS / LbMAS.** A shared blackboard is the only communication and memory channel, and a control unit picks the next agent. It reports competitive accuracy with fewer tokens. This is a shared-memory channel (our B/C), but every agent still reads the whole board, so it is broadcast-like in cost; they do not separate pushed vs pulled content or measure prefill.
- **Blackboard for data discovery (Salemi et al.).** A central agent posts requests and subordinate agents volunteer, with no central assignment. The work focuses on scaling to large data lakes; the blackboard is a coordination medium, not a cost-measured channel.
- **STORM.** Treats a shared code workspace as versioned files and mediates reads and writes to detect conflicts at write time, against a git-worktree-per-agent baseline. It shows that file workspaces need consistency control. Our pipeline is sequential, so we see the cost side without the concurrency side.
- **GVS5H.** Fresh instances of one model coordinate through a ledger in a shared file system, with large gains on LiveCodeBench. It is direct evidence that file-mediated coordination (our B/C) works well in practice.
- **Agentic File System.** An "everything is a file" abstraction that mounts memories, tools, and documents as governed context resources under a token budget. It is the closest *design* analogue to our files/handles channels; it proposes an abstraction and does not run a controlled channel comparison.
- **File-native context.** An empirical study of agents reading context through file operations versus prompt-stuffed context, across formats and model tiers. It supports B/C/D as viable and shows model-dependent effects.
- **MemGPT / Letta.** OS-style virtual context management (main context ↔ external storage through function calls). It is the intellectual ancestor of "pull details on demand", but single-agent.
- **AIOS.** An LLM agent OS with scheduler, context manager, memory manager, and storage manager (LSFS). It supplies the "agents need OS services" framing; we focus specifically on IPC between agents.
- **LLM as OS (Ge et al.).** A vision paper mapping OS concepts to LLM/agent concepts. It is a good citation for the OS analogy, though it does not discuss IPC trade-offs quantitatively.
- **Collaborative Memory.** Private vs shared memory tiers with access-control policies across users and agents. It is the shared-memory analogue with permissions, relevant if handles carry capabilities.
- **Intrinsic Memory Agents.** Per-agent structured JSON memory updated from each agent's own outputs, with high token efficiency. It is an alternative to broadcasting full transcripts.
- **A-MEM.** Zettelkasten-style linked memory notes for agents. It is relevant to our C (files + index).
- **SWE-agent and OpenHands.** Agents use file read/write/list/search tools through an agent-computer interface. They are the standard precedent for our B/C/D tool set, but single-agent and not focused on inter-agent communication.
- **CoALA.** A framework separating working memory from long-term episodic, semantic, and procedural memory. Use it for terminology.
- **Classics.** Cite Hearsay-II and Nii for the original blackboard architecture, and Linda for tuple-space shared-memory coordination (`out`/`in`/`rd` maps naturally onto write/read/list file tools).

---

## 4. KV-cache sharing across agents or requests (the zero-copy angle)

| Short name | Title | Authors | Venue / year | ID | URL |
| --- | --- | --- | --- | --- | --- |
| vLLM / PagedAttention | Efficient Memory Management for Large Language Model Serving with PagedAttention | W. Kwon et al. | SOSP 2023 | arXiv:2309.06180 | https://arxiv.org/abs/2309.06180 |
| vLLM APC docs | Automatic Prefix Caching (design doc) | vLLM project | Docs | none | https://docs.vllm.ai/en/latest/design/prefix_caching.html |
| SGLang / RadixAttention | SGLang: Efficient Execution of Structured Language Model Programs | L. Zheng et al. | NeurIPS 2024 | arXiv:2312.07104 | https://arxiv.org/abs/2312.07104 |
| Prompt Cache | Prompt Cache: Modular Attention Reuse for Low-Latency Inference | I. Gim et al. | MLSys 2024 | arXiv:2311.04934 | https://arxiv.org/abs/2311.04934 |
| CacheBlend | CacheBlend: Fast Large Language Model Serving for RAG with Cached Knowledge Fusion | J. Yao et al. | EuroSys 2025† | arXiv:2405.16444 | https://arxiv.org/abs/2405.16444 |
| KVLink | KVLink: Accelerating Large Language Models via Efficient KV Cache Reuse | J. Yang et al. | NeurIPS 2025 | arXiv:2502.16002 | https://arxiv.org/abs/2502.16002 |
| DroidSpeak | DroidSpeak: KV Cache Sharing Across Fine-tuned Model Variants (arXiv title: "...for Cross-LLM Communication and Multi-LLM Serving") | Y. Liu et al. | NSDI 2026 | arXiv:2411.02820 | https://www.usenix.org/conference/nsdi26/presentation/liu-yuhan |
| KVCOMM | KVCOMM: Online Cross-context KV-cache Communication for Efficient LLM-based Multi-agent Systems | H. Ye et al. | NeurIPS 2025 | arXiv:2510.12872 | https://arxiv.org/abs/2510.12872 |
| KVFlow | KVFlow: Efficient Prefix Caching for Accelerating LLM-Based Multi-Agent Workflows | Z. Pan et al. | NeurIPS 2025 | arXiv:2507.07400 | https://arxiv.org/abs/2507.07400 |
| TokenDance | TokenDance: Scaling Multi-Agent LLM Serving via Collective KV Cache Sharing | Z. Bian et al. | arXiv, Apr 2026 (under review) | arXiv:2604.03143 | https://arxiv.org/abs/2604.03143 |
| TokenCake | TokenCake: A KV-Cache-centric Serving Framework for LLM-based Multi-Agent Applications | Z. Bian et al. | EuroSys 2027 (accepted, per arXiv comment) | arXiv:2510.18586 | https://arxiv.org/abs/2510.18586 |
| CacheScout | Learning Agent Execution for KV-Cache Management in Agentic Serving | R. Zhang et al. | arXiv, Jul 2026 | arXiv:2608.14624 | https://arxiv.org/abs/2608.14624 |
| Parrot | Parrot: Efficient Serving of LLM-based Applications with Semantic Variable | C. Lin et al. | OSDI 2024 | arXiv:2405.19888 | https://arxiv.org/abs/2405.19888 |
| Autellix | Autellix: An Efficient Serving Engine for LLM Agents as General Programs | M. Luo et al. | arXiv 2025 | arXiv:2502.13965 | https://arxiv.org/abs/2502.13965 |
| Continuum | Continuum: Efficient and Robust Multi-Turn LLM Agent Scheduling with KV Cache Time-to-Live | H. Li et al. | arXiv 2025 | arXiv:2511.02230 | https://arxiv.org/abs/2511.02230 |
| Don't Break the Cache | Don't Break the Cache: An Evaluation of Prompt Caching for Long-Horizon Agentic Tasks | E. Lumer et al. | arXiv, Jan 2026 | arXiv:2601.06007 | https://arxiv.org/abs/2601.06007 |
| Hydragen | Hydragen: High-Throughput LLM Inference with Shared Prefixes | J. Juravsky et al. | arXiv 2024 | arXiv:2402.05099 | https://arxiv.org/abs/2402.05099 |
| ChunkAttention | ChunkAttention: Efficient Self-Attention with Prefix-Aware KV Cache and Two-Phase Partition | L. Ye et al. | ACL 2024 | arXiv:2402.15220 | https://arxiv.org/abs/2402.15220 |
| Preble | Preble: Efficient Distributed Prompt Scheduling for LLM Serving | V. Srivatsa et al. | ICLR 2025 | arXiv:2407.00023 | https://arxiv.org/abs/2407.00023 |
| CachedAttention | Cost-Efficient Large Language Model Serving for Multi-turn Conversations with CachedAttention | B. Gao et al. | USENIX ATC 2024 | arXiv:2403.19708 | https://arxiv.org/abs/2403.19708 |
| LMCache | LMCache: An Efficient KV Cache Layer for Enterprise-Scale LLM Inference | Y. Liu et al. | arXiv 2025 | arXiv:2510.09665 | https://arxiv.org/abs/2510.09665 |
| Mooncake | Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving | R. Qin et al. | FAST 2025† (extended in ACM TOS) | arXiv:2407.00079 | https://arxiv.org/abs/2407.00079 |
| PrefillShare | PrefillShare: A Shared Prefill Module for KV Reuse in Multi-LLM Disaggregated Serving | S. Woo et al. | arXiv, Feb 2026 | arXiv:2602.12029 | https://arxiv.org/abs/2602.12029 |
| ForkKV | ForkKV: Scaling Multi-LoRA Agent Serving via Copy-on-Write Disaggregated KV Cache | S. Wang et al. | arXiv, Apr 2026 | arXiv:2604.06370 | https://arxiv.org/abs/2604.06370 |

### Notes on each entry
- **PagedAttention and APC.** Paged KV blocks, plus a block-hash prefix cache: each full block is hashed together with its parent hash and token IDs. This is exactly the mechanism our zero-copy A1 exploits. Cite PagedAttention for the paging and the APC doc for the hashing semantics; APC has no paper of its own.
- **SGLang / RadixAttention.** A radix tree over token prefixes for automatic KV reuse, plus cache-aware scheduling. It is the other mainstream prefix cache. Our ordering trick is engine-agnostic and should transfer to it.
- **Prompt Cache.** Reuses attention states of predefined prompt *modules* at non-prefix positions through a schema. Unlike our approach, it needs a prompt schema and tolerates position shifts.
- **CacheBlend.** Fuses precomputed KV caches of non-prefix chunks (RAG) with selective recompute to fix cross-attention. It is approximate, while our zero-copy is an exact prefix hit obtained by reordering.
- **KVLink.** Precomputes document KV independently and concatenates it, with positional re-encoding and fine-tuning. It is another non-prefix reuse method that requires model changes.
- **DroidSpeak.** Shares KV across *different* fine-tuned models of the same architecture by recomputing a few layers. It is relevant when Researcher/Writer/Reviewer use different models; ours use one model, so plain prefix caching suffices.
- **KVCOMM.** Directly targets the multi-agent case: when an agent receives a predecessor's message, the full context is reprocessed. KVCOMM reuses KV across agents despite diverging prefixes by estimating offset deviations from anchors. This is **the closest systems work to our zero-copy A1**. KVCOMM changes the engine and approximates; we avoid divergence by *ordering the prompt* so the shared part is a true prefix, which needs no engine change and is exact.
- **KVFlow.** Workflow-aware eviction and prefetch: it models agent schedules as an Agent Step Graph to keep agents' fixed prompts cached. It is complementary, since it improves cache retention while we increase the shareable prefix.
- **TokenDance.** Targets the "All-Gather" round in which every agent receives all outputs, exactly our A1 broadcast. It shares KV collectively and stores sibling caches as diffs. It is the strongest systems evidence that broadcast creates massive KV redundancy, measured with engine changes; we measure logical-vs-physical cost across *channel* choices.
- **TokenCake.** Agent-aware KV scheduling: it offloads idle caches during function calls and partitions memory. Relevant to the B/C/D channels, where tool calls create pauses.
- **CacheScout.** Learns agent execution transitions to drive KV eviction and prefetch. It reports that fixed agent context is 53–62% of prompt tokens in MAS workloads, which supports why prefill (not logical tokens) is the right cost metric.
- **Parrot.** "Semantic Variables" expose inter-call dataflow to the serving system, enabling prefix sharing and dataflow scheduling. A semantic variable is close to our handle; Parrot exploits it in the engine, while we compare it with other channels at the application level.
- **Autellix.** Program-level scheduling for agentic programs to cut head-of-line blocking. It is relevant to end-to-end latency, not channel design.
- **Continuum.** Keeps KV across tool-call pauses using a time-to-live, which matters for our file-tool channels (B/C/D) because tool calls break reuse.
- **Don't Break the Cache.** Evaluates provider prompt caching for agentic tasks: full-context caching can *hurt* latency, and putting dynamic content last is recommended. It is empirical support for our zero-copy ordering rule (stable shared content first, per-agent content last), measured on commercial APIs rather than an open engine.
- **Hydragen and ChunkAttention.** Kernel-level shared-prefix attention. Background for why shared prefixes are cheap.
- **Preble, CachedAttention, LMCache, and Mooncake.** Prefix-aware distributed scheduling, multi-turn KV persistence, and KV storage layers. Use them as background for "prefix caching is now standard infrastructure".
- **PrefillShare and ForkKV.** 2026 multi-model and multi-LoRA KV sharing for agents. Relevant if the paper discusses per-role specialized models.

---

## 5. Classic OS IPC work (for the analogy)

| Short name | Title | Authors | Venue / year | DOI | URL |
| --- | --- | --- | --- | --- | --- |
| Duality | On the Duality of Operating System Structures | H. C. Lauer and R. M. Needham | ACM SIGOPS OSR 13(2), 1979 | 10.1145/850657.850658 | https://doi.org/10.1145/850657.850658 |
| UNIX (pipes) | The UNIX Time-Sharing System | D. M. Ritchie and K. Thompson | CACM 17(7), 1974 | 10.1145/361011.361061 | https://doi.org/10.1145/361011.361061 |
| RC 4000 nucleus | The Nucleus of a Multiprogramming System | P. Brinch Hansen (single author) | CACM 13(4), 1970 | 10.1145/362258.362278 | https://doi.org/10.1145/362258.362278 |
| Mach | Mach: A New Kernel Foundation for UNIX Development | M. Accetta et al. | USENIX Summer Conference 1986 (no DOI) | none | https://home.cs.colorado.edu/~rhan/CSCI_5573_Fall_2011/Papers/accetta86.pdf |
| Mach memory/communication duality | The Duality of Memory and Communication in the Implementation of a Multiprocessor Operating System | M. Young et al. | SOSP 1987 | 10.1145/41457.37507 | https://doi.org/10.1145/41457.37507 |
| L4 IPC | Improving IPC by Kernel Design | J. Liedtke (single author) | SOSP 1993 | 10.1145/168619.168633 | https://doi.org/10.1145/168619.168633 |
| Microkernel construction | On µ-Kernel Construction | J. Liedtke (single author) | SOSP 1995 | 10.1145/224056.224075 | https://doi.org/10.1145/224056.224075 |
| LRPC | Lightweight Remote Procedure Call | B. N. Bershad et al. | ACM TOCS 8(1), 1990 (SOSP 1989) | 10.1145/77648.77650 | https://doi.org/10.1145/77648.77650 |
| RPC | Implementing Remote Procedure Calls | A. D. Birrell and B. J. Nelson | ACM TOCS 2(1), 1984 | 10.1145/2080.357392 | https://doi.org/10.1145/2080.357392 |
| fbufs | Fbufs: A High-Bandwidth Cross-Domain Transfer Facility | P. Druschel and L. L. Peterson | SOSP 1993 | 10.1145/168619.168634 | https://doi.org/10.1145/168619.168634 |
| IO-Lite | IO-Lite: A Unified I/O Buffering and Caching System | V. S. Pai et al. | ACM TOCS 18(1), 2000 (OSDI 1999) | 10.1145/332799.332895 | https://doi.org/10.1145/332799.332895 |
| Capabilities | Programming Semantics for Multiprogrammed Computations | J. B. Dennis and E. C. Van Horn | CACM 9(3), 1966 | 10.1145/365230.365252 | https://doi.org/10.1145/365230.365252 |
| Multikernel | The Multikernel: A New OS Architecture for Scalable Multicore Systems | A. Baumann et al. | SOSP 2009 | 10.1145/1629575.1629579 | https://doi.org/10.1145/1629575.1629579 |

### Notes on each entry
- **Duality (Lauer & Needham).** Message-oriented and procedure/shared-state-oriented systems are duals with equivalent performance when implemented well. This is the natural framing for "pipes vs files", and our result can be read as the duality breaking because tokens are not free to copy and prefix caching is order-sensitive.
- **UNIX (Ritchie & Thompson).** The origin of pipes and of the "file as universal interface" idea, which correspond to our A2 and B.
- **RC 4000 nucleus (Brinch Hansen).** The first message-passing kernel, a historical anchor for message-based IPC.
- **Mach and Mach memory/communication duality.** Mach sends large messages by copy-on-write VM remapping instead of copying. This is the OS precedent for our "zero-copy" A1: the logical message is large, but the physical cost is shared.
- **L4 IPC and microkernel construction (Liedtke).** Fast IPC by kernel design (register passing, direct process switch) shows that the IPC mechanism, not the abstraction, dominated cost. This parallels our finding that the engine's prefix cache, not logical tokens, sets real cost.
- **LRPC and RPC.** LRPC optimizes the common same-machine case with shared argument stacks. Map the analogy carefully: our agents share one engine, much like same-machine RPC.
- **fbufs and IO-Lite.** Zero-copy cross-domain buffer transfer and unified buffering. These are direct analogues of reusing one KV copy across agents.
- **Capabilities (Dennis & Van Horn).** Capabilities are unforgeable references to objects. Our D "handles" are references, so cite this if you discuss handle naming or access control.
- **Multikernel (Barrelfish).** Revisits shared memory vs message passing on modern hardware and chooses explicit messages. A modern precedent for "revisit IPC when the cost model changes", which is exactly our title's move.

The Silberschatz textbook chapter is already cited.

---

## 6. Evaluation methodology (datasets and LLM-as-judge)

| Short name | Title | Authors | Venue / year | ID | URL |
| --- | --- | --- | --- | --- | --- |
| HotpotQA | HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering | Z. Yang et al. | EMNLP 2018 | arXiv:1809.09600; ACL D18-1259 | https://aclanthology.org/D18-1259/ |
| 2WikiMultihopQA | Constructing A Multi-hop QA Dataset for Comprehensive Evaluation of Reasoning Steps | X. Ho et al. | COLING 2020 | arXiv:2011.01060; ACL 2020.coling-main.580 | https://aclanthology.org/2020.coling-main.580/ |
| MuSiQue | MuSiQue: Multihop Questions via Single-hop Question Composition | H. Trivedi et al. | TACL 2022 | arXiv:2108.00573 | https://arxiv.org/abs/2108.00573 |
| Bamboogle / compositionality gap | Measuring and Narrowing the Compositionality Gap in Language Models | O. Press et al. | Findings of EMNLP 2023 | arXiv:2210.03350 | https://arxiv.org/abs/2210.03350 |
| FActScore | FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation | S. Min et al. | EMNLP 2023 | arXiv:2305.14251; ACL 2023.emnlp-main.741 | https://aclanthology.org/2023.emnlp-main.741/ |
| SAFE / LongFact | Long-form factuality in large language models | J. Wei et al. | NeurIPS 2024 | arXiv:2403.18802 | https://arxiv.org/abs/2403.18802 |
| MT-Bench | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | L. Zheng et al. | NeurIPS 2023 (Datasets & Benchmarks) | arXiv:2306.05685 | https://arxiv.org/abs/2306.05685 |
| G-Eval | G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment | Y. Liu et al. | EMNLP 2023 | arXiv:2303.16634; DOI 10.18653/v1/2023.emnlp-main.153 | https://arxiv.org/abs/2303.16634 |
| Judging the Judges | Judging the Judges: Evaluating Alignment and Vulnerabilities in LLMs-as-Judges | A. S. Thakur et al. | GEM Workshop 2025 (ACL) | arXiv:2406.12624 | https://aclanthology.org/2025.gem-1.33/ |
| JUDGE-BENCH | LLMs instead of Human Judges? A Large Scale Empirical Study across 20 NLP Evaluation Tasks | A. Bavaresco et al. | ACL 2025 | arXiv:2406.18403 | https://arxiv.org/abs/2406.18403 |
| Self-preference | LLM Evaluators Recognize and Favor Their Own Generations | A. Panickssery et al. | NeurIPS 2024 | arXiv:2404.13076 | https://arxiv.org/abs/2404.13076 |
| Qwen3 | Qwen3 Technical Report | A. Yang et al. | arXiv 2025 | arXiv:2505.09388 | https://arxiv.org/abs/2505.09388 |

### Notes on each entry
- **HotpotQA and 2WikiMultihopQA.** Our two datasets. 2Wiki adds evidence chains (reasoning-path annotations), which can ground the "information delivery" metric by checking whether each hop's evidence reaches the Writer and Reviewer.
- **MuSiQue and Bamboogle.** Optional harder multi-hop sets that resist shortcuts. Cite them if you discuss dataset limitations.
- **FActScore.** Decomposes text into atomic facts and checks each against a source. This is the natural template for measuring information delivery and loss between agents at the fact level.
- **SAFE / LongFact.** LLM agent fact-checking with search, showing LLM raters can agree with or beat crowdworkers. Supports using an LLM judge for fact checks.
- **MT-Bench.** The canonical LLM-as-judge agreement study (about 80% agreement with humans), which also documents position, verbosity, and self-enhancement biases.
- **G-Eval.** A CoT plus form-filling judge with improved human correlation. A baseline judge design.
- **Judging the Judges and JUDGE-BENCH.** Show that judge agreement varies widely across models and tasks, and that judges can be lenient or manipulable. Cite them to justify reporting judge-human agreement on a sample, or using a judge from a different model family than Qwen3.
- **Self-preference.** Judges favor their own generations. Using Qwen3-8B as both generator and judge would be exposed to this bias, so cite it with a mitigation.
- **Qwen3.** Our base model.

---

## Closest prior work and how our paper differs

The four closest works each cover one slice of our question.

1. **TOAP (Sharma, Zenodo 2026).** Asks almost our exact question — reference vs summary vs KV transfer between agents — and finds summaries lose facts while references do not. It is a small-n, non-peer-reviewed study on commercial APIs (plus a separate T4 KV-bridge microbenchmark). It does not run a single controlled pipeline that varies broadcast/pipe/files/index/handles on a production engine with automatic prefix caching, or report post-cache prefill alongside billing tokens.
2. **PACT, "What Should Agents Say?" (Huang et al., 2026).** Also varies what crosses the inter-agent channel (full output vs conclusion vs summary vs action-state). It stays inside message passing and optimizes message *content*. We add the shared-state channels (files, index, handles) and show that logical-token savings and real prefill savings can diverge once the engine caches prefixes.
3. **KVCOMM (NeurIPS 2025) and TokenDance (2026).** Attack the same redundancy our zero-copy A1 exploits: broadcast and all-gather contexts re-prefilled per agent. Both modify the serving engine and, in KVCOMM's case, approximate KV for diverging prefixes. Our zero-copy variant gets exact reuse on unmodified vLLM purely by prompt ordering, and we position it as one IPC option against non-copying channels rather than as a serving system.
4. **AgentPrune / AgentDropout / G-Designer (topology pruning) and LbMAS (blackboard).** Reduce MAS tokens by changing who communicates, or replace messages with a shared board. They measure logical tokens only. We hold topology fixed (Researcher → Writer → Reviewer) and isolate the channel, framing the space with OS IPC (Lauer & Needham's duality, Mach's copy-on-write messaging, capabilities as handles). We report both the billing view and the physical prefill, latency, and file-I/O view, plus fact-level information loss.
