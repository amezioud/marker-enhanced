"""Detect project context from the current working directory."""
from __future__ import annotations

from pathlib import Path

_PATTERNS: dict[str, list[str]] = {
    "terraform":      ["*.tf", "*.tfvars", ".terraform"],
    "docker-compose": ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"],
    "docker":         ["Dockerfile", "Dockerfile.*", ".dockerignore"],
    "kubernetes":     ["Chart.yaml", "kustomization.yaml", "kustomization.yml"],
    "ansible":        ["ansible.cfg", "site.yml", "playbook.yml", "inventory"],
    "git":            [".git"],
    "make":           ["Makefile", "makefile"],
    "python":         ["requirements.txt", "pyproject.toml", "setup.py"],
    "npm":            ["package.json"],
    "systemd":        ["*.service", "*.timer", "*.socket"],
}

# Command prefixes (including abbreviations) relevant to each context
_PREFIXES: dict[str, list[str]] = {
    "terraform":      ["terraform", "tf", "tfa", "tfp"],
    "docker-compose": ["docker-compose", "dc"],
    "docker":         ["docker", "d"],
    "kubernetes":     ["kubectl", "k", "helm", "kustomize"],
    "ansible":        ["ansible", "ansible-playbook", "ansible-vault", "ap", "av"],
    "git":            ["git", "g", "gh", "glab"],
    "make":           ["make"],
    "python":         ["python", "python3", "pip", "pip3", "pytest"],
    "npm":            ["npm", "yarn", "npx"],
    "systemd":        ["systemctl", "journalctl"],
}

CONTEXT_BOOST = 0.4


def detect(directory: Path | None = None) -> set[str]:
    """Return the set of detected contexts for the given directory."""
    cwd = directory or Path.cwd()
    detected: set[str] = set()
    for ctx, patterns in _PATTERNS.items():
        for pattern in patterns:
            if "*" not in pattern:
                if (cwd / pattern).exists():
                    detected.add(ctx)
                    break
            elif list(cwd.glob(pattern)):
                detected.add(ctx)
                break
    return detected


def boosted_prefixes(contexts: set[str]) -> frozenset[str]:
    """Return all command prefixes that should be boosted for the detected contexts."""
    prefixes: set[str] = set()
    for ctx in contexts:
        prefixes.update(_PREFIXES.get(ctx, []))
    return frozenset(prefixes)
