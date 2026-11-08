import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";

import { api } from "../api/client";
import { CourseCards } from "./Courses";

const SPINE = [
  ["Single intake desk", "Python · Module 0"],
  ["Batch validation", "Python · Modules 2 to 4"],
  ["File and JSON store", "Python · Module 8"],
  ["Backend service", "Python for Backend/AI"],
  ["Grounded AI agents", "AI Engineering"],
] as const;

const LESSON_STEPS = [
  ["01", "Video", "A short walkthrough, chaptered by concept, so you can jump back to the moment you need."],
  ["02", "Explain", "Say it in your own words. A shaky answer gives you feedback, never a locked door."],
  ["03", "Activities", "Only what the lesson needs: predict, trace, debug, build, in a live playground that runs your code."],
  ["04", "Cold Check", "A day later, a short check with no AXIS help. This is what makes a skill truly yours."],
] as const;

const AXIS_MODES = [
  ["Coach", "Explains syntax and error messages plainly, without writing your solution."],
  ["Hybrid", "Helps you break the task down, then you write it."],
  ["Socratic", "Only questions that help you inspect your own logic. Never code."],
] as const;

export function Home() {
  const progress = useQuery({ queryKey: ["proficiency", "home"], queryFn: () => api.proficiency({}) });
  const next = progress.data?.next_action;

  return (
    <main>
      <section className="hero container">
        <div className="hero-copy">
          <span className="kicker">Aethelgard Academy</span>
          <h1>Learn to build, and direct, real software in the AI era.</h1>
          <p className="lead">
            For career switchers from policy, operations and the social sector, and for students who want industry
            skills. Every lesson grows one real system, from a single intake desk to a grounded AI service.
          </p>
          <div className="actions">
            <Link to="/courses" className="button button-primary">
              Explore courses
            </Link>
            {next && (
              <Link to="/units/$unitId" params={{ unitId: next.unit_id }} className="button">
                Continue {next.unit_id}
              </Link>
            )}
          </div>
        </div>
        <figure className="card spine" aria-label="The project spine: one system that grows through every course">
          <figcaption className="eyebrow">One project spine, every lesson</figcaption>
          <ol>
            {SPINE.map(([name, where], index) => (
              <li key={name} className={index === 0 ? "spine-first" : ""}>
                <span className="spine-name">{name}</span>
                <span className="muted small">{where}</span>
              </li>
            ))}
          </ol>
        </figure>
      </section>

      <section className="container section" aria-labelledby="how">
        <h2 id="how" className="section-title">
          How every lesson works
        </h2>
        <div className="grid grid-four">
          {LESSON_STEPS.map(([number, name, text]) => (
            <div key={name} className="card step-card">
              <span className="mono accent">{number}</span>
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

      <section className="container section" aria-labelledby="tracks">
        <div className="section-head">
          <h2 id="tracks" className="section-title">
            Courses
          </h2>
          <Link to="/courses">See all courses</Link>
        </div>
        <CourseCards />
      </section>
    </main>
  );
}
