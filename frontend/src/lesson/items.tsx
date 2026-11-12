import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type ReactNode } from "react";

import { api, type Exercise } from "../api/client";
import { CodeEditor } from "./CodeEditor";
import { RunTerminal } from "./RunTerminal";

export type Answer = {
  choice?: string;
  trace_answers?: string[];
  trace_states?: { line: number; state: Record<string, string> }[];
  locate?: { line: number; error_type: string };
  files?: Record<string, string>;
  tests?: string;
  fields?: Record<string, string | string[]>;
  plan?: string[];
};

export interface ItemProps {
  exercise: Exercise;
  busy: boolean;
  submitLabel: string;
  onSubmit: (answer: Answer) => void;
}

function Submit({ disabled, busy, label }: { disabled?: boolean; busy: boolean; label: string }) {
  return (
    <div className="actions">
      <button type="submit" className="button button-primary" disabled={disabled || busy}>
        {busy ? "Checking…" : label}
      </button>
    </div>
  );
}

function CodeBlock({ lines }: { lines: string[] }) {
  return (
    <pre className="code-block">
      <code>
        {lines.map((line, index) => (
          <span key={index} className="code-line">
            <span className="code-number" aria-hidden="true">
              {index + 1}
            </span>
            {line}
            {"\n"}
          </span>
        ))}
      </code>
    </pre>
  );
}

function Options({
  name,
  legend,
  options,
  value,
  onChange,
}: {
  name: string;
  legend: string;
  options: { key: string; text: string }[];
  value: string;
  onChange: (key: string) => void;
}) {
  return (
    <fieldset className="options">
      <legend className="eyebrow">{legend}</legend>
      {options.map((option) => (
        <label key={option.key} className={`option${value === option.key ? " option-chosen" : ""}`}>
          <input type="radio" name={name} checked={value === option.key} onChange={() => onChange(option.key)} />
          <span className="option-text">{option.text}</span>
        </label>
      ))}
    </fieldset>
  );
}

function ChoiceForm({
  name,
  legend,
  options,
  before,
  props,
}: {
  name: string;
  legend: string;
  options: { key: string; text: string }[];
  before?: ReactNode;
  props: ItemProps;
}) {
  const [choice, setChoice] = useState("");
  return (
    <form
      className="item-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit({ choice });
      }}
    >
      {before}
      <Options name={name} legend={legend} options={options} value={choice} onChange={setChoice} />
      <Submit disabled={!choice} busy={props.busy} label={props.submitLabel} />
    </form>
  );
}

function Material({ lines }: { lines?: string[] }) {
  if (!lines?.length) return null;
  return <pre className="material">{lines.join("\n")}</pre>;
}

function PredictItem(props: ItemProps) {
  const block = props.exercise.predict!;
  return <ChoiceForm name="predict" legend="Your prediction" options={block.options} before={<CodeBlock lines={block.code} />} props={props} />;
}

function TraceItem(props: ItemProps) {
  const block = props.exercise.trace!;
  const stateRows = block.state_rows ?? [];
  const [text, setText] = useState("");
  const [cells, setCells] = useState<Record<string, string>>({});
  const cellKey = (line: number, name: string) => `${line}:${name}`;
  const allCellsFilled = stateRows.every((row) => row.names.every((name) => (cells[cellKey(row.line, name)] ?? "").trim()));
  return (
    <form
      className="item-form"
      onSubmit={(event) => {
        event.preventDefault();
        const answer: Answer = { trace_answers: text.split("\n").filter((line) => line.trim()) };
        if (stateRows.length) {
          answer.trace_states = stateRows.map((row) => ({
            line: row.line,
            state: Object.fromEntries(row.names.map((name) => [name, cells[cellKey(row.line, name)] ?? ""])),
          }));
        }
        props.onSubmit(answer);
      }}
    >
      <CodeBlock lines={block.code} />
      {block.input && <p className="small muted">Input: {block.input}</p>}
      <label className="field">
        <span>What the terminal shows, one line each</span>
        <textarea rows={4} value={text} onChange={(event) => setText(event.target.value)} />
      </label>
      {stateRows.length > 0 && (
        <table className="state-table">
          <caption className="small muted">Fill in what each name holds after the line.</caption>
          <tbody>
            {stateRows.map((row) => (
              <tr key={row.line}>
                <th scope="row">After line {row.line}</th>
                {row.names.map((name) => (
                  <td key={name}>
                    <label className="field">
                      <span>{name}</span>
                      <input
                        type="text"
                        aria-label={`${name} after line ${row.line}`}
                        value={cells[cellKey(row.line, name)] ?? ""}
                        onChange={(event) => setCells({ ...cells, [cellKey(row.line, name)]: event.target.value })}
                      />
                    </label>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <Submit disabled={!text.trim() || !allCellsFilled} busy={props.busy} label={props.submitLabel} />
    </form>
  );
}

function DebugLocateItem(props: ItemProps) {
  const block = props.exercise.debug_locate!;
  const [line, setLine] = useState("");
  const [errorType, setErrorType] = useState("");
  return (
    <form
      className="item-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit({ locate: { line: Number(line), error_type: errorType } });
      }}
    >
      <CodeBlock lines={block.broken_code} />
      {block.stdin && <p className="small muted">Input: {block.stdin}</p>}
      <label className="field">
        <span>Which line fails?</span>
        <select value={line} onChange={(event) => setLine(event.target.value)}>
          <option value="">Choose a line</option>
          {block.broken_code.map((_, index) => (
            <option key={index} value={index + 1}>
              Line {index + 1}
            </option>
          ))}
        </select>
      </label>
      <Options name="error" legend="What kind of error is it?" options={block.error_types} value={errorType} onChange={setErrorType} />
      <Submit disabled={!line || !errorType} busy={props.busy} label={props.submitLabel} />
    </form>
  );
}

function ContractItem(props: ItemProps) {
  const block = props.exercise.specify_contract!;
  const [single, setSingle] = useState<Record<string, string>>({});
  const [multi, setMulti] = useState<Record<string, string[]>>({});
  const complete = block.fields.every((field) => field.kind === "multi" || single[field.id]);

  function toggle(fieldId: string, key: string) {
    const current = multi[fieldId] ?? [];
    setMulti({ ...multi, [fieldId]: current.includes(key) ? current.filter((k) => k !== key) : [...current, key] });
  }

  return (
    <form
      className="item-form"
      onSubmit={(event) => {
        event.preventDefault();
        const fields: Record<string, string | string[]> = {};
        for (const field of block.fields) {
          fields[field.id] = field.kind === "multi" ? (multi[field.id] ?? []) : (single[field.id] ?? "");
        }
        props.onSubmit({ fields });
      }}
    >
      <Material lines={block.material} />
      {block.fields.map((field) =>
        field.kind === "multi" ? (
          <fieldset key={field.id} className="options">
            <legend className="eyebrow">{field.label}</legend>
            {field.options.map((option) => (
              <label key={option.key} className="option">
                <input type="checkbox" checked={(multi[field.id] ?? []).includes(option.key)} onChange={() => toggle(field.id, option.key)} />
                <span className="option-text">{option.text}</span>
              </label>
            ))}
          </fieldset>
        ) : (
          <Options
            key={field.id}
            name={field.id}
            legend={field.label}
            options={field.options}
            value={single[field.id] ?? ""}
            onChange={(key) => setSingle({ ...single, [field.id]: key })}
          />
        ),
      )}
      <Submit disabled={!complete} busy={props.busy} label={props.submitLabel} />
    </form>
  );
}

function PlanItem(props: ItemProps) {
  const block = props.exercise.decompose_plan!;
  const [plan, setPlan] = useState<string[]>([]);
  const text = (id: string) => block.steps.find((step) => step.id === id)?.text ?? id;

  function toggle(id: string) {
    setPlan(plan.includes(id) ? plan.filter((step) => step !== id) : [...plan, id]);
  }

  function move(index: number, by: number) {
    const next = [...plan];
    const [step] = next.splice(index, 1);
    if (step !== undefined) next.splice(index + by, 0, step);
    setPlan(next);
  }

  return (
    <form
      className="item-form"
      onSubmit={(event) => {
        event.preventDefault();
        props.onSubmit({ plan });
      }}
    >
      <Material lines={block.material} />
      <fieldset className="options">
        <legend className="eyebrow">Choose the sub-tasks you need</legend>
        {block.steps.map((step) => (
          <label key={step.id} className="option">
            <input type="checkbox" checked={plan.includes(step.id)} onChange={() => toggle(step.id)} />
            <span className="option-text">{step.text}</span>
          </label>
        ))}
      </fieldset>
      {plan.length > 0 && (
        <div className="plan">
          <span className="eyebrow">Put them in order</span>
          <ol className="plan-list">
            {plan.map((id, index) => (
              <li key={id}>
                <span>{text(id)}</span>
                <span className="plan-moves">
                  <button type="button" className="button button-small" disabled={index === 0} aria-label={`Move ${text(id)} up`} onClick={() => move(index, -1)}>
                    Up
                  </button>
                  <button type="button" className="button button-small" disabled={index === plan.length - 1} aria-label={`Move ${text(id)} down`} onClick={() => move(index, 1)}>
                    Down
                  </button>
                </span>
              </li>
            ))}
          </ol>
        </div>
      )}
      <Submit disabled={plan.length === 0} busy={props.busy} label={props.submitLabel} />
    </form>
  );
}

const SAVE_DELAY_MS = 800;

/** The learner's text for an exercise, saved quietly as they type. */
function useDraft(exerciseId: string, starter: string) {
  const client = useQueryClient();
  const draft = useQuery({
    queryKey: ["draft", exerciseId],
    queryFn: () => api.getDraft(exerciseId),
    staleTime: Infinity,
  });
  const code = useRef(starter);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const saved = draft.data?.files["solution.py"];
  if (saved !== undefined && code.current === starter) code.current = saved;

  useEffect(() => () => clearTimeout(timer.current), []);

  function update(value: string) {
    code.current = value;
    clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      void api.saveDraft(exerciseId, { "solution.py": value }).catch(() => undefined);
      client.setQueryData(["draft", exerciseId], { files: { "solution.py": value } });
    }, SAVE_DELAY_MS);
  }

  return { ready: !draft.isPending, code, update };
}

export function CodeWorkspace({
  exerciseId,
  starter,
  label,
  run = true,
  children,
}: {
  exerciseId: string;
  starter: string[];
  label: string;
  run?: boolean;
  children: (getCode: () => string) => ReactNode;
}) {
  const start = starter.join("\n");
  const { ready, code, update } = useDraft(exerciseId, start);
  const [version, setVersion] = useState(0);
  const getCode = () => code.current;

  if (!ready) return <p className="muted small">Loading your work…</p>;

  return (
    <div className="workspace">
      <div className="workspace-head">
        <span>solution.py</span>
        <button
          type="button"
          className="button button-small"
          onClick={() => {
            update(start);
            setVersion(version + 1);
          }}
        >
          Reset code
        </button>
      </div>
      <CodeEditor key={version} value={code.current} onChange={update} label={label} />
      {run && <RunTerminal getCode={getCode} exerciseId={exerciseId} />}
      {children(getCode)}
    </div>
  );
}

function CodeItem({ starter, label, field, run, before, props }: { starter: string[]; label: string; field: "files" | "tests"; run?: boolean; before?: ReactNode; props: ItemProps }) {
  return (
    <div className="item-form">
      {before}
      <CodeWorkspace exerciseId={props.exercise.exercise_id} starter={starter} label={label} run={run}>
        {(getCode) => (
          <form
            onSubmit={(event) => {
              event.preventDefault();
              props.onSubmit(field === "tests" ? { tests: getCode() } : { files: { "solution.py": getCode() } });
            }}
          >
            <Submit busy={props.busy} label={props.submitLabel} />
          </form>
        )}
      </CodeWorkspace>
    </div>
  );
}

export function ItemForm(props: ItemProps) {
  const { exercise } = props;
  switch (exercise.item_type) {
    case "predict":
      return <PredictItem {...props} />;
    case "trace":
      return <TraceItem {...props} />;
    case "debug_locate":
      return <DebugLocateItem {...props} />;
    case "choice":
      return (
        <ChoiceForm name="choice" legend="Your answer" options={exercise.choice!.options} before={<Material lines={exercise.choice!.material} />} props={props} />
      );
    case "explain_model_choice":
      return (
        <ChoiceForm
          name="model"
          legend="Which mental model fits?"
          options={exercise.explain_model_choice!.options}
          before={<Material lines={exercise.explain_model_choice!.material} />}
          props={props}
        />
      );
    case "explain_spot_flaw":
      return <ChoiceForm name="flaw" legend="Which sentence is wrong?" options={exercise.explain_spot_flaw!.sentences} props={props} />;
    case "specify_contract":
      return <ContractItem {...props} />;
    case "decompose_plan":
      return <PlanItem {...props} />;
    case "specify_by_tests": {
      const block = exercise.specify_by_tests!;
      return <CodeItem starter={block.starter_tests} label="Your tests" field="tests" run={false} before={<p className="mono">{block.signature}</p>} props={props} />;
    }
    case "decompose_code": {
      const block = exercise.decompose_code!;
      const before = (
        <p className="small muted">
          Keep <span className="mono">{block.entry_function}</span> as the entry function, with at least {block.structure.min_helpers} helper functions called from it, and no function over{" "}
          {block.structure.max_lines_per_function} lines.
        </p>
      );
      return <CodeItem starter={block.starter} label="Your code" field="files" before={before} props={props} />;
    }
    case "debug":
      return <CodeItem starter={exercise.debug!.broken_code} label="Your code" field="files" props={props} />;
    case "playground": {
      const block = exercise.playground!;
      const before = block.tasks?.length ? (
        <ul className="task-list">
          {block.tasks.map((task) => (
            <li key={task.id}>{task.label}</li>
          ))}
        </ul>
      ) : null;
      return <CodeItem starter={block.starter} label="Your code" field="files" run={!!block.make} before={before} props={props} />;
    }
    default:
      return <p className="error-note">This kind of exercise cannot be shown yet.</p>;
  }
}
