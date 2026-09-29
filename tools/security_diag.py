#!/usr/bin/env python3
"""Diagnostic sécurité Quintessences — orchestrateur unique.

Exécuté par les hooks git (pre-commit / post-commit / pre-push) et
manuellement. Produit un rapport markdown dans ``output/security-diag/``
et un code retour bloquant sur finding P0/P1.

Usage :
    python tools/security_diag.py --staged            # secrets sur diff stagé
    python tools/security_diag.py --mode quick        # scan rapide (secrets + config)
    python tools/security_diag.py --mode full         # + Bandit, pip-audit, cargo/npm
    python tools/security_diag.py --root ../Forge --mode full
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Console Windows (cp1252) : forcer UTF-8 pour les accents et le rapport.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

VERSION = "1.0.0"
MAX_FILE_BYTES = 512 * 1024
SCAN_EXTENSIONS = {
    ".py", ".sh", ".yml", ".yaml", ".json", ".toml", ".cfg", ".ini",
    ".md", ".kt", ".kts", ".java", ".ts", ".tsx", ".js", ".jsx",
    ".xml", ".properties", ".gradle", ".tf", ".ps1", ".bat", ".txt",
    ".env", ".pem", ".key", ".sql",
}

# ---------------------------------------------------------------------------
# Modèles
# ---------------------------------------------------------------------------


@dataclass
class Finding:
    severity: str  # "P0" | "P1" | "P2"
    category: str
    path: str
    line: int
    message: str


@dataclass
class DiagResult:
    findings: list[Finding] = field(default_factory=list)
    tool_notes: list[str] = field(default_factory=list)

    @property
    def blocking(self) -> bool:
        return any(f.severity in ("P0", "P1") for f in self.findings)


# ---------------------------------------------------------------------------
# Scan secrets
# ---------------------------------------------------------------------------

# (nom, motif, groupe_valeur) — groupe 0 = le motif entier est le secret,
# groupe N = la valeur à contrôler est capturée dans le groupe N.
SECRET_PATTERNS: list[tuple[str, re.Pattern[str], int]] = [
    ("cle_privée_PEM", re.compile(
        r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY(?: BLOCK)?-----"), 0),
    ("jeton_github", re.compile(
        r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b|github_pat_[A-Za-z0-9_]{22,}"), 0),
    ("cle_openai", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), 0),
    ("cle_aws", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), 0),
    ("secret_aws", re.compile(
        r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})"), 1),
    ("secret_générique", re.compile(
        r"(?i)(?:password|passwd|secret|token|api[_-]?key)"
        r"\s*[:=]\s*['\"]([^'\"\s]{8,})['\"]"), 1),
    ("jwt", re.compile(
        r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"), 0),
    ("cle_nvidia", re.compile(r"\bnvapi-[A-Za-z0-9_-]{30,}\b"), 0),
    ("url_avec_identifiants", re.compile(
        r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)"
        r"(?:\+[a-z]+)?://[^:/@\s]+:([^@\s]{4,})@"), 1),
]

# Placeholders repérés sur la correspondance ENTIÈRE (mot-clé inclus).
PLACEHOLDER_RE = re.compile(
    r"(?i)(changeme|change[-_]?me|example|exemple|dummy|placeholder|your[-_]|"
    r"xxx|\*\*\*|<[^>]+>|\$\{|\{\{|ci_|_ci\b|test[-_]?only|fake|sample|"
    r"gsie_ci_registry|gsie-registry-ci|\.{2,}|"
    r"(?:access|refresh|id)_token)")

# Placeholders repérés sur la VALEUR seule : variables d'environnement,
# variables psql (:'var'), noms auto-descriptifs (*_password, *_token…)
# et valeurs canoniques factices (pass, secret, dev, user…).
VALUE_PLACEHOLDER_RE = re.compile(
    r"(?i)(changeme|change[-_]?me|example|exemple|dummy|placeholder|your[-_]|"
    r"xxx|\*\*\*|\.{2,}|•|<[^>]*>|\$\{|\$[a-z_]|\{\{|ci_|_ci\b|"
    r"test[-_]?only|fake|sample|"
    r"(?:access|refresh|id)[-_]?token\b|"
    r"(?:^|[-_])(?:pass|password|passwd|pwd|secret|token|key|user|dev|test|"
    r"admin|name)(?:[-_]|$))")

# Chemins exclus du scan secrets : fixtures de test, exemples, rapports
# d'audit qui citent légitimement des motifs, et ce script lui-même.
ALLOWLIST_RE = re.compile(
    r"(?i)(\.example\b|(^|/)tests?/|(^|/)fixtures?/|test_[^/]*\.py|conftest\.py|"
    r"TEST-ONLY|\.env\.example|generate[_-](?:jwt|interop)|"
    r"23_QUALITY_MANAGEMENT|21_EXPERIMENTS|\.github/workflows|"
    r"skills-lock\.json|security_diag\.py|/tools/hooks/|"
    r"web/assets|node_modules|\.min\.js|(^|/)dist/|(^|/)build/|\.venv|"
    r"script_sandbox\.py|debug_install\.py|build_release\.py|"
    r"TOOLS/url_audit)")


def is_allowlisted(rel_path: str) -> bool:
    return bool(ALLOWLIST_RE.search(rel_path.replace(os.sep, "/")))


def line_has_secret(line: str) -> tuple[str, re.Match[str]] | None:
    for name, pattern, vg in SECRET_PATTERNS:
        match = pattern.search(line)
        if not match:
            continue
        value = match.group(vg) if vg else match.group(0)
        if PLACEHOLDER_RE.search(match.group(0)) or \
                VALUE_PLACEHOLDER_RE.search(value):
            continue
        return name, match
    return None


def scan_secrets_lines(root: Path, lines: list[tuple[str, int, str]],
                       category: str, out: DiagResult) -> None:
    for rel_path, lineno, text in lines:
        if is_allowlisted(rel_path):
            continue
        hit = line_has_secret(text)
        if hit:
            name, match = hit
            sev = "P0" if name in ("cle_privée_PEM", "jeton_github",
                                   "cle_aws", "secret_aws", "url_avec_identifiants") else "P1"
            out.findings.append(Finding(
                sev, category, rel_path, lineno,
                f"{name} : {match.group(0)[:40]}…"))


def git(root: Path, *args: str, check: bool = False) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120)
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)}")
    return result.stdout


def scan_staged(root: Path, out: DiagResult) -> None:
    """Secrets dans le diff stagé (lignes ajoutées uniquement)."""
    diff = git(root, "diff", "--cached", "-U0", "--diff-filter=ACMR")
    current = ""
    lineno = 0
    rows: list[tuple[str, int, str]] = []
    for raw in diff.splitlines():
        if raw.startswith("+++ b/"):
            current = raw[6:]
        elif raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            lineno = int(m.group(1)) - 1 if m else 0
        elif raw.startswith("+") and not raw.startswith("+++"):
            lineno += 1
            rows.append((current, lineno, raw[1:]))
        elif not raw.startswith("-"):
            lineno += 1
    scan_secrets_lines(root, rows, "secret-stagé", out)


def scan_commit(root: Path, ref: str, out: DiagResult) -> None:
    diff = git(root, "diff", f"{ref}~1", ref, "-U0", "--diff-filter=ACMR")
    rows: list[tuple[str, int, str]] = []
    current = ""
    for raw in diff.splitlines():
        if raw.startswith("+++ b/"):
            current = raw[6:]
        elif raw.startswith("+") and not raw.startswith("+++"):
            rows.append((current, 0, raw[1:]))
    scan_secrets_lines(root, rows, "secret-commit", out)


def scan_tree(root: Path, out: DiagResult) -> None:
    """Secrets dans l'arborescence suivie par git."""
    for rel in git(root, "ls-files").splitlines():
        p = root / rel
        if not p.is_file() or p.stat().st_size > MAX_FILE_BYTES:
            continue
        if p.suffix.lower() not in SCAN_EXTENSIONS and p.name != ".env":
            continue
        if is_allowlisted(rel):
            continue
        try:
            for i, text in enumerate(p.read_text(
                    encoding="utf-8", errors="replace").splitlines(), 1):
                hit = line_has_secret(text)
                if hit:
                    name, match = hit
                    sev = "P0" if name != "secret_générique" else "P1"
                    out.findings.append(Finding(
                        sev, "secret-arborescence", rel, i,
                        f"{name} : {match.group(0)[:40]}…"))
        except OSError:
            continue


# ---------------------------------------------------------------------------
# Vérifications de configuration (grep ciblés)
# ---------------------------------------------------------------------------

CONFIG_CHECKS: list[tuple[str, str, re.Pattern[str], re.Pattern[str] | None]] = [
    ("P2", "config", re.compile(r"(?m)^\s*image:\s*\S+:latest\b|FROM\s+\S+:latest\b"),
     re.compile(r"docker-compose|Dockerfile")),
    ("P1", "crypto", re.compile(r"\bverify\s*=\s*False\b|CERT_NONE|check_hostname\s*=\s*False"),
     re.compile(r"\.py$")),
    ("P1", "exec", re.compile(r"\bshell\s*=\s*True\b"), re.compile(r"\.py$")),
    ("P2", "exec", re.compile(r"(?<![\w.])(?:eval|exec)\s*\("),
     re.compile(r"\.py$")),
    ("P2", "crypto", re.compile(r"\bpickle\.loads?\s*\(|hashlib\.(?:md5|sha1)\s*\("),
     re.compile(r"\.py$")),
    ("P2", "cors", re.compile(r"allow_origins\s*=\s*\[\s*[\"']\*[\"']|ws_allowed_origins.*[\"']\*[\"']"),
     re.compile(r"\.py$")),
    ("P2", "http-clair", re.compile(
        r"['\"]http://(?!localhost\b|127\.0\.0\.1|0\.0\.0\.0|"
        r"[\w.-]*(?:opengis\.net|w3\.org|topografix\.com|mrcc\.com|"
        r"georss\.org|purl\.org|apache\.org|maven\.|json-schema\.org|"
        r"spdx\.|osgeo\.org|qgis\.org|gnu\.org|ietf\.org|unicode\.org|"
        r"kernel\.org|exslt\.org|openoffice\.org|docs\.oasis-open\.org|"
        r"schemas\.|example\.(?:com|org|net))\b)[A-Za-z0-9]"),
     re.compile(r"\.(py|kt|ts|tsx|js|json|ya?ml)$")),
    ("P1", "android", re.compile(r"usesCleartextTraffic\s*=\s*[\"']true"),
     re.compile(r"\.xml$")),
    ("P2", "android", re.compile(r"android:allowBackup\s*=\s*[\"']true"),
     re.compile(r"\.xml$")),
    ("P2", "perm", re.compile(r"\bchmod\s+777\b|MODE_WORLD_(?:READABLE|WRITEABLE)"),
     None),
    ("P2", "debug", re.compile(r"(?m)^\s*(?:DEBUG|debug)\s*[:=]\s*(?:true|True)\b"),
     re.compile(r"\.(py|ya?ml|json|toml)$")),
]


def scan_config(root: Path, out: DiagResult) -> None:
    for rel in git(root, "ls-files").splitlines():
        if is_allowlisted(rel):
            continue
        p = root / rel
        if not p.is_file() or p.stat().st_size > MAX_FILE_BYTES:
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for sev, cat, pattern, path_re in CONFIG_CHECKS:
            if path_re and not path_re.search(rel):
                continue
            for m in pattern.finditer(content):
                line = content.count("\n", 0, m.start()) + 1
                line_text = content.splitlines()[line - 1]
                stripped = line_text.lstrip()
                if ("nosec" in line_text or "noqa" in line_text
                        or "usedforsecurity" in line_text):
                    continue  # marqueur de revue humaine / usage non-sécu documenté
                if stripped.startswith(("#", "//")):
                    continue  # commentaire — jamais exécutable
                out.findings.append(Finding(
                    sev, cat, rel, line,
                    m.group(0).strip()[:80]))


# ---------------------------------------------------------------------------
# Outils externes (mode full)
# ---------------------------------------------------------------------------


def run_tool(cmd: list[str], cwd: Path, timeout: int = 600) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, str(exc)


def uvx_tool(root: Path, package: str, args: list[str]) -> tuple[int, str] | None:
    """Lance un outil via uvx si uv est disponible."""
    if not shutil.which("uv"):
        return None
    return run_tool(["uvx", "--from", package, *args], root)


def run_bandit(root: Path, out: DiagResult) -> None:
    targets = [d for d in ("GSIE/API/src", "tools", "src")
               if (root / d).is_dir()]
    if not targets:
        out.tool_notes.append("bandit : aucun répertoire Python source trouvé")
        return
    with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False) as tmp:
        report = tmp.name
    args = ["bandit", "-r", *targets, "-f", "json", "-o", report, "-ll"]
    res = uvx_tool(root, "bandit==1.7.10", args)
    if res is None:
        res = run_tool(["bandit", *args[1:]], root) if shutil.which("bandit") else None
    try:
        data = json.loads(Path(report).read_text(encoding="utf-8"))
        for r in data.get("results", []):
            sev = {"HIGH": "P1", "MEDIUM": "P2"}.get(
                r.get("issue_severity", ""), "P2")
            out.findings.append(Finding(
                sev, "sast-bandit",
                os.path.relpath(r.get("filename", ""), root),
                r.get("line_number", 0),
                f"{r.get('test_id')} {r.get('issue_text', '')[:100]}"))
        out.tool_notes.append(
            f"bandit : {len(data.get('results', []))} finding(s) (sev≥medium)")
    except (OSError, json.JSONDecodeError):
        out.tool_notes.append(f"bandit : échec ({'uvx absent' if res is None else res[1][:120]})")
    finally:
        Path(report).unlink(missing_ok=True)


def run_pip_audit(root: Path, out: DiagResult) -> None:
    projects = [d for d in ("GSIE/API", "Forge", ".")
                if (root / d / "uv.lock").exists() or (root / d / "requirements.txt").exists()]
    for proj in projects[:3]:
        pdir = root / proj
        with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
            req = tmp.name
        produced = False
        if (pdir / "uv.lock").exists() and shutil.which("uv"):
            rc, txt = run_tool(
                ["uv", "export", "--frozen", "--format", "requirements-txt",
                 "--no-hashes", "-o", req], pdir)
            produced = rc == 0 and Path(req).stat().st_size > 0
        elif (pdir / "requirements.txt").exists():
            shutil.copy(pdir / "requirements.txt", req)
            produced = True
        if not produced:
            out.tool_notes.append(f"pip-audit {proj} : export impossible")
            Path(req).unlink(missing_ok=True)
            continue
        res = uvx_tool(root, "pip-audit==2.9.0",
                       ["pip-audit", "-r", req, "-f", "json"])
        Path(req).unlink(missing_ok=True)
        if res is None:
            out.tool_notes.append(f"pip-audit {proj} : uv absent, ignoré")
            continue
        try:
            start = res[1].find("{")
            if start < 0:
                raise json.JSONDecodeError("no JSON", res[1], 0)
            vulns, _ = json.JSONDecoder().raw_decode(res[1][start:])
            deps = vulns.get("dependencies", vulns if isinstance(vulns, list) else [])
            count = sum(len(d.get("vulns", [])) for d in deps)
            for dep in deps:
                for v in dep.get("vulns", []):
                    fix = "fix dispo" if v.get("fix_versions") else "sans fix"
                    out.findings.append(Finding(
                        "P1", "cve-dépendance", proj, 0,
                        f"{dep.get('name')} {dep.get('version')} — "
                        f"{v.get('id')} ({fix})"))
            out.tool_notes.append(f"pip-audit {proj} : {count} CVE")
        except json.JSONDecodeError:
            out.tool_notes.append(f"pip-audit {proj} : sortie non-JSON "
                                  f"(rc={res[0]})")


def run_cargo_audit(root: Path, out: DiagResult) -> None:
    locks = [d for d in ("GSIE/ENGINES/EVIDENCE_ENGINE/rust", ".")
             if (root / d / "Cargo.lock").exists()]
    if not locks:
        return
    if not (shutil.which("cargo") and
            run_tool(["cargo", "audit", "--version"], root)[0] == 0):
        out.tool_notes.append("cargo-audit : binaire absent, ignoré")
        return
    for d in locks[:1]:
        rc, txt = run_tool(["cargo", "audit", "--json"], root / d)
        try:
            data = json.loads(txt)
            for v in data.get("vulnerabilities", {}).get("list", []):
                adv = v.get("advisory", {})
                pkg = v.get("package", {})
                out.findings.append(Finding(
                    "P1", "cve-rust", d, 0,
                    f"{pkg.get('name')} {pkg.get('version')} — {adv.get('id')}"))
            out.tool_notes.append(f"cargo-audit {d} : exécuté (rc={rc})")
        except json.JSONDecodeError:
            out.tool_notes.append(f"cargo-audit {d} : sortie non-JSON")


def run_npm_audit(root: Path, out: DiagResult) -> None:
    pkg_dirs = [d for d in ("apps/QGISIA", ".")
                if (root / d / "package-lock.json").exists()]
    if not pkg_dirs or not shutil.which("npm"):
        if pkg_dirs:
            out.tool_notes.append("npm-audit : npm absent, ignoré")
        return
    for d in pkg_dirs[:1]:
        rc, txt = run_tool(["npm", "audit", "--omit=dev", "--json"],
                           root / d, timeout=180)
        try:
            data = json.loads(txt)
            meta = data.get("metadata", {}).get("vulnerabilities", {})
            crit = meta.get("critical", 0) + meta.get("high", 0)
            if crit:
                out.findings.append(Finding(
                    "P1", "cve-npm", d, 0,
                    f"{crit} vulnérabilité(s) high/critical — "
                    f"voir `npm audit` dans {d}"))
            out.tool_notes.append(f"npm-audit {d} : {meta}")
        except json.JSONDecodeError:
            out.tool_notes.append(f"npm-audit {d} : échec (rc={rc})")


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------


def write_report(root: Path, result: DiagResult, mode: str, ref: str) -> Path:
    outdir = root / "output" / "security-diag"
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report = outdir / f"security-diag-{stamp}.md"
    counts = {s: sum(1 for f in result.findings if f.severity == s)
              for s in ("P0", "P1", "P2")}
    lines = [
        f"# Diagnostic sécurité — {datetime.now():%Y-%m-%d %H:%M:%S}",
        "",
        f"Racine : `{root}` · Mode : `{mode}` · Réf : `{ref}`",
        "",
        "## Synthèse",
        "",
        "| Sévérité | Nombre |", "|---|---|",
        f"| P0 (bloquant) | {counts['P0']} |",
        f"| P1 (élevé) | {counts['P1']} |",
        f"| P2 (moyen) | {counts['P2']} |",
        "", "## Findings", ""]
    for f in sorted(result.findings,
                    key=lambda x: (x.severity, x.category, x.path, x.line)):
        lines.append(f"- **[{f.severity}]** `{f.category}` — `{f.path}:{f.line}`"
                     f" — {f.message}")
    if not result.findings:
        lines.append("Aucun finding.")
    lines += ["", "## Outils", "", "| Outil | Statut |", "|---|---|"]
    lines += [f"| {n} |" for n in result.tool_notes] or ["| aucun | |"]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (outdir / "latest.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    return report


# ---------------------------------------------------------------------------
# Entrée
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="Diagnostic sécurité Quintessences")
    ap.add_argument("--root", default=".", help="racine du dépôt à scanner")
    ap.add_argument("--mode", choices=("quick", "full"), default="quick")
    ap.add_argument("--staged", action="store_true",
                    help="scan des secrets du diff stagé uniquement")
    ap.add_argument("--commit", default=None,
                    help="scan des secrets d'un commit (ex: HEAD)")
    ap.add_argument("--no-report", action="store_true")
    ap.add_argument("--version", action="version", version=VERSION)
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not (root / ".git").exists():
        print(f"Erreur : {root} n'est pas un dépôt git.", file=sys.stderr)
        return 2

    result = DiagResult()
    ref = args.commit or git(root, "rev-parse", "--short", "HEAD").strip() or "?"

    if args.staged:
        scan_staged(root, result)
        mode = "staged"
    else:
        if args.commit:
            scan_commit(root, args.commit, result)
        scan_tree(root, result)
        scan_config(root, result)
        mode = args.mode

    if args.mode == "full" and not args.staged:
        run_bandit(root, result)
        run_pip_audit(root, result)
        run_cargo_audit(root, result)
        run_npm_audit(root, result)

    # Déduplication : même (catégorie, fichier, ligne, message).
    seen: set[tuple[str, str, int, str]] = set()
    result.findings = [f for f in result.findings
                       if (f.category, f.path, f.line, f.message) not in seen
                       and not seen.add((f.category, f.path, f.line, f.message))]

    report = ""
    if not args.no_report and not args.staged:
        report = str(write_report(root, result, mode, ref))

    counts = {s: sum(1 for f in result.findings if f.severity == s)
              for s in ("P0", "P1", "P2")}
    print(f"security-diag [{mode}] {root.name} — "
          f"P0:{counts['P0']} P1:{counts['P1']} P2:{counts['P2']}"
          + (f" -> {report}" if report else ""))
    for f in result.findings:
        if f.severity in ("P0", "P1"):
            print(f"  [{f.severity}] {f.path}:{f.line} — {f.message}",
                  file=sys.stderr)
    return 1 if result.blocking else 0


if __name__ == "__main__":
    sys.exit(main())
