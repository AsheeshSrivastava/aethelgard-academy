import type { Schemas } from "../api/client";

export const courses: Schemas["Course"][] = [
  { course_id: "python", title: "Python", summary: "Read and build Python.", stage_count: 22, unit_count: 111 },
  { course_id: "backend", title: "Python for Backend/AI", summary: "Backend services.", stage_count: 21, unit_count: 98 },
  { course_id: "ai-engineering", title: "AI Engineering", summary: "Model applications.", stage_count: 18, unit_count: 81 },
];

export const courseMap: Schemas["CourseMap"] = {
  course: courses[0]!,
  stages: [
    {
      stage: 0,
      label: "Stage 0",
      title: "Running your first program",
      units: [
        {
          unit_id: "PY-0.4",
          title: "Run a first program",
          concept_line: "A program is text.",
          target_skills: [{ skill_id: "CO-1", skill_name: "Predict before running", goal_level: "Understand" }],
          authored: true,
          decision: "Progress",
          cold_check_state: "passed",
        },
        {
          unit_id: "PY-0.1",
          title: "Python as an executing program",
          concept_line: "Python runs statements in order.",
          target_skills: [{ skill_id: "CO-2", skill_name: "Trace state", goal_level: "Understand" }],
          authored: true,
          decision: "Undecided",
          cold_check_state: "not_ready",
        },
      ],
      build: { title: "Stage 0 build", kind: "script", maturity: "P1", locked: true, pending_units: ["PY-0.1"], authored: true, status: "draft", review_planned: false },
    },
    {
      stage: 1,
      label: "Stage 1",
      title: "Values, text and collections",
      units: [
        {
          unit_id: "PY-1.2",
          title: "Numbers, booleans and None",
          concept_line: "Every value has a type.",
          target_skills: [{ skill_id: "VE-6", skill_name: "Check beyond it runs", goal_level: "Apply" }],
          authored: false,
          decision: "Strengthen",
          cold_check_state: "not_ready",
        },
      ],
      build: { title: "Stage 1 build", kind: "script", maturity: "P1", locked: false, pending_units: [], authored: false, review_planned: false },
    },
  ],
};

export const unit = {
  unit_id: "PY-0.1",
  title: "Python as an executing program",
  stage: 0,
  stage_label: "Stage 0",
  concept_line: "Python runs statements in order, and each statement can change the program's state.",
  target_skills: [
    { skill_id: "CO-1", skill_name: "Predict before running", goal_level: "Understand" },
    { skill_id: "CO-2", skill_name: "Trace state", goal_level: "Understand" },
  ],
  methods: ["Explain", "Predict", "Trace"],
  prerequisites: ["PY-0.4"],
  activities: ["video", "explain", "predict", "trace", "playground", "cold_check"],
} as unknown as Schemas["Unit"];

export const proficiency: Schemas["ProficiencyView"] = {
  stage: 0,
  skills: [
    {
      skill_id: "CO-1",
      skill_name: "Predict before running",
      target_level: "Apply",
      current_level: "Understand",
      confidence: "provisional",
      evidence_counts: { explain: 2, perform: 0, diagnose: 0 },
      decision: "Strengthen",
      reason: "Evidence shows Understand; the target is Apply.",
      entry_ids: ["e1"],
    },
    {
      skill_id: "CO-2",
      skill_name: "Trace state",
      target_level: "Understand",
      current_level: "Understand",
      confidence: "supported",
      evidence_counts: { explain: 3, perform: 0, diagnose: 0 },
      decision: "Progress",
      reason: "Sufficient evidence.",
      entry_ids: ["e2", "e3"],
    },
    {
      skill_id: "DE-2",
      skill_name: "Ask the tool to explain",
      target_level: "Understand",
      current_level: null,
      confidence: null,
      evidence_counts: { explain: 0, perform: 0, diagnose: 0 },
      decision: "Undecided",
      reason: "Insufficient evidence.",
      entry_ids: [],
    },
  ],
  units: [
    { unit_id: "PY-0.4", decision: "Progress" },
    { unit_id: "PY-0.1", decision: "Strengthen" },
  ],
  next_action: {
    unit_id: "PY-0.1",
    skill_id: "CO-1",
    activity: "debug-validate",
    decision: "Strengthen",
    message: "Evidence shows Understand; the target is Apply.",
  },
};

export const ledger = [
  {
    entry_id: "e2",
    learner_id: "default_learner",
    unit_id: "PY-0.1",
    skill_id: "CO-2",
    evidence_category: "Explain / Reason",
    evidence_strength: "Strong",
    assistance_level: "none",
    demonstration_context: "Trace attempt",
    recorded_at: "2026-06-01T09:00:00Z",
    activity: "Trace",
    cold_check: true,
  },
  {
    entry_id: "e1",
    learner_id: "default_learner",
    unit_id: "PY-0.1",
    skill_id: "CO-1",
    evidence_category: "Explain / Reason",
    evidence_strength: "Moderate",
    assistance_level: "small_hint",
    demonstration_context: "Predict attempt",
    recorded_at: "2026-05-31T09:00:00Z",
    activity: "Predict",
    cold_check: false,
  },
];

export const concepts: Schemas["ConceptSummary"][] = [
  { concept_id: "print-function", name: "print() function", category: "Core tools", summary: "Shows values.", status: "draft", units: [], doc_url: "" },
  { concept_id: "variables", name: "Variables", category: "State", summary: "A name for a value.", status: "draft", units: [], doc_url: "" },
];

export const conceptNote: Schemas["ConceptDetail"] = {
  ...concepts[1]!,
  aliases: ["names"],
  doc_url: "https://docs.python.org/3/",
  content_markdown: "Use `input()` here, then see [[print-function|the print() function]].",
  related: [{ concept_id: "print-function", name: "print() function" }],
  used_in: [{ unit_id: "PY-0.1", title: "Python as an executing program" }],
};
