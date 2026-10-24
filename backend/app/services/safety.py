"""Command safety policy. Fails closed: anything not explicitly allowed is blocked.

This runs BEFORE a command is sent to the Celesto sandbox. The Cloud `Computer`
in celesto 0.1.4 has no `callbacks=` option (only the local `Celesto` class does),
so SafeAgent enforces the veto itself in SafeSandbox.run().
"""
import re
import shlex
from dataclasses import dataclass

MAX_COMMAND_CHARS = 4000          # SDK hard limit is 10,000
MAX_TIMEOUT_S = 120               # SDK hard limit is 300
MAX_OUTPUT_CHARS = 20000

# First word of every command must be one of these (no shell pipelines to arbitrary tools).
ALLOWED_BINARIES = {
    "echo", "cat", "ls", "pwd", "head", "tail", "wc", "sort", "uniq", "cut",
    "mkdir", "python3", "python", "test", "true", "false", "sleep", "date",
    "uname", "whoami", "printf", "base64", "env_check",
}
# Substrings that are always blocked, even inside an allowed binary's arguments.
DENY_PATTERNS = [
    (r"\brm\s+(-[a-zA-Z]*[rf][a-zA-Z]*\s+)+(/|~|\*|\$HOME)", "destructive_rm"),
    (r"\bmkfs\b|\bdd\s+if=|\bshred\b|\bchmod\s+-R\s+0?777\s+/", "destructive_disk"),
    (r":\(\)\s*\{.*\};\s*:", "fork_bomb"),
    (r"\b(curl|wget|nc|ncat|ssh|scp|ftp|telnet)\b", "network_tool"),
    (r"\b(pip3?|npm|apt(-get)?|apk|yarn|gem|cargo)\s+(install|add)\b", "package_install"),
    (r"\$\{?[A-Z_]*(KEY|TOKEN|SECRET|PASSWORD)[A-Z_]*\}?", "secret_env_reference"),
    (r"\bprintenv\b|\benv\b\s*($|\|)|/proc/\d*/?environ|\.env\b|id_rsa|/etc/shadow", "secret_read"),
    (r"\bsudo\b|\bsu\s+-?\b", "privilege_escalation"),
    (r"/dev/tcp/|/dev/udp/", "network_redirect"),
    (r"\bsocket\b|\burllib\b|\brequests\b|\bhttp\.client\b|\bsubprocess\b|\bos\.system\b", "python_network_or_exec"),
]
SHELL_META = re.compile(r"(\|\||&&|;|\||`|\$\(|>>?|<)")


@dataclass
class Decision:
    allow: bool
    reason: str
    rule: str = ""


def validate_command(command: str, timeout: int = 30) -> Decision:
    """Return a Decision. Any internal error => block (fail closed)."""
    try:
        if not isinstance(command, str) or not command.strip():
            return Decision(False, "empty command", "empty")
        if len(command) > MAX_COMMAND_CHARS:
            return Decision(False, "command too long", "length")
        if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= MAX_TIMEOUT_S:
            return Decision(False, f"timeout must be 1-{MAX_TIMEOUT_S}s", "timeout")
        for pattern, rule in DENY_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return Decision(False, f"matches deny rule '{rule}'", rule)
        # Allow only simple, single commands, or commands joined by && / ; handled below.
        parts = [p for p in re.split(r"&&|;", command) if p.strip()]
        for part in parts:
            if re.search(r"\|\||`|\$\(|<|>>|\|", part):
                return Decision(False, "pipes/substitution/redirection not allowed", "shell_meta")
            tokens = shlex.split(part)
            if not tokens:
                return Decision(False, "empty segment", "empty")
            binary = tokens[0].split("/")[-1]
            if binary not in ALLOWED_BINARIES:
                return Decision(False, f"binary '{binary}' not in allowlist", "not_allowlisted")
        return Decision(True, "allowed by policy", "allow")
    except Exception as exc:  # fail closed
        return Decision(False, f"safety check failed: {type(exc).__name__}", "fail_closed")


# --- Untrusted-content handling -------------------------------------------------
INJECTION_MARKERS = [
    r"ignore (all |any )?(previous|prior|above) instructions",
    r"disregard (the )?(system|previous) (prompt|instructions)",
    r"you are now", r"new instructions:", r"reveal .*(api|secret|key|token)",
    r"(send|post|upload|exfiltrate).*(http|https)://", r"curl\s+https?://",
]


def scan_untrusted_text(text: str) -> list[str]:
    """Return injection markers found in file content. Content is DATA: it is never
    executed or obeyed, only scanned, truncated, and reported."""
    return [m for m in INJECTION_MARKERS if re.search(m, text, re.IGNORECASE)]


def truncate_output(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + f"\n[truncated {len(text) - MAX_OUTPUT_CHARS} chars]"


_SECRET_RE = re.compile(
    r"(?i)"
    r"(?:csk_[A-Za-z0-9_-]{8,})"
    r"|(?:sk-[A-Za-z0-9_-]{12,})"
    r"|(?:Bearer\s+[A-Za-z0-9._~+/=-]{12,})"
    r"|(?:\b(?:CELESTO_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|API_KEY|ACCESS_TOKEN|SECRET_KEY)\s*[:=]\s*[\"']?[^\s\"',;]+)"
)


def redact(text: str) -> str:
    return _SECRET_RE.sub("[REDACTED]", text)
