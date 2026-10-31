# Stage 0 Seeds: Owner Review

- **Status:** Drafted by Claude. All 20 seeds approved by the owner on 2026-10-31, so every seed now has `curator_approved: true`.
- **Date:** 2026-10-31
- **Seeds:** 20 (PY-0.4: 7, PY-0.1: 7, PY-0.3: 6). Files are in each unit's `exercises/` folder.
- **Checked with real Python:** every answer key, expected output and fix. Every `wrong_solution` fails and every broken script fails. Each `debug_locate` key was checked by running the broken code.

Cold Check seeds are reserved: learners never see them in normal steps. The free-text Explain check stays in `meta.json`, so Explain has no normal seed.

## PY-0.4: Run a first program

Target skills, all at Understand: CO-1, VE-4. Activities: Explain, Predict, Debug & Validate.

**Ungraded playground:** Rewritten with no `def`. It is now a plain script that cleans a name and ward code and builds a ticket, using `.strip()`, `.title()`, `.upper()` and `str()`, which this unit's lesson now introduces. It writes no evidence. Checked: a correct solution passes its tests and the blank starter fails.

### predict-1

- **Activity and skill:** Predict, CO-1
- **Prompt:** The reception terminal runs this script, and a citizen types `{{person}}`. Commit to your answer before you run anything: what appears on the terminal?
- **Answer:** A: Reception open / Registering {{person}} / Done
- **Why it tests the skill:** Five lines, as the roadmap outcome asks. Wrong answers come from running a comment, printing the variable's name, or running lines out of order.

### predict-2

- **Activity and skill:** Predict, CO-1
- **Prompt:** The terminal asks for a ward number, and a citizen types `12`. What appears on the terminal?
- **Answer:** B: 1212
- **Why it tests the skill:** Prediction rests on the unit's key fact that input() always returns text. This is the spine's rule that data from outside is text.

### debug-validate-1

- **Activity and skill:** Debug & Validate, VE-4
- **Prompt:** This script stops with an error when it reaches the second line. Run it, read the error's type, message and line number, then fix the script.
- **Answer:** Fixed script: `citizen = input(); print("Registering", citizen)`
- **Why it tests the skill:** A NameError on a typo. The message names the misspelled word and the line, so reading it is the fastest route to the fix. Quoting the word silences the error but fails the checks.

### debug-validate-2

- **Activity and skill:** Debug & Validate, VE-4
- **Prompt:** Python refuses to run this script at all. Read the error, find what it points at, and fix the script.
- **Answer:** Fixed script: `ward = input(); print("Ward:", ward)`
- **Why it tests the skill:** A SyntaxError, a second kind of first error, where nothing runs. It teaches that the error type says what went wrong.

### cold-predict-1 (Cold Check)

- **Activity and skill:** Predict, CO-1
- **Prompt:** A citizen types `north-01` at the terminal. What appears on the terminal?
- **Answer:** C: Terminal ready / Ward: north-01 / Next citizen
- **Why it tests the skill:** New script, same reasoning as predict-1. Tests CO-1 through Predict, its main activity, with no AXIS help.

### debug-validate-3

- **Activity and skill:** Debug & Validate, VE-4
- **Prompt:** This script stops with an error on its very first line. Read the error and fix the script so it registers the citizen who typed their name.
- **Answer:** Fixed script: `citizen = input(); print("Registering", citizen)`
- **Why it tests the skill:** The same NameError type as debug-validate-1, but the cause is order, not spelling, so copying the earlier fix fails.

### cold-debug-validate-1 (Cold Check)

- **Activity and skill:** Debug & Validate, VE-4
- **Prompt:** This script stops with an error when a citizen types `north-01`. Run it in your head or read it closely: on which line does it fail, and what kind of error is it?
- **Answer:** Line 3, NameError: a name Python does not know
- **Why it tests the skill:** Exactly the roadmap outcome: names the line and kind of error. Key-graded, and checked by running the broken code. Tests VE-4 through Debug & Validate, its main activity.

## PY-0.1: Python as an executing program

Target skills, all at Understand: CO-1, CO-2, CO-6. Activities: Explain, Predict, Trace.

**Ungraded playground:** The existing exercise fits the unit: `input()`, `print()` and an f-string. It writes no evidence. Checked: a correct solution passes its tests and the blank starter fails.

### predict-1

- **Activity and skill:** Predict, CO-1
- **Prompt:** The intake desk runs this program, and the applicant types `{{person}}`. Commit to your answer before you run anything: what appears on the terminal?
- **Answer:** A: Desk open / Applicant: {{person}} /  / Record: {{person}}
- **Why it tests the skill:** SPEC-13's worked example. Tests order, the returned value, and the blank line, using the unit's lesson content.

### predict-2

- **Activity and skill:** Predict, CO-1
- **Prompt:** An applicant types `{{person}}`. What appears on the terminal?
- **Answer:** C: {{person}} waiting /  / {{person}} registered / Ticket for {{person}}
- **Why it tests the skill:** A longer script, closer to the roadmap's 10-line outcome. Option B is the classic misconception that a later change reaches back.

### trace-1

- **Activity and skill:** Trace, CO-2
- **Prompt:** Follow the applicant's status line by line. Write the value of `status` after each line, then what the terminal shows.
- **Answer:** Output: waiting / checked in
- **Why it tests the skill:** SPEC-13's worked example. The learner fills in the state table the roadmap outcome describes.

### trace-2

- **Activity and skill:** Trace, CO-2
- **Prompt:** The desk counts citizens as they are registered. Write the value of `count` after each line, then what the terminal shows.
- **Answer:** Output: 1 / 3
- **Why it tests the skill:** Each line changes state using its own earlier value, so the learner must hold the state in mind.

### cold-predict-1 (Cold Check)

- **Activity and skill:** Predict, CO-1
- **Prompt:** A visitor types `Kofi Mensah` at the queue desk. What appears on the terminal?
- **Answer:** B: Queue open /  / Next: Kofi Mensah
- **Why it tests the skill:** SPEC-13's worked example. Tests CO-1 through Predict.

### cold-trace-1 (Cold Check)

- **Activity and skill:** Trace, CO-2
- **Prompt:** Two names point at a desk label. Follow the values, then write what the terminal shows.
- **Answer:** Output: B A
- **Why it tests the skill:** SPEC-13's worked example. Changing one name must not change the other. Tests CO-2 through Trace.

### cold-explain-1 (Cold Check)

- **Activity and skill:** Explain, CO-6
- **Prompt:** A new colleague explains how the intake script runs. One sentence is wrong. Which one?
- **Answer:** C: A variable stores the code that made its value, and that code runs again each time the variable is used.
- **Why it tests the skill:** SPEC-13's worked example. Tests the mental model itself, which is the Learning Method's 'spot what is wrong' part of the CO-6 check.

## PY-0.3: Tool help versus your own reasoning

Target skills, all at Understand: DE-2, DE-3, DE-4. Activities: Explain, Direct.

**Ungraded playground:** The existing exercise has no `def`. It uses `.strip()` and `.upper()`, which learners now meet in PY-0.4. Its code comment names BU-1 and VE-4, which are not this unit's skills. It writes no evidence. Checked: a correct solution passes its tests and the blank starter fails.

### direct-1

- **Activity and skill:** Direct, DE-2
- **Prompt:** An AI tool gave you `name.strip().upper()` and it works, but you do not know why `.strip()` comes first. What is the best thing to ask the tool next?
- **Answer:** B: Explain what each part does, and what would change if the order were swapped.
- **Why it tests the skill:** The roadmap outcome: say what to ask a tool to explain rather than do. Wrong answers hand the work over or ask for a verdict.

### direct-2

- **Activity and skill:** Direct, DE-3
- **Prompt:** The intake desk needs a new ticket script, and you are working with an AI tool. Which of these must stay with you?
- **Answer:** C: Deciding which personal details the ticket may show.
- **Why it tests the skill:** The roadmap outcome: sort contributions into 'fine to delegate' and 'must own'. It matches Task B in the unit's playground.

### direct-3

- **Activity and skill:** Direct, DE-4
- **Prompt:** AXIS says a Python function behaves one way, and a blog post says another. What settles the question?
- **Answer:** D: The official documentation, and running the code yourself.
- **Why it tests the skill:** The roadmap outcome: name which source would settle a question. It matches Part 3 of the unit's playground.

### cold-direct-1 (Cold Check)

- **Activity and skill:** Direct, DE-2
- **Prompt:** An AI tool fixed your script, and now it runs. You could not explain the fix to a colleague. What should you do before you keep it?
- **Answer:** B: Ask the tool to explain why the old code failed and what the change does, then check you can say it yourself.
- **Why it tests the skill:** A new situation for the same habit. Tests DE-2 through Direct, its main activity, with AXIS off.

### cold-direct-2 (Cold Check)

- **Activity and skill:** Direct, DE-3
- **Prompt:** Your team is shipping a citizen registration script with AI help. Which of these is fine to delegate to the tool?
- **Answer:** D: Drafting the boilerplate for a function you have already designed.
- **Why it tests the skill:** The reverse of direct-2: pick what can be delegated, so memorising that answer does not help. Tests DE-3 through Direct.

### cold-direct-3 (Cold Check)

- **Activity and skill:** Direct, DE-4
- **Prompt:** An AI tool says the code below prints `amaraokafor`, because `.strip()` removes every space. Your colleague says it keeps the middle space. What is the quickest reliable way to settle it?
- **Answer:** B: Run the line, and read the official documentation for `str.strip`.
- **Why it tests the skill:** A real claim that can be checked by running it. Tests DE-4 through Direct.
- [ ] Approve   - [ ] Reject
