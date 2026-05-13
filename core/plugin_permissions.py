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
