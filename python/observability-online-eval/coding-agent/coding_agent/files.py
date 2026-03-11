"""
FilesDict and parsing utilities for converting LLM output into files.

Adapted from gpt-engineer's files_dict.py and chat_to_files.py, simplified
for cookbook clarity.
"""

import re
from collections import OrderedDict
from pathlib import Path
from typing import Union


class FilesDict(dict):
    """Dict mapping filename -> content. Type-checked keys/values."""

    def __setitem__(self, key: Union[str, Path], value: str):
        if not isinstance(key, (str, Path)):
            raise TypeError("Keys must be strings or Paths")
        if not isinstance(value, str):
            raise TypeError("Values must be strings")
        super().__setitem__(str(key), value)

    def to_context(self) -> str:
        """Format files for LLM context with line numbers."""
        parts = []
        for filename, content in self.items():
            lines = content.split("\n")
            numbered = "\n".join(
                f"{i + 1} {line}" for i, line in enumerate(lines)
            )
            parts.append(f"File: {filename}\n{numbered}")
        return "\n\n".join(parts)

    def to_display(self) -> str:
        """Format for user-facing output."""
        parts = []
        for filename, content in self.items():
            parts.append(f"{filename}\n```\n{content}\n```")
        return "\n\n".join(parts)


def parse_chat_to_files(chat_response: str) -> FilesDict:
    """Parse LLM response (filename + code blocks) into FilesDict."""
    regex = r"(\S+)\n\s*```[^\n]*\n(.+?)```"
    matches = re.finditer(regex, chat_response, re.DOTALL)

    files = FilesDict()
    for match in matches:
        # Clean the file path
        path = re.sub(r'[\:<>"|?*]', "", match.group(1))
        path = re.sub(r"^\[(.*)\]$", r"\1", path)
        path = re.sub(r"^`(.*)`$", r"\1", path)
        path = re.sub(r"[\]\:]$", "", path)
        content = match.group(2)
        files[path.strip()] = content.strip()
    return files


def parse_diffs(diff_string: str) -> list[dict]:
    """Parse unified diff blocks from LLM response.

    Returns a list of dicts with keys:
      - filename_pre: original filename (or /dev/null for new files)
      - filename_post: new filename
      - hunks: list of (action, line) tuples where action is +, -, or ' '
      - is_new: whether this is a new file
    """
    # Match diff blocks fenced with ```
    block_pattern = re.compile(
        r"```(?:diff)?\s*\n(---\s+\S+.*?\n\+\+\+\s+\S+.*?\n(?:@@.*?@@\n(?:[-+ ].*?\n)*?)*?)```",
        re.DOTALL,
    )

    diffs = []
    for block_match in block_pattern.finditer(diff_string):
        block = block_match.group(1)
        lines = block.strip().split("\n")

        filename_pre = None
        filename_post = None
        hunks = []
        current_hunk = None

        for line in lines:
            if line.startswith("--- "):
                filename_pre = line[4:].strip()
            elif line.startswith("+++ "):
                filename_post = line[4:].strip()
            elif line.startswith("@@ "):
                header_match = re.match(r"@@ -(\d+)", line)
                current_hunk = {
                    "hunk_start": int(header_match.group(1)) if header_match else 1,
                    "lines": [],
                }
                hunks.append(current_hunk)
            elif current_hunk is not None:
                if line.startswith("+"):
                    current_hunk["lines"].append(("+", line[1:]))
                elif line.startswith("-"):
                    current_hunk["lines"].append(("-", line[1:]))
                else:
                    current_hunk["lines"].append((" ", line[1:] if line.startswith(" ") else line))

        if filename_post:
            diffs.append({
                "filename_pre": filename_pre,
                "filename_post": filename_post,
                "hunks": hunks,
                "is_new": filename_pre == "/dev/null",
            })

    return diffs


def apply_diffs(diffs: list[dict], existing_files: FilesDict) -> FilesDict:
    """Apply parsed diffs to existing files. Returns updated FilesDict."""
    files = FilesDict(existing_files.copy())
    REMOVE_FLAG = "<REMOVE_LINE>"

    for diff in diffs:
        if diff["is_new"]:
            # New file: collect all added lines from all hunks
            content = "\n".join(
                line for hunk in diff["hunks"] for action, line in hunk["lines"] if action == "+"
            )
            files[diff["filename_post"]] = content
        else:
            source_name = diff["filename_pre"]
            if source_name not in files:
                continue

            # Convert file to ordered line dict
            source_lines = files[source_name].split("\n")
            line_dict = OrderedDict(
                (i + 1, line) for i, line in enumerate(source_lines)
            )

            for hunk in diff["hunks"]:
                current_line = hunk["hunk_start"]
                for action, content in hunk["lines"]:
                    if action == " ":
                        current_line += 1
                    elif action == "+":
                        # Insert after current position
                        current_line -= 1
                        if current_line in line_dict and line_dict[current_line] != REMOVE_FLAG:
                            line_dict[current_line] += "\n" + content
                        else:
                            line_dict[current_line] = content
                        current_line += 1
                    elif action == "-":
                        line_dict[current_line] = REMOVE_FLAG
                        current_line += 1

            # Remove flagged lines and reassemble
            line_dict = {
                k: v for k, v in line_dict.items() if REMOVE_FLAG not in v
            }
            files[diff["filename_post"]] = "\n".join(line_dict.values())

    return files
