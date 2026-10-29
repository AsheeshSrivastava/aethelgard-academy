---
source_id: concepts/py-1.1-names-and-bindings
version: v1.0.0
licence: Proprietary-LMS
---

# Names and Object Bindings

In Python, a variable name is an assigned label or reference pointing to an object residing in memory; assignment moves the label, it does not copy the underlying object.

Unlike legacy physical registries where writing an entry creates a permanent static box, Python names act as dynamic reference tags pointing to objects in the heap.

Understanding that names are pointers prevents critical concurrency bugs and unexpected state mutations when handling shared dictionaries or records.
