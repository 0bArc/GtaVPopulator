"""
Static scan of plugin .py sources for capability hints (not sandbox enforcement).
"""

from pathlib import Path


_DANGEROUS_MARKERS = (
    ("eval(", "dynamic_exec"),
    ("exec(", "dynamic_exec"),
    ("compile(", "dynamic_exec"),
    ("__import__(", "dynamic_import"),
    ("pickle.loads", "unsafe_deserialize"),
    ("marshal.loads", "unsafe_deserialize"),
    ("ctypes.", "native_bridge"),
    ("os.system", "subprocess"),
    ("os.popen", "subprocess"),
    ("subprocess.", "subprocess"),
    ("socket.", "network"),
    ("urllib.request", "network"),
    ("requests.", "network"),
    ("httpx.", "network"),
    ("aiohttp.", "network"),
    ("ftplib.", "network"),
    ("smtplib.", "network"),
    ("shutil.rmtree", "filesystem_write"),
    ("os.remove", "filesystem_write"),
    ("os.unlink", "filesystem_write"),
    ("Path.unlink", "filesystem_write"),
)

_DANGEROUS_ONLY = frozenset(
    {
        "dynamic_exec",
        "unsafe_deserialize",
        "native_bridge",
        "subprocess",
    }
)


def score_dangerous_tags_by_source(source: str) -> int:
    """
    Score dangerous tags by source text.
    """
    base_score = 0
    
    # if dynamic_exec or subprocess, add 10 points, if network add 5
    for needle, tag in _DANGEROUS_MARKERS:

        if tag in _DANGEROUS_ONLY:
            base_score += 10
        elif tag == "network":
            base_score += 5
        elif tag == "filesystem_write":
            base_score += 5
        elif tag == "native_bridge":
            base_score += 5
        elif tag == "unsafe_deserialize":
            base_score += 5
        elif tag == "dynamic_exec":
            base_score += 5
        elif tag == "subprocess":
            base_score += 5
        elif tag == "native_bridge":
            base_score += 5
        elif tag == "unsafe_deserialize":
            base_score += 5
        elif tag == "dynamic_import":
            base_score += 5
        elif tag == "pickle.loads":
            base_score += 5
        elif tag == "marshal.loads":
            base_score += 5
        elif tag == "ctypes.":
            base_score += 5
        elif tag == "os.system":
            base_score += 5
        elif tag == "os.popen":
            base_score += 5
        elif tag == "subprocess.":
            base_score += 5
        elif tag == "socket.":
            base_score += 5
        elif tag == "urllib.request":
            base_score += 5
        elif tag == "requests.":
            base_score += 5
        elif tag == "httpx.":
            base_score += 5
        elif tag == "aiohttp.":
            base_score += 5
        elif tag == "ftplib.":
            base_score += 5
        elif tag == "smtplib.":
            base_score += 5
        elif tag == "shutil.rmtree":
            base_score += 5
        elif tag == "os.remove":
            base_score += 5
        elif tag == "os.unlink":
            base_score += 5
        elif tag == "Path.unlink":
            base_score += 5
    
    return base_score


def analyze_python_plugin_source(path: Path) -> dict:
    """
    Return permission-like tags + dangerous flag from source text heuristics.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {
            "path": str(path),
            "permissions": [],
            "signals": [],
            "dangerous": False,
            "error": "unreadable",
        }

    lower = text.lower()
    permissions = []
    signals = []

    for needle, tag in _DANGEROUS_MARKERS:
        if needle.lower() in lower:
            if tag not in permissions:
                permissions.append(tag)
            signals.append(f"{tag}:{needle}")

    dangerous = any(p in _DANGEROUS_ONLY for p in permissions)

    return {
        "path": str(path),
        "permissions": permissions,
        "signals": signals[:24],
        "dangerous": dangerous,
    }
