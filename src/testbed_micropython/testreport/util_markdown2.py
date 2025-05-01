import markdown2

# See: https://github.com/trentm/python-markdown2/wiki/Extras
_MARKDOWN = markdown2.Markdown(
    extras=[
        "tables",  # Tables using the same format as GFM and PHP-Markdown Extra.
        "footnotes",  # support footnotes as in use on daringfireball.net and implemented in other Markdown processors (tho not in Markdown.pl v1.0.1).
        "target-blank-links",  # Add target="_blank" to all <a> tags with an href. This causes the link to be opened in a new tab upon a click.
        # "html-classes",  # Takes a dict mapping html tag names (lowercase) to a string to use for a "class" tag attribute. Currently only supports "pre", "code", "table" and "img" tags. Add an issue if you require this for other tags.
    ]
)

_HTML_BODY = r"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html lang="en">
<head>
<title>[[TITLE]]</title>
<style>
body {
    font-family: 'Arial', Verdana, sans-serif;
    font-size: 14px;
}
table, th, td {
  border: 1px solid black;
  border-collapse: collapse;
  padding: 4px;
}
</style>
</head>
<body>
[[BODY]]
</body>
</html>
"""


def markdown2html(markdown_content: str, title: str) -> str:
    # Convert Markdown to HTML
    html_content = _MARKDOWN.convert(markdown_content)

    # Return the HTML content
    return _HTML_BODY.replace("[[TITLE]]", title).replace("[[BODY]]", html_content)
