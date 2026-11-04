/** Python colouring for .py files only; anything else (README.md, notes) is plain text. */
export function languageOf(fileName: string): "python" | "text" {
  return fileName.toLowerCase().endsWith(".py") ? "python" : "text";
}
