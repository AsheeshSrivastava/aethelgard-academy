// Plain meanings of the levels and the progress labels, approved by the owner on 2026-11-04 (ADR-0016 amendment).

export const LEVEL_MEANINGS: [string, string][] = [
  ["Understand", "You can explain the idea in your own words and predict what code will do."],
  ["Apply", "You can use it correctly on a familiar task."],
  ["Adapt", "You can handle a twist: new input, a bug, a changed requirement."],
  ["Own", "You can frame the problem yourself and direct tools, with little help."],
];

export const DECISION_MEANINGS: [string, string][] = [
  ["Progress", "You have shown enough for this unit's target. Move on."],
  ["Accelerate", "You are already above the target. You can go faster."],
  ["Strengthen", "Nearly there. One skill needs a bit more practice; the reason says which."],
  ["Rebuild", "The idea itself looks shaky. Go back to the explanation before practising more."],
  ["Undecided", "Not enough evidence yet. Do the next activity."],
];
