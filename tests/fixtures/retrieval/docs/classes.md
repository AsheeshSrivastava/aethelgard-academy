# Classes and objects

## Defining a class
A class is a blueprint, and an object is one thing built from it. Write `class Course:` and create an object with `Course()`. The special method `__init__` runs when the object is created and sets its starting data.

## self
Every method takes `self` as its first parameter, the object the method was called on. Use `self.title = title` to store data on the object. Forgetting `self` in the definition gives `TypeError: Course.start() takes 0 positional arguments but 1 was given`.

## Attributes and methods
Data stored on an object is an attribute, and a function defined in the class is a method. Call a method with a dot: `course.start()`. Attributes assigned in `__init__` belong to each object. An attribute assigned directly in the class body is shared by all objects.

## Dataclasses
For a class that mostly holds data, put `@dataclass` above it and list the fields: `title: str`, `weeks: int = 4`. Python writes `__init__`, a readable `__repr__` and equality for you. Fields with defaults must come after fields without them.
