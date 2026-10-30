"""Concept Library & Knowledge Management System (KMS) Catalog.

Maintains canonical technical concepts, operational definitions, execution rules,
official upstream documentation anchors, and cross-references to curriculum units.
"""

from typing import List, Optional
from lms.core.models import ConceptItem


DEFAULT_CONCEPTS: List[ConceptItem] = [
    ConceptItem(
        concept_id="sequential-execution",
        name="Sequential Statement Execution (Top-to-Bottom)",
        category="Execution Model",
        summary="Python reads and executes statements one at a time strictly in order from top to bottom.",
        execution_rules="Line N executes completely before Line N+1 begins. Variables created on Line N do not exist prior to that line.",
        doc_url="https://docs.python.org/3/reference/executionmodel.html",
        units=["PY-0.1", "PY-0.4"],
    ),
    ConceptItem(
        concept_id="assignment-evaluation",
        name="Right-to-Left Assignment Order",
        category="Execution Model",
        summary="In any assignment statement (variable = expression), the right-hand side executes first.",
        execution_rules="Python evaluates the right-hand expression completely, produces a return value, and then binds that value to the variable name on the left.",
        doc_url="https://docs.python.org/3/reference/simple_stmts.html#assignment-statements",
        units=["PY-0.1"],
    ),
    ConceptItem(
        concept_id="built-in-input",
        name="input() Built-in Function",
        category="Core Primitives",
        summary="Pauses execution, reads user text from standard input (stdin), and returns it as a string.",
        execution_rules="Always returns a string (str), even if the user typed numbers. Trailing newlines are stripped from the return value.",
        doc_url="https://docs.python.org/3/library/functions.html#input",
        units=["PY-0.1", "PY-0.4"],
    ),
    ConceptItem(
        concept_id="built-in-print",
        name="print() Built-in Function",
        category="Core Primitives",
        summary="Writes formatted text to standard output (stdout).",
        execution_rules="Calling print() with no arguments writes an empty line to stdout. A blank line in code does not produce a blank line on screen.",
        doc_url="https://docs.python.org/3/library/functions.html#print",
        units=["PY-0.1", "PY-0.4"],
    ),
    ConceptItem(
        concept_id="variables-identifiers",
        name="Variables & Memory Identifiers",
        category="State & Memory",
        summary="A named label in memory that references a stored value.",
        execution_rules="Variables in Python do not have static type declarations; they point to objects in heap memory. Referencing an unassigned variable raises NameError.",
        doc_url="https://docs.python.org/3/reference/executionmodel.html#naming-and-binding",
        units=["PY-0.1"],
    ),
    ConceptItem(
        concept_id="formatted-strings",
        name="Formatted String Literals (f-strings)",
        category="String Formatting",
        summary="Prefixing a string with 'f' allows embedding Python expressions directly inside {curly_braces}.",
        execution_rules="Expressions inside {brackets} are evaluated at runtime and converted to strings before output.",
        doc_url="https://docs.python.org/3/tutorial/inputoutput.html#formatted-string-literals",
        units=["PY-0.1", "PY-0.4"],
    ),
    ConceptItem(
        concept_id="comments-pseudocode",
        name="Comments as Pseudocode Blueprint",
        category="Engineering Discipline",
        summary="Lines starting with '#' are ignored by Python and used to plan steps before writing syntax.",
        execution_rules="Comments produce zero bytecode and have zero runtime effect. Used for decomposition (Activity 5).",
        doc_url="https://docs.python.org/3/tutorial/introduction.html#first-steps-towards-programming",
        units=["PY-0.1", "PY-0.3"],
    ),
    ConceptItem(
        concept_id="standard-streams",
        name="Standard Streams (stdin, stdout, stderr)",
        category="System Architecture",
        summary="The fundamental input and output communication channels connecting an operating system process to the outside world.",
        execution_rules="stdin handles ingress (read by input()), stdout handles normal egress (written by print()), stderr handles error reporting.",
        doc_url="https://docs.python.org/3/library/sys.html#sys.stdin",
        units=["PY-0.1", "PY-0.4"],
    ),
    ConceptItem(
        concept_id="ai-reasoning-boundary",
        name="Tool Help vs Developer Reasoning (DE-3)",
        category="AI Discipline",
        summary="AI can generate candidate code, but the human architect owns correctness, verification, and boundary integrity.",
        execution_rules="Code provided by AI must be audited against official documentation and tested against deterministic assertions before deployment.",
        doc_url="https://docs.python.org/3/tutorial/errors.html",
        units=["PY-0.3"],
    ),
]


class ConceptCatalog:
    """In-memory searchable registry of technical concepts."""

    def __init__(self, concepts: Optional[List[ConceptItem]] = None):
        self._concepts = list(concepts) if concepts is not None else list(DEFAULT_CONCEPTS)

    def list_all(self) -> List[ConceptItem]:
        return list(self._concepts)

    def search(self, query: str) -> List[ConceptItem]:
        q = query.lower().strip()
        if not q:
            return self.list_all()
        return [
            c for c in self._concepts
            if q in c.name.lower() or q in c.summary.lower() or q in c.category.lower() or any(q in u.lower() for u in c.units)
        ]

    def get(self, concept_id: str) -> Optional[ConceptItem]:
        for c in self._concepts:
            if c.concept_id == concept_id:
                return c
        return None
