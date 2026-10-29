"""LMS Main Entrypoint."""

import sys
from pathlib import Path


def main() -> None:
    from lms.cli import (
        handle_list_command,
        handle_pull_command,
        handle_verify_command,
    )

    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("LMS Platform CLI - Hybrid Workspace Tool")
        print("\nCommands:")
        print("  lms list              List all curriculum units")
        print("  lms pull <unit_id>    Pull exercise into local workspace (for Zed / VS Code)")
        print("  lms verify <unit_id>  Run local tests and submit evidence")
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

    else:
        print(f"Unknown command: {cmd}. Run 'lms --help' for usage.")


if __name__ == "__main__":
    main()
