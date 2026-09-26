#!/usr/bin/env python3
"""
test_healkristin.py

Randomised test harness for the "HealkrISTin" project (AED, IST Lisboa).

What it does, each run:
  1. Compiles healkristin.c (once).
  2. For NUM_TESTS iterations:
       - randomly generates a valid .quests / .map / .position trio, each
         with a RANDOM base filename (sometimes all three share one base,
         sometimes each file gets its own - both are legal per the
         statement, which says the three names may be "distintos ou
         iguais entre si"). This checks that the program derives the
         .results name from the .quests file specifically, rather than
         assuming a fixed/shared name.
       - runs the compiled binary against them (optionally under
         valgrind's memcheck, to catch invalid reads/writes and leaks -
         see USE_VALGRIND below)
       - computes the CORRECT answer itself (independent union-find,
         following the rules in the project statement) for every task
         it knows how to check (currently Task1 and Task2)
       - compares the program's .results file against that correct
         answer and reports OK / MISMATCH / CRASH / VALGRIND_ERROR / NO OUTPUT
  3. Prints a summary. Files for a test case are deleted automatically
     if and only if that case passed; every non-OK case's files are left
     on disk under ./runs/<case>/ so you can inspect or replay them.

Only Task1 and Task2 are checked for correctness, because those are the
only ones implemented in healkristin.c right now (see the switch in
QuestsMan). You'll be asked at startup which tasks (1-6) to include in
the generated .quests files; any of Task3-6 you pick still get generated
(with a random city argument where needed) and run, purely to fuzz for
crashes - their output isn't graded until you extend `build_expected`.

Usage:
    python3 test_healkristin.py           run without valgrind (default)
    python3 test_healkristin.py -v        also run every case under valgrind
    python3 test_healkristin.py -h        list the flags and what they do,
                                           without compiling or running anything
    (then answer the "which tasks" prompt, e.g. "1 2 4", or just press
    Enter to include all of Task1-Task6)

Everything else you're likely to want to tweak is in the CONFIG block below.
"""

import argparse
import difflib
import os
import random
import shlex
import shutil
import string
import subprocess
import sys
from pathlib import Path

# ============================== CONFIG ==================================

SOURCE_FILE = "healkristin.c"     # path to the C source to compile
BUILD_DIR   = "build"             # where the compiled binary goes
WORK_DIR    = "runs"              # scratch dir, one subfolder per test

MIN_NAME_LEN = 1        # random .quests/.map/.position base filenames are
MAX_NAME_LEN = 50        # generated with lengths in this range
SAME_BASENAME_PROB = 0.5  # chance all three files share one random base
                           # name, vs. each getting its own random name

# --- Randomisation ranges: edit these two to control test size ----------
MIN_CITIES  = 1       # smallest number of cities (C) to generate.
MAX_CITIES  = 20       # <-- set this to whatever you want to stress-test
MIN_LINKS   = 0        # smallest number of physical links (L) to generate.
MAX_LINKS   = 30        # <-- "map size"; set this too

MAX_COORD   = 50       # .position plane is randomised as Xmax,Ymax in [1, MAX_COORD]

NUM_TESTS   = 250        # how many random cases to run this session
TIMEOUT_SEC = 5         # kill a run that hangs longer than this (seconds)
SEED        = None      # int for reproducible runs, or None for fresh randomness

VERBOSE_DIFF = True   # print a line-by-line diff on mismatch

USE_VALGRIND_DEFAULT = False  # overridden by the -v/--valgrind CLI flag
VALGRIND_TIMEOUT_SEC = 20    # valgrind is much slower than a native run
VALGRIND_ERROR_EXITCODE = 99 # sentinel exit code valgrind returns when it
                              # found errors (invalid reads/writes, leaks, ...)
VALGRIND_LOG_CHARS = 4000    # truncate a very long valgrind report when printing

ALL_TASKS = [1, 2, 3, 4, 5, 6]           # tasks defined in the statement
TASK_NEEDS_ARG = {1: False, 2: False, 3: True, 4: True, 5: False, 6: True}
CHECKABLE_TASKS = {1, 2}                 # tasks this harness knows how to grade

# ==========================================================================


# -------------------------------- CLI flags ---------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        prog="test_healkristin.py",
        description="Randomised test harness for the HealkrISTin project.",
    )
    parser.add_argument(
        "-v", "--valgrind",
        action="store_true",
        help=(
            "also run every test case under valgrind's memcheck "
            "(invalid reads/writes, leaks). Off by default, since it's "
            "much slower. Ignored (with a warning) if valgrind isn't installed."
        ),
    )
    # -h/--help is added automatically by argparse: it prints the flags
    # above and exits immediately, before anything is compiled or run.
    return parser.parse_args()


# ------------------------------ Task selection -----------------------------

def prompt_task_selection():
    """Asks the user which tasks to exercise. Empty input -> all tasks."""
    prompt = (
        f"Which tasks do you want to test {tuple(ALL_TASKS)}? "
        "(e.g. '1 2 4', or press Enter for all): "
    )
    raw = input(prompt).strip()
    if not raw:
        chosen = list(ALL_TASKS)
    else:
        chosen = []
        for tok in raw.split():
            try:
                n = int(tok)
            except ValueError:
                print(f"Ignoring '{tok}' (not a number).")
                continue
            if n not in ALL_TASKS:
                print(f"Ignoring {n} (not a valid task number, must be 1-6).")
                continue
            if n not in chosen:
                chosen.append(n)
        if not chosen:
            print("No valid tasks selected, defaulting to all tasks.")
            chosen = list(ALL_TASKS)
    chosen.sort()

    uncheckable = [t for t in chosen if t not in CHECKABLE_TASKS]
    if uncheckable:
        print(
            f"Note: Task{{{','.join(str(t) for t in uncheckable)}}} "
            "aren't implemented in healkristin.c yet, so they'll be "
            "generated and run (to fuzz for crashes) but not graded."
        )
    return chosen


# ---------------------------- Compilation --------------------------------

def compile_program(source_path: Path, build_dir: Path) -> Path:
    build_dir.mkdir(parents=True, exist_ok=True)
    binary_path = build_dir / "healkristin"
    cmd = ["gcc", "-Wall", "-O2", "-o", str(binary_path), str(source_path)]
    print(f"  $ {' '.join(shlex.quote(a) for a in cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    if proc.returncode != 0:
        print("Compilation failed - fix the C code before testing.")
        sys.exit(1)
    return binary_path


# ---------------------------- Reference model -----------------------------

class DSU:
    """Plain union-find used ONLY to compute the correct answer, independent
    of whatever algorithm healkristin.c itself uses internally."""

    def __init__(self, n):
        self.parent = list(range(n + 1))  # 1-indexed, 0 unused

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def correct_clusters(cities, edges):
    """Returns clusters as a list of sorted lists of city ids, the list
    itself sorted by each cluster's smallest city id (per spec section 3.2)."""
    dsu = DSU(cities)
    for p, q in edges:
        dsu.union(p, q)
    groups = {}
    for c in range(1, cities + 1):
        groups.setdefault(dsu.find(c), []).append(c)
    clusters = [sorted(g) for g in groups.values()]
    clusters.sort(key=lambda g: g[0])
    return clusters


def expected_block_task1(clusters):
    return f"Task1 {len(clusters)}"


def expected_block_task2(clusters):
    lines = [f"Task2 {len(clusters)}"]
    for cl in clusters:
        lines.append("Cluster: " + " ".join(str(c) for c in cl) + " ")
    return "\n".join(lines)


# ------------------------------ Generation --------------------------------

def random_name():
    """A random, harmless base filename (letters+digits, starts with a
    letter) - used for the .quests/.map/.position basenames themselves."""
    length = random.randint(MIN_NAME_LEN, MAX_NAME_LEN)
    first = random.choice(string.ascii_lowercase)
    rest = "".join(random.choices(string.ascii_letters + string.digits, k=length - 1))
    return first + rest


def random_basenames():
    """Picks the three basenames (quests/map/position). Per the statement
    these may be equal or all different, so we exercise both."""
    if random.random() < SAME_BASENAME_PROB:
        base = random_name()
        return base, base, base
    return random_name(), random_name(), random_name()


def generate_map(cities, min_links, max_links):
    links = random.randint(min_links, max_links)
    edges = []
    if cities >= 1:
        for _ in range(links):
            p = random.randint(1, cities)
            q = random.randint(1, cities)
            edges.append((p, q))
    lines = [f"{cities} {links}"]
    for p, q in edges:
        lines.append(f"{p} {q}")
    return "\n".join(lines) + "\n", edges, links


def generate_position(cities, max_coord):
    xmax = random.randint(1, max_coord)
    ymax = random.randint(1, max_coord)
    lines = [f"{xmax} {ymax}"]
    for city in range(1, cities + 1):
        x = random.randint(1, xmax)
        y = random.randint(1, ymax)
        lines.append(f"{city} {x} {y}")
    return "\n".join(lines) + "\n"


def generate_quests(cities, selected_tasks):
    tasks = []
    for n in selected_tasks:
        if TASK_NEEDS_ARG[n]:
            arg = random.randint(1, cities) if cities >= 1 else 0
            tasks.append(f"Task{n} {arg}")
        else:
            tasks.append(f"Task{n}")
    random.shuffle(tasks)
    return "\n".join(tasks) + "\n", tasks


# ------------------------------ Execution ----------------------------------

def run_case(binary_path: Path, case_dir: Path, quests_base, map_base, position_base, use_valgrind):
    quests_f = f"{quests_base}.quests"
    map_f = f"{map_base}.map"
    position_f = f"{position_base}.position"
    # The .results file name is derived from the .quests basename, per
    # section 4 of the statement - this is exactly what we're checking.
    results_f = case_dir / f"{quests_base}.results"

    prog_argv = [str(binary_path.resolve()), quests_f, map_f, position_f]

    log_path = None
    if use_valgrind:
        log_path = case_dir / "valgrind.log"
        argv = [
            "valgrind",
            "--quiet",
            f"--error-exitcode={VALGRIND_ERROR_EXITCODE}",
            "--leak-check=full",
            "--track-origins=yes",
            f"--log-file={log_path}",
        ] + prog_argv
        timeout = VALGRIND_TIMEOUT_SEC
    else:
        argv = prog_argv
        timeout = TIMEOUT_SEC

    shell_cmd = " ".join(shlex.quote(a) for a in argv)
    print(f"  $ cd {shlex.quote(str(case_dir))} && {shell_cmd}")

    try:
        proc = subprocess.run(
            argv,
            cwd=case_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "TIMEOUT", None, "", "", log_path

    if proc.returncode < 0:
        sig = -proc.returncode
        return f"CRASH (signal {sig})", None, proc.stdout, proc.stderr, log_path

    if use_valgrind and proc.returncode == VALGRIND_ERROR_EXITCODE:
        return "VALGRIND_ERROR", None, proc.stdout, proc.stderr, log_path

    if not results_f.exists():
        return "NO_RESULTS_FILE", None, proc.stdout, proc.stderr, log_path

    return "RAN", results_f.read_text(), proc.stdout, proc.stderr, log_path


def print_valgrind_log(log_path):
    if log_path is None or not log_path.exists():
        return
    content = log_path.read_text().strip()
    if not content:
        return
    if len(content) > VALGRIND_LOG_CHARS:
        content = content[:VALGRIND_LOG_CHARS] + "\n... (truncated, see the full log file)"
    print(f"\n  valgrind report ({log_path}):")
    for line in content.splitlines():
        print(f"    {line}")


# ------------------------------- Checking -----------------------------------

def build_expected(quest_lines, clusters):
    """Builds the reference .results content for the tasks we can verify
    (Task1, Task2), in the order they appear in the .quests file, blocks
    separated by one blank line, per section 4 of the statement."""
    blocks = []
    for line in quest_lines:
        name = line.split()[0]
        if name == "Task1":
            blocks.append(expected_block_task1(clusters))
        elif name == "Task2":
            blocks.append(expected_block_task2(clusters))
        # Task3/Task4/etc: not implemented yet, nothing to check.
    return "\n\n".join(blocks)


def locate_first_diff(expected_stripped, actual_stripped):
    """Returns (line_number, expected_line_or_None, actual_line_or_None)
    for the first point where the two texts diverge, 1-indexed."""
    exp_lines = expected_stripped.splitlines()
    act_lines = actual_stripped.splitlines()
    for i, (e, a) in enumerate(zip(exp_lines, act_lines), start=1):
        if e != a:
            return i, e, a
    # one is a prefix of the other
    if len(exp_lines) != len(act_lines):
        i = min(len(exp_lines), len(act_lines)) + 1
        e = exp_lines[i - 1] if i - 1 < len(exp_lines) else None
        a = act_lines[i - 1] if i - 1 < len(act_lines) else None
        return i, e, a
    return None, None, None  # identical (shouldn't happen if caller already checked)


def check_case(actual_text, quest_lines, clusters):
    """Returns (verdict, diff_text_or_None, location_or_None).
    Compares only the Task1/Task2 content: we pull those blocks out of the
    actual output (in the order they appear) and diff them against the
    reference, so the check still works even if the file also contains
    stray/misplaced blocks - the harness will surface that misalignment as
    a mismatch. location is (line_number, expected_line, actual_line)."""
    expected = build_expected(quest_lines, clusters)

    actual_stripped = actual_text.strip("\n")
    expected_stripped = expected.strip("\n")

    if actual_stripped == expected_stripped:
        return "OK", None, None

    diff = "\n".join(
        difflib.unified_diff(
            expected_stripped.splitlines(),
            actual_stripped.splitlines(),
            fromfile="expected",
            tofile="actual",
            lineterm="",
        )
    )
    location = locate_first_diff(expected_stripped, actual_stripped)
    return "MISMATCH", diff, location


# --------------------------------- Main --------------------------------------

def main():
    args = parse_args()

    if SEED is not None:
        random.seed(SEED)

    root = Path(".").resolve()
    source_path = root / SOURCE_FILE
    if not source_path.exists():
        print(f"Can't find {SOURCE_FILE} next to this script.")
        sys.exit(1)

    binary_path = compile_program(source_path, root / BUILD_DIR)

    selected_tasks = prompt_task_selection()
    print(f"Testing tasks: {selected_tasks}\n")

    use_valgrind = args.valgrind or USE_VALGRIND_DEFAULT
    if use_valgrind and shutil.which("valgrind") is None:
        print(
            "Note: valgrind not found on PATH - skipping memory-error checks. "
            "Install it (e.g. `sudo apt install valgrind`) to enable them.\n"
        )
        use_valgrind = False
    elif not use_valgrind:
        print("valgrind checks disabled (pass -v/--valgrind to enable them).\n")

    work_dir = root / WORK_DIR
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()

    tally = {
        "OK": 0,
        "MISMATCH": 0,
        "CRASH": 0,
        "VALGRIND_ERROR": 0,
        "TIMEOUT": 0,
        "NO_RESULTS_FILE": 0,
    }
    stopped_early = False
    tests_run = 0

    for i in range(1, NUM_TESTS + 1):
        tests_run = i
        case_id = f"case{i:04d}"
        case_dir = work_dir / case_id
        case_dir.mkdir()

        quests_base, map_base, position_base = random_basenames()
        quests_path = case_dir / f"{quests_base}.quests"
        map_path = case_dir / f"{map_base}.map"
        position_path = case_dir / f"{position_base}.position"

        cities = random.randint(MIN_CITIES, MAX_CITIES)
        map_text, edges, links = generate_map(cities, MIN_LINKS, MAX_LINKS)
        position_text = generate_position(cities, MAX_COORD) if cities >= 1 else "1 1\n"
        quests_text, quest_lines = generate_quests(cities, selected_tasks)

        map_path.write_text(map_text)
        position_path.write_text(position_text)
        quests_path.write_text(quests_text)

        status, actual_text, stdout, stderr, log_path = run_case(
            binary_path, case_dir, quests_base, map_base, position_base, use_valgrind
        )

        names_note = (
            f"names: {quests_base}.quests {map_base}.map {position_base}.position"
        )
        print(f"[{case_id}] cities={cities} links={links} quests={quest_lines} ({names_note})")

        if status.startswith("CRASH") or status == "TIMEOUT":
            kind = "CRASH" if status.startswith("CRASH") else "TIMEOUT"
            tally[kind] += 1
            print(f"  -> {status}")
            if stderr.strip():
                print(f"  stderr: {stderr.strip()[:300]}")
            print_valgrind_log(log_path)
            print_failure_location(
                case_dir, quests_path, map_path, position_path, None, binary_path
            )
            stopped_early = True
            break

        if status == "VALGRIND_ERROR":
            tally["VALGRIND_ERROR"] += 1
            print("  -> VALGRIND_ERROR (memcheck found invalid reads/writes and/or leaks)")
            print_valgrind_log(log_path)
            print_failure_location(
                case_dir, quests_path, map_path, position_path, None, binary_path
            )
            stopped_early = True
            break

        if status == "NO_RESULTS_FILE":
            tally["NO_RESULTS_FILE"] += 1
            print("  -> NO RESULTS FILE produced")
            print_valgrind_log(log_path)
            print_failure_location(
                case_dir, quests_path, map_path, position_path, None, binary_path
            )
            stopped_early = True
            break

        clusters = correct_clusters(cities, edges) if cities >= 1 else []
        verdict, diff, location = check_case(actual_text, quest_lines, clusters)
        tally[verdict] += 1

        if verdict == "OK":
            print("  -> OK")
            shutil.rmtree(case_dir)  # only successful runs get cleaned up
        else:
            results_path = case_dir / f"{quests_base}.results"
            print("  -> MISMATCH")
            if VERBOSE_DIFF:
                print(diff)
            if location and location[0] is not None:
                line_no, exp_line, act_line = location
                print(f"\n  First divergence at output line {line_no}:")
                print(f"    expected: {exp_line!r}")
                print(f"    actual:   {act_line!r}")
            print_valgrind_log(log_path)
            print_failure_location(
                case_dir, quests_path, map_path, position_path, results_path, binary_path
            )
            stopped_early = True
            break

    print("\n===================== SUMMARY =====================")
    for k, v in tally.items():
        print(f"{k:16s}: {v}")
    print(f"{'tests run':16s}: {tests_run} / {NUM_TESTS} requested")
    if stopped_early:
        print("\nStopped at the first non-OK result (see the case details above).")
    else:
        print(f"\nAll {tests_run} case(s) passed - {work_dir} has been cleaned up.")
        if work_dir.exists() and not any(work_dir.iterdir()):
            work_dir.rmdir()
    print("=====================================================")


def print_failure_location(case_dir, quests_path, map_path, position_path, results_path, binary_path):
    print(f"\n  Failing case files kept at: {case_dir}")
    print(f"    quests:   {quests_path}")
    print(f"    map:      {map_path}")
    print(f"    position: {position_path}")
    if results_path is not None and results_path.exists():
        print(f"    results:  {results_path}")
    print(
        "  Reproduce with:\n"
        f"    cd {case_dir} && {binary_path.resolve()} "
        f"{quests_path.name} {map_path.name} {position_path.name}"
    )


if __name__ == "__main__":
    main()
