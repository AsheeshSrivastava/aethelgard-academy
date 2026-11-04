import { python } from "@codemirror/lang-python";
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { EditorState } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { tags } from "@lezer/highlight";
import { basicSetup } from "codemirror";
import { useEffect, useRef } from "react";

const theme = EditorView.theme(
  {
    "&": { backgroundColor: "#12161C", color: "#E8ECF1", fontSize: "14px" },
    ".cm-content": { fontFamily: "var(--font-mono)", caretColor: "#E8ECF1", padding: "12px 0" },
    ".cm-gutters": { backgroundColor: "#12161C", color: "#7A8592", border: "none" },
    ".cm-activeLine, .cm-activeLineGutter": { backgroundColor: "#1D232B" },
    "&.cm-focused .cm-cursor": { borderLeftColor: "#E8ECF1" },
    "&.cm-focused": { outline: "2px solid #5CC4C0" },
    ".cm-selectionBackground, &.cm-focused .cm-selectionBackground": { backgroundColor: "#2F6462 !important" },
  },
  { dark: true },
);

// The editor is dark in both themes, so its colours are chosen for a dark ground.
const highlight = HighlightStyle.define([
  { tag: tags.keyword, color: "#C9A7F5" },
  { tag: [tags.string, tags.special(tags.string)], color: "#A5E3C0" },
  { tag: tags.comment, color: "#9AA4B1", fontStyle: "italic" },
  { tag: [tags.number, tags.bool, tags.null], color: "#F7C58A" },
  { tag: [tags.function(tags.variableName), tags.function(tags.propertyName)], color: "#8FC7FF" },
  { tag: [tags.definition(tags.variableName), tags.className], color: "#8FC7FF" },
  { tag: tags.propertyName, color: "#8FDCD9" },
  { tag: [tags.operator, tags.punctuation], color: "#C9CED6" },
]);

/** `value` sets the starting text; remount with a new key to replace it. */
export function CodeEditor({
  value,
  onChange,
  label,
  language = "python",
}: {
  value: string;
  onChange: (value: string) => void;
  label: string;
  language?: "python" | "text";
}) {
  const host = useRef<HTMLDivElement>(null);
  const change = useRef(onChange);
  change.current = onChange;

  useEffect(() => {
    if (!host.current) return;
    const view = new EditorView({
      parent: host.current,
      state: EditorState.create({
        doc: value,
        extensions: [
          basicSetup,
          ...(language === "python" ? [python()] : []),
          theme,
          syntaxHighlighting(highlight),
          EditorView.contentAttributes.of({ "aria-label": label, "data-language": language }),
          EditorView.updateListener.of((update) => {
            if (update.docChanged) change.current(update.state.doc.toString());
          }),
        ],
      }),
    });
    return () => view.destroy();
    // The editor owns its text after mount; a key change gives it new text.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <div ref={host} className="code-editor" />;
}
