import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import type { ReactNode } from "react";

import { api } from "../api/client";
import { ErrorNote, Loading } from "../components/common";

/* Front page (redesign step 3, owner-approved mock "Landing"). Every number comes from the API;
   nothing here is a placeholder. The code sample is a plan in comments, never build answers. */

const ICONS: Record<string, ReactNode> = {
  build: <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9z" />,
  ask: (
    <>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      <path d="M9.5 8.5a2.5 2.5 0 0 1 4.8 1c0 1.5-2.3 2-2.3 2M12 14h.01" />
    </>
  ),
  check: <path d="M20 6 9 17l-5-5" />,
  play: <polygon points="6 4 20 12 6 20 6 4" />,
  talk: <path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 8.5 8.5 0 0 1-3.8-.9L3 21l2-5.2A8.4 8.4 0 0 1 12 3a8.4 8.4 0 0 1 9 8.5z" />,
  code: <path d="m16 18 6-6-6-6M8 6l-6 6 6 6" />,
  terminal: <path d="m4 17 6-6-6-6M12 19h8" />,
  inbox: <path d="M22 12h-6l-2 3h-4l-2-3H2M5.5 5.1 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.1z" />,
  layers: <path d="m12 2 10 5-10 5L2 7zM2 17l10 5 10-5M2 12l10 5 10-5" />,
  database: (
    <>
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M21 12c0 1.7-4 3-9 3s-9-1.3-9-3M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5" />
    </>
  ),
  server: <path d="M4 3h16v7H4zM4 14h16v7H4zM8 6.5h.01M8 17.5h.01" />,
  spark: <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8" />,
  book: <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5zM4 19.5V21h16" />,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
};

function Icon({ name, size = 20 }: { name: keyof typeof ICONS; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {ICONS[name]}
    </svg>
  );
}

const PROMISES = [
  ["build", "Learn by building, not watching", ""],
  ["ask", "AXIS coach asks, never just tells", "ld-tile-warm"],
  ["check", "Cold Checks prove it stuck", "ld-tile-ok"],
] as const;

const SPINE = [
  ["inbox", "Intake desk", "Python · Module 0"],
  ["layers", "Batch checks", "Python · Modules 2 to 4"],
  ["database", "JSON store", "Python · Module 8"],
  ["server", "Backend service", "Python for Backend/AI"],
  ["spark", "AI agent", "AI Engineering"],
] as const;

const LESSON_STEPS = [
  ["play", "01", "Video", "A short walkthrough, chaptered by concept, so you can jump back to the moment you need."],
  ["talk", "02", "Explain", "One idea at a time, then say it in your own words. A shaky answer gets feedback, never a locked door."],
  ["code", "03", "Practise", "Predict, debug, build. Only what this lesson needs."],
  ["terminal", "04", "Playground", "Try your own ideas in a live Python sandbox."],
  ["check", "05", "Cold Check", "A day later, with no AXIS help. Pass it and the skill is yours."],
] as const;

const AXIS_MODES = [
  ["Coach", "Explains syntax and error messages plainly, without writing your solution."],
  ["Hybrid", "Helps you break the task down, then you write it."],
  ["Socratic", "Only questions that help you inspect your own logic. Never code."],
] as const;

const LADDER = [
  ["Understand", "Explain it"],
  ["Apply", "Use it as shown"],
  ["Adapt", "Use it somewhere new"],
  ["Own", "Direct tools to build it"],
] as const;

/** A small picture per course; any course without one gets the plain accent strip. */
function CourseVisual({ courseId }: { courseId: string }) {
  if (courseId === "python") {
    return (
      <div className="ld-course-visual" aria-hidden="true">
        <span className="ld-mini-code">
          <span className="ld-kw">def</span> <span className="ld-fn">check_in</span>(name):
          <br />
          {"    "}
          <span className="ld-cm"># clean it, then print the slip</span>
        </span>
      </div>
    );
  }
  if (courseId === "backend") {
    return (
      <div className="ld-course-visual ld-visual-info" aria-hidden="true">
        <span className="ld-pill ld-pill-info">POST /intake</span>
        <Icon name="arrow" size={18} />
        <span className="ld-pill ld-pill-ok">201 Created</span>
      </div>
    );
  }
  if (courseId === "ai-engineering") {
    return (
      <div className="ld-course-visual ld-visual-warm" aria-hidden="true">
        <span className="ld-pill">Question</span>
        <Icon name="arrow" size={18} />
        <span className="ld-pill ld-pill-warm">Retrieve</span>
        <Icon name="arrow" size={18} />
        <span className="ld-pill">Answer</span>
      </div>
    );
  }
  return <div className="ld-course-visual" aria-hidden="true" />;
}

function LandingCourses() {
  const courses = useQuery({ queryKey: ["courses"], queryFn: api.courses });
  if (courses.isPending) return <Loading what="courses" />;
  if (courses.isError) return <ErrorNote error={courses.error} />;
  return (
    <div className="ld-course-grid">
      {courses.data.map((course) => (
        <Link key={course.course_id} to="/courses/$courseId" params={{ courseId: course.course_id }} className="card ld-course-card">
          <CourseVisual courseId={course.course_id} />
          <span className="ld-course-body">
            <span className="ld-course-title">{course.title}</span>
            <span className="muted small">{course.summary}</span>
            <span className="muted small mono">
              {course.stage_count} modules · {course.unit_count} units
            </span>
          </span>
        </Link>
      ))}
    </div>
  );
}

function Stats() {
  const courses = useQuery({ queryKey: ["courses"], queryFn: api.courses });
  const units = courses.data?.reduce((sum, course) => sum + course.unit_count, 0);
  const stats: [keyof typeof ICONS, string | number | undefined, string][] = [
    ["book", courses.data?.length, "courses in one path"],
    ["code", units, "hands-on units"],
    ["layers", 1, "real system you grow"],
    ["ask", AXIS_MODES.length, "AXIS coaching modes"],
  ];
  return (
    <section className="ld-stats" aria-label="The path in numbers">
      <div className="container ld-stats-inner">
        {stats.map(([icon, value, label]) => (
          <div key={label} className="ld-stat">
            <span className="ld-tile ld-tile-lg">
              <Icon name={icon} size={22} />
            </span>
            <span className="ld-stat-text">
              <span className="ld-stat-value">{value ?? "–"}</span>
              <span className="muted small">{label}</span>
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}

export function Home() {
  const progress = useQuery({ queryKey: ["proficiency", "home"], queryFn: () => api.proficiency({}) });
  const next = progress.data?.next_action;

  return (
    <main className="landing">
      <section className="ld-hero">
        <div className="container ld-hero-inner">
          <div className="ld-hero-copy">
            <span className="eyebrow ld-eyebrow">Aethelgard</span>
            <h1 className="ld-title">
              Learn to build, and direct, <span className="ld-title-accent">real software</span> in the AI era.
            </h1>
            <p className="ld-lead">
              For career switchers from policy, operations and the social sector, and for students who want industry
              skills. Every lesson grows one real system, from a pantry intake desk to a grounded AI service.
            </p>
            <div className="actions">
              <Link to="/courses" className="button button-primary ld-button">
                Explore courses
              </Link>
              {next && (
                <Link to="/units/$unitId" params={{ unitId: next.unit_id }} className="button ld-button">
                  Continue {next.unit_id}
                </Link>
              )}
            </div>
            <ul className="ld-promises">
              {PROMISES.map(([icon, text, tone]) => (
                <li key={text}>
                  <span className={`ld-tile ${tone}`}>
                    <Icon name={icon} />
                  </span>
                  {text}
                </li>
              ))}
            </ul>
          </div>

          <figure className="card ld-spine" aria-label="The project spine: one system that grows through every course">
            <figcaption className="ld-spine-head">
              <span className="eyebrow ld-eyebrow">One project, every lesson</span>
              <span className="ld-spine-title">One system grows with you</span>
            </figcaption>
            <ol className="ld-spine-nodes">
              {SPINE.map(([icon, name, where], index) => (
                <li key={name} className={index === 0 ? "ld-node ld-node-first" : "ld-node"}>
                  <span className="ld-node-icon">
                    <Icon name={icon} size={24} />
                  </span>
                  <span className="ld-node-name">{name}</span>
                  <span className="muted small">{where}</span>
                </li>
              ))}
            </ol>
            <pre className="ld-plan" aria-label="Your first build starts as a plan">
              <span className="ld-cm"># Module 0 build: the intake desk check-in</span>
              {"\n"}
              <span className="ld-cm"># 1. Ask who has arrived and what they need</span>
              {"\n"}
              <span className="ld-cm"># 2. Clean what they typed</span>
              {"\n"}
              <span className="ld-cm"># 3. Print their check-in slip</span>
            </pre>
          </figure>
        </div>
      </section>

      <Stats />

      <section className="container ld-section" aria-labelledby="how">
        <div className="ld-section-head">
          <span className="eyebrow ld-eyebrow">How every lesson works</span>
          <h2 id="how" className="ld-section-title">
            See it, say it, do it, keep it.
          </h2>
        </div>
        <div className="ld-steps">
          {LESSON_STEPS.map(([icon, number, name, text]) => (
            <div key={name} className={name === "Cold Check" ? "card ld-step ld-step-last" : "card ld-step"}>
              <span className="ld-step-top">
                <span className={name === "Cold Check" ? "ld-tile ld-tile-ok" : "ld-tile"}>
                  <Icon name={icon} />
                </span>
                <span className="mono muted small">{number}</span>
              </span>
              <h3>{name}</h3>
              <p className="muted small">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="axis-band" aria-labelledby="axis">
        <div className="container axis-inner">
          <div className="axis-copy">
            <span className="kicker kicker-light">Meet AXIS</span>
            <h2 id="axis">A facilitator that sits beside you, not an answer machine.</h2>
            <p>
              AXIS sees your code and your last run, and answers only from the course and pinned official
              documentation. You choose how much help you want.
            </p>
          </div>
          <div className="grid axis-modes">
            {AXIS_MODES.map(([name, text]) => (
              <div key={name} className="axis-mode">
                <h3>{name}</h3>
                <p>{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="container ld-section" aria-labelledby="tracks">
        <div className="ld-section-head ld-section-head-row">
          <div>
            <span className="eyebrow ld-eyebrow">Courses</span>
            <h2 id="tracks" className="ld-section-title">
              Three courses, one growing system
            </h2>
          </div>
          <Link to="/courses" className="button">
            All courses
          </Link>
        </div>
        <LandingCourses />
      </section>

      <section className="container ld-section ld-section-last" aria-labelledby="ladder">
        <div className="card ld-ladder">
          <div className="ld-ladder-copy">
            <span className="eyebrow ld-eyebrow">How you grow a skill</span>
            <h2 id="ladder" className="ld-ladder-title">
              Understand, Apply, Adapt, Own
            </h2>
            <p className="muted">Each skill climbs four rungs. You see exactly where you are and what moves you up.</p>
          </div>
          <ol className="ld-rungs">
            {LADDER.map(([level, meaning], index) => (
              <li key={level} className={`ld-rung ld-rung-${index + 1}`}>
                <span className="ld-rung-bar" aria-hidden="true" />
                <span className="ld-rung-name">{level}</span>
                <span className="muted small">{meaning}</span>
              </li>
            ))}
          </ol>
        </div>
      </section>
    </main>
  );
}
