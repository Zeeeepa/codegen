#!/usr/bin/env python3
"""
Eversale Local Proxy — Launcher Module

Manages the proxy server lifecycle:
  - Spawns proxy_server.py as a background subprocess
  - Checks if proxy is already running (idempotent)
  - Waits for health check before returning
  - PID file management for cleanup
  - Graceful shutdown

Usage:
    from proxy_launcher import ensure_proxy, stop_proxy

    # Call at eversale startup — idempotent
    ensure_proxy()

    # Call at shutdown
    stop_proxy()
"""

import os
import sys
import time
import signal
import socket
import subprocess
import json
import logging
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger("eversale.proxy.launcher")

# Defaults
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
HEALTH_TIMEOUT = 15  # seconds to wait for proxy to become healthy
HEALTH_POLL_INTERVAL = 0.3  # seconds between health checks


def _get_eversale_home() -> Path:
    return Path(os.environ.get("EVERSALE_HOME", Path.home() / ".eversale"))


def _get_pid_file() -> Path:
    return _get_eversale_home() / "proxy.pid"


def _get_log_file() -> Path:
    log_dir = _get_eversale_home() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "proxy.log"


def _get_port() -> int:
    return int(os.environ.get("EVERSALE_PROXY_PORT", str(DEFAULT_PORT)))


def _get_host() -> str:
    return os.environ.get("EVERSALE_PROXY_HOST", DEFAULT_HOST)


def _is_port_open(host: str, port: int) -> bool:
    """Check if a TCP port is accepting connections."""
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


def _is_proxy_healthy(host: str, port: int) -> bool:
    """Check if the proxy server is responding to health checks."""
    try:
        url = f"http://{host}:{port}/health"
        req = Request(url, method="GET")
        with urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                return data.get("status") == "ok"
    except (URLError, json.JSONDecodeError, Exception):
        pass
    return False


def _read_pid() -> Optional[int]:
    """Read PID from pid file, return None if invalid."""
    pid_file = _get_pid_file()
    if not pid_file.exists():
        return None
    try:
        pid = int(pid_file.read_text().strip())
        # Check if process is still running
        os.kill(pid, 0)  # Sends signal 0 — doesn't kill, just checks existence
        return pid
    except (ValueError, ProcessLookupError, PermissionError, OSError):
        # PID file exists but process is dead — clean up
        try:
            pid_file.unlink()
        except OSError:
            pass
        return None


def _write_pid(pid: int) -> None:
    """Write PID to pid file."""
    pid_file = _get_pid_file()
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(pid))


def _remove_pid() -> None:
    """Remove PID file."""
    try:
        _get_pid_file().unlink(missing_ok=True)
    except OSError:
        pass


def ensure_proxy(
    host: Optional[str] = None,
    port: Optional[int] = None,
    timeout: float = HEALTH_TIMEOUT,
) -> bool:
    """
    Ensure the proxy server is running. Idempotent.

    1. Check if proxy is already running and healthy → return True
    2. Check if port is in use by something else → raise error
    3. Spawn proxy_server.py as background subprocess
    4. Wait for health check → return True/False

    Returns:
        True if proxy is running and healthy.
    """
    host = host or _get_host()
    port = port or _get_port()

    # 1. Check if already running
    existing_pid = _read_pid()
    if existing_pid and _is_proxy_healthy(host, port):
        logger.info(f"Proxy already running (PID {existing_pid}) on {host}:{port}")
        return True

    # 2. Check if port is occupied by something else
    if _is_port_open(host, port) and not _is_proxy_healthy(host, port):
        logger.warning(
            f"Port {port} is in use by another process. "
            f"Set EVERSALE_PROXY_PORT to use a different port."
        )
        # Try to use the existing server anyway — it might be compatible
        return False

    # 3. Spawn the proxy server
    logger.info(f"Starting proxy server on {host}:{port}...")

    proxy_script = Path(__file__).parent / "proxy_server.py"
    if not proxy_script.exists():
        logger.error(f"Proxy server script not found: {proxy_script}")
        return False

    log_file = _get_log_file()
    log_handle = open(log_file, "a")

    # Determine Python executable
    python_exe = sys.executable or "python3"

    env = os.environ.copy()
    env["EVERSALE_PROXY_HOST"] = host
    env["EVERSALE_PROXY_PORT"] = str(port)

    try:
        proc = subprocess.Popen(
            [python_exe, str(proxy_script), "--host", host, "--port", str(port)],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env=env,
            # Detach from parent process
            start_new_session=True,
        )
    except Exception as e:
        logger.error(f"Failed to start proxy: {e}")
        log_handle.close()
        return False

    _write_pid(proc.pid)
    logger.info(f"Proxy spawned with PID {proc.pid}, waiting for health check...")

    # 4. Wait for health check
    start = time.time()
    while time.time() - start < timeout:
        # Check if process died
        if proc.poll() is not None:
            logger.error(
                f"Proxy process exited with code {proc.returncode}. "
                f"Check logs: {log_file}"
            )
            _remove_pid()
            return False

        if _is_proxy_healthy(host, port):
            logger.info(
                f"✅ Proxy is healthy on {host}:{port} "
                f"(startup: {int((time.time() - start) * 1000)}ms)"
            )
            return True

        time.sleep(HEALTH_POLL_INTERVAL)

    logger.warning(
        f"Proxy did not become healthy within {timeout}s. "
        f"Check logs: {log_file}"
    )
    return False


def stop_proxy() -> bool:
    """
    Stop the proxy server if running.

    Returns:
        True if stopped successfully or was not running.
    """
    pid = _read_pid()
    if pid is None:
        logger.info("No proxy running (no PID file)")
        return True

    logger.info(f"Stopping proxy (PID {pid})...")
    try:
        if sys.platform == "win32":
            # Windows: use taskkill
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            os.kill(pid, signal.SIGTERM)

            # Wait for graceful shutdown
            for _ in range(30):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.1)
                except ProcessLookupError:
                    break
            else:
                # Force kill if still alive
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

        _remove_pid()
        logger.info("Proxy stopped")
        return True

    except ProcessLookupError:
        _remove_pid()
        logger.info("Proxy was already stopped")
        return True
    except Exception as e:
        logger.error(f"Failed to stop proxy: {e}")
        return False


def get_proxy_url() -> str:
    """Get the proxy server URL."""
    host = _get_host()
    port = _get_port()
    return f"http://{host}:{port}"


def get_proxy_status() -> dict:
    """Get proxy server status."""
    host = _get_host()
    port = _get_port()
    pid = _read_pid()

    status = {
        "running": False,
        "healthy": False,
        "pid": pid,
        "url": f"http://{host}:{port}",
        "log_file": str(_get_log_file()),
    }

    if pid:
        status["running"] = True
        status["healthy"] = _is_proxy_healthy(host, port)

        if status["healthy"]:
            try:
                url = f"http://{host}:{port}/health"
                with urlopen(Request(url), timeout=3) as resp:
                    data = json.loads(resp.read().decode())
                    status.update(data)
            except Exception:
                pass

    return status


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Eversale Proxy Launcher")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("start", help="Start the proxy server")
    sub.add_parser("stop", help="Stop the proxy server")
    sub.add_parser("status", help="Check proxy status")
    sub.add_parser("restart", help="Restart the proxy server")
    args = parser.parse_args()

    if args.command == "start" or args.command is None:
        ok = ensure_proxy()
        sys.exit(0 if ok else 1)
    elif args.command == "stop":
        ok = stop_proxy()
        sys.exit(0 if ok else 1)
    elif args.command == "status":
        status = get_proxy_status()
        print(json.dumps(status, indent=2))
    elif args.command == "restart":
        stop_proxy()
        time.sleep(0.5)
        ok = ensure_proxy()
        sys.exit(0 if ok else 1)

