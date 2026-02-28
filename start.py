"""Windows-compatible launcher for co-vibe.
Patches known Windows issues at import time, then runs co-vibe.
"""
import signal
import sys
import os

# Patch 1: Add missing SIGHUP for Windows
if not hasattr(signal, 'SIGHUP'):
    signal.SIGHUP = None
    _original_signal = signal.signal
    def _patched_signal(signalnum, handler):
        if signalnum is None:
            return signal.SIG_DFL
        return _original_signal(signalnum, handler)
    signal.signal = _patched_signal

# Patch 2: Fix User-Agent for Cloudflare (Groq API)
import urllib.request
_original_urlopen = urllib.request.urlopen
def _patched_urlopen(req, *args, **kwargs):
    if isinstance(req, urllib.request.Request):
        if not req.has_header('User-agent') and not req.has_header('User-Agent'):
            req.add_header('User-Agent', 'co-vibe/1.4.0 (+https://github.com/ochyai/co-vibe)')
    return _original_urlopen(req, *args, **kwargs)
urllib.request.urlopen = _patched_urlopen

# Patch 3: Fix encoding for Windows Japanese console
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

# Run co-vibe
sys.argv[0] = os.path.join(os.path.dirname(__file__), 'co-vibe.py')
exec(open(sys.argv[0], encoding='utf-8').read())
