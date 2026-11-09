import { pythonLanguage } from "@codemirror/lang-python";
import { classHighlighter, highlightCode } from "@lezer/highlight";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState, type ReactElement, type ReactNode } from "react";
import Markdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

import { api } from "../api/client";
import { parseQuickCheck, parseSteps, QuickCheckBox, StepsFigure } from "./LessonBlocks";
import { remarkWikiLinks } from "./wikiLinks";

function highlightPython(code: string): ReactNode[] {
  const parts: ReactNode[] = [];
  highlightCode(
    code,
    pythonLanguage.parser.parse(code),
    classHighlighter,
    (text, classes) => {
      parts.push(
        classes ? (
          <span key={parts.length} className={classes}>
            {text}
          </span>
        ) : (
          text
        ),
      );
    },
    () => parts.push("\n"),
  );
  return parts;
}

function CodeBlock({ children }: { children?: ReactNode }) {
  const [copied, setCopied] = useState(false);
  const element = children as ReactElement<{ className?: string; children?: ReactNode }>;
  const text = String(element.props.children ?? "").replace(/\n$/, "");
  const isPython = /language-(python|py)\b/.test(element.props.className ?? "");

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // The browser refused the clipboard; the code can still be selected by hand.
    }
  }

  return (
    <div className="code-wrap">
      <button type="button" className="copy-button" onClick={copy} aria-label={copied ? "Copied" : "Copy code"}>
        {copied ? "Copied" : "Copy"}
      </button>
      {/* Focusable, so a keyboard can scroll a wide block on a phone (WCAG 2.1.1; step 7 audit). */}
      <pre tabIndex={0}>
        <code>{isPython ? highlightPython(text) : text}</code>
      </pre>
    </div>
  );
}

const components: Components = {
  pre: ({ children }) => <CodeBlock>{children}</CodeBlock>,
  a: ({ href, children }) =>
    href ? (
      <a href={href} target="_blank" rel="noreferrer">
        {children}
      </a>
    ) : (
      <span>{children}</span>
    ),
  // A reply must not be able to load anything from another site.
  img: ({ alt }) => <span>{alt}</span>,
  // Tables scroll sideways on a phone; focusable so a keyboard can scroll them too.
  table: ({ children }) => <table tabIndex={0}>{children}</table>,
};

function ConceptLink({ slug, label }: { slug: string; label?: string }) {
  const concepts = useQuery({ queryKey: ["concepts"], queryFn: () => api.concepts() });
  const concept = concepts.data?.find((item) => item.concept_id === slug);
  const unknown = concepts.isSuccess && !concept;

  useEffect(() => {
    if (unknown && import.meta.env.DEV) console.warn(`Wiki link to unknown concept: ${slug}`);
  }, [unknown, slug]);

  if (!concept) return <span>{label ?? slug}</span>;
  return (
    <Link to="/concepts/$slug" params={{ slug }}>
      {label ?? concept.name}
    </Link>
  );
}

const withConceptLinks = { ...components, "concept-link": ConceptLink } as Components;

const onlyWebLinks = (url: string) => (/^https?:\/\//i.test(url) ? url : "");

const PLUGINS = [remarkGfm];
const PLUGINS_WITH_LINKS = [remarkGfm, remarkWikiLinks];

/** The text inside a fenced block, and its language (`language-steps` and so on). */
function fenced(children: ReactNode): { language: string; text: string } {
  const element = children as ReactElement<{ className?: string; children?: ReactNode }>;
  const language = /language-([\w-]+)/.exec(element?.props?.className ?? "")?.[1] ?? "";
  return { language, text: String(element?.props?.children ?? "").replace(/\n$/, "") };
}

function textOf(node: unknown): string {
  const item = node as { value?: string; children?: unknown[] };
  return item.value ?? (item.children ?? []).map(textOf).join("");
}

/** Lesson-only blocks (SPEC-19): steps diagrams, quick checks and the key-idea box. */
function lessonComponents(base: Components, unitId: string): Components {
  return {
    ...base,
    pre: ({ children }) => {
      const { language, text } = fenced(children);
      if (language === "steps") {
        const block = parseSteps(text);
        if (block) return <StepsFigure block={block} />;
      }
      if (language === "quickcheck") {
        const block = parseQuickCheck(text);
        if (block) return <QuickCheckBox unitId={unitId} block={block} />;
      }
      return <CodeBlock>{children}</CodeBlock>;
    },
    blockquote: ({ node, children }) => (
      <blockquote className={/^\s*Key idea:/.test(textOf(node)) ? "key-idea" : undefined}>{children}</blockquote>
    ),
  };
}

/** Curriculum text and AXIS replies. Raw HTML is shown as text, never run. */
export function Prose({ children, wikiLinks = false, unitId }: { children: string; wikiLinks?: boolean; unitId?: string }) {
  const base = wikiLinks ? withConceptLinks : components;
  const chosen = useMemo(() => (unitId ? lessonComponents(base, unitId) : base), [base, unitId]);
  return (
    <div className="prose">
      <Markdown remarkPlugins={wikiLinks ? PLUGINS_WITH_LINKS : PLUGINS} urlTransform={onlyWebLinks} components={chosen}>
        {children}
      </Markdown>
    </div>
  );
}
