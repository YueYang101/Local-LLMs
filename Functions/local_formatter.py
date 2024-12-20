import html

class LocalFormatter:
    """
    Stateful formatter to convert plain text into HTML incrementally.
    """

    def __init__(self):
        self.buffer = ""
        self.in_code_block = False
        self.in_list = False

    def feed_text(self, text: str):
        self.buffer += text
        output = []
        lines = self.buffer.split("\n")
        self.buffer = lines.pop()

        for line in lines:
            formatted = self.format_line(line.rstrip())
            if formatted:
                output.append(formatted)

        return "".join(output)

    def close(self):
        output = []

        if self.buffer.strip():
            formatted = self.format_line(self.buffer.strip())
            if formatted:
                output.append(formatted)

        if self.in_code_block:
            output.append("</code></pre>")
            self.in_code_block = False

        if self.in_list:
            output.append("</ul>")
            self.in_list = False

        self.buffer = ""
        return "".join(output)

    def format_line(self, line: str):
        if line.strip() == "":
            return "<br>"

        if line.strip() == "```":
            if self.in_code_block:
                self.in_code_block = False
                return "</code></pre>"
            else:
                self.in_code_block = True
                return "<pre><code>"

        if self.in_code_block:
            return html.escape(line) + "\n"

        if line.startswith(("- ", "* ")):
            if not self.in_list:
                self.in_list = True
                return f"<ul><li>{line[2:].strip()}</li>"
            return f"<li>{line[2:].strip()}</li>"

        if self.in_list:
            self.in_list = False
            return f"</ul>{self.format_regular_line(line)}"

        if line.startswith("## "):
            return f"<h2>{line[3:].strip()}</h2>"
        elif line.startswith("# "):
            return f"<h1>{line[2:].strip()}</h1>"

        if "**" in line:
            line = self.format_bold_text(line)

        return self.format_regular_line(line)

    def format_bold_text(self, line: str):
        return line.replace("**", "<strong>", 1).replace("**", "</strong>", 1)

    def format_regular_line(self, line: str):
        return f"<p>{line}</p>"