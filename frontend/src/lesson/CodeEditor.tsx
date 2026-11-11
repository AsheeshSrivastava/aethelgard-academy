import { python } from "@codemirror/lang-python";
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { EditorState } from "@codemirror/state";
import { EditorView } from "@codemirror/view";
import { tags } from "@lezer/highlight";
import { basicSetup } from "codemirror";
import { useEffect, useRef } from "react";

const theme = EditorView.theme(
  {
    "&": { backgroundColor: "var(--code-bg)", color: "var(--code-text)", fontSize: "14px" },
    ".cm-content": { fontFamily: "var(--font-mono)", caretColor: "var(--code-text)", padding: "12px 0" },
    ".cm-gutters": { backgroundColor: "var(--code-bg)", color: "var(--code-muted)", border: "none" },
    // Translucent: the active line sits above the selection layer and would hide it.
    ".cm-activeLine": { backgroundColor: "var(--code-active-line)" },
    ".cm-activeLineGutter": { backgroundColor: "var(--code-active)" },
    "&.cm-focused .cm-cursor": { borderLeftColor: "var(--code-text)" },
    "&.cm-focused": { outline: "2px solid var(--code-focus)" },
    // !important beats the base theme's more specific selection rules.
    ".cm-selectionBackground": { backgroundColor: "var(--code-selection-blur) !important" },
    "&.cm-focused .cm-selectionBackground": { backgroundColor: "var(--code-selection) !important" },
    ".cm-selectionMatch": { backgroundColor: "rgba(130, 170, 255, 0.18)" },
  },
  { dark: true },
);

// The editor is dark in both themes; its colours are theme tokens (tokens.css, step 6).
const highlight = HighlightStyle.define([
  { tag: tags.keyword, color: "var(--syn-keyword)" },
  { tag: [tags.string, tags.special(tags.string)], color: "var(--syn-string)" },
  { tag: tags.comment, color: "var(--syn-comment)", fontStyle: "italic" },
  { tag: [tags.number, tags.bool, tags.null], color: "var(--syn-number)" },
  { tag: [tags.function(tags.variableName), tags.function(tags.propertyName)], color: "var(--syn-function)" },
  { tag: [tags.definition(tags.variableName), tags.className], color: "var(--syn-function)" },
  { tag: tags.propertyName, color: "var(--syn-property)" },
  { tag: [tags.operator, tags.punctuation], color: "var(--syn-operator)" },
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
