# Handling errors with exceptions

## try and except
Put code that may fail inside `try`, and the recovery steps inside `except`. Name the error you expect, as in `except ValueError:`. A bare `except:` hides every mistake, including typing errors in your own code, so avoid it. Python runs the first `except` block whose type matches.

## else and finally
The `else` block runs only when `try` raised nothing. The `finally` block always runs, whether or not an error happened, which makes it the place to release a resource such as a network connection. Keep the `try` block short so you know which line failed.

## Raising your own errors
Use `raise ValueError("age must be positive")` to signal bad input. Pick the built-in type that fits: `ValueError` for a wrong value, `TypeError` for a wrong type. Inside an `except` block, a bare `raise` sends the same error upward again. Write `raise NewError(...) from err` to keep the original error as the cause.

## Reading a traceback
A traceback lists the calls that led to the error, with the most recent call last. Read the last line first, because it names the error type and message. The lines above it show the file and line number where each call happened. Start at the bottom frame that sits in your own code.
