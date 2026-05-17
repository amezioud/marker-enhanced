"""Download and convert tldr-pages to marker format."""
from __future__ import annotations

import io
import re
import urllib.request
import zipfile
from pathlib import Path
from typing import Iterator

from ..command import Command, save

TLDR_ZIP_URL = "https://github.com/tldr-pages/tldr/archive/refs/heads/main.zip"

_PLATFORMS = ("common", "linux", "osx", "sunos", "windows")
_PAGE_RE = re.compile(r"tldr-main/pages/(\w+)/(.+)\.md$")

# Default topic whitelist for a DevOps / cloud / web-hosting engineer.
# Add or remove entries in $MARKER_DATA_HOME/topics.txt to customise.
DEFAULT_TOPICS: frozenset[str] = frozenset({
    # containers & orchestration
    "docker", "docker-compose", "docker-machine",
    "kubectl", "helm", "k9s", "kustomize", "minikube", "k3s", "skaffold",
    "podman", "buildah",
    # infra as code
    "terraform", "ansible", "ansible-playbook", "ansible-vault",
    "packer", "vagrant",
    # cloud CLIs
    "aws", "gcloud", "az",
    # ssh / file transfer / networking
    "ssh", "ssh-keygen", "ssh-copy-id", "scp", "sftp", "rsync",
    "curl", "wget", "httpie",
    "nmap", "netstat", "ss", "ip", "iptables", "ufw", "nft",
    "dig", "nslookup", "host", "traceroute", "ping", "mtr",
    "nc", "tcpdump", "tshark",
    "openssl", "certbot",
    # web servers / proxy
    "nginx", "apache", "caddy", "haproxy", "traefik",
    # process / system / init
    "systemctl", "journalctl", "systemd-analyze",
    "cron", "crontab", "at",
    "ps", "top", "htop", "kill", "killall", "lsof", "strace", "ltrace",
    "free", "df", "du", "iostat", "vmstat", "sar",
    "ulimit", "sysctl",
    # files / shell utilities
    "find", "grep", "awk", "sed", "xargs", "sort", "cut", "tr",
    "tar", "zip", "unzip", "gzip", "gunzip", "bzip2", "zstd",
    "chmod", "chown", "ln", "cp", "mv", "rm",
    "tail", "head", "less", "cat", "tee",
    "env", "export", "source",
    # git
    "git", "gh",
    # databases
    "mysql", "mysqldump", "psql", "pg_dump", "redis-cli",
    "mongodump", "mongorestore",
    # package managers
    "apt", "apt-get", "dpkg", "yum", "dnf", "rpm",
    "pip", "pip3", "npm", "yarn",
    # monitoring / logs
    "prometheus", "alertmanager",
    "logrotate",
    # terminal multiplexers
    "tmux", "screen",
    # editors
    "vim", "nano",
    # misc devops
    "jq", "yq", "envsubst",
    "make", "cmake",
    "gpg", "age",
    "vault",
})


def _load_topics(data_dir: Path) -> frozenset[str]:
    """Merge DEFAULT_TOPICS with optional $MARKER_DATA_HOME/topics.txt.

    Lines without prefix add to the defaults.
    Lines prefixed with '-' remove from the defaults.
    """
    topics_file = data_dir / "topics.txt"
    if not topics_file.exists():
        return DEFAULT_TOPICS

    topics = set(DEFAULT_TOPICS)
    for raw in topics_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-"):
            topics.discard(line[1:].strip())
        else:
            topics.add(line)
    return frozenset(topics)


def _parse_page(content: str) -> Iterator[Command]:
    description = ""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("- "):
            description = line[2:].rstrip(":")
        elif line.startswith("`") and line.endswith("`"):
            cmd = line[1:-1].strip()
            if cmd:
                yield Command(cmd, description)
                description = ""


def update(data_dir: Path) -> dict[str, int]:
    """Download tldr-pages zip, filter by topic whitelist, write per-platform txt files."""
    data_dir.mkdir(parents=True, exist_ok=True)
    topics = _load_topics(data_dir)

    with urllib.request.urlopen(TLDR_ZIP_URL, timeout=30) as resp:
        zf = zipfile.ZipFile(io.BytesIO(resp.read()))

    buckets: dict[str, list[Command]] = {p: [] for p in _PLATFORMS}

    for name in zf.namelist():
        m = _PAGE_RE.match(name)
        if not m:
            continue
        platform, command_name = m.group(1), m.group(2)
        if platform not in buckets:
            continue
        if command_name not in topics:
            continue
        content = zf.read(name).decode("utf-8", errors="replace")
        buckets[platform].extend(_parse_page(content))

    counts: dict[str, int] = {}
    for platform, cmds in buckets.items():
        if cmds:
            save(cmds, data_dir / f"tldr_{platform}.txt")
            counts[platform] = len(cmds)
    return counts


def load(data_dir: Path, os_name: str) -> list[Command]:
    """Load cached tldr pages (common + os-specific) from data_dir."""
    from ..command import load as cmd_load

    cmds = cmd_load(data_dir / "tldr_common.txt")
    cmds += cmd_load(data_dir / f"tldr_{os_name}.txt")
    return cmds