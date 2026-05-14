"""
Static scan of plugin .py sources for capability hints (not sandbox enforcement).
Improved scoring + more dangerous markers.
"""

from pathlib import Path

# ==================== DANGEROUS MARKERS ====================

_DANGEROUS_MARKERS = (
    # === High Risk (Code Execution) ===
    ("eval(", "dynamic_exec"),
    ("exec(", "dynamic_exec"),
    ("compile(", "dynamic_exec"),
    ("__import__(", "dynamic_import"),
    ("importlib.import_module", "dynamic_import"),
    
    # === Unsafe Deserialization ===
    ("pickle.loads", "unsafe_deserialize"),
    ("pickle.load", "unsafe_deserialize"),
    ("marshal.loads", "unsafe_deserialize"),
    ("yaml.load", "unsafe_deserialize"),           # especially without SafeLoader
    ("yaml.full_load", "unsafe_deserialize"),
    
    # === Native / Memory Unsafe ===
    ("ctypes.", "native_bridge"),
    ("cffi.", "native_bridge"),
    ("pywin32", "native_bridge"),
    
    # === Subprocess / Shell Execution ===
    ("subprocess.", "subprocess"),
    ("os.system(", "subprocess"),
    ("os.popen", "subprocess"),
    ("os.spawn", "subprocess"),
    ("commands.getoutput", "subprocess"),
    ("commands.getstatusoutput", "subprocess"),
    
    # === Network ===
    ("socket.", "network"),
    ("urllib.request", "network"),
    ("urllib3", "network"),
    ("requests.", "network"),
    ("httpx.", "network"),
    ("aiohttp.", "network"),
    ("ftplib.", "network"),
    ("smtplib.", "network"),
    ("http.client", "network"),
    
    # === Filesystem Dangerous Operations ===
    ("shutil.rmtree", "filesystem_write"),
    ("os.remove", "filesystem_write"),
    ("os.unlink", "filesystem_write"),
    ("Path.unlink", "filesystem_write"),
    ("os.rmdir", "filesystem_write"),
    ("shutil.move", "filesystem_write"),
    ("os.rename", "filesystem_write"),          # can be used maliciously
    ("open(", "filesystem_write"),              # broad, but useful signal
    
    # === Privilege / System ===
    ("os.exec", "system_execution"),
    ("runas", "privilege_escalation"),
    ("admin", "privilege_escalation"),          # heuristic
    
    # === Debugging / Injection ===
    ("pdb.", "debug_tools"),
    ("code.interact", "debug_tools"),
    ("breakpoint(", "debug_tools"),
)

# Tags that make a plugin "dangerous" by default
_DANGEROUS_ONLY = frozenset({
    "dynamic_exec",
    "unsafe_deserialize",
    "native_bridge",
    "subprocess",
    "system_execution",
    "privilege_escalation",
})


def score_dangerous_tags_by_source(source: str) -> int:
    """
    Properly calculate danger score based on what was ACTUALLY found.
    """
    if not source:
        return 0

    lower = source.lower()
    score = 0
    found_tags = set()

    for needle, tag in _DANGEROUS_MARKERS:
        if needle.lower() in lower:
            if tag not in found_tags:
                found_tags.add(tag)

                if tag in _DANGEROUS_ONLY:
                    score += 60          # High risk
                elif tag in ("network", "filesystem_write"):
                    score += 25
                else:
                    score += 15

    # Multi-risk bonus
    if len(found_tags) >= 3:
        score += 40
    elif len(found_tags) >= 2:
        score += 20

    # Very broad heuristic: if it imports many things + has exec/subprocess
    if "dynamic_exec" in found_tags or "subprocess" in found_tags:
        score += 20

    return score


def analyze_python_plugin_source(path: Path) -> dict:
    """
    Analyze a plugin file and return security report.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {
            "path": str(path),
            "permissions": [],
            "signals": [],
            "dangerous": False,
            "score": 0,
            "error": f"unreadable: {e}",
        }

    lower = text.lower()
    permissions = []
    signals = []

    for needle, tag in _DANGEROUS_MARKERS:
        if needle.lower() in lower:
            if tag not in permissions:
                permissions.append(tag)
            signals.append(f"{tag}:{needle.strip()}")

    dangerous = any(p in _DANGEROUS_ONLY for p in permissions)
    score = score_dangerous_tags_by_source(text)

    return {
        "path": str(path),
        "permissions": permissions,
        "signals": signals[:30],           # limit output size
        "dangerous": dangerous,
        "score": score,
    }