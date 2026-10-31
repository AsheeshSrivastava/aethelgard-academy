import {
  createBrowserHistory,
  createRootRoute,
  createRoute,
  createRouter,
  lazyRouteComponent,
  type RouterHistory,
} from "@tanstack/react-router";

import { Layout } from "./components/Layout";
import { Concepts } from "./pages/Concepts";
import { CourseMap } from "./pages/CourseMap";
import { Courses } from "./pages/Courses";
import { Home } from "./pages/Home";
import { Progress } from "./pages/Progress";
import { UnitMap } from "./pages/UnitMap";

const rootRoute = createRootRoute({ component: Layout });

const routeTree = rootRoute.addChildren([
  createRoute({ getParentRoute: () => rootRoute, path: "/", component: Home }),
  createRoute({ getParentRoute: () => rootRoute, path: "/courses", component: Courses }),
  createRoute({ getParentRoute: () => rootRoute, path: "/courses/$courseId", component: CourseMap }),
  createRoute({
    getParentRoute: () => rootRoute,
    path: "/concepts",
    component: Concepts,
    validateSearch: (search: Record<string, unknown>) => (typeof search.q === "string" && search.q ? { q: search.q } : {}) as { q?: string },
  }),
  createRoute({
    getParentRoute: () => rootRoute,
    path: "/concepts/$slug",
    // The renderer pulls in code colouring, so it loads only when a note opens.
    component: lazyRouteComponent(() => import("./pages/ConceptNote"), "ConceptNote"),
  }),
  createRoute({
    getParentRoute: () => rootRoute,
    path: "/courses/$courseId/stages/$stage/build",
    component: lazyRouteComponent(() => import("./pages/StageBuild"), "StageBuild"),
  }),
  createRoute({ getParentRoute: () => rootRoute, path: "/units/$unitId", component: UnitMap }),
  createRoute({
    getParentRoute: () => rootRoute,
    path: "/units/$unitId/$step",
    // The editor and terminal are large, so they load only on lesson pages.
    component: lazyRouteComponent(() => import("./pages/Lesson"), "Lesson"),
  }),
  createRoute({
    getParentRoute: () => rootRoute,
    path: "/progress",
    component: Progress,
    validateSearch: (search: Record<string, unknown>) => ({
      course: typeof search.course === "string" ? search.course : "python",
      stage: typeof search.stage === "number" ? search.stage : undefined,
    }),
  }),
]);

export function makeRouter(history: RouterHistory = createBrowserHistory()) {
  return createRouter({ routeTree, history, defaultPreload: "intent", scrollRestoration: true });
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof makeRouter>;
  }
}
