"""Verify that every inline `python3 -c "..."` snippet in markdown files is syntactically valid.

We had bugs where indentation in escalation rollback was wrong (mixed column-0 and 5-space
indent), causing IndentationError at runtime. This test catches that class of bug at CI time
without needing to actually execute the snippets.

Heuristic: scan all .md files under skills/armchair-architect/ for fenced bash blocks; inside
each block, look for `python3 -c "` openers and grab everything up to the matching closing `"`.
Compile each snippet with ast.parse — any SyntaxError fails the test.
"""
import ast
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SKILL_ROOT = REPO / "skills" / "armchair-architect"

# Match a triple-backtick bash fence and its body
BASH_FENCE = re.compile(r"```bash\s*\n(.*?)\n```", re.DOTALL)

# Match `python3 -c "...."` — quoted body (greedy across newlines), allowing escaped quotes.
PY_C_SNIPPET = re.compile(r'python3\s+-c\s+"((?:[^"\\]|\\.)*)"', re.DOTALL)


def shell_unescape(s):
    """Apply bash double-quoted string unescaping: \\" -> ", \\\\ -> \\, \\$ -> $, \\` -> `.
    This is what the user's shell does before passing the -c arg to python.
    """
    out = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] in '"\\$`':
            out.append(s[i + 1])
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def iter_markdown_files():
    for p in SKILL_ROOT.rglob("*.md"):
        # Skip the lite variant — its snippets are illustrative for non-Claude-Code envs
        if "armchair-architect-lite" in str(p):
            continue
        yield p


def extract_python_snippets(text):
    snippets = []
    for fence in BASH_FENCE.findall(text):
        for snippet in PY_C_SNIPPET.findall(fence):
            snippets.append(shell_unescape(snippet))
    return snippets


class TestInlineSnippetsCompile(unittest.TestCase):
    def test_all_inline_python_snippets_are_syntactically_valid(self):
        failures = []
        total = 0
        for md in iter_markdown_files():
            text = md.read_text()
            for i, snippet in enumerate(extract_python_snippets(text)):
                total += 1
                try:
                    ast.parse(snippet)
                except SyntaxError as e:
                    rel = md.relative_to(REPO)
                    failures.append(f"{rel} (snippet #{i + 1}): {e}\n--- snippet ---\n{snippet}\n--- end ---")
        if failures:
            self.fail(
                f"{len(failures)} of {total} inline python3 -c snippets have syntax errors:\n\n"
                + "\n\n".join(failures)
            )


class TestStateLibImported(unittest.TestCase):
    """If a step file uses inline state ops (json.load on .pipeline/...) instead of the library,
    flag it. The library exists precisely to avoid these snippets drifting apart again.
    """

    ALLOWED_INLINE = {
        # progress.md snapshot reads implementation_plan.json, not state.json — ok
        "impl/execute/default.md",
    }

    def test_no_unauthorized_inline_state_reads(self):
        offenders = []
        for md in iter_markdown_files():
            rel = str(md.relative_to(SKILL_ROOT))
            if rel in self.ALLOWED_INLINE:
                continue
            text = md.read_text()
            for snippet in extract_python_snippets(text):
                if ".pipeline/" in snippet and "import state" not in snippet:
                    offenders.append(f"{rel}: snippet uses raw .pipeline/ paths — should use 'import state' from lib/state.py\n{snippet}")
        if offenders:
            self.fail("\n\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
