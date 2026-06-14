"""
security.py -- Input validation and sanitisation for ATS Resume Scorer.

Protects against:
  SSRF          : URL validation blocks private/internal IP ranges and
                  non-http(s) schemes before any outbound request is made.
  DoS (files)   : File size hard-capped; streaming download aborts early.
  File spoofing : Magic-byte check ensures uploaded file matches extension.
  XSS           : html.escape() wrapper for any user data going into HTML.
  API key abuse : Format check rejects obviously bogus Anthropic keys.
"""

from __future__ import annotations

import html
import ipaddress
import re
import socket
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Tuneable limits
# ---------------------------------------------------------------------------

MAX_RESUME_MB: float = 10          # hard cap for uploaded / downloaded resumes
MAX_JD_CHARS: int   = 50_000      # job description input cap
MAX_URL_LEN: int    = 2_048       # max URL length we will process
MAX_FILENAME_LEN: int = 255       # safe filename length
MAX_DOWNLOAD_BYTES: int = int(MAX_RESUME_MB * 1024 * 1024)

ALLOWED_SCHEMES = frozenset({"http", "https"})

# Magic bytes for file-type verification (extension → list of valid headers)
_MAGIC: dict[str, list[bytes]] = {
    "pdf":  [b"%PDF"],
    "docx": [b"PK\x03\x04"],        # ZIP-based: DOCX, XLSX, PPTX
    "doc":  [b"\xd0\xcf\x11\xe0"],  # OLE2 compound document (legacy .doc)
    "rtf":  [b"{\\rtf"],
}

# IPv4 networks that must never be fetched (SSRF prevention)
_PRIVATE_V4 = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),       # loopback
    ipaddress.ip_network("169.254.0.0/16"),    # link-local / cloud metadata
    ipaddress.ip_network("100.64.0.0/10"),     # shared address space
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("240.0.0.0/4"),       # reserved
    ipaddress.ip_network("198.51.100.0/24"),   # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),    # TEST-NET-3
]

_PRIVATE_V6 = [
    ipaddress.ip_network("::1/128"),            # loopback
    ipaddress.ip_network("fc00::/7"),           # ULA
    ipaddress.ip_network("fe80::/10"),          # link-local
    ipaddress.ip_network("::ffff:0:0/96"),      # IPv4-mapped
]


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class SecurityError(ValueError):
    """Raised when a request violates a security policy.
    Message is safe to display directly to the user.
    """


# ---------------------------------------------------------------------------
# HTML sanitisation
# ---------------------------------------------------------------------------

def sanitize_html(text: str, max_len: int = 500) -> str:
    """HTML-escape a user-supplied string for safe inline HTML insertion."""
    if not isinstance(text, str):
        text = str(text)
    return html.escape(text[:max_len], quote=True)


# ---------------------------------------------------------------------------
# URL / SSRF validation
# ---------------------------------------------------------------------------

def validate_url(url: str) -> str:
    """
    Validate a URL before making any outbound HTTP request.

    Checks (in order):
      1. Length guard
      2. Scheme must be http or https
      3. No embedded credentials (user:pass@host)
      4. Hostname present
      5. If raw IP — blocked if private/reserved
      6. DNS resolution — every resolved address blocked if private/reserved

    Returns the original URL string on success.
    Raises SecurityError with a user-safe message on failure.
    """
    url = (url or "").strip()
    if not url:
        raise SecurityError("URL is empty.")
    if len(url) > MAX_URL_LEN:
        raise SecurityError(
            f"URL exceeds the maximum allowed length ({MAX_URL_LEN} characters)."
        )

    try:
        parsed = urlparse(url)
    except Exception:
        raise SecurityError("The URL could not be parsed. Please check it and try again.")

    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        raise SecurityError(
            f"Only https:// and http:// URLs are supported. "
            f"Got scheme: {scheme!r}"
        )

    if parsed.username or parsed.password:
        raise SecurityError("URLs with embedded credentials are not allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise SecurityError("The URL has no hostname.")

    # --- Raw IP literal check (no DNS needed) ---
    try:
        addr = ipaddress.ip_address(hostname)
        _assert_public_ip(addr)
    except ValueError:
        pass  # Not a bare IP address — fall through to DNS

    # --- DNS resolution check ---
    try:
        # Timeout via default socket timeout (set to 5 s below)
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(5)
        try:
            infos = socket.getaddrinfo(hostname, None)
        finally:
            socket.setdefaulttimeout(old_timeout)
    except socket.timeout:
        raise SecurityError(f"DNS lookup timed out for host: {hostname!r}")
    except socket.gaierror:
        raise SecurityError(
            f"Could not resolve hostname {hostname!r}. "
            "Check the URL and your internet connection."
        )

    for info in infos:
        addr_str = info[4][0]
        try:
            addr = ipaddress.ip_address(addr_str)
            _assert_public_ip(addr)
        except SecurityError:
            raise SecurityError(
                "The URL resolves to a private or reserved IP address and "
                "cannot be fetched for security reasons."
            )

    return url


def _assert_public_ip(
    addr: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> None:
    """Raise SecurityError if the IP is not a routable public address."""
    if isinstance(addr, ipaddress.IPv4Address):
        if addr.is_loopback or addr.is_multicast or addr.is_reserved or addr.is_unspecified:
            raise SecurityError(f"Blocked IP: {addr}")
        for net in _PRIVATE_V4:
            if addr in net:
                raise SecurityError(f"Blocked private IP: {addr}")
    else:  # IPv6
        if addr.is_loopback or addr.is_multicast or addr.is_unspecified:
            raise SecurityError(f"Blocked IPv6: {addr}")
        for net in _PRIVATE_V6:
            if addr in net:
                raise SecurityError(f"Blocked private IPv6: {addr}")


def validate_dropbox_url(url: str) -> str:
    """Validate + SSRF-check a Dropbox URL (must be *.dropbox.com)."""
    url = validate_url(url)
    host = (urlparse(url).hostname or "").lower()
    if not (host == "dropbox.com" or host.endswith(".dropbox.com")):
        raise SecurityError(
            "The URL must be from dropbox.com. "
            f"Got host: {host!r}"
        )
    return url


def validate_gdrive_url(url: str) -> str:
    """Validate + SSRF-check a Google Drive URL (must be *.google.com)."""
    url = validate_url(url)
    host = (urlparse(url).hostname or "").lower()
    if not (host == "drive.google.com" or host.endswith(".google.com")):
        raise SecurityError(
            "The URL must be from drive.google.com. "
            f"Got host: {host!r}"
        )
    return url


# ---------------------------------------------------------------------------
# File validation
# ---------------------------------------------------------------------------

def validate_file_size(file_bytes: bytes, max_mb: float = MAX_RESUME_MB) -> None:
    """Raise SecurityError if the file exceeds the size limit."""
    max_bytes = int(max_mb * 1024 * 1024)
    size_mb = len(file_bytes) / (1024 * 1024)
    if len(file_bytes) > max_bytes:
        raise SecurityError(
            f"File is too large ({size_mb:.1f} MB). "
            f"Maximum allowed size is {max_mb:.0f} MB. "
            "Resumes should be well under 5 MB."
        )


def validate_file_magic(file_bytes: bytes, filename: str) -> None:
    """
    Verify that the file's leading bytes match its claimed extension.
    TXT, HTML, HTM are text-based with no fixed magic — they pass without check.
    Raises SecurityError if the bytes don't match.
    """
    if not filename or "." not in filename:
        return
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in _MAGIC:
        return  # txt / html / htm — no binary magic check needed

    magic_options = _MAGIC[ext]
    if not any(file_bytes[:len(m)] == m for m in magic_options):
        raise SecurityError(
            f"The file content doesn't match its .{ext} extension. "
            "It may be corrupt, misnamed, or disguised as a different format."
        )


def validate_filename(filename: str) -> str:
    """
    Strip path separators and shell-dangerous characters from a filename.
    Returns a safe string (never empty).
    """
    safe = re.sub(r"[/\\:*?\"<>|\x00-\x1f]", "_", filename or "resume")
    safe = safe.strip(". ")
    return (safe or "resume")[:MAX_FILENAME_LEN]


# ---------------------------------------------------------------------------
# Streaming download with size cap
# ---------------------------------------------------------------------------

def safe_download(url: str, *, timeout: int = 20) -> tuple[bytes, str]:
    """
    Download `url` with:
      - SSRF validation first
      - 20-second timeout
      - Hard cap at MAX_DOWNLOAD_BYTES (streams, aborts early)
      - Returns (content_bytes, guessed_filename)

    Raises SecurityError or RuntimeError on failure.
    """
    try:
        import requests as _req
    except ImportError:
        raise RuntimeError("requests is not installed. Run: pip install requests")

    # SSRF check before any connection
    validate_url(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        r = _req.get(
            url,
            headers=headers,
            timeout=timeout,
            stream=True,
            allow_redirects=True,
        )
    except _req.exceptions.Timeout:
        raise RuntimeError("Download timed out. Check your internet connection.")
    except _req.exceptions.ConnectionError:
        raise RuntimeError("Could not connect to the URL. Check it and try again.")
    except Exception as exc:
        raise RuntimeError(f"Download failed: {type(exc).__name__}")

    if r.status_code != 200:
        raise RuntimeError(
            f"Server returned HTTP {r.status_code}. "
            "The file may not be publicly accessible."
        )

    # Stream read with size cap
    chunks: list[bytes] = []
    total = 0
    for chunk in r.iter_content(chunk_size=65_536):
        total += len(chunk)
        if total > MAX_DOWNLOAD_BYTES:
            r.close()
            raise SecurityError(
                f"Downloaded file exceeds the {MAX_RESUME_MB:.0f} MB limit. "
                "Only resume-sized files are supported."
            )
        chunks.append(chunk)
    content = b"".join(chunks)

    # Guess filename from Content-Disposition header or URL path
    cd = r.headers.get("Content-Disposition", "")
    fn_match = re.search(r'filename[*]?=["\']?([^"\';\r\n]+)', cd)
    filename = fn_match.group(1).strip().strip('"\'') if fn_match else ""

    if not filename:
        path = url.split("?")[0].rstrip("/")
        filename = path.split("/")[-1] or "resume"

    filename = validate_filename(filename)

    if not any(
        filename.lower().endswith(ext)
        for ext in (".pdf", ".docx", ".doc", ".txt", ".rtf", ".html", ".htm")
    ):
        ct = r.headers.get("Content-Type", "")
        if "pdf" in ct:
            filename += ".pdf"
        elif "word" in ct or "docx" in ct:
            filename += ".docx"
        else:
            filename += ".pdf"

    return content, filename


# ---------------------------------------------------------------------------
# API key format validation
# ---------------------------------------------------------------------------

_API_KEY_RE = re.compile(r"^sk-ant-[a-zA-Z0-9\-_]{20,}$")


def validate_api_key_format(key: str) -> None:
    """
    Lightweight format check for Anthropic API keys.
    Raises SecurityError for obviously wrong formats.
    Does NOT make a network call — just validates the shape.
    """
    key = (key or "").strip()
    if not key:
        raise SecurityError("API key is empty. Enter your Anthropic API key.")
    if len(key) < 20:
        raise SecurityError(
            "That doesn't look like a valid API key (too short). "
            "Anthropic keys start with 'sk-ant-'."
        )
    if not key.startswith("sk-ant-"):
        raise SecurityError(
            "That doesn't look like an Anthropic API key. "
            "Keys start with 'sk-ant-'. Get yours at console.anthropic.com."
        )
    if not _API_KEY_RE.match(key):
        raise SecurityError(
            "API key contains invalid characters. "
            "Anthropic keys are alphanumeric (plus hyphens and underscores)."
        )


# ---------------------------------------------------------------------------
# Input length caps
# ---------------------------------------------------------------------------

def cap_jd_text(jd_text: str) -> str:
    """Truncate job description to MAX_JD_CHARS to prevent DoS."""
    return jd_text[:MAX_JD_CHARS] if len(jd_text) > MAX_JD_CHARS else jd_text
