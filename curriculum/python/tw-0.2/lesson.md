# TW-0.2: Reviewing an AI-Drafted README

> **The Concept:** An AI draft reads well whether or not it is true; you find out by running what it claims.

---

## 1. Operational Context: The Draft That Looked Finished

The pantry coordinator asked AXIS to "write a README for `door_sign.py`". In seconds it produced five tidy sections. It looked finished, so it went into the folder.

On Saturday a volunteer copied the run command. It named a file that does not exist. They tried the right file, and the sign did not look like the sample run. Nobody had told them to install `uv`. Three small mistakes, and the README cost more time than having none.

Drafting a README is now quick work for AI. **Reviewing it is your job**, and in this course it is the evidence that you can do it (Learning Method Amendment A2).

---

## 2. Run What It Claims

An AI writes what a README usually says. It has not run your script. Check the claims you can test:

1. **The command.** Copy it exactly and run it. Does it start *this* script?
2. **The sample run.** Type the same input. Is the output identical, letter for letter and capital for capital?
3. **What you need first.** Picture a fresh computer. Is every install or setup step written down? The command `uv run` needs `uv`.

Then read the rest against the checklist from TW-0.1: what it does, and its limits.

---

## 3. The Three Mistakes to Hunt

Most errors in AI-drafted READMEs fall into three kinds:

- **A wrong run command:** a file name that is close but not right, or a flag the script does not have.
- **A sample output the code cannot produce:** wrong capitals, missing words, a format the code never prints.
- **A missing setup step:** usually the tool the command depends on.

In this module you are told how many mistakes are planted. Later modules stop telling you.

---

## 4. Asking AXIS for a Draft

A good request gives AXIS the facts it cannot guess: the file name, the exact command you use, and one real run you copied from your terminal. Then you review the draft as above and fix it. Using the draft is expected; your fixes and your reasons are what count.

The playground holds a script with no README yet. Ask AXIS for a draft, paste it in, and fix it until every check passes.
