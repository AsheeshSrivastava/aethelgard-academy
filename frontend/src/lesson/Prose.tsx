import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Curriculum text. Raw HTML in it is shown as text, never run. */
export function Prose({ children }: { children: string }) {
  return (
    <div className="prose">
      <Markdown remarkPlugins={[remarkGfm]}>{children}</Markdown>
    </div>
  );
}
