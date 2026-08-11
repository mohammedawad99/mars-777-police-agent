"""Read a module's **code** rather than its prose.

An architecture guard that greps raw source answers the wrong question: a
docstring explaining *why* a module never opens a socket contains the word
`socket`, and the guard fires on the explanation instead of the defect. These
helpers strip every string literal and comment first, so what remains is
identifiers, operators and structure - which is what the boundary rules are
actually about.

Imports are read from the AST for the same reason, and because a dotted module
path is a fact rather than a substring.
"""

import ast
import inspect
import io
import tokenize
from types import ModuleType

_PROSE = {tokenize.STRING, tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE}


def code_of(module: ModuleType) -> str:
    """Return *module*'s source with every literal string and comment removed."""
    source = inspect.getsource(module)
    kept: list[str] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type in _PROSE or token.type == getattr(tokenize, "FSTRING_MIDDLE", -1):
            continue
        kept.append(token.string)
    return " ".join(kept)


def tokens_of(module: ModuleType) -> set[str]:
    """Return *module*'s distinct code tokens.

    Exact tokens, never substrings: `config_sha256` is not the `sha256` function
    and `opening` is not the `open` builtin, and a guard that cannot tell them
    apart fires on correct code.
    """
    return set(code_of(module).split())


def imports_of(module: ModuleType) -> set[str]:
    """Return every module path *module* imports, absolute or relative."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(inspect.getsource(module))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add("." * (node.level or 0) + (node.module or ""))
    return found
