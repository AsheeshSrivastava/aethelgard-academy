# Reading and writing files

## Opening a file safely
Use `with open("notes.txt") as f:` so Python closes the file for you, even when an error happens. Without `with`, you must call `f.close()` yourself. The default mode is read-only. A missing path raises `FileNotFoundError: [Errno 2] No such file or directory`, and a relative path is resolved from the folder where you started Python, not from the folder of your script.

## Reading text
`f.read()` returns the whole file as one string. `f.readlines()` returns a list of lines, each ending in a newline. For a large file, loop with `for line in f:` to read one line at a time without loading everything. Call `line.strip()` to drop the trailing newline.

## Writing text
Open with mode `"w"` to write. This empties the file first, so use `"a"` to append to the end instead. `f.write(text)` does not add a newline, so add `\n` yourself. A file opened for writing creates the file when it does not exist.

## Encodings
Text files are bytes on disk, and an encoding maps bytes to characters. Pass `encoding="utf-8"` to `open` so your program behaves the same on every machine. If the file was saved with another encoding you may see `UnicodeDecodeError: 'utf-8' codec can't decode byte`. Open it with the right encoding, or with `errors="replace"` to swap unreadable bytes for a marker character.
