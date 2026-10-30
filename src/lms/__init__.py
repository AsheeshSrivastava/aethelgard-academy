"""LMS Main Entrypoint."""

import sys
from pathlib import Path


def main() -> None:
    from lms.cli import (
        handle_ask_command,
        handle_explain_command,
        handle_index_upstream_command,
        handle_list_command,
        handle_pull_command,
        handle_verify_command,
    )

    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("LMS Platform CLI - Hybrid Workspace Tool")
        print("\nCommands:")
        print("  lms list                     List all curriculum units")
        print("  lms pull <unit_id>           Pull exercise into local workspace (for Zed / VS Code)")
        print("  lms verify <unit_id>         Run local tests and submit evidence")
        print("  lms explain <unit_id> <text> Submit CO-6 concept check explanation")
        print("  lms ask <unit_id> <question> Consult AXIS AI with Socratic guardrails")
        print("  lms index-upstream           Index upstream technical docs into persistent artifacts")
        return

    cmd = args[0].lower()

    if cmd == "list":
        print(handle_list_command())

    elif cmd == "pull":
        if len(args) < 2:
            print("Error: Specify a unit ID, e.g.: lms pull PY-0.4")
            return
        res = handle_pull_command(args[1], target_dir=Path("workspace"))
        print(res["message"])

    elif cmd == "verify":
        if len(args) < 2:
            print("Error: Specify a unit ID, e.g.: lms verify PY-0.4")
            return
        res = handle_verify_command(args[1], workspace_dir=Path("workspace"))
        print(res["message"])
        if not res["success"] and "stderr" in res:
            print(res["stderr"])

    elif cmd == "explain":
        if len(args) < 3:
            print("Error: Specify a unit ID and your explanation, e.g.: lms explain PY-0.4 'string formatting'")
            return
        res = handle_explain_command(args[1], explanation=" ".join(args[2:]))
        print(f"Status: {res['status']}")
        print(f"Feedback: {res['feedback']}")

    elif cmd == "ask":
        if len(args) < 3:
            print("Error: Specify a unit ID and your question, e.g.: lms ask PY-0.4 'what is string strip?' [mode]")
            return
        # Support optional mode as third argument: lms ask PY-0.4 "question" coach
        mode = "socratic"
        if len(args) >= 4 and args[-1].lower() in ("socratic", "coach", "hybrid"):
            mode = args[-1].lower()
            question_text = " ".join(args[2:-1])
        else:
            question_text = " ".join(args[2:])
        res = handle_ask_command(args[1], question=question_text, mode=mode)
        print(f"AXIS [{res['mode']}]: {res['reply']}")
        if res.get("suggested_action"):
            print(f"Action: {res['suggested_action']}")
        print(f"Assistance Tier: {res['detected_assistance_level']}")
        print(f"Backend: {res.get('backend', 'Offline Mock')}")

    elif cmd == "index-upstream":
        corpus_path = Path("reference/upstream")
        out_path = Path("data/index")
        for i, arg in enumerate(args):
            if arg == "--corpus" and i + 1 < len(args):
                corpus_path = Path(args[i + 1])
            elif arg == "--output" and i + 1 < len(args):
                out_path = Path(args[i + 1])
        res = handle_index_upstream_command(corpus_dir=corpus_path, output_dir=out_path)
        print(res["message"])

    else:
        print(f"Unknown command: {cmd}. Run 'lms --help' for usage.")


if __name__ == "__main__":
    main()
