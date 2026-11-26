# Machine-led facilitation: a short desk review

For the [facilitation decision paper](axis-facilitation-decision-paper.md). Written 2026-11-27. A **quick, non-systematic** review: a few searches and page reads in one sitting, not a literature review. No study below was read in full.

**How each source was read** (the label after each claim):
- **part**: part of the full text.
- **abstract**: the abstract or catalogue record only.
- **secondary**: someone else's account of it.
- **search summary**: only a search engine's summary.

## 1. Which tutor behaviours improve what a learner can do alone?

| Finding | Strength | Source |
| :--- | :--- | :--- |
| Open access to GPT raised practice grades 48%, but grades fell 17% when it was taken away. A version with safeguards raised practice grades 127% and "largely mitigated" the harm. About 1,000 high-school maths students | Randomised field experiment, **abstract** | [Bastani et al., PNAS 2025](https://econpapers.repec.org/RePEc:nas:journl:v:122:y:2025:p:e2422633122) |
| In the same study the safeguarded tutor gave hints rather than answers, and its students did about the same as the control group on the exam without AI | **secondary** | [Wharton](https://knowledge.wharton.upenn.edu/article/without-guardrails-generative-ai-can-harm-education) |
| Using the model to produce solutions raised topics covered but lowered understanding; using it to ask for explanations raised understanding. No effect on learning overall. It widened the gap between students with more and less prior knowledge | Lab and field experiments, **abstract** (no figures) | [Lehmann et al.](https://arxiv.org/abs/2409.09047) |
| A Socratic tutor gave larger gains in later sessions than a prompt-coaching tutor, though students rated it less efficient. 66 graduate students. Not compared with no tutor | **abstract** (no figures) | [Brender et al.](https://arxiv.org/abs/2607.03303) |
| Socratic drafts from a model, **checked by human tutors**, did slightly better than human tutors alone on new problems (66.2% against 60.7%). 165 UK secondary students | Exploratory trial, **abstract** | [LearnLM and Eedi](https://arxiv.org/abs/2512.23633) |
| A carefully designed tutor beat an active-learning class on post-lesson quizzes (effect about 0.63). 194 physics undergraduates. The authors credit self-pacing, personal feedback and step-by-step design. The text read does not say plainly that the tutor was off during the quiz | Randomised crossover trial, **part** | [Kestin et al., Sci Rep 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12179260/) |
| Asking for hints too early, or skimming them, goes with lower learning in tutoring systems | Correlation, **search summary** | [An et al., LAK 2026](https://www.cs.cmu.edu/afs/cs.cmu.edu/Web/People/bmclaren/pubs/AnEtAl-RevisitingTheHintButton-LAK2026.pdf) |

**Read together:** help that keeps the learner doing the thinking does better than help that does it for them. A guardrail can remove harm without by itself producing a gain.

## 2. How does a machine tutor differ from a human facilitator?

| Difference | Basis |
| :--- | :--- |
| Step-based tutoring systems came close to human tutors: effects of 0.76 and 0.79 against no tutoring. These are engineered systems that follow each step, **not** open chatbots | [VanLehn 2011](https://eric.ed.gov/?id=EJ946764), **abstract** |
| It is always there and the learner controls it, so help can be pulled until the task is done for them | Bastani (a "crutch"), **abstract**; An et al., **search summary** |
| Better scores with the tool can hide weaker ability without it, so in-tool success is a poor signal | Bastani, **abstract** |
| It sees only what is sent to it. AXIS gets no run output and no earlier turns | Our code (decision paper section 1) |
| It cannot read tiredness, doubt or confidence, or build a relationship as a trainer can | **Inference**, not sourced |

## 3. What is known for adults, and for programming?

| Finding | Source |
| :--- | :--- |
| 52 adult Python users learning a new library (Trio): those with a GPT-4o assistant scored 4.15 points (15.4%) lower on a quiz **taken without AI** (d = 0.738, p = 0.01), with no clear time saving. The abstract names debugging, code reading and conceptual understanding | [Shen and Tamkin 2026](https://arxiv.org/html/2601.20245), **part** |
| In the same study, some ways of using AI kept learning (asking conceptual questions, asking for explanations) and delegating the code did not | **search summary** of the rest of the paper |
| 50 students in a first Python course: the group with an LLM tutor improved over the term and the control group did not. These are within-group tests, not a direct comparison | [Lyu et al.](https://arxiv.org/html/2404.13414v3), **part** |
| Guidance that novices need can hold back people with more experience (the "expertise reversal effect", Kalyuga and colleagues) | [Wikipedia](https://en.wikipedia.org/wiki/Expertise_reversal_effect), **secondary**; the primary papers were not read |

**Not found:** a randomised trial of a guard-railed AI tutor for adults learning programming, measured without the tool. **Not read:** the primary worked-example studies, the original help-abuse work in tutoring systems (Baker, Aleven and Koedinger), and the Kulik and Fletcher meta-analysis. **Nothing was searched** on AI facilitation for governance, change management or design judgement.

The coding study tested a general assistant that could write the code, which is not what AXIS does. It shows the risk, not how AXIS performs.

## 4. What this means for the decisions

| Item | Evidence | Why |
| :--- | :--- | :--- |
| **D1** allow process moves with no source | **Supports, indirectly** | Hints over answers and explanation over delegation did better. No study tested "process moves" as such |
| **D2** memory, last 4 exchanges | **Leaves open** | Following the learner's steps matters; nothing says 4. Memory also makes it easier to pull help turn after turn |
| **D3** rubric and scripted dialogues | **Leaves open** | Useful for checking behaviour. They do not measure learning, which needs unaided performance |
| **D4** hold back the fixed reply | **Supports, weakly** | A fixed question cannot respond to the learner. No direct study |
| **D5** same rubric for the with-source eval | **Leaves open** | No evidence either way |
| **A1** send AXIS the error output | **Supports, indirectly** | Step-based support; debugging is where the coding study names a loss |
| **A2** server builds the history | Not an evidence question | Security |
| **A3** clear history during a Cold Check | Not an evidence question | A Cold Check is meant to show what the learner can do alone |
| **A4** record the highest help level | **Supports, indirectly** | How help is used decides the result, so it must be visible |
| **A5** teach with an example when a novice is stuck | **Supports** (secondary source) | Expertise reversal; the physics tutor used step-by-step solutions |
| **A6** no memory before the freeze | Not an evidence question | Time and risk |
| **A7** judgement subjects: decision, reason, risk | **Leaves open** | Nothing searched |

### Two things the evidence suggests that neither paper had
1. **Ask for an attempt before stepping up.** Otherwise the ladder rewards asking again.
2. **Judge by what the learner can do without AXIS.** Cold Checks are the nearest signal. The LMS is not an exam, so they need only be a fair signal. (The server-side AXIS block of SPEC-32 is approved and not yet built.)

## 5. Limits of this review
Not systematic; mostly abstracts and summaries; several sources are preprints; most learners studied are school pupils or undergraduates; models change quickly, so a result for one model may not hold for another. Effects from different studies cannot be compared with each other.
