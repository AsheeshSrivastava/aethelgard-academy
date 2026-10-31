# SPEC-14: Concept Library

- **Status:** Accepted for implementation
- **Governed by:** ADR-0003 (Stage 2 store), ADR-0002 (SQLite for learner state), ADR-0008 (curriculum lives as packages), SPEC-12 (Learner Experience API), SPEC-13 (findings, not crashes)
- **Date:** 2026-10-31

---

## 1. Purpose

While reading a lesson, or later when stuck, a learner needs one clear place that says what a thing is. The Concept Library is that place: short Markdown notes, reached by search or by a link inside a lesson or another note.

Opening a note is a reading aid. **It is not evidence.** Nothing here touches the Evidence Ledger, the Cold Check, or progression.

Out of scope: indexing concept notes for AXIS retrieval (ADR-0003 section 4 covers that review), and editing notes in the browser.

---

## 2. Where notes live

One Markdown file per concept, under `curriculum/concepts/`. The file name is the slug.

```text
curriculum/concepts/
  variables.md
  print-function.md
```

Decisions:
- **Files, not database rows.** Notes are curriculum: reviewed, versioned and committed like lessons (ADR-0008). They are loaded once at startup.
- **Recent searches are learner state**, so they go in SQLite (ADR-0002).
- The owner chose on 2026-10-31 to move six of the old `docs/concepts/` notes here as drafts. The three that overlapped the new notes (`built-in-print`, `comments-pseudocode`, `variables-memory`) were removed, with the script that generated them; git history keeps them. `DEFAULT_CONCEPTS` is removed.

### 2.1 File format

```markdown
---
id: print-function
title: The print() function
category: Core tools
summary: print() shows values on the terminal.
status: draft
units: ["PY-0.1", "PY-0.4"]
related: ["variables", "expressions"]
aliases: ["print", "print()", "output"]
doc_url: https://docs.python.org/3/library/functions.html#print
---

The body, in Markdown. It does not repeat the title: the page shows it.
```

| Field | Required | Rule |
| :--- | :--- | :--- |
| `id` | yes | Lowercase words joined by `-`. Must equal the file name. This is the slug. |
| `title` | yes | Shown as the page heading. |
| `category` | yes | Free text. |
| `summary` | yes | One sentence, shown in search results. |
| `status` | yes | `draft` or `approved`. A draft is shown with a Draft label. |
| `units` | no | Unit ids that use this concept. |
| `related` | no | Slugs of related concepts. |
| `aliases` | no | Other words a learner might search for. |
| `doc_url` | no | Official documentation, `http` or `https` only. |

Frontmatter is parsed as safe YAML. An unknown key is an error, so a typing mistake cannot pass silently.

### 2.2 Bad notes

A bad note never stops the app (SPEC-13). It is skipped, and a finding with code `concept-invalid` names the file and says what is wrong. That covers: no frontmatter, broken YAML, a missing or unknown field, a bad `id` or `status`, an empty body, text that is not UTF-8. A second note claiming a slug is impossible because the id must equal the file name.

---

## 3. Wiki links

Written in lesson text and in concept notes:

```text
[[variables]]                 the link shows the concept's title
[[variables|a variable]]      the link shows "a variable"
[[variables\|a variable]]     the same, inside a Markdown table
```

- A link opens `/concepts/<slug>` inside the app.
- Inside code blocks and inline code, `[[x]]` stays as written, because it can be real Python.
- AXIS replies and exercise prompts do not turn `[[x]]` into links. A Cold Check must never hold a way out to a note.
- An unknown slug shows as plain text (the label, or the slug), and the browser console warns in development. The learner never sees a broken link.
- While the list of concepts is loading, the text shows plain, then becomes a link.

### 3.1 Curriculum checks

`check_concept_links` adds these findings to `catalog.findings` at startup:

| Code | Severity | Means |
| :--- | :--- | :--- |
| `concept-link-broken` | error | A lesson or note links to a slug that does not exist. |
| `concept-related-unknown` | error | `related` names a slug that does not exist. |
| `concept-unit-unknown` | error | `units` names a unit that does not exist. |

Links inside code in the source text are ignored, matching section 3.

---

## 4. Search

Pure and deterministic, in `lms/core/concepts.py`. The query and each field are lowercased. A query matches a field when every word of the query appears in it. A query with no letters or digits, such as `#`, is matched as written.

Each note gets the rank of its best field:

| Rank | Match |
| :--- | :--- |
| 1 | Title equals the query |
| 2 | Title starts with the query |
| 3 | Title contains the query |
| 4 | An alias equals the query, or contains it |
| 5 | The summary contains it |
| 6 | The body contains it |

Ties go by title, A to Z. No match on any field means the note is not returned. A blank query returns nothing from search; the route then lists every note, A to Z.

---

## 5. API

### `GET /api/v1/concepts?q=`

No `q`: every note, A to Z. With `q`: ranked matches. `q` is at most 200 characters; longer is `422`. `search=` is kept as another name for `q` while `/legacy` lives.

Returns `ConceptSummary[]`: `concept_id, name, category, summary, status, units, doc_url`. No body, so a list stays small.

`concept_id` is the slug and `name` is the title. These are the existing `ConceptItem` names, kept so `/legacy` and the AXIS citations keep working.

### `GET /api/v1/concepts/{slug}`

Returns `ConceptDetail`: every `ConceptItem` field, including `content_markdown`, plus:
- `aliases: [str]`
- `related: [{concept_id, name}]`, from the note's `related`, skipping unknown slugs
- `used_in: [{unit_id, title}]`, units named in `units` plus units whose lesson links to the note, in teaching order, without repeats, skipping unknown units

Unknown slug: `404` problem.

The markdown is returned as written. Making it safe is the renderer's job (section 7).

### `GET /api/v1/learners/me/concepts/recent`

Returns `ConceptSummary[]`, newest first, at most 5. A note that no longer exists is left out.

### `PUT /api/v1/learners/me/concepts/recent/{slug}`

`204`. Records that the learner opened this note **from the library page**. Opening the same note again moves it to the top, so it appears once. Only the newest 5 are kept. Unknown slug: `404` problem.

Wiki links and direct visits do not call this. Resetting a unit does not touch it.

---

## 6. Frontend

**Top bar:** a `Concept library` link between Courses and My progress.

**`/concepts`:**
- A search box, labelled, with a short wait after typing (250 ms) so each key press is not a request.
- The query is kept in the address (`?q=`), so Back returns to the same results.
- With no query: the latest 5 opened notes under the box. With no recent notes: a short line saying how to start.
- With a query: the results, each with title, category, summary and a Draft label if draft, and a line that counts them for screen readers.
- No results: a plain message.
- Keyboard: Enter opens the top result. Down moves from the box into the results, Up and Down move between them, Up from the first goes back to the box.

**`/concepts/:slug`:** back arrow to the library, title, Draft label if draft, category, summary, the body, then Related concepts, Used in units and a link to the official documentation. Each list is left out if empty. An unknown slug shows a plain "not found" message with the back arrow.

The note page loads only when opened, since the renderer pulls in the code colouring.

---

## 7. Rendering and safety

Notes use the same `Prose` renderer as lessons and AXIS, with wiki links on. All of its rules hold: raw HTML is shown as text, images are dropped, only `http` and `https` links work, code blocks get colours and Copy.

Links come only from the plugin that reads text in `[[...]]`, and a slug that fails the id rule stays plain text. So a note cannot build a link to anywhere else.

---

## 8. Acceptance

1. All four draft notes load with no findings. Their Python blocks compile.
2. Search: title beats alias beats summary beats body; ties are A to Z; `print()` and `#` find something sensible; odd input never fails.
3. Recent: order, repeats move to the top, never more than 5, per learner, a deleted note is left out, the ledger is unchanged.
4. Bad notes: each case in section 2.2 gives `concept-invalid` and the others still load.
5. Wiki links: `[[slug]]`, `[[slug|label]]`, inside a table, inside code, unknown slug, a slug with bad characters.
6. Stage 0 lessons link to the notes, and the curriculum checks report no broken links.
7. Browser: search, open, recent list, a wiki link from Explain, and back, in light, dark and phone width.
