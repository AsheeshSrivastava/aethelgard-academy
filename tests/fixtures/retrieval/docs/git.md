# Version control with git

## Saving work with commits
`git status` shows what changed. `git add file.py` stages a change, and `git commit -m "message"` records the staged changes as a commit. Write the message in the imperative, such as "Add login check". A commit is a snapshot you can return to.

## Branches
A branch is a movable label for a line of commits. `git switch -c fix-login` creates a branch and moves to it. Work on a branch keeps the main branch stable until you are ready. `git branch` lists branches and shows the current one.

## Merging and conflicts
`git merge fix-login` brings a branch into the current one. When both branches changed the same lines, git stops with `CONFLICT (content): Merge conflict in app.py`. Open the file, find the markers `<<<<<<<`, `=======` and `>>>>>>>`, keep the right text, delete the markers, then `git add` the file and finish with `git commit`.

## Undoing mistakes
`git restore file.py` throws away uncommitted edits to a file. `git restore --staged file.py` unstages it but keeps your edits. To undo a commit that is already shared, use `git revert <hash>`, which adds a new commit that cancels the old one. `git reset --hard` destroys uncommitted work, so check `git status` first.
