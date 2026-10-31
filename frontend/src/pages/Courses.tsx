import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";

import { api } from "../api/client";
import { BackLink, ErrorNote, Loading } from "../components/common";

export function CourseCards({ showSummary = false }: { showSummary?: boolean }) {
  const courses = useQuery({ queryKey: ["courses"], queryFn: api.courses });

  if (courses.isPending) return <Loading what="courses" />;
  if (courses.isError) return <ErrorNote error={courses.error} />;

  return (
    <div className="grid grid-three">
      {courses.data.map((course) => (
        <Link key={course.course_id} to="/courses/$courseId" params={{ courseId: course.course_id }} className="card course-card">
          <span className="course-title">{course.title}</span>
          {showSummary && <span className="muted small">{course.summary}</span>}
          <span className="muted small">
            {course.stage_count} stages · {course.unit_count} units
          </span>
        </Link>
      ))}
    </div>
  );
}

export function Courses() {
  return (
    <main className="container page">
      <BackLink to="/" label="Home" />
      <h1 className="page-title">Courses</h1>
      <p className="lead">Three courses, one growing system. Start with Python, then go on to backend and AI work.</p>
      <CourseCards showSummary />
    </main>
  );
}
