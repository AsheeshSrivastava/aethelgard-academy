# Database basics with SQL

## Reading rows
`SELECT name, city FROM students;` returns those columns for every row. `SELECT *` returns all columns. Add `WHERE city = 'Pune'` to keep matching rows, `ORDER BY name` to sort, and `LIMIT 10` to cap the count.

## Joining tables
A join combines rows from two tables that share a value. `SELECT s.name, c.title FROM students s JOIN courses c ON c.id = s.course_id;` pairs each student with a course. An inner join drops rows with no match, while a `LEFT JOIN` keeps every row from the left table and fills the gaps with NULL.

## Counting and grouping
`COUNT(*)` counts rows. With `GROUP BY city` the database makes one result row for each city, so `SELECT city, COUNT(*) FROM students GROUP BY city;` counts students per city. Filter groups with `HAVING`, not `WHERE`, because `WHERE` runs before grouping.

## Passing values safely
Never build a query by pasting user text into the string, because a value such as `x'; DROP TABLE students; --` can run as SQL. This attack is called SQL injection. Use placeholders: `cur.execute("SELECT * FROM students WHERE name = ?", (name,))`. If you see `sqlite3.OperationalError: no such table: students`, the table was never created in that database file, or you opened a different file.
