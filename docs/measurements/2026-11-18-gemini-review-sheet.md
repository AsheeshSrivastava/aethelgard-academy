# Review sheet: 24 questions from the six Gemini sets (SPEC-25 R8)

SET_VERSION `5d5fbd741a89ee65`. Seed 25. Four questions per set, one of each kind. Fill the two boxes for each question:
put `y` or `n`. The bar is 22 of 24 `y` on **each** box (90%). Below that, the sets are not used as a gate until fixed.

- *Realistic?* Would a learner plausibly type or paste this?
- *Page right?* Is the expected page really the best place in the docs to answer it? (The expected path is the folder or page name.)

| # | Set / kind | Question | Expected page | Realistic? | Page right? |
| --- | --- | --- | --- | --- | --- |
| 1 | fastapi-docs / plain | how do i add middleware that runs before and after every request? | `tutorial/middleware` | [ ] | [ ] |
| 2 | fastapi-docs / error | calling /users/me gives 422 Input should be a valid integer because it matches /users/{user_id}, how do i fix it? | `tutorial/path-params` | [ ] | [ ] |
| 3 | fastapi-docs / paraphrase | how do i make sure a database session closes after the endpoint finishes even if an error happens? | `tutorial/dependencies/dependencies-with-yield` | [ ] | [ ] |
| 4 | fastapi-docs / pasted | why does my partial update wipe out fields i didn't send?? PATCH /items/foo with {"price": 25.0} Response: {"name": "Foo", "description": null, "price": 25.0} C... | `tutorial/body-updates` | [ ] | [ ] |
| 5 | httpx-docs / plain | how do i configure an http or socks proxy in httpx? | `advanced/proxies` | [ ] | [ ] |
| 6 | httpx-docs / error | httpx returns a 301 or 302 response instead of following the redirect like requests does, why? | `compatibility, quickstart` | [ ] | [ ] |
| 7 | httpx-docs / paraphrase | how do i send files in a multipart upload? | `quickstart` | [ ] | [ ] |
| 8 | httpx-docs / pasted | why did i get 302 instead of the final page?? r = httpx.get("https://example.org/old") print(r.status_code) # 302 C:\Users\sam\shop\client.py:6 def fetch_page()... | `compatibility, quickstart` | [ ] | [ ] |
| 9 | pydantic-docs / plain | how do i validate a list of dicts without wrapping it in a BaseModel class? | `type_adapter` | [ ] | [ ] |
| 10 | pydantic-docs / error | my pydantic dataclass fails with TypeError or schema error when using forward references | `dataclasses, forward_annotations` | [ ] | [ ] |
| 11 | pydantic-docs / paraphrase | how do i drop None values or unprovided keys when turning an object back into a dict? | `serialization` | [ ] | [ ] |
| 12 | pydantic-docs / pasted | why didn't pydantic catch this invalid default value?? no error raised when defining User, User() returns age='not-a-number' C:\Users\sam\shop\schemas\user.py:4... | `fields` | [ ] | [ ] |
| 13 | pytest-docs / plain | what does exit code 5 mean in pytest? | `reference/exit-codes` | [ ] | [ ] |
| 14 | pytest-docs / error | i keep getting PytestUnknownMarkWarning for my custom slow tag, how do i fix it? | `how-to/mark, reference/reference` | [ ] | [ ] |
| 15 | pytest-docs / paraphrase | where do i save default command flags in my project repo so i don't have to pass them every time? | `reference/customize, example/simple` | [ ] | [ ] |
| 16 | pytest-docs / pasted | why is pytest complaining about my test method?? E TypeError: TestCart.test_save() missing 1 required positional argument: 'tmp_path' C:\Users\sam\shop\tests\te... | `how-to/unittest` | [ ] | [ ] |
| 17 | python-docs / plain | how do i make a custom object work with a with statement? | `reference/datamodel` | [ ] | [ ] |
| 18 | python-docs / error | python gives IndentationError unindent does not match any outer indentation level, what causes that? | `reference/lexical_analysis` | [ ] | [ ] |
| 19 | python-docs / paraphrase | how do i make my custom class printable in a nice human-readable way and comparable with ==? | `reference/datamodel` | [ ] | [ ] |
| 20 | python-docs / pasted | why did rex get buddy's tricks?? print(rex.tricks) # ['roll over', 'play dead'] C:\Users\sam\shop\pets.py:6 class Dog: tricks = [] def add_trick(self, trick): s... | `tutorial/classes` | [ ] | [ ] |
| 21 | uv-docs / plain | how do i set up uv inside a dockerfile for production? | `guides/integration/docker` | [ ] | [ ] |
| 22 | uv-docs / error | uv complains about requires-python mismatch when i try to add a dependency that needs python 3.11+ | `concepts/resolution` | [ ] | [ ] |
| 23 | uv-docs / paraphrase | how do i see why a package is installed in my environment as a dependency tree? | `getting-started/features` | [ ] | [ ] |
| 24 | uv-docs / pasted | why did uv add fail with a python version error?? × No solution found when resolving dependencies: ╰─▶ Because the current Python version (3.9.18) does not sati... | `concepts/resolution` | [ ] | [ ] |

Totals: realistic ___ / 24, page right ___ / 24.
