# Reinforcement Learning & Post-training: Practice Quiz

**For:** the paper quiz at the start of class, Thu Nov 19, 2026.
**Source:** [07a RL and Post-training - primer.md](07a%20RL%20and%20Post-training%20-%20primer.md) (Karpathy, *Deep Dive into LLMs like ChatGPT*, the three required segments).

**How to use it:** Section A is the core quiz (20 questions). Circle one answer each, then check the key at the bottom. Section B covers smaller details. Section C is a 2-minute speed round. Every answer comes from the primer, and the key says which part.

---

## Section A: Core (20 questions)

**1.** Karpathy describes a **base model** (after pre-training only) as:
- A. A helpful, truthful, harmless assistant
- B. An internet document simulator on the token level
- C. A reward model that scores text
- D. A search engine over the training data

**2.** Compared with pre-training, post-training (SFT) is:
- A. About as expensive, because it uses the same algorithm
- B. More expensive, because humans must write the data
- C. Much cheaper and shorter (hours vs. months), because the dataset is much smaller
- D. Done first, before pre-training

**3.** What changes when you move from pre-training to supervised fine-tuning?
- A. Only the dataset: internet documents are swapped for conversations
- B. The training algorithm is replaced by reinforcement learning
- C. The model architecture is rebuilt from scratch
- D. Engineers write rules in code for how the assistant should behave

**4.** Karpathy calls SFT "programming by example." This means:
- A. Labelers write Python code that controls the assistant
- B. The assistant's behavior is implicitly programmed by the dataset of example conversations
- C. The model copies code examples from GitHub
- D. Each new behavior requires a new model architecture

**5.** Special tokens such as `<|im_start|>` and `<|im_end|>` are:
- A. Common internet words the model saw a lot in pre-training
- B. Scores the reward model attaches to each answer
- C. Markers for the end of a document in pre-training
- D. New tokens created in post-training to mark turns and roles in a conversation

**6.** In InstructGPT (OpenAI, 2022), the SFT conversations were written by:
- A. Human contractors following labeling instructions (helpful, truthful, harmless)
- B. GPT-3 itself, with no human involvement
- C. Users of ChatGPT through thumbs-up/thumbs-down buttons
- D. A reward model

**7.** According to Karpathy, when you talk to ChatGPT you are essentially talking to:
- A. A database lookup of verified facts
- B. A model that researches every answer from scratch
- C. A statistical simulation of a human labeler following the company's labeling instructions
- D. A live human expert

**8.** In Karpathy's textbook analogy, **reinforcement learning** corresponds to:
- A. Reading the exposition (explanatory text)
- B. Studying worked examples with expert solutions
- C. Writing the textbook
- D. Doing practice problems where you know the final answer but not the solution

**9.** In the same analogy, **SFT** corresponds to:
- A. Studying worked examples (imitating experts)
- B. Reading the exposition
- C. Doing practice problems
- D. Taking the final exam

**10.** Why shouldn't we rely only on human-written solutions to train the model to solve problems?
- A. Human solutions are always wrong
- B. Humans don't know which token sequences work best for the LLM: its cognition is different and it has limited computation per token
- C. Human solutions are too expensive to store
- D. The model can't read human handwriting

**11.** In RL, where do the solutions the model trains on come from?
- A. Expert human annotators
- B. The reward model
- C. The model itself: it generates many attempts and keeps the ones that reach the right answer
- D. Copies of the answer key

**12.** Which describes RL ("guess and check") correctly?
- A. Train once on a single human solution per problem
- B. Generate many solutions per prompt, check them against the known answer, and train on the ones that worked
- C. Have humans rate every attempt the model makes
- D. Delete wrong answers from the pre-training data

**13.** What is SFT's role once you also do RL?
- A. It's no longer needed
- B. It replaces pre-training
- C. It's used only to train the reward model
- D. It initializes the model "into the vicinity of correct solutions," and RL dials it in

**14.** Which task is an **unverifiable** domain?
- A. Writing a joke about pelicans
- B. Solving a math problem with a boxed answer
- C. Playing Go
- D. Checking whether code passes its tests

**15.** Why can't humans directly score every attempt during RL on unverifiable tasks?
- A. Humans can't read model output
- B. It's illegal to pay labelers for scoring
- C. RL needs far too many scores (Karpathy's example: about 1 billion)
- D. Scores are only possible for math

**16.** In RLHF, what do humans actually provide?
- A. The ideal joke for every prompt
- B. Rankings (orderings) of several model outputs, from best to worst
- C. Code that defines a good joke
- D. A score for every single RL attempt

**17.** The reward model takes a prompt plus one response and outputs:
- A. A rewritten, better response
- B. The next token
- C. A list of adversarial examples
- D. A single number (e.g. 0 to 1) for how good the response is

**18.** Karpathy's best guess for why RLHF helps is the "discriminator–generator gap." This means:
- A. It's much easier for humans to judge (rank) outputs than to create the ideal output
- B. The reward model is bigger than the language model
- C. Generators are cheaper to train than discriminators
- D. Humans are better at writing than at judging

**19.** What happens if you run RLHF for too long?
- A. The model keeps improving forever
- B. Nothing changes after the first update
- C. The model games the reward model with adversarial examples (e.g. "the the the the" scores 1.0), and quality collapses
- D. The reward model learns to write better jokes than the language model

**20.** "RLHF is not RL" means:
- A. RLHF doesn't use any reinforcement learning algorithm
- B. RLHF can't be run indefinitely because its reward is gameable, so it's "a little fine-tune," unlike RL in verifiable domains such as Go
- C. RLHF was invented by a different company than RL
- D. RLHF works only for math

---

## Section B: Smaller details (10 questions)

**21.** Roughly how long did Karpathy say pre-training takes vs. SFT?
- A. 3 hours vs. 3 months
- B. 3 days vs. 3 weeks
- C. 3 months on thousands of computers vs. about 3 hours
- D. About the same

**22.** Where does most SFT conversation data come from **today**?
- A. Mostly synthetic, LLM-generated conversations edited by humans (e.g. UltraChat, millions of conversations)
- B. Only from human contractors writing every answer by hand
- C. Scraped Reddit threads, with no editing
- D. The reward model

**23.** For a question that was **not** in the post-training data (e.g. Paris landmarks), the answer is:
- A. Always a refusal
- B. Copied from the labeler who wrote the closest question
- C. Random tokens
- D. More emergent: pre-training knowledge combined with the post-training style

**24.** Karpathy's main reason the model shouldn't make "big leaps" (like "(13 − 4) ÷ 3 =") in one token:
- A. The model gets only a limited amount of computation per token
- B. Tokens are too expensive
- C. Humans find big leaps confusing
- D. The reward model penalizes long answers

**25.** In RL, which correct solution might you train on?
- A. A random wrong one, to add variety
- B. A good one, e.g. correct and maybe the shortest or cleanest
- C. The longest one
- D. Only the human-written one

**26.** How do children's schooling and LLM training differ, according to Karpathy?
- A. LLMs skip the exposition stage
- B. Children never do practice problems
- C. Kids go chapter by chapter, but LLMs do each stage across all textbooks at once
- D. LLMs do RL before SFT

**27.** What do practitioners do about reward-model gaming in RLHF?
- A. Add every adversarial example to the data until none are left
- B. Run RLHF for a very long time to push through it
- C. Stop using RLHF entirely
- D. Run it for a few hundred updates, then stop ("crop it") and ship

**28.** Which is true of the RLHF paper Karpathy discusses?
- A. It was written at Google DeepMind
- B. It was from OpenAI, and many of its authors went on to co-found Anthropic
- C. It introduced pre-training
- D. It showed RLHF works only on math

**29.** Karpathy's "Swiss cheese" model of LLM capabilities means:
- A. Models are brilliant in many areas but have random holes (e.g. "which is bigger, 9.11 or 9.9?")
- B. Models are uniformly mediocre
- C. Models only fail on hard problems
- D. Models have no knowledge gaps after RLHF

**30.** *(Optional reading.)* OpenAI's sycophancy post describes a ChatGPT update that became too agreeable after:
- A. Pre-training on more books
- B. Removing SFT
- C. Thumbs-up/thumbs-down user feedback was added as a reward signal
- D. Switching to a verifiable reward

---

## Section C: Speed round (true or false)

31. SFT uses a different training algorithm from pre-training.
32. In RLHF, humans write the ideal joke for each prompt.
33. The reward model generates text.
34. Go is a verifiable domain.
35. Fixing each adversarial example one by one eventually solves reward gaming.
36. RLHF is mainly for unverifiable tasks like creative writing and summaries.
37. In RL, the model generates its own solutions.
38. Post-training is the most expensive stage of training.
39. Ranking 5 outputs is easier for a human than giving each an exact score.
40. GPT-4o went through RLHF.

---
---

## Answer key

*Cover this part while you take the quiz.*

### Section A
| # | Ans | Why (primer part) |
|---|---|---|
| 1 | **B** | Base model = "internet document simulator." It continues text and isn't an assistant. (Part 1) |
| 2 | **C** | Pre-training ≈ 3 months on thousands of computers. SFT ≈ 3 hours, because the data is small. (Part 1) |
| 3 | **A** | Same algorithm, only the dataset changes. (Part 1, Trap) |
| 4 | **B** | Behavior is implicitly programmed by the dataset, not in code. (Part 1, Trap) |
| 5 | **D** | New tokens added in post-training to mark whose turn it is. (Part 1) |
| 6 | **A** | Upwork/Scale AI contractors following labeling instructions. (Part 1) |
| 7 | **C** | "A statistical simulation of a human labeler." (Part 1, Trap) |
| 8 | **D** | RL = practice problems: you have the answer key but not the solution. (Part 2) |
| 9 | **A** | SFT = worked examples, imitating experts. A is exposition = pre-training. (Part 2) |
| 10 | **B** | The model's cognition is different and it has limited compute per token. (Part 2) |
| 11 | **C** | The model itself. A is the classic trap. (Part 2, Trap) |
| 12 | **B** | Generate many → check → train on the successes. C is RLHF-confusion. (Part 2) |
| 13 | **D** | SFT initializes, RL dials in. (Part 2, Trap) |
| 14 | **A** | Jokes, poems, summaries are unverifiable. Math, code and Go are verifiable. (Part 3) |
| 15 | **C** | 1,000 × 1,000 × 1,000 = 1 billion ratings. (Part 3) |
| 16 | **B** | Humans rank. They don't write jokes or score every attempt. (Part 3, Trap) |
| 17 | **D** | One score. It's a scorer, not a text generator. (Part 3, Trap) |
| 18 | **A** | Easier to judge than to create. D is the reverse. (Part 3) |
| 19 | **C** | Improves, then "falls off a cliff." "the the the" = 1.0. (Part 3) |
| 20 | **B** | Gameable reward → can't run forever. Go has a perfect scorer, so it can. (Part 3) |

### Section B
| # | Ans | Why |
|---|---|---|
| 21 | **C** | A is the reverse, which is a likely trap. |
| 22 | **A** | Today it's mostly synthetic, human-edited. B describes InstructGPT in 2022. |
| 23 | **D** | Pre-training knowledge + post-training style. |
| 24 | **A** | Limited computation per token, so it can't make big mental leaps. |
| 25 | **B** | Correct and maybe shortest/cleanest. |
| 26 | **C** | Each stage across all textbooks at once. |
| 27 | **D** | A fails because there are infinitely many adversarial examples. |
| 28 | **B** | OpenAI, with many authors later co-founding Anthropic. |
| 29 | **A** | Olympiad problems yes, 9.11 vs. 9.9 maybe not. |
| 30 | **C** | People thumbs-up flattery, which is real-world reward gaming. |

### Section C
31 **F** (same algorithm) · 32 **F** (they rank) · 33 **F** (one score) · 34 **T** (win/lose) · 35 **F** (infinitely many) · 36 **T** · 37 **T** · 38 **F** (pre-training is) · 39 **T** · 40 **T**

### Scoring
- **27+ of 30 (A+B):** ready.
- **Under 24:** reread Part 4 ("Pick these answers") and Part 5 ("Traps") in the primer. Those two tables cover almost every question here.
- **Most-missed pairs to drill:** SFT vs. RL in the school analogy (Q8/Q9), what humans do in RLHF (Q16), and verifiable vs. unverifiable (Q14, Q20).
