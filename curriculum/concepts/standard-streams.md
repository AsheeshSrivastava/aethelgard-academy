---
id: standard-streams
title: Standard streams
category: System basics
summary: Every program has three channels to the outside world, called stdin, stdout and stderr.
status: draft
units: ["PY-0.1", "PY-0.4"]
related: ["built-in-input", "print-function"]
aliases: ["stdin", "stdout", "stderr", "streams", "standard input", "standard output"]
doc_url: https://docs.python.org/3/library/sys.html#sys.stdin
---

A running program has three channels that connect it to the outside world.

| Channel | Direction | Used by |
| --- | --- | --- |
| `stdin` (standard input) | Data coming in | [[built-in-input\|input()]] reads from it |
| `stdout` (standard output) | Normal results going out | [[print-function\|print()]] writes to it |
| `stderr` (standard error) | Error messages going out | Python writes errors here |

In a terminal, all of this looks like one screen: you type into it, and results and errors both show up on it. To the system they are separate channels.

## Why it matters

Keeping errors apart from results means a problem does not get mixed into the program's real output. When one program's output feeds another, the error messages stay out of the data.
