"""Overlay Sarp's module onto a disposable, detached team checkout and test it.

No fetch, checkout, commit, push or teammate source edit is performed. The caller
supplies the clean, detached scratch checkout. Only Sarp's module and named test
files are copied there; no real DB, provider credential or cloud is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

TEAM_REVISION = "929776ccc51d914084ebb49d5997942c51c64b58"
ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-team-revision", default=TEAM_REVISION)
    parser.add_argument("--node", default="node")
    parser.add_argument("--require-postgres", action="store_true")
    args = parser.parse_args()
    team, output = args.team_root.resolve(), args.output_dir.resolve()
    if team == ROOT or team in ROOT.parents or ROOT in team.parents:
        parser.error("Use a separate disposable checkout, outside the development repository")
    if output == team or team in output.parents or output == ROOT or ROOT in output.parents:
        parser.error("Evidence output must be outside both source checkouts")
    git = os.environ.get("GIT_BINARY") or shutil.which("git")
    if not git:
        parser.error("Git is required; set GIT_BINARY if it is not on PATH")

    def git_read(*arguments, check=True):
        return subprocess.run([git, "-c", "safe.directory=" + team.as_posix(), "-C", str(team),
                               *arguments], capture_output=True, text=True, check=check)

    if git_read("symbolic-ref", "--quiet", "HEAD", check=False).returncode == 0:
        parser.error("Team checkout must be detached; do not pass a teammate's active branch")
    revision = git_read("rev-parse", "HEAD").stdout.strip()
    if revision != args.expected_team_revision:
        parser.error("Unexpected team revision; review and pin it explicitly")
    if git_read("status", "--porcelain").stdout.strip():
        parser.error("Use a clean disposable checkout (an overlaid checkout cannot be reused)")
    if args.require_postgres and not os.environ.get("TEST_DATABASE_URL", "").startswith("postgres"):
        parser.error("TEST_DATABASE_URL must name an isolated PostgreSQL test database")

    # Guard teammate inputs: these must still have the original bytes after tests.
    tracked = git_read("ls-files", "-z").stdout.split("\0")
    protected = {p: digest(team/p) for p in tracked if p and (team/p).is_file()
                 and not p.startswith("backend/src/fridgely_collections/")}
    overlays = {}
    files = list((ROOT/"backend/src/fridgely_collections").glob("*.py")) + [
        ROOT/"backend/tests/test_history_dependency_failures.py",
        ROOT/"backend/integration_tests/test_sarp_collections_contract.py",
    ]
    for source in files:
        if source.parent.name == "integration_tests":
            relative = "backend/tests/" + source.name
        else:
            relative = source.relative_to(ROOT).as_posix()
        target = (team/relative).resolve()
        if not target.is_relative_to(team):
            parser.error("Overlay target escapes the disposable checkout")
        if target.exists() and not relative.startswith("backend/src/fridgely_collections/"):
            parser.error("Refusing to overwrite an existing teammate test")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        overlays[relative] = digest(source)

    output.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONPATH": str(team/"backend/src"), "FRIDGELY_PYTHON": sys.executable,
           "PYTHONDONTWRITEBYTECODE": "1"}
    # Never use an inherited live-provider key for compatibility verification.
    env.pop("OPENAI_API_KEY", None)
    env.pop("DATABASE_URL", None)
    commands = [
        ("python", [sys.executable, "-m", "pytest", "backend/tests", "-q",
                    "--basetemp=" + str(output/"pytest-tmp"),
                    "--junitxml=" + str(output/"team-junit.xml")]),
        ("acceptance", [args.node, "--test", "--test-reporter=tap",
                        "tests/functional/requirements.test.mjs"]),
    ]
    evidence = {"team_revision": revision, "python": sys.version.split()[0],
                "overlay_sha256": overlays, "results": {},
                "postgres_requested": args.require_postgres,
                "provider": "controlled fixtures; live OpenAI not exercised"}
    failed = False
    for label, command in commands:
        result = subprocess.run(command, cwd=team, env=env, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=600)
        (output/(label + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
        summary = {"exit_code": result.returncode}
        if label == "python" and (output/"team-junit.xml").exists():
            suites = ET.parse(output/"team-junit.xml").getroot()
            cases = list(suites.iter("testcase"))
            summary.update(tests=len(cases),
                failures=sum(c.find("failure") is not None for c in cases),
                errors=sum(c.find("error") is not None for c in cases),
                skipped=sum(c.find("skipped") is not None for c in cases),
                passed=sum(all(c.find(k) is None for k in ["failure", "error", "skipped"]) for c in cases))
            if args.require_postgres and summary["skipped"]:
                failed = True
        if label == "acceptance":
            for field in ["tests", "pass", "fail", "skipped"]:
                match = re.search(r"^# " + field + r" (\d+)\s*$", result.stdout, re.M)
                if match:
                    summary[field] = int(match.group(1))
        evidence["results"][label] = summary
        failed |= result.returncode != 0
        print(label + ": " + json.dumps(summary), flush=True)

    changed = [path for path, sha in protected.items() if not (team/path).is_file()
               or digest(team/path) != sha]
    evidence["teammate_inputs_preserved"] = not changed
    failed |= bool(changed)
    (output/"summary.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    if changed:
        print("Teammate inputs changed unexpectedly: " + ", ".join(changed), file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
