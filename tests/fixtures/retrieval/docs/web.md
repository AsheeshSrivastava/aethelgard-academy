# How web requests work

## Requests and responses
A browser or program sends a request to a server and gets back a response. A request has a method, a path, headers and sometimes a body. The response has a status code, headers and a body.

## Methods
`GET` reads data and must not change anything on the server. `POST` sends data to create something. `PUT` replaces an item and `DELETE` removes it. Choosing the method that matches the meaning keeps an API predictable.

## Status codes
Codes starting with 2 mean success: `200 OK`, `201 Created`. Codes starting with 4 mean the caller made a mistake: `404 Not Found` for a missing item, `401 Unauthorized` for missing login, `422` when the data fails validation. Codes starting with 5 mean the server failed, such as `500 Internal Server Error`. Return the code that tells the truth about what happened.

## JSON bodies
APIs usually send data as JSON. In Python, `json.loads(text)` turns a JSON string into dictionaries and lists, and `json.dumps(data)` turns data into a string. `json.JSONDecodeError: Expecting value` means the text is empty or is not JSON, such as an HTML error page. Set the header `Content-Type: application/json` when you send JSON.
