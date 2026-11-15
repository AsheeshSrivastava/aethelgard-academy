# Writing functions

## Defining and calling
Define a function with `def name(parameters):` and an indented body. Call it with parentheses and arguments. A function that reaches the end without a `return` statement gives back None, which is why printing the result of a function that only prints shows None.

## Default values
Give a parameter a default with `def greet(name="friend"):`. Parameters with defaults must come after those without. Never use a list or dictionary as a default value. Python builds the default once, when the function is defined, so every call shares the same list and items from earlier calls remain. Use `None` as the default and create the list inside the function.

## Positional and keyword arguments
Pass arguments by position, `area(3, 4)`, or by name, `area(width=3, height=4)`. Naming makes calls easier to read. Python raises `TypeError: area() missing 1 required positional argument: 'height'` when you leave one out, and a different `TypeError` when you pass too many.

## Collecting extra arguments
A parameter written `*args` collects extra positional arguments into a tuple. A parameter written `**kwargs` collects extra named arguments into a dictionary. Use a star at the call site to unpack a list into arguments, `f(*items)`, or two stars for a dictionary, `f(**options)`.
