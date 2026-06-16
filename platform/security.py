import ast

BANNED_IMPORTS = frozenset({
    "socket", "subprocess", "ctypes", "multiprocessing",
    "importlib", "urllib", "http", "ftplib", "smtplib",
    "os", "shutil", "pathlib", "pty", "signal",
    "resource", "mmap", "fcntl", "tempfile", "glob",
})

BANNED_CALLS = frozenset({"exec", "eval", "__import__", "compile", "open"})


def check_player_source(source: str) -> tuple[bool, str]:
    """
    Parse source with ast and check for forbidden patterns.
    Returns (True, "") if safe; (False, reason) if rejected.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BANNED_IMPORTS:
                    return False, f"forbidden import '{alias.name}'"
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in BANNED_IMPORTS:
                return False, f"forbidden import 'from {node.module}'"
        elif isinstance(node, ast.Call):
            fname = ""
            if isinstance(node.func, ast.Name):
                fname = node.func.id
            elif isinstance(node.func, ast.Attribute):
                fname = node.func.attr
            if fname in BANNED_CALLS:
                return False, f"forbidden call '{fname}()'"

    return True, ""
