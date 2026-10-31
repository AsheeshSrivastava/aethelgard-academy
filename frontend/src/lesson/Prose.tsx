import { pythonLanguage } from "@codemirror/lang-python";
import { classHighlighter, highlightCode } from "@lezer/highlight";
import { useState, type ReactElement, type ReactNode } from "react";
import Markdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

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
      <pre>
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
};

const onlyWebLinks = (url: string) => (/^https?:\/\//i.test(url) ? url : "");

/** Curriculum text and AXIS replies. Raw HTML is shown as text, never run. */
export function Prose({ children }: { children: string }) {
  return (
    <div className="prose">
      <Markdown remarkPlugins={[remarkGfm]} urlTransform={onlyWebLinks} components={components}>
        {children}
      </Markdown>
    </div>
  );
}
