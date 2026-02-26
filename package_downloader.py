#!/usr/bin/env python3
"""
Package Downloader - Multi-ecosystem package downloader with version management.

Downloads packages from NPM, PyPI, and GitHub to a local directory.
Automatically detects newer versions, archives old ones, and reports actions.

Usage:
    python package_downloader.py                          # Uses packages.txt in same dir
    python package_downloader.py -f my_packages.txt       # Custom input file
    python package_downloader.py -o D:\\MyDownloads        # Custom output dir
    python package_downloader.py --dry-run                # Preview without downloading
    python package_downloader.py --github-token ghp_xxx   # Use GitHub token for higher rate limits
"""

import os
import re
import sys
import json
import shutil
import hashlib
import logging
import argparse
import datetime
import glob
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library is required. Install with: pip install requests")
    sys.exit(1)

try:
    from packaging.version import Version, InvalidVersion
except ImportError:
    print("WARNING: 'packaging' library not found. Install with: pip install packaging")
    print("         Falling back to basic string version comparison.\n")
    Version = None
    InvalidVersion = None


# ============================================================
# CONFIGURATION
# ============================================================
DEFAULT_DOWNLOAD_DIR = r"C:\Users\L\Desktop\DOw"
DEFAULT_INPUT_FILE = "packages.txt"
ARCHIVE_SUBDIR = "_Archive"
MAX_WORKERS = 8
REQUEST_TIMEOUT = 60
CHUNK_SIZE = 8192
USER_AGENT = "PackageDownloader/2.0 (github.com/Zeeeepa)"

# ============================================================
# ENUMS & DATA CLASSES
# ============================================================

class SourceType(Enum):
    NPM = "npm"
    PYPI = "pypi"
    GITHUB = "github"
    UNKNOWN = "unknown"


class ActionType(Enum):
    UPDATED = "Updated"
    STAYED_SAME = "StayedSame"
    NEW_DOWNLOAD = "NewDownload"
    FAILED = "Failed"
    SKIPPED = "Skipped"
    NOT_FOUND = "NotFound"


@dataclass
class PackageEntry:
    raw_input: str
    name: str = ""
    source: SourceType = SourceType.UNKNOWN
    github_owner: str = ""
    github_repo: str = ""
    npm_scope: str = ""
    detected_from: str = ""


@dataclass
class PackageResult:
    entry: PackageEntry
    action: ActionType = ActionType.SKIPPED
    remote_version: str = ""
    local_version: str = ""
    downloaded_file: str = ""
    archived_files: list = field(default_factory=list)
    error_msg: str = ""


# ============================================================
# LOGGING SETUP
# ============================================================

class ColorFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[41m',
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logger = logging.getLogger('pkgdl')
    # Prevent duplicate handlers on re-init
    if logger.handlers:
        logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter('%(levelname)s %(message)s'))
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


log = setup_logging()


# ============================================================
# VERSION COMPARISON
# ============================================================

def parse_version(v_str: str) -> Optional[object]:
    """Parse version string, returns comparable object or None."""
    if not v_str:
        return None
    v_str = v_str.lstrip("v").strip()
    if Version is not None:
        try:
            return Version(v_str)
        except (InvalidVersion, Exception):
            pass
    # Fallback: tuple-based comparison
    parts = re.split(r'[.\-_]', v_str)
    numeric = []
    for p in parts:
        try:
            numeric.append(int(p))
        except ValueError:
            numeric.append(0)
    return tuple(numeric) if numeric else None


def is_newer(remote_v: str, local_v: str) -> bool:
    """Check if remote version is newer than local version."""
    rv = parse_version(remote_v)
    lv = parse_version(local_v)
    if rv is None or lv is None:
        return remote_v != local_v  # Different = assume newer
    try:
        return rv > lv
    except TypeError:
        return str(remote_v) != str(local_v)


# ============================================================
# INPUT PARSER
# ============================================================

def parse_input_file(filepath: str) -> list:
    """Parse the packages.txt file and return list of PackageEntry objects."""
    entries = []
    seen = set()

    if not os.path.exists(filepath):
        log.error(f"Input file not found: {filepath}")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, raw_line in enumerate(f, 1):
            line = raw_line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            entry = parse_single_entry(line)
            if entry is None:
                continue

            # Deduplicate by (source, name)
            key = (entry.source.value, entry.name.lower())
            if key in seen:
                log.debug(f"Skipping duplicate: {entry.name} ({entry.source.value})")
                continue
            seen.add(key)
            entries.append(entry)

    log.info(f"Parsed {len(entries)} unique packages from {filepath}")
    return entries


def parse_single_entry(line: str) -> Optional[PackageEntry]:
    """Parse a single line into a PackageEntry."""
    entry = PackageEntry(raw_input=line)

    # --- NPM URL ---
    npm_match = re.match(
        r'https?://(?:www\.)?npmjs\.com/package/(@?[^/#?\s]+(?:/[^/#?\s]+)?)',
        line
    )
    if npm_match:
        pkg_name = npm_match.group(1)
        entry.name = pkg_name
        entry.source = SourceType.NPM
        entry.detected_from = "npm_url"
        if pkg_name.startswith('@'):
            parts = pkg_name.split('/')
            entry.npm_scope = parts[0] if len(parts) > 1 else ""
        return entry

    # --- PyPI URL ---
    pypi_match = re.match(
        r'https?://pypi\.org/project/([^/#?\s]+)',
        line
    )
    if pypi_match:
        pkg_name = pypi_match.group(1).rstrip('/')
        entry.name = pkg_name
        entry.source = SourceType.PYPI
        entry.detected_from = "pypi_url"
        return entry

    # --- GitHub URL ---
    gh_match = re.match(
        r'https?://github\.com/([^/\s]+)/([^/\s#?]+)',
        line
    )
    if gh_match:
        owner = gh_match.group(1)
        repo = gh_match.group(2).rstrip('/')
        entry.name = f"{owner}/{repo}"
        entry.github_owner = owner
        entry.github_repo = repo
        entry.source = SourceType.GITHUB
        entry.detected_from = "github_url"
        return entry

    # --- Bare package name (no URL) ---
    # Clean up trailing slashes, whitespace
    name = line.strip().rstrip('/')
    if not name or len(name) > 200:
        return None

    # Skip lines that look like section headers or archive references
    if name.startswith('[') or name.endswith('.tar.gz') or name.endswith('.zip') or name.endswith('.whl'):
        return None

    # If it contains a slash and looks like github owner/repo
    if '/' in name and not name.startswith('@'):
        parts = name.split('/')
        if len(parts) == 2 and all(p.strip() for p in parts):
            entry.name = name
            entry.github_owner = parts[0].strip()
            entry.github_repo = parts[1].strip()
            entry.source = SourceType.GITHUB
            entry.detected_from = "bare_github"
            return entry

    # Otherwise treat as a bare package name -> try PyPI first, then NPM
    entry.name = name
    entry.source = SourceType.UNKNOWN  # Will be resolved at download time
    entry.detected_from = "bare_name"
    return entry


# ============================================================
# REGISTRY API CLIENTS
# ============================================================

class RegistrySession:
    """Shared HTTP session with common settings."""

    def __init__(self, github_token: str = ""):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.github_token = github_token
        if github_token:
            self.session.headers.update({"Authorization": f"token {github_token}"})

    def get(self, url, **kwargs):
        kwargs.setdefault('timeout', REQUEST_TIMEOUT)
        return self.session.get(url, **kwargs)


def fetch_pypi_info(session: RegistrySession, pkg_name: str) -> Optional[dict]:
    """Fetch package info from PyPI JSON API. Returns dict with version, download_url, filename."""
    url = f"https://pypi.org/pypi/{pkg_name}/json"
    try:
        resp = session.get(url)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        version = data['info']['version']

        # Find best download: prefer sdist (.tar.gz), fallback to wheel
        urls = data.get('urls', [])
        sdist = [u for u in urls if u.get('packagetype') == 'sdist']
        wheel = [u for u in urls if u.get('packagetype') == 'bdist_wheel']
        chosen = (sdist or wheel or urls)

        if not chosen:
            # Try to get from releases
            releases = data.get('releases', {})
            if version in releases and releases[version]:
                chosen = releases[version]
                sdist = [u for u in chosen if u.get('packagetype') == 'sdist']
                wheel = [u for u in chosen if u.get('packagetype') == 'bdist_wheel']
                chosen = sdist or wheel or chosen

        if not chosen:
            return {'version': version, 'download_url': None, 'filename': None}

        pick = chosen[0]
        return {
            'version': version,
            'download_url': pick['url'],
            'filename': pick['filename'],
        }
    except Exception as e:
        log.debug(f"PyPI fetch error for {pkg_name}: {e}")
        return None


def fetch_npm_info(session: RegistrySession, pkg_name: str) -> Optional[dict]:
    """Fetch package info from NPM registry. Returns dict with version, download_url, filename."""
    # NPM registry URL - scoped packages need encoding
    encoded = pkg_name.replace('/', '%2f')
    url = f"https://registry.npmjs.org/{encoded}"
    try:
        resp = session.get(url)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        dist_tags = data.get('dist-tags', {})
        version = dist_tags.get('latest', '')
        if not version:
            return None

        versions_data = data.get('versions', {})
        version_info = versions_data.get(version, {})
        dist = version_info.get('dist', {})
        tarball_url = dist.get('tarball', '')

        if not tarball_url:
            return None

        # Generate clean filename
        safe_name = pkg_name.replace('@', '').replace('/', '-')
        filename = f"{safe_name}-{version}.tgz"

        return {
            'version': version,
            'download_url': tarball_url,
            'filename': filename,
        }
    except Exception as e:
        log.debug(f"NPM fetch error for {pkg_name}: {e}")
        return None


def fetch_github_info(session: RegistrySession, owner: str, repo: str) -> Optional[dict]:
    """Fetch latest release or default branch archive from GitHub."""
    # Try releases first
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        resp = session.get(url)
        if resp.status_code == 200:
            data = resp.json()
            tag = data.get('tag_name', '')
            version = tag.lstrip('v') if tag else ''

            # Prefer source tarball, then zipball, then assets
            tarball = data.get('tarball_url', '')
            zipball = data.get('zipball_url', '')

            # Check for .tar.gz or .zip assets
            assets = data.get('assets', [])
            source_asset = None
            for a in assets:
                name = a.get('name', '')
                if name.endswith('.tar.gz') or name.endswith('.zip'):
                    source_asset = a
                    break

            if source_asset:
                dl_url = source_asset['browser_download_url']
                filename = source_asset['name']
            elif tarball:
                dl_url = tarball
                filename = f"{owner}-{repo}-{version}.tar.gz"
            elif zipball:
                dl_url = zipball
                filename = f"{owner}-{repo}-{version}.zip"
            else:
                dl_url = None
                filename = None

            if dl_url:
                return {'version': version, 'download_url': dl_url, 'filename': filename}
    except Exception as e:
        log.debug(f"GitHub release fetch error for {owner}/{repo}: {e}")

    # Fallback: download default branch archive
    try:
        repo_url = f"https://api.github.com/repos/{owner}/{repo}"
        resp = session.get(repo_url)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        repo_data = resp.json()
        default_branch = repo_data.get('default_branch', 'main')
        pushed_at = repo_data.get('pushed_at', '')

        # Use date as version proxy
        if pushed_at:
            version = pushed_at[:10].replace('-', '')
        else:
            version = "latest"

        dl_url = f"https://api.github.com/repos/{owner}/{repo}/tarball/{default_branch}"
        filename = f"{owner}-{repo}-{version}.tar.gz"

        return {'version': version, 'download_url': dl_url, 'filename': filename}
    except Exception as e:
        log.debug(f"GitHub repo fetch error for {owner}/{repo}: {e}")
        return None


# ============================================================
# LOCAL FILE SCANNER
# ============================================================

def scan_local_files(download_dir: str, pkg_name: str, source: SourceType) -> list:
    """Find existing downloaded files for a package. Returns list of (filepath, version)."""
    results = []
    safe_name = sanitize_name(pkg_name)

    # Build glob patterns to match various naming schemes
    patterns = [
        f"{safe_name}-*.tar.gz",
        f"{safe_name}-*.tgz",
        f"{safe_name}-*.zip",
        f"{safe_name}-*.whl",
        f"{safe_name}_*.tar.gz",
        f"{safe_name}_*.zip",
    ]

    # For GitHub packages like "owner-repo-*"
    if source == SourceType.GITHUB and '/' in pkg_name:
        owner, repo = pkg_name.split('/', 1)
        gh_patterns = [
            f"{owner}-{repo}-*.tar.gz",
            f"{owner}-{repo}-*.zip",
            f"{repo}-*.tar.gz",
            f"{repo}-*.zip",
        ]
        patterns.extend(gh_patterns)

    for pattern in patterns:
        full_pattern = os.path.join(download_dir, pattern)
        for fpath in glob.glob(full_pattern):
            if os.path.isfile(fpath):
                version = extract_version_from_filename(fpath, safe_name, source, pkg_name)
                results.append((fpath, version))

    # Deduplicate by filepath
    seen_paths = set()
    unique = []
    for fpath, ver in results:
        if fpath not in seen_paths:
            seen_paths.add(fpath)
            unique.append((fpath, ver))

    return unique


def sanitize_name(name: str) -> str:
    """Convert package name to filesystem-safe form."""
    safe = name.replace('@', '').replace('/', '-').replace('\\', '-')
    safe = re.sub(r'[<>:"|?*]', '_', safe)
    return safe


def extract_version_from_filename(filepath: str, safe_name: str, source: SourceType, pkg_name: str = "") -> str:
    """Extract version string from a downloaded filename."""
    basename = os.path.basename(filepath)

    # Remove common extensions
    for ext in ['.tar.gz', '.tgz', '.zip', '.whl']:
        if basename.endswith(ext):
            basename = basename[:-len(ext)]
            break

    # Try to extract version after the package name
    prefixes = [safe_name]
    if source == SourceType.GITHUB and '/' in pkg_name:
        owner, repo = pkg_name.split('/', 1)
        prefixes.extend([f"{owner}-{repo}", repo])

    for prefix in prefixes:
        if basename.lower().startswith(prefix.lower()):
            remainder = basename[len(prefix):]
            remainder = remainder.lstrip('-_')
            if remainder:
                return remainder

    # Fallback: look for version-like pattern anywhere
    ver_match = re.search(r'(\d+[\.\d]*\w*)', basename)
    if ver_match:
        return ver_match.group(1)

    return ""


# ============================================================
# DOWNLOAD ENGINE
# ============================================================

def download_file(session: RegistrySession, url: str, dest_path: str) -> bool:
    """Download a file with progress indication. Returns True on success."""
    try:
        resp = session.get(url, stream=True, timeout=REQUEST_TIMEOUT * 3)
        resp.raise_for_status()

        total = int(resp.headers.get('content-length', 0))
        downloaded = 0

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        with open(dest_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

        # Verify file was actually written
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            size_mb = os.path.getsize(dest_path) / (1024 * 1024)
            log.debug(f"  Downloaded {size_mb:.1f} MB -> {os.path.basename(dest_path)}")
            return True
        else:
            log.warning(f"  Downloaded file is empty: {dest_path}")
            return False

    except Exception as e:
        log.error(f"  Download failed: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False


def archive_files(files: list, download_dir: str) -> list:
    """Move files to _Archive subdirectory. Returns list of archived paths."""
    archive_dir = os.path.join(download_dir, ARCHIVE_SUBDIR)
    os.makedirs(archive_dir, exist_ok=True)
    archived = []

    for fpath in files:
        if not os.path.exists(fpath):
            continue
        basename = os.path.basename(fpath)
        dest = os.path.join(archive_dir, basename)

        # If archive already has same file, add timestamp
        if os.path.exists(dest):
            name, ext = os.path.splitext(basename)
            # Handle .tar.gz double extension
            if basename.endswith('.tar.gz'):
                name = basename[:-7]
                ext = '.tar.gz'
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(archive_dir, f"{name}_{ts}{ext}")

        try:
            shutil.move(fpath, dest)
            archived.append(dest)
            log.debug(f"  Archived: {basename} -> _Archive/")
        except Exception as e:
            log.warning(f"  Failed to archive {basename}: {e}")

    return archived


# ============================================================
# MAIN PROCESSING LOGIC
# ============================================================

def process_package(session: RegistrySession, entry: PackageEntry, download_dir: str, dry_run: bool = False) -> PackageResult:
    """Process a single package: check version, archive old, download new."""
    result = PackageResult(entry=entry)

    try:
        # 1. Resolve source and fetch remote info
        info = resolve_and_fetch(session, entry)

        if info is None:
            result.action = ActionType.NOT_FOUND
            result.error_msg = f"Not found in any registry"
            log.warning(f"  [{entry.name}] Not found in any registry")
            return result

        result.remote_version = info.get('version', '')
        dl_url = info.get('download_url', '')
        filename = info.get('filename', '')

        if not dl_url:
            result.action = ActionType.FAILED
            result.error_msg = "No download URL available"
            log.warning(f"  [{entry.name}] No download URL available (version: {result.remote_version})")
            return result

        # 2. Scan for existing local files
        local_files = scan_local_files(download_dir, entry.name, entry.source)

        if local_files:
            # Find the newest local version
            best_local = max(local_files, key=lambda x: parse_version(x[1]) or "")
            result.local_version = best_local[1]

            # 3. Compare versions
            if result.remote_version and result.local_version:
                if not is_newer(result.remote_version, result.local_version):
                    result.action = ActionType.STAYED_SAME
                    log.info(f"  [{entry.name}] Up to date (v{result.local_version})")
                    return result

            # 4. Archive old files
            old_paths = [fp for fp, _ in local_files]
            if not dry_run:
                result.archived_files = archive_files(old_paths, download_dir)
            else:
                result.archived_files = old_paths
            action = ActionType.UPDATED
        else:
            action = ActionType.NEW_DOWNLOAD

        # 5. Download
        dest_path = os.path.join(download_dir, filename)

        if dry_run:
            result.action = action
            result.downloaded_file = dest_path
            log.info(f"  [{entry.name}] DRY RUN: Would {action.value} -> {filename}")
            return result

        success = download_file(session, dl_url, dest_path)
        if success:
            result.action = action
            result.downloaded_file = dest_path
            log.info(f"  [{entry.name}] {action.value}: v{result.remote_version} -> {filename}")
        else:
            result.action = ActionType.FAILED
            result.error_msg = "Download failed"
            log.error(f"  [{entry.name}] Download failed")

    except Exception as e:
        result.action = ActionType.FAILED
        result.error_msg = str(e)
        log.error(f"  [{entry.name}] Error: {e}")

    return result


def resolve_and_fetch(session: RegistrySession, entry: PackageEntry) -> Optional[dict]:
    """Resolve package source and fetch remote info."""
    if entry.source == SourceType.PYPI:
        return fetch_pypi_info(session, entry.name)

    elif entry.source == SourceType.NPM:
        return fetch_npm_info(session, entry.name)

    elif entry.source == SourceType.GITHUB:
        return fetch_github_info(session, entry.github_owner, entry.github_repo)

    elif entry.source == SourceType.UNKNOWN:
        # Try PyPI first, then NPM
        info = fetch_pypi_info(session, entry.name)
        if info:
            entry.source = SourceType.PYPI
            log.debug(f"  [{entry.name}] Resolved as PyPI package")
            return info

        # Try with underscores/hyphens variants for PyPI
        alt_name = entry.name.replace('-', '_')
        if alt_name != entry.name:
            info = fetch_pypi_info(session, alt_name)
            if info:
                entry.source = SourceType.PYPI
                entry.name = alt_name
                log.debug(f"  [{entry.name}] Resolved as PyPI package (alt name)")
                return info

        alt_name2 = entry.name.replace('_', '-')
        if alt_name2 != entry.name:
            info = fetch_pypi_info(session, alt_name2)
            if info:
                entry.source = SourceType.PYPI
                entry.name = alt_name2
                log.debug(f"  [{entry.name}] Resolved as PyPI package (alt name)")
                return info

        # Try NPM
        info = fetch_npm_info(session, entry.name)
        if info:
            entry.source = SourceType.NPM
            log.debug(f"  [{entry.name}] Resolved as NPM package")
            return info

        return None

    return None


# ============================================================
# REPORT GENERATOR
# ============================================================

def generate_report(results: list, download_dir: str, dry_run: bool = False) -> str:
    """Generate a detailed report of all actions taken."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("=" * 72)
    lines.append(f"  PACKAGE DOWNLOADER REPORT  {'(DRY RUN)' if dry_run else ''}")
    lines.append(f"  Generated: {now}")
    lines.append(f"  Download Dir: {download_dir}")
    lines.append("=" * 72)
    lines.append("")

    # Group by action
    groups = {}
    for r in results:
        groups.setdefault(r.action, []).append(r)

    # Summary counts
    lines.append("SUMMARY")
    lines.append("-" * 40)
    total = len(results)
    for action in [ActionType.UPDATED, ActionType.NEW_DOWNLOAD, ActionType.STAYED_SAME,
                   ActionType.NOT_FOUND, ActionType.FAILED, ActionType.SKIPPED]:
        count = len(groups.get(action, []))
        pct = (count / total * 100) if total else 0
        icon = {
            ActionType.UPDATED: "🔄",
            ActionType.NEW_DOWNLOAD: "✅",
            ActionType.STAYED_SAME: "⏸️ ",
            ActionType.NOT_FOUND: "❓",
            ActionType.FAILED: "❌",
            ActionType.SKIPPED: "⏭️ ",
        }.get(action, "  ")
        lines.append(f"  {icon} {action.value:<15} {count:>4}  ({pct:.0f}%)")
    lines.append("  " + "─" * 30)
    lines.append(f"     TOTAL           {total:>4}")
    lines.append("")

    # Detailed lists
    if ActionType.UPDATED in groups:
        lines.append("🔄 UPDATED (newer version downloaded, old archived)")
        lines.append("-" * 60)
        for r in sorted(groups[ActionType.UPDATED], key=lambda x: x.entry.name):
            src = r.entry.source.value.upper()
            lines.append(f"  [{src:6}] {r.entry.name}")
            lines.append(f"           v{r.local_version} -> v{r.remote_version}")
            if r.downloaded_file:
                lines.append(f"           File: {os.path.basename(r.downloaded_file)}")
        lines.append("")

    if ActionType.NEW_DOWNLOAD in groups:
        lines.append("✅ NEW DOWNLOADS (first time)")
        lines.append("-" * 60)
        for r in sorted(groups[ActionType.NEW_DOWNLOAD], key=lambda x: x.entry.name):
            src = r.entry.source.value.upper()
            lines.append(f"  [{src:6}] {r.entry.name}  v{r.remote_version}")
            if r.downloaded_file:
                lines.append(f"           File: {os.path.basename(r.downloaded_file)}")
        lines.append("")

    if ActionType.STAYED_SAME in groups:
        lines.append("⏸️  STAYED SAME (already up to date)")
        lines.append("-" * 60)
        for r in sorted(groups[ActionType.STAYED_SAME], key=lambda x: x.entry.name):
            src = r.entry.source.value.upper()
            lines.append(f"  [{src:6}] {r.entry.name}  v{r.local_version}")
        lines.append("")

    if ActionType.NOT_FOUND in groups:
        lines.append("❓ NOT FOUND (package not in any registry)")
        lines.append("-" * 60)
        for r in sorted(groups[ActionType.NOT_FOUND], key=lambda x: x.entry.name):
            lines.append(f"  {r.entry.name}  (searched: {r.entry.detected_from})")
        lines.append("")

    if ActionType.FAILED in groups:
        lines.append("❌ FAILED")
        lines.append("-" * 60)
        for r in sorted(groups[ActionType.FAILED], key=lambda x: x.entry.name):
            src = r.entry.source.value.upper()
            lines.append(f"  [{src:6}] {r.entry.name}")
            lines.append(f"           Error: {r.error_msg}")
        lines.append("")

    lines.append("=" * 72)
    report_text = "\n".join(lines)
    return report_text


def save_report(report_text: str, download_dir: str):
    """Save report to file."""
    report_path = os.path.join(download_dir, "download_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)
    log.info(f"Report saved to: {report_path}")


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    global log

    parser = argparse.ArgumentParser(
        description="Multi-ecosystem package downloader with version management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python package_downloader.py
  python package_downloader.py -f my_packages.txt -o D:\\Downloads
  python package_downloader.py --dry-run
  python package_downloader.py --github-token ghp_xxxxxxxxxxxx
  python package_downloader.py -w 16 -v
        """
    )
    parser.add_argument('-f', '--file', default=DEFAULT_INPUT_FILE,
                        help=f"Input file with package list (default: {DEFAULT_INPUT_FILE})")
    parser.add_argument('-o', '--output', default=DEFAULT_DOWNLOAD_DIR,
                        help=f"Download directory (default: {DEFAULT_DOWNLOAD_DIR})")
    parser.add_argument('--dry-run', action='store_true',
                        help="Preview actions without downloading")
    parser.add_argument('--github-token', default=os.environ.get('GITHUB_TOKEN', ''),
                        help="GitHub personal access token for higher API rate limits")
    parser.add_argument('-w', '--workers', type=int, default=MAX_WORKERS,
                        help=f"Number of concurrent downloads (default: {MAX_WORKERS})")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Enable debug logging")
    parser.add_argument('--sequential', action='store_true',
                        help="Download one at a time (no parallelism)")

    args = parser.parse_args()
    log = setup_logging(verbose=args.verbose)

    # Banner
    print()
    print("=" * 60)
    print("  📦 Package Downloader v2.0")
    print("  Multi-ecosystem: NPM | PyPI | GitHub")
    print("=" * 60)
    print()

    download_dir = args.output
    os.makedirs(download_dir, exist_ok=True)
    archive_dir = os.path.join(download_dir, ARCHIVE_SUBDIR)
    os.makedirs(archive_dir, exist_ok=True)

    log.info(f"Download directory: {download_dir}")
    log.info(f"Archive directory:  {archive_dir}")
    if args.dry_run:
        log.info("🔍 DRY RUN MODE - no files will be downloaded or moved")
    print()

    # Parse input
    entries = parse_input_file(args.file)
    if not entries:
        log.error("No packages to process!")
        sys.exit(1)

    # Count by source
    source_counts = {}
    for e in entries:
        source_counts[e.source.value] = source_counts.get(e.source.value, 0) + 1
    log.info(f"Package sources: {dict(source_counts)}")
    print()

    # Create session
    session = RegistrySession(github_token=args.github_token)

    # Process packages
    results = []
    total = len(entries)

    if args.sequential or args.workers <= 1:
        # Sequential processing
        for i, entry in enumerate(entries, 1):
            print(f"\n[{i}/{total}] Processing: {entry.name} ({entry.source.value})")
            result = process_package(session, entry, download_dir, dry_run=args.dry_run)
            results.append(result)
    else:
        # Parallel processing
        log.info(f"Using {args.workers} parallel workers")
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_map = {}
            for i, entry in enumerate(entries, 1):
                future = executor.submit(process_package, session, entry, download_dir, args.dry_run)
                future_map[future] = (i, entry)

            for future in as_completed(future_map):
                i, entry = future_map[future]
                try:
                    result = future.result()
                    results.append(result)
                    icon = {
                        ActionType.UPDATED: "🔄",
                        ActionType.NEW_DOWNLOAD: "✅",
                        ActionType.STAYED_SAME: "⏸️",
                        ActionType.NOT_FOUND: "❓",
                        ActionType.FAILED: "❌",
                    }.get(result.action, "  ")
                    print(f"  [{i}/{total}] {icon} {entry.name}: {result.action.value}")
                except Exception as e:
                    log.error(f"  [{i}/{total}] {entry.name}: Unexpected error: {e}")
                    results.append(PackageResult(
                        entry=entry,
                        action=ActionType.FAILED,
                        error_msg=str(e)
                    ))

    # Generate and display report
    print()
    report = generate_report(results, download_dir, dry_run=args.dry_run)
    print(report)

    if not args.dry_run:
        save_report(report, download_dir)

    # Exit code: 0 if all succeeded, 1 if any failures
    failed = sum(1 for r in results if r.action in (ActionType.FAILED,))
    if failed:
        log.warning(f"\n⚠️  {failed} package(s) failed. Check report for details.")
        sys.exit(1)

    print("\n✨ Done!")


if __name__ == "__main__":
    main()
