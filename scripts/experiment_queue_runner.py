"""Self-healing queue for the full-room experiment.

Each stage runs in its own process. A non-zero exit, timeout, CUDA out-of-memory,
missing module, bad path, or CUDA context error is logged, diagnosed, and
retried for that stage only. After three retries the stage is marked failed
and the queue continues.

Invoke from the repo root:

    .venv\\Scripts\\python.exe scripts/experiment_queue_runner.py
    .venv\\Scripts\\python.exe scripts/experiment_queue_runner.py --dry-run
    .venv\\Scripts\\python.exe scripts/experiment_queue_runner.py --status
    .venv\\Scripts\\python.exe scripts/experiment_queue_runner.py --self-test

Stages already on disk are skipped: Experiment 1 dual-pass (PR #41), the
Phase 0 decision, the full-room checkpoints, and scenes A–J. Remaining work
is one process per scene and model, then the catch-table aggregate.

Logs (created on a real run, not by --dry-run):

    logs/experiment_queue.log
    logs/experiment_queue_failures.log
    logs/experiment_queue_recovery.jsonl
    logs/experiment_queue_state.json

See docs/research/40-experiment-queue-runner.md.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
QUEUE_LOG = LOG_DIR / "experiment_queue.log"
FAILURE_LOG = LOG_DIR / "experiment_queue_failures.log"
RECOVERY_LOG = LOG_DIR / "experiment_queue_recovery.jsonl"
STATE_PATH = LOG_DIR / "experiment_queue_state.json"

REPO_PY = ROOT / ".venv" / "Scripts" / "python.exe"
POINTCEPT_PY = Path(r"C:\Repos\openwall-stud-frame-ranks45\.venv\Scripts\python.exe")
RANDLA_PY = Path(r"C:\Repos\openwall-stud-frame-ranks45\.venv-o3dml\Scripts\python.exe")

MAX_RETRIES = 3
GPU_WAIT_S = 60
GPU_WAIT_LIMIT = 10
GPU_BUSY_MIB = 6000

# Top-level import names the runner may pip-install into the stage venv.
# Torch and the geometry stack stay pinned; a retry must not replace them.
INSTALL_BLOCKLIST = frozenset(
    {
        "torch",
        "torchvision",
        "torchaudio",
        "open3d",
        "numpy",
        "cuda",
        "cupy",
        "pytorch",
    }
)
MODULE_RE = re.compile(r"No module named ['\"]([A-Za-z][A-Za-z0-9_]{0,40})(?:\.[A-Za-z0-9_.]+)?['\"]")
MODULE_RE_BARE = re.compile(r"No module named ([A-Za-z][A-Za-z0-9_]{0,40})\b")

LETTERS = tuple("ABCDEFGHIJ")
# Geometry and the two supervised heads have full-room entry points.
# Foundation tools stay prompt/zero-shot; the scenario script records
# not_adapted instead of inventing a catch table. See doc 40.
MODELS = (
    ("open3d", "geometry", (REPO_PY,), 600),
    ("pointcept", "gpu", (POINTCEPT_PY, REPO_PY), 900),
    ("open3d_ml", "gpu", (RANDLA_PY, REPO_PY), 900),
    ("pcl", "geometry", (REPO_PY,), 600),
    ("pyransac3d", "geometry", (REPO_PY,), 600),
    ("pointsam", "foundation", (REPO_PY,), 120),
    ("sam3d", "foundation", (POINTCEPT_PY, REPO_PY), 120),
    ("openmask3d", "foundation", (REPO_PY,), 120),
    ("segment3d", "foundation", (REPO_PY,), 120),
)


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _append(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def log_line(message: str, *, log_path: Path = QUEUE_LOG) -> None:
    line = f"{_now()} {message}"
    print(line, flush=True)
    _append(log_path, line)


def log_failure(stage_id: str, attempt: int, stderr: str, *, log_path: Path = FAILURE_LOG) -> None:
    body = stderr if stderr.strip() else "(empty stderr)"
    _append(
        log_path,
        "\n".join(
            [
                f"===== {_now()} stage={stage_id} attempt={attempt} =====",
                body.rstrip(),
                "",
            ]
        ),
    )


def log_recovery(record: dict, *, log_path: Path = RECOVERY_LOG) -> None:
    _append(log_path, json.dumps(record, sort_keys=True))


def load_state(path: Path = STATE_PATH) -> dict:
    if not path.is_file():
        return {"stages": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state: dict, path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def diagnose_failure(stderr: str, stdout: str = "") -> dict:
    """Classify a failed stage. Does not apply a fix."""
    text = f"{stderr}\n{stdout}"
    lowered = text.lower()
    if "out of memory" in lowered or "outofmemoryerror" in lowered:
        return {
            "cause": "gpu_oom",
            "action": "clear_cache_reduce_batch_fresh_context",
        }
    module = MODULE_RE.search(text) or MODULE_RE_BARE.search(text)
    if module is not None or "modulenotfounderror" in lowered:
        name = module.group(1) if module is not None else ""
        return {"cause": "missing_module", "action": "pip_install_venv", "module": name}
    if (
        "no such file" in lowered
        or "filenotfounderror" in lowered
        or "cannot find the path" in lowered
        or "winerror 2" in lowered
        or "winerror 3" in lowered
        or "the system cannot find the file" in lowered
    ):
        return {"cause": "bad_path", "action": "switch_interpreter_or_skip_missing"}
    if "cuda" in lowered and "out of memory" not in lowered:
        return {"cause": "cuda_context", "action": "reset_context_and_retry"}
    if "timeout" in lowered:
        return {"cause": "timeout", "action": "retry_same_stage"}
    return {"cause": "unknown", "action": "retry_same_stage"}


def _marker_present(relative: str) -> bool:
    return (ROOT / relative).is_file()


def build_stages() -> list[dict]:
    """Queue order. Skip-if-present stages have no command."""
    stages: list[dict] = [
        {
            "id": "exp1_dual_pass",
            "phase": "A",
            "title": "Experiment 1 dual-threshold rebuild (PR #41)",
            "skip_if": ("artifacts/phase_neg1/experiment1_dual_pass.json",),
        },
        {
            "id": "fullroom_phase0",
            "phase": "B0",
            "title": "Full-room training decision",
            "skip_if": ("docs/research/37-fullroom-training-decision.md",),
        },
        {
            "id": "fullroom_phase1",
            "phase": "B1",
            "title": "Full-room stud-head checkpoints",
            "skip_if": (
                "artifacts/checkpoints/stud-heads/fullroom/pointcept_stud_2class_fullroom.pth",
                "artifacts/checkpoints/stud-heads/fullroom/randlanet_stud_2class_fullroom.pth",
            ),
        },
        {
            "id": "fullroom_phase2",
            "phase": "B2",
            "title": "Scenes A–J expected colors",
            "skip_if": ("artifacts/fullroom/scenes_expected.json",),
        },
    ]
    scenario = ROOT / "scripts" / "run_fullroom_scenario.py"
    for model, kind, interpreters, timeout_s in MODELS:
        for letter in LETTERS:
            stages.append(
                {
                    "id": f"fullroom_{letter}_{model}",
                    "phase": "B4",
                    "title": f"Scene {letter} model {model}",
                    "letter": letter,
                    "model": model,
                    "kind": kind,
                    "interpreters": interpreters,
                    "timeout_s": timeout_s,
                    "cmd_tail": [str(scenario), "--letter", letter, "--model", model],
                    "result": f"artifacts/fullroom/results/{letter}_{model}.json",
                }
            )
    stages.append(
        {
            "id": "fullroom_phase5_aggregate",
            "phase": "B5",
            "title": "Catch-table aggregate",
            "kind": "geometry",
            "interpreters": (REPO_PY,),
            "timeout_s": 180,
            "cmd_tail": [str(ROOT / "scripts" / "aggregate_fullroom_catch.py")],
            "result": "artifacts/fullroom/catch_summary.json",
        }
    )
    return stages


def _gpu_used_mib() -> int | None:
    try:
        completed = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    line = completed.stdout.strip().splitlines()
    if not line:
        return None
    try:
        return int(line[0].strip())
    except ValueError:
        return None


def wait_for_gpu(stage_id: str) -> None:
    for attempt in range(GPU_WAIT_LIMIT):
        used = _gpu_used_mib()
        if used is None or used < GPU_BUSY_MIB:
            return
        log_line(f"stage={stage_id} gpu_busy used_mib={used} wait_s={GPU_WAIT_S} n={attempt + 1}")
        time.sleep(GPU_WAIT_S)
    log_line(f"stage={stage_id} gpu_still_busy proceeding")


def _existing_interpreter(candidates: tuple[Path, ...]) -> tuple[Path | None, list[str]]:
    missing: list[str] = []
    for path in candidates:
        if path.is_file():
            return path, missing
        missing.append(str(path))
    return None, missing


def apply_recovery(diagnosis: dict, env: dict, interpreter: Path | None) -> tuple[dict, dict]:
    """Return updated env and a recovery record. May pip-install once."""
    record = {
        "time": _now(),
        "cause": diagnosis.get("cause"),
        "action": diagnosis.get("action"),
        "applied": False,
        "detail": "",
    }
    cause = diagnosis.get("cause")
    if cause == "gpu_oom":
        env["FULLROOM_OOM_RETRY"] = "1"
        env["FULLROOM_BATCH"] = "1"
        env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
        record["applied"] = True
        record["detail"] = (
            "Set FULLROOM_BATCH=1, PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True, "
            "FULLROOM_OOM_RETRY=1. The next process starts a fresh CUDA context and "
            "clears the cache. Trained sampler sizes are not changed."
        )
    elif cause == "cuda_context":
        env["FULLROOM_CUDA_RESET"] = "1"
        record["applied"] = True
        record["detail"] = "Next process is a new interpreter. FULLROOM_CUDA_RESET=1 clears the cache at start."
    elif cause == "missing_module":
        module = str(diagnosis.get("module") or "")
        if interpreter is None:
            record["detail"] = "No interpreter available for pip install."
        elif module in INSTALL_BLOCKLIST or not module:
            record["detail"] = f"Refused to pip-install {module!r} (empty or pinned stack)."
        elif env.get(f"FULLROOM_INSTALLED_{module}") == "1":
            record["detail"] = f"Already attempted pip install of {module} in this stage."
        else:
            completed = subprocess.run(
                [str(interpreter), "-m", "pip", "install", module],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=300,
            )
            env[f"FULLROOM_INSTALLED_{module}"] = "1"
            record["applied"] = completed.returncode == 0
            tail = (completed.stderr or completed.stdout or "")[-500:]
            record["detail"] = f"pip install {module} exit={completed.returncode} {tail}"
    elif cause == "bad_path":
        record["applied"] = True
        record["detail"] = "Interpreter list is walked at the start of the next attempt."
    else:
        record["detail"] = "No automatic patch. The same stage is restarted."
        record["applied"] = True
    return env, record


def run_command(cmd: list[str], env: dict, timeout_s: int) -> tuple[int, str, str]:
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        stderr = (stderr or "") + "\nTIMEOUT\n"
        return 124, stdout or "", stderr
    return int(proc.returncode or 0), stdout or "", stderr or ""


def _result_ok(stage: dict) -> bool:
    relative = stage.get("result")
    if not relative:
        return True
    path = ROOT / relative
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return payload.get("status") in {"ok", "not_adapted"}


def execute_stage(stage: dict, env: dict) -> tuple[int, str, str, Path | None]:
    if stage.get("kind") == "gpu":
        wait_for_gpu(stage["id"])
    interpreter, missing = _existing_interpreter(tuple(stage.get("interpreters") or ()))
    if missing:
        log_line(f"stage={stage['id']} missing_interpreter {missing}")
    if interpreter is None:
        return 127, "", f"FileNotFoundError: none of {missing} exist", None
    cmd = [str(interpreter), *stage["cmd_tail"]]
    code, stdout, stderr = run_command(cmd, env, int(stage["timeout_s"]))
    if code == 0 and not _result_ok(stage):
        code = 1
        stderr += "\nresult JSON missing or status not ok/not_adapted\n"
    return code, stdout, stderr, interpreter


def run_queue(
    stages: list[dict],
    *,
    state_path: Path,
    queue_log: Path,
    failure_log: Path,
    recovery_log: Path,
    dry_run: bool = False,
    retry_failed: bool = False,
) -> dict:
    state = load_state(state_path)
    summary = {"finished": [], "skipped": [], "failed": [], "pending": [], "running": []}
    base_env = os.environ.copy()
    base_env.setdefault("PYTHONUNBUFFERED", "1")

    for stage in stages:
        stage_id = stage["id"]
        prior = state["stages"].get(stage_id, {})
        status = prior.get("status")
        if status in {"success", "skipped_present"} or (status == "failed" and not retry_failed):
            bucket = "skipped" if status == "skipped_present" else ("failed" if status == "failed" else "finished")
            summary[bucket].append(stage_id)
            continue
        markers = stage.get("skip_if")
        if markers and all(_marker_present(item) for item in markers):
            if not dry_run:
                state["stages"][stage_id] = {
                    "status": "skipped_present",
                    "time": _now(),
                    "title": stage["title"],
                    "markers": list(markers),
                }
                save_state(state, state_path)
                log_line(f"stage={stage_id} skipped_present", log_path=queue_log)
            summary["skipped"].append(stage_id)
            continue
        if stage.get("result") and _result_ok(stage):
            if not dry_run:
                state["stages"][stage_id] = {
                    "status": "success",
                    "time": _now(),
                    "title": stage["title"],
                    "result": stage.get("result"),
                    "note": "result file already ok",
                }
                save_state(state, state_path)
                log_line(f"stage={stage_id} success existing_result", log_path=queue_log)
            summary["finished"].append(stage_id)
            continue
        if dry_run:
            summary["pending"].append(stage_id)
            continue

        env = dict(base_env)
        success = False
        attempts_used = 0
        for attempt in range(1, MAX_RETRIES + 2):
            attempts_used = attempt
            state["stages"][stage_id] = {
                "status": "running",
                "attempt": attempt,
                "time": _now(),
                "title": stage["title"],
            }
            save_state(state, state_path)
            log_line(f"stage={stage_id} start attempt={attempt}", log_path=queue_log)
            code, stdout, stderr, interpreter = execute_stage(stage, env)
            if code == 0:
                log_line(f"stage={stage_id} success attempt={attempt}", log_path=queue_log)
                state["stages"][stage_id] = {
                    "status": "success",
                    "attempts": attempt,
                    "time": _now(),
                    "title": stage["title"],
                    "result": stage.get("result"),
                }
                save_state(state, state_path)
                summary["finished"].append(stage_id)
                success = True
                break
            log_failure(stage_id, attempt, stderr, log_path=failure_log)
            diagnosis = diagnose_failure(stderr, stdout)
            if attempt > MAX_RETRIES:
                log_line(
                    f"stage={stage_id} failed attempts={attempt} cause={diagnosis['cause']}",
                    log_path=queue_log,
                )
                break
            env, recovery = apply_recovery(diagnosis, env, interpreter)
            recovery["stage"] = stage_id
            recovery["attempt"] = attempt
            log_recovery(recovery, log_path=recovery_log)
            log_line(
                f"stage={stage_id} recover cause={diagnosis['cause']} action={recovery['action']} "
                f"applied={recovery['applied']} detail={recovery['detail']}",
                log_path=queue_log,
            )
        if not success:
            state["stages"][stage_id] = {
                "status": "failed",
                "attempts": attempts_used,
                "time": _now(),
                "title": stage["title"],
            }
            save_state(state, state_path)
            summary["failed"].append(stage_id)
    summary["self_healing"] = True
    summary["max_retries"] = MAX_RETRIES
    return summary


def format_status(state: dict, stages: list[dict]) -> str:
    lines = ["self_healing=enabled", f"max_retries={MAX_RETRIES}"]
    known = {stage["id"] for stage in stages}
    by_status: dict[str, list[str]] = {
        "finished": [],
        "running": [],
        "failed": [],
        "skipped_present": [],
        "pending": [],
    }
    recorded = state.get("stages", {})
    for stage in stages:
        row = recorded.get(stage["id"])
        if row is None:
            by_status["pending"].append(stage["id"])
            continue
        status = row.get("status")
        if status == "success":
            by_status["finished"].append(stage["id"])
        elif status == "running":
            by_status["running"].append(stage["id"])
        elif status == "failed":
            by_status["failed"].append(stage["id"])
        elif status == "skipped_present":
            by_status["skipped_present"].append(stage["id"])
        else:
            by_status["pending"].append(stage["id"])
    for key in ("finished", "running", "skipped_present", "failed", "pending"):
        rows = by_status[key]
        lines.append(f"{key} ({len(rows)}): {', '.join(rows) if rows else '-'}")
    extra = sorted(set(recorded) - known)
    if extra:
        lines.append(f"state_not_in_queue: {', '.join(extra)}")
    return "\n".join(lines)


def self_test() -> int:
    """Fail one stage on a fake OOM, recover it, and keep going after a hard failure."""
    with tempfile.TemporaryDirectory(prefix="fullroom-queue-") as tmp:
        root = Path(tmp)
        queue_log = root / "experiment_queue.log"
        failure_log = root / "experiment_queue_failures.log"
        recovery_log = root / "experiment_queue_recovery.jsonl"
        state_path = root / "experiment_queue_state.json"
        ok_script = root / "ok.py"
        oom_script = root / "oom.py"
        bad_script = root / "bad.py"
        ok_script.write_text("raise SystemExit(0)\n", encoding="utf-8")
        oom_script.write_text(
            "import os, sys\n"
            "if os.environ.get('FULLROOM_OOM_RETRY') == '1':\n"
            "    raise SystemExit(0)\n"
            "sys.stderr.write('CUDA out of memory\\n')\n"
            "raise SystemExit(1)\n",
            encoding="utf-8",
        )
        bad_script.write_text("import sys\nsys.stderr.write('boom\\n')\nraise SystemExit(2)\n", encoding="utf-8")
        py = Path(sys.executable)
        stages = [
            {
                "id": "selftest_ok",
                "title": "ok",
                "kind": "geometry",
                "interpreters": (py,),
                "timeout_s": 30,
                "cmd_tail": [str(ok_script)],
            },
            {
                "id": "selftest_oom",
                "title": "oom",
                "kind": "geometry",
                "interpreters": (py,),
                "timeout_s": 30,
                "cmd_tail": [str(oom_script)],
            },
            {
                "id": "selftest_bad",
                "title": "bad",
                "kind": "geometry",
                "interpreters": (py,),
                "timeout_s": 30,
                "cmd_tail": [str(bad_script)],
            },
        ]
        summary = run_queue(
            stages,
            state_path=state_path,
            queue_log=queue_log,
            failure_log=failure_log,
            recovery_log=recovery_log,
            dry_run=False,
        )
        diagnosis = diagnose_failure("CUDA out of memory\n")
        module = diagnose_failure("ModuleNotFoundError: No module named 'not_a_real_pkg'\n")
        path = diagnose_failure("FileNotFoundError: [WinError 3] The system cannot find the path\n")
        cuda = diagnose_failure("CUDA error: device-side assert triggered\n")
        if diagnosis["cause"] != "gpu_oom":
            raise SystemExit(f"oom diagnose failed: {diagnosis}")
        if module["cause"] != "missing_module" or module["module"] != "not_a_real_pkg":
            raise SystemExit(f"module diagnose failed: {module}")
        if path["cause"] != "bad_path":
            raise SystemExit(f"path diagnose failed: {path}")
        if cuda["cause"] != "cuda_context":
            raise SystemExit(f"cuda diagnose failed: {cuda}")
        if summary["finished"] != ["selftest_ok", "selftest_oom"]:
            raise SystemExit(f"finished {summary['finished']}")
        if summary["failed"] != ["selftest_bad"]:
            raise SystemExit(f"failed {summary['failed']}")
        recovery_text = recovery_log.read_text(encoding="utf-8")
        if "gpu_oom" not in recovery_text or "selftest_oom" not in recovery_text:
            raise SystemExit("recovery log missing the OOM record")
        if "selftest_bad" not in failure_log.read_text(encoding="utf-8"):
            raise SystemExit("failure log missing the hard failure")
        state = load_state(state_path)
        if state["stages"]["selftest_oom"]["status"] != "success":
            raise SystemExit("oom stage was not recovered")
        if state["stages"]["selftest_bad"]["status"] != "failed":
            raise SystemExit("hard failure aborted or was not marked failed")
    print("self-test passed", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Self-healing full-room experiment queue.")
    parser.add_argument("--dry-run", action="store_true", help="List stages and skip decisions. Do not run them.")
    parser.add_argument("--status", action="store_true", help="Print finished, running, failed, and pending stages.")
    parser.add_argument("--self-test", action="store_true", help="Run a throwaway queue that recovers one fake OOM.")
    parser.add_argument("--retry-failed", action="store_true", help="Re-queue stages already marked failed.")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    stages = build_stages()
    if args.status:
        print(format_status(load_state(), stages), flush=True)
        return 0
    if args.dry_run:
        summary = run_queue(
            stages,
            state_path=STATE_PATH,
            queue_log=QUEUE_LOG,
            failure_log=FAILURE_LOG,
            recovery_log=RECOVERY_LOG,
            dry_run=True,
        )
        print(json.dumps(summary, indent=2), flush=True)
        return 0
    summary = run_queue(
        stages,
        state_path=STATE_PATH,
        queue_log=QUEUE_LOG,
        failure_log=FAILURE_LOG,
        recovery_log=RECOVERY_LOG,
        retry_failed=args.retry_failed,
    )
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
