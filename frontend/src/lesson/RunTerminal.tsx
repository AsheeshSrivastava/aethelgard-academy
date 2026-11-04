import "@xterm/xterm/css/xterm.css";

import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";
import { useEffect, useRef, useState } from "react";

type RunEvent =
  | { type: "stdout" | "stderr"; data: string }
  | { type: "awaiting_input" }
  | { type: "exit"; code: number; duration_ms: number; timed_out: boolean }
  | { type: "error"; message: string };

const socketUrl = () => `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/api/v1/runs`;

/** Runs the learner's code on the server and connects the program to a real terminal. */
/** A lesson passes getCode (one file); a build passes getFiles (every .py file, run from `entry`). */
export function RunTerminal({
  getCode,
  getFiles,
  exerciseId,
  entry = "solution.py",
}: {
  getCode?: () => string;
  getFiles?: () => Record<string, string>;
  exerciseId: string;
  entry?: string;
}) {
  const host = useRef<HTMLDivElement>(null);
  const terminal = useRef<Terminal | null>(null);
  const socket = useRef<WebSocket | null>(null);
  const waiting = useRef(false);
  const line = useRef("");
  const [running, setRunning] = useState(false);
  const [needsInput, setNeedsInput] = useState(false);

  useEffect(() => {
    if (!host.current) return;
    const term = new Terminal({
      convertEol: true,
      rows: 10,
      fontFamily: '"JetBrains Mono", ui-monospace, monospace',
      fontSize: 13,
      theme: { background: "#0B0E12", foreground: "#E8ECF1", cursor: "#5CC4C0" },
    });
    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(host.current);
    fit.fit();
    term.onData((data) => {
      if (!waiting.current) return;
      if (data === "\r") {
        term.write("\r\n");
        socket.current?.send(JSON.stringify({ type: "stdin", data: line.current }));
        line.current = "";
        waiting.current = false;
        setNeedsInput(false);
      } else if (data === "\x7f") {
        if (line.current) {
          line.current = line.current.slice(0, -1);
          term.write("\b \b");
        }
      } else if (data >= " ") {
        line.current += data;
        term.write(data);
      }
    });
    terminal.current = term;
    // Follows both the window and the AXIS panel handle.
    const observer = new ResizeObserver(() => fit.fit());
    observer.observe(host.current);
    return () => {
      observer.disconnect();
      socket.current?.close();
      term.dispose();
    };
  }, []);

  function handle(event: RunEvent, ws: WebSocket) {
    const term = terminal.current;
    if (!term) return;
    if (event.type === "stdout") term.write(event.data);
    else if (event.type === "stderr") term.write(`\x1b[31m${event.data}\x1b[0m`);
    else if (event.type === "exit") {
      const note = event.timed_out ? "Stopped at a limit." : `Finished with exit code ${event.code}.`;
      term.writeln(`\r\n\x1b[90m${note}\x1b[0m`);
      ws.close();
    } else if (event.type === "awaiting_input") {
      waiting.current = true;
      setNeedsInput(true);
      term.focus();
    } else if (event.type === "error") {
      term.writeln(`\x1b[31m${event.message}\x1b[0m`);
      ws.close();
    }
  }

  function run() {
    const term = terminal.current;
    if (!term) return;
    term.clear();
    term.reset();
    line.current = "";
    waiting.current = false;
    const ws = new WebSocket(socketUrl());
    socket.current = ws;
    setRunning(true);
    ws.onopen = () =>
      ws.send(
        JSON.stringify({
          type: "start",
          files: getFiles ? getFiles() : { [entry]: getCode?.() ?? "" },
          entry,
          exercise_id: exerciseId,
        }),
      );
    ws.onmessage = (message) => handle(JSON.parse(String(message.data)) as RunEvent, ws);
    ws.onclose = () => {
      waiting.current = false;
      setNeedsInput(false);
      setRunning(false);
    };
  }

  return (
    <div className="run-terminal">
      <div className="run-bar">
        <span className="run-status">{needsInput ? "Waiting for your input. Type here and press Enter." : running ? "Running…" : "Terminal"}</span>
        {running ? (
          <button type="button" className="button button-small" onClick={() => socket.current?.close()}>
            Stop
          </button>
        ) : (
          <button type="button" className="button button-small" onClick={run}>
            Run
          </button>
        )}
      </div>
      <div ref={host} className="terminal-host" aria-label="Program terminal" role="group" />
    </div>
  );
}
