import logging

class LocalFormatter:
    """
    A stateful local formatter that converts plain text with simple markers into HTML incrementally.
    
    Rules:
    - Lines starting with '# ' become <h1>
    - Lines starting with '## ' become <h2>
    - Triple backticks ``` start/end a code block <pre><code>...</code></pre>
    - Normal lines become <p>...</p>
    - Blank lines are ignored or can be handled as paragraph breaks
    
    This formatter is incremental: call feed_text(chunk) multiple times.
    It buffers partial lines if needed.
    """

    def __init__(self):
        self.buffer = ""
        self.in_code_block = False

    def feed_text(self, text: str):
        """
        Feed new text chunks to the formatter. Text may contain partial lines.
        We'll split by newline and process line by line.
        """
        self.buffer += text
        output = []

        # Process complete lines
        lines = self.buffer.split("\n")
        # Keep the last line in buffer if it's incomplete (no trailing newline)
        self.buffer = lines.pop()  # last element might be incomplete line

        for line in lines:
            line = line.rstrip("\r")  # remove trailing carriage returns if any
            formatted = self.format_line(line)
            if formatted is not None:
                output.append(formatted)

        return "".join(output)

    def close(self):
        """
        Close the formatter, flush any remaining buffer.
        If there's a partial line, process it.
        Also close code blocks if still open.
        """
        output = []
        if self.buffer.strip():
            # Process last partial line
            formatted = self.format_line(self.buffer.strip())
            if formatted:
                output.append(formatted)
        self.buffer = ""

        if self.in_code_block:
            # Close any open code block
            output.append("</code></pre>")
            self.in_code_block = False

        return "".join(output)

    def format_line(self, line: str):
        """
        Format a single complete line into HTML according to the rules.
        """
        if line.strip() == "":
            # Empty line - no <p> for now, or could add a <br>.
            # Let's ignore blank lines for simplicity.
            return None

        # Check for code block delimiters
        if line.strip() == "```":
            if self.in_code_block:
                # Close code block
                self.in_code_block = False
                return "</code></pre>"
            else:
                # Start code block
                self.in_code_block = True
                return "<pre><code>"

        if self.in_code_block:
            # Inside a code block, output as-is
            # Escape HTML if needed, here we trust code block as is.
            # For extra safety, you might want to HTML-escape code lines.
            return line + "\n"

        # Not in code block, check for headings
        if line.startswith("## "):
            return f"<h2>{line[3:].strip()}</h2>"
        elif line.startswith("# "):
            return f"<h1>{line[2:].strip()}</h1>"
        else:
            # Regular paragraph
            return f"<p>{line}</p>"