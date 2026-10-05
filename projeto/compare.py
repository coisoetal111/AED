#!/usr/bin/env python3
"""
compare.py

Head-to-head comparison harness for TWO "HealkrISTin" implementations
(AED, IST Lisboa). Built on the exact same input generation, reference
model (independent union-find correctness checking) and measurement
machinery as test_healkristin.py - but instead of testing one binary and
stopping at the first problem, it compiles BOTH SOURCE_FILE_A and
SOURCE_FILE_B, runs them against byte-identical generated input for every
case, times each, measures each one's peak RAM footprint ("peak storage"),
and tallies which one wins more often.

What it does, each run:
  1. Compiles both C sources (once each).
  2. For NUM_TESTS iterations (default 500 - this is a statistics-gathering
     tool, so it does NOT stop at the first failure the way
     test_healkristin.py does; it runs every requested case regardless):
       - generates ONE random .quests/.map/.position trio
       - copies that SAME content into two separate sub-folders and runs
         binary A and binary B against their own copy (so their .results
         files, named from the shared .quests basename, don't collide)
       - checks each binary's output against the independent reference
         model, for context (not used to decide the winner)
       - compares A's and B's time and peak storage for this case and
         prints a compact one-line winner summary
  3. After all cases, prints how many cases each binary won on time, on
     peak storage, and overall (time wins + storage wins combined), plus
     each binary's correctness pass rate across the session.
  4. Every case's files are deleted immediately after being compared -
     this tool is for statistics, not for keeping failing cases around to
     debug (that's what test_healkristin.py's -r/--rerun is for).

--hell mode here runs HELL_REPEATS (default 10) huge cases, same as
test_healkristin.py, but - consistent with the rest of this tool - runs
ALL of them regardless of individual failures, rather than stopping at
the first one, so you get a full comparative picture at that scale too.

Scope note: -e/--exel (the single-binary performance-sweep-to-Excel mode)
and -r/--rerun (replay-a-failed-case mode) are intentionally NOT included
here. Both are built around a single-binary workflow (one Excel file per
sweep; one replayed case) that doesn't translate cleanly to a two-binary
comparison without a genuinely different design - ask if you'd like a
two-binary version of either and I'll build it as its own thing rather
than bolt it on awkwardly.

Usage:
    python3 compare.py           compare on NUM_TESTS random cases (no valgrind)
    python3 compare.py -v        also run every case of both binaries under valgrind
    python3 compare.py --hell    compare on HELL_REPEATS huge cases instead
    python3 compare.py -h        list the flags and what they do

Everything you're likely to want to tweak (including which two source
files to compare) is in the CONFIG block below.
"""

import argparse
import difflib
import os
import random
import re
import shlex
import shutil
import signal
import string
import subprocess
import time
import sys
from pathlib import Path

# ============================== CONFIG ==================================

SOURCE_FILE_A = "healkristin.c"   # first implementation to compare
SOURCE_FILE_B = "failure_1.c"     # second implementation to compare
BUILD_DIR = "build_compare"       # where both compiled binaries go
WORK_DIR = "runs_compare"         # scratch dir, cleaned up continuously

MIN_NAME_LEN = 3        # random .quests/.map/.position base filenames are
MAX_NAME_LEN = 12        # generated with lengths in this range
SAME_BASENAME_PROB = 0.5  # chance all three files share one random base
                           # name, vs. each getting its own random name

# --- Randomisation ranges: edit these two to control test size ----------
MIN_CITIES  = 1        # smallest number of cities (C) to generate.
MAX_CITIES  = 30        # <-- set this to whatever you want to stress-test
MIN_LINKS   = 0        # smallest number of physical links (L) to generate.
MAX_LINKS   = 40        # <-- "map size"; set this too

MAX_COORD   = 50       # .position plane is randomised as Xmax,Ymax in [1, MAX_COORD]

NUM_TESTS   = 500       # how many random cases to compare this session -
                         # deliberately much higher than
                         # test_healkristin.py's default (25), since this
                         # is a statistics-gathering tool, not a
                         # stop-at-first-bug debugging tool
TIMEOUT_SEC = 5          # kill a run that hangs longer than this (seconds)
SEED        = None       # int for reproducible runs, or None for fresh randomness

USE_VALGRIND_DEFAULT = False  # overridden by the -v/--valgrind CLI flag
VALGRIND_TIMEOUT_SEC = 20    # valgrind is much slower than a native run
VALGRIND_ERROR_EXITCODE = 99 # sentinel exit code valgrind returns when it
                              # found errors (invalid reads/writes, leaks, ...)
VALGRIND_LOG_CHARS = 4000    # truncate a very long valgrind report when printing

ALL_TASKS = [1, 2, 3, 4, 5, 6]           # tasks defined in the statement
TASK_NEEDS_ARG = {1: False, 2: False, 3: True, 4: True, 5: False, 6: True}
CHECKABLE_TASKS = {1, 2, 3}              # tasks this harness knows how to grade

MIN_TASK_REPEATS = 1   # a selected task line may appear this many times...
MAX_TASK_REPEATS = 3   # ...up to this many times in one .quests file, each
                        # occurrence with its own random argument.

# --- --hell mode: absolutely huge cases ------------------------------------
HELL_REPEATS = 10           # how many huge cases to compare (edit freely) -
                             # ALL of them run regardless of failures, unlike
                             # test_healkristin.py's stop-at-first-failure
HELL_MIN_CITIES = 20_000    # "tens of thousands of cities"
HELL_MAX_CITIES = 50_000
HELL_MIN_LINKS  = 100_000   # "hundreds of thousands of links"
HELL_MAX_LINKS  = 400_000
HELL_MAX_COORD  = 1_000_000_000
HELL_TIMEOUT_SEC = 120
HELL_VALGRIND_TIMEOUT_SEC = 900

WINDOWS_MAX_COMPONENT_LEN = 255
EXT_QUESTS, EXT_MAP, EXT_POSITION, EXT_RESULTS = ".quests", ".map", ".position", ".results"

# --- peak storage (peak RAM footprint) tracking ----------------------------
# Same meaning as in test_healkristin.py: the process's peak resident
# memory, read via os.wait4()'s rusage at reap time (exact, not sampled).
# Blocked entirely under -v/--valgrind, same as the other script, since
# valgrind's own overhead makes the number meaningless as a measure of
# the target program - that also means time/storage "wins" under -v
# should be read as "which ran under valgrind faster/leaner", not as a
# measure of the programs' own native performance.
STORAGE_WARN_MB = 90

TIMEOUT_POLL_INTERVAL = 0.001  # how often we check whether a case has
                                # finished yet, to enforce our own timeout
                                # (the actual peak-RSS reading itself is a
                                # single exact value from the kernel at
                                # reap time, via os.wait4 - no sampling)

# ==========================================================================


# -------------------------------- CLI flags ---------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        prog="compare.py",
        description="Head-to-head comparison harness for two HealkrISTin implementations.",
    )
    parser.add_argument(
        "-v", "--valgrind",
        action="store_true",
        help=(
            "also run every case of BOTH binaries under valgrind's memcheck "
            "(invalid reads/writes, leaks). Off by default, since it's much "
            "slower. Ignored (with a warning) if valgrind isn't installed. "
            "Blocks the peak-storage warning/comparison entirely, since "
            "valgrind's own overhead makes that number meaningless."
        ),
    )
    parser.add_argument(
        "--hell",
        action="store_true",
        help=(
            "compare on HELL_REPEATS (default 10) huge cases instead of "
            "NUM_TESTS normal ones - tens of thousands of cities, hundreds "
            "of thousands of links, filenames at the Windows/NTFS "
            "255-character limit. Unlike test_healkristin.py, ALL repeats "
            "run regardless of individual failures (this tool gathers "
            "statistics, it doesn't stop to debug one case)."
        ),
    )
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

def compile_program(source_path: Path, build_dir: Path, binary_name: str) -> Path:
    build_dir.mkdir(parents=True, exist_ok=True)
    binary_path = build_dir / binary_name
    cmd = ["gcc", "-Wall", "-O2", "-o", str(binary_path), str(source_path), "-lm"]
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


def city_to_cluster_map(clusters):
    """Maps each city id to the index of the cluster (in `clusters`) it
    belongs to, so membership can be checked in O(1) instead of scanning
    every cluster list."""
    mapping = {}
    for idx, cl in enumerate(clusters):
        for c in cl:
            mapping[c] = idx
    return mapping


def closest_outside_cluster(cities, clusters, positions, ref):
    """Reference solution for Task3: nearest city (by squared Euclidean
    distance, which preserves ordering without needing floats/rounding)
    that is NOT in the same cluster as `ref`. Returns -2 for the "problema
    mal definido" cases from section 4.1 (bad ref city, or only one
    cluster in the whole map). Ties are broken by smallest city id, which
    matches the natural result of scanning cities in increasing order and
    only replacing the best candidate on a strictly smaller distance."""
    if ref < 1 or ref > cities:
        return -2
    cluster_of = city_to_cluster_map(clusters)
    ref_cluster = cluster_of[ref]
    rx, ry = positions[ref]
    best_city, best_dist2 = None, None
    for c in range(1, cities + 1):
        if cluster_of[c] == ref_cluster:
            continue
        x, y = positions[c]
        d2 = (x - rx) ** 2 + (y - ry) ** 2
        if best_dist2 is None or d2 < best_dist2:
            best_dist2 = d2
            best_city = c
    return best_city if best_city is not None else -2


def expected_block_task3(clusters, positions, cities, arg):
    ans = closest_outside_cluster(cities, clusters, positions, arg)
    return f"Task3 {arg} {ans}"


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


def hell_random_name(length):
    """Same shape as random_name(), but with an exact requested length."""
    first = random.choice(string.ascii_lowercase)
    rest = "".join(random.choices(string.ascii_letters + string.digits, k=length - 1))
    return first + rest


def hell_basenames():
    """One basename per file (never shared), each sized so its filename
    lands exactly at the 255-character Windows/NTFS limit - as long as a
    name can legally be without tipping over it."""
    quests_len = WINDOWS_MAX_COMPONENT_LEN - max(len(EXT_QUESTS), len(EXT_RESULTS))
    map_len = WINDOWS_MAX_COMPONENT_LEN - len(EXT_MAP)
    position_len = WINDOWS_MAX_COMPONENT_LEN - len(EXT_POSITION)
    return (
        hell_random_name(quests_len),
        hell_random_name(map_len),
        hell_random_name(position_len),
    )


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
    positions = {}
    for city in range(1, cities + 1):
        x = random.randint(1, xmax)
        y = random.randint(1, ymax)
        positions[city] = (x, y)
        lines.append(f"{city} {x} {y}")
    return "\n".join(lines) + "\n", positions


def generate_quests(cities, selected_tasks):
    tasks = []
    for n in selected_tasks:
        repeats = random.randint(MIN_TASK_REPEATS, MAX_TASK_REPEATS)
        for _ in range(repeats):
            if TASK_NEEDS_ARG[n]:
                arg = random.randint(1, cities) if cities >= 1 else 0
                tasks.append(f"Task{n} {arg}")
            else:
                tasks.append(f"Task{n}")
    random.shuffle(tasks)
    return "\n".join(tasks) + "\n", tasks


# ------------------------------ Execution ----------------------------------

FORK_AVAILABLE = hasattr(os, "fork") and hasattr(os, "wait4")  # POSIX only


def fork_exec_with_rusage(argv, cwd, timeout, stdout_path, stderr_path):
    """Runs argv as a child process and returns (returncode, peak_kb,
    timed_out). peak_kb comes from os.wait4()'s rusage.ru_maxrss, which the
    kernel accumulates over the CHILD'S ENTIRE LIFETIME and reports exactly
    at reap time - unlike polling /proc/<pid>/status, this can't miss a
    short-lived process's peak no matter how fast it exits. POSIX only
    (guarded by FORK_AVAILABLE; callers fall back to peak_kb=None elsewhere)."""
    pid = os.fork()
    if pid == 0:
        # child: redirect stdio, exec - any failure here just exits 127
        try:
            os.chdir(cwd)
            out_fd = os.open(str(stdout_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
            err_fd = os.open(str(stderr_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
            os.dup2(out_fd, 1)
            os.dup2(err_fd, 2)
            os.close(out_fd)
            os.close(err_fd)
            os.execvp(argv[0], argv)
        except Exception:
            pass
        os._exit(127)

    # parent: poll non-blockingly so we can enforce our own timeout
    start = time.perf_counter()
    while True:
        wpid, status, usage = os.wait4(pid, os.WNOHANG)
        if wpid != 0:
            break
        if time.perf_counter() - start > timeout:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _, status, usage = os.wait4(pid, 0)
            peak_kb = usage.ru_maxrss if usage else None
            return None, peak_kb, True
        time.sleep(TIMEOUT_POLL_INTERVAL)

    peak_kb = usage.ru_maxrss if usage else None
    if os.WIFSIGNALED(status):
        returncode = -os.WTERMSIG(status)
    else:
        returncode = os.WEXITSTATUS(status)
    return returncode, peak_kb, False


def run_case(binary_path: Path, case_dir: Path, quests_base, map_base, position_base,
             use_valgrind, timeout_override=None):
    quests_f = f"{quests_base}.quests"
    map_f = f"{map_base}.map"
    position_f = f"{position_base}.position"
    # The .results file name is derived from the .quests basename, per
    # section 4 of the statement - this is exactly what we're checking.
    results_f = case_dir / f"{quests_base}.results"

    log_path = case_dir / "valgrind.log" if use_valgrind else None
    argv = build_argv(binary_path, quests_f, map_f, position_f, use_valgrind, log_path)
    timeout = timeout_override
    if timeout is None:
        timeout = VALGRIND_TIMEOUT_SEC if use_valgrind else TIMEOUT_SEC

    shell_cmd = " ".join(shlex.quote(a) for a in argv)
    print(f"  $ cd {shlex.quote(str(case_dir))} && {shell_cmd}")

    stdout_path = case_dir / "._stdout.tmp"
    stderr_path = case_dir / "._stderr.tmp"
    t0 = time.perf_counter()

    if FORK_AVAILABLE:
        returncode, peak_kb, timed_out = fork_exec_with_rusage(
            argv, case_dir, timeout, stdout_path, stderr_path
        )
    else:
        # non-POSIX fallback (e.g. native Windows Python): no peak-memory
        # reading available, but everything else still works.
        try:
            proc = subprocess.run(
                argv, cwd=case_dir, capture_output=False, timeout=timeout,
                stdout=open(stdout_path, "w"), stderr=open(stderr_path, "w"),
            )
            returncode, peak_kb, timed_out = proc.returncode, None, False
        except subprocess.TimeoutExpired:
            returncode, peak_kb, timed_out = None, None, True

    elapsed = time.perf_counter() - t0
    peak_mb = peak_kb / 1024 if peak_kb is not None else None
    stdout = stdout_path.read_text() if stdout_path.exists() else ""
    stderr = stderr_path.read_text() if stderr_path.exists() else ""
    _cleanup_tmp(stdout_path, stderr_path)

    if timed_out:
        return "TIMEOUT", None, stdout, stderr, log_path, elapsed, peak_mb

    if returncode < 0:
        sig = -returncode
        return f"CRASH (signal {sig})", None, stdout, stderr, log_path, elapsed, peak_mb

    if use_valgrind and returncode == VALGRIND_ERROR_EXITCODE:
        return "VALGRIND_ERROR", None, stdout, stderr, log_path, elapsed, peak_mb

    if not results_f.exists():
        return "NO_RESULTS_FILE", None, stdout, stderr, log_path, elapsed, peak_mb

    return "RAN", results_f.read_text(), stdout, stderr, log_path, elapsed, peak_mb


def _cleanup_tmp(*paths):
    for p in paths:
        try:
            p.unlink()
        except FileNotFoundError:
            pass


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

def build_expected(quest_lines, clusters, positions, cities):
    """Builds the reference .results content for the tasks we can verify
    (Task1, Task2, Task3), in the order they appear in the .quests file,
    blocks separated by one blank line, per section 4 of the statement."""
    blocks = []
    for line in quest_lines:
        parts = line.split()
        name = parts[0]
        if name == "Task1":
            blocks.append(expected_block_task1(clusters))
        elif name == "Task2":
            blocks.append(expected_block_task2(clusters))
        elif name == "Task3":
            arg = int(parts[1])
            blocks.append(expected_block_task3(clusters, positions, cities, arg))
        # Task4/5/6: not implemented yet, nothing to check.
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


def _split_blocks(text):
    """Splits already-stripped .results text into per-task blocks, on the
    blank-line separators the statement mandates between tasks (tolerant
    of trailing whitespace on the blank line itself)."""
    if not text:
        return []
    return re.split(r"\n[ \t]*\n", text)


def _task_number(quest_line):
    return int(quest_line.split()[0][4:])  # "Task12 x" -> 12


def check_case(actual_text, quest_lines, clusters, positions, cities):
    """Returns (verdict, diff_text_or_None, location_or_None).
    Only Task1/Task2/Task3 (CHECKABLE_TASKS) are graded. A program that
    also implements Task4/5/6 legitimately emits extra blocks for those,
    so - unlike a naive whole-file compare - we split the actual output
    into one block per line of the .quests file (blank-line separated, as
    required by section 4) and keep only the blocks whose corresponding
    .quests line is a checkable task, before comparing against the
    reference. If the block count doesn't match the number of .quests
    lines, we can't safely align them - that's reported as its own
    mismatch rather than risking a bogus line-by-line diff. location is
    (line_number, expected_line, actual_line)."""
    expected = build_expected(quest_lines, clusters, positions, cities)
    expected_stripped = expected.strip("\n")

    actual_stripped = actual_text.strip("\n")
    actual_blocks = _split_blocks(actual_stripped)

    if len(actual_blocks) != len(quest_lines):
        diff = "\n".join(
            difflib.unified_diff(
                expected_stripped.splitlines(),
                actual_stripped.splitlines(),
                fromfile="expected (checkable tasks only)",
                tofile="actual (full .results, RAW - block count mismatch)",
                lineterm="",
            )
        )
        note = (
            f"NOTE: expected {len(quest_lines)} blank-line-separated blocks "
            f"(one per .quests line) but the .results file has "
            f"{len(actual_blocks)}. Showing the raw file below instead of "
            "a filtered comparison, since blocks can't be safely matched "
            "up to .quests lines when the counts differ."
        )
        return "MISMATCH", note + "\n\n" + diff, None

    actual_checkable_blocks = [
        block for block, line in zip(actual_blocks, quest_lines)
        if _task_number(line) in CHECKABLE_TASKS
    ]
    actual_filtered = "\n\n".join(actual_checkable_blocks)

    if actual_filtered == expected_stripped:
        return "OK", None, None

    diff = "\n".join(
        difflib.unified_diff(
            expected_stripped.splitlines(),
            actual_filtered.splitlines(),
            fromfile="expected",
            tofile="actual (Task4/5/6 blocks excluded - not graded)",
            lineterm="",
        )
    )
    location = locate_first_diff(expected_stripped, actual_filtered)
    return "MISMATCH", diff, location


# --------------------------------- Main --------------------------------------

def format_storage_suffix(peak_mb, use_valgrind):
    if peak_mb is None:
        return "peak storage: n/a (not supported on this platform)"
    note = " (includes valgrind's own overhead)" if use_valgrind else ""
    return f"peak storage: {peak_mb:.2f} MB{note}"


def print_storage_warning(peak_mb, use_valgrind=False):
    # Blocked entirely under valgrind: its own instrumentation overhead
    # inflates peak RSS by itself, so the number no longer reflects the
    # target program and a threshold check on it would be meaningless.
    if use_valgrind:
        return
    if peak_mb is None or peak_mb <= STORAGE_WARN_MB:
        return
    print("  " + "!" * 62)
    print(f"  !!! WARNING: peak storage usage was {peak_mb:.2f} MB "
          f"(over {STORAGE_WARN_MB} MB) !!!")
    print("  " + "!" * 62)


def build_argv(binary_path, quests_f, map_f, position_f, use_valgrind, log_path=None):
    """Builds the exact argv used to run one case against one binary,
    optionally wrapped in valgrind."""
    prog_argv = [str(binary_path.resolve()), quests_f, map_f, position_f]
    if not use_valgrind:
        return prog_argv
    return [
        "valgrind",
        "--quiet",
        f"--error-exitcode={VALGRIND_ERROR_EXITCODE}",
        "--leak-check=full",
        "--track-origins=yes",
    ] + ([f"--log-file={log_path}"] if log_path is not None else []) + prog_argv

# --------------------------------- Compare ------------------------------------

def run_one_side(binary_path, case_dir, quests_base, map_base, position_base,
                  use_valgrind, timeout, cities, edges, quest_lines, positions):
    """Runs one binary against one case and returns a small result dict:
    status (raw execution outcome), verdict (OK/MISMATCH when it actually
    ran, else same as status), elapsed, peak_mb, log_path."""
    status, actual_text, stdout, stderr, log_path, elapsed, peak_mb = run_case(
        binary_path, case_dir, quests_base, map_base, position_base,
        use_valgrind, timeout_override=timeout,
    )

    if status == "RAN":
        clusters = correct_clusters(cities, edges) if cities >= 1 else []
        verdict, diff, location = check_case(actual_text, quest_lines, clusters, positions, cities)
    else:
        kind = "CRASH" if status.startswith("CRASH") else status
        verdict = kind

    return {
        "status": status,
        "verdict": verdict,
        "elapsed": elapsed,
        "peak_mb": peak_mb,
        "log_path": log_path,
        "stderr": stderr,
    }


def compare_one_case(binary_a, binary_b, case_dir, quests_base, map_base, position_base,
                      use_valgrind, timeout, cities, edges, quest_lines, positions,
                      label_a, label_b):
    """Runs both binaries against byte-identical copies of the same case
    (in case_dir/'A' and case_dir/'B'), prints one compact summary line,
    and returns (result_a, result_b, time_winner, storage_winner) where
    the winners are 'A', 'B', 'tie', or None (storage only: blocked under
    valgrind, or unmeasurable on this platform)."""
    dir_a = case_dir / "A"
    dir_b = case_dir / "B"
    dir_a.mkdir(parents=True, exist_ok=True)
    dir_b.mkdir(parents=True, exist_ok=True)

    result_a = run_one_side(
        binary_a, dir_a, quests_base, map_base, position_base,
        use_valgrind, timeout, cities, edges, quest_lines, positions,
    )
    result_b = run_one_side(
        binary_b, dir_b, quests_base, map_base, position_base,
        use_valgrind, timeout, cities, edges, quest_lines, positions,
    )

    # time winner
    if result_a["elapsed"] is None or result_b["elapsed"] is None:
        time_winner = None
    elif result_a["elapsed"] < result_b["elapsed"]:
        time_winner = "A"
    elif result_b["elapsed"] < result_a["elapsed"]:
        time_winner = "B"
    else:
        time_winner = "tie"

    # storage winner - blocked entirely under valgrind
    if use_valgrind:
        storage_winner = None
    elif result_a["peak_mb"] is None or result_b["peak_mb"] is None:
        storage_winner = None
    elif result_a["peak_mb"] < result_b["peak_mb"]:
        storage_winner = "A"
    elif result_b["peak_mb"] < result_a["peak_mb"]:
        storage_winner = "B"
    else:
        storage_winner = "tie"

    def fmt_side(label, r):
        time_s = f"{r['elapsed']:.4f}s" if r["elapsed"] is not None else "n/a"
        if use_valgrind:
            storage_s = "storage blocked (-v)"
        elif r["peak_mb"] is not None:
            storage_s = f"{r['peak_mb']:.2f}MB"
            if r["peak_mb"] > STORAGE_WARN_MB:
                storage_s += "(!)"
        else:
            storage_s = "n/a"
        return f"{label}: {r['verdict']:<12} {time_s:>10} {storage_s:>14}"

    winners_bit = f"time:{time_winner or 'n/a'} storage:{storage_winner or 'n/a'}"
    print(f"  {fmt_side(label_a, result_a)} | {fmt_side(label_b, result_b)} | {winners_bit}")

    for label, result in ((label_a, result_a), (label_b, result_b)):
        if result["verdict"] == "VALGRIND_ERROR":
            print(f"  -- {label} valgrind report --")
            print_valgrind_log(result["log_path"])

    return result_a, result_b, time_winner, storage_winner


def new_tally():
    return {
        "cases_run": 0,
        "status_counts_a": {},
        "status_counts_b": {},
        "time_wins": {"A": 0, "B": 0, "tie": 0},
        "storage_wins": {"A": 0, "B": 0, "tie": 0},
        "storage_comparable": 0,
    }


def record_tally(tally, result_a, result_b, time_winner, storage_winner):
    tally["cases_run"] += 1
    tally["status_counts_a"][result_a["verdict"]] = tally["status_counts_a"].get(result_a["verdict"], 0) + 1
    tally["status_counts_b"][result_b["verdict"]] = tally["status_counts_b"].get(result_b["verdict"], 0) + 1
    if time_winner is not None:
        tally["time_wins"][time_winner] += 1
    if storage_winner is not None:
        tally["storage_wins"][storage_winner] += 1
        tally["storage_comparable"] += 1


def print_final_summary(tally, label_a, label_b, use_valgrind):
    n = tally["cases_run"]
    print("\n===================== SUMMARY =====================")
    print(f"cases compared: {n}\n")

    print(f"Correctness ({label_a}):")
    for k, v in sorted(tally["status_counts_a"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:16s}: {v}")
    print(f"\nCorrectness ({label_b}):")
    for k, v in sorted(tally["status_counts_b"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:16s}: {v}")

    tw = tally["time_wins"]
    print(f"\nTime wins   - {label_a}: {tw['A']}   {label_b}: {tw['B']}   tie: {tw['tie']}")

    if use_valgrind:
        print("Storage wins - blocked under -v/--valgrind (not comparable)")
    else:
        sw = tally["storage_wins"]
        print(f"Storage wins - {label_a}: {sw['A']}   {label_b}: {sw['B']}   tie: {sw['tie']}"
              f"  (of {tally['storage_comparable']} comparable case(s))")

    score_a = tw["A"] + (0 if use_valgrind else tally["storage_wins"]["A"])
    score_b = tw["B"] + (0 if use_valgrind else tally["storage_wins"]["B"])
    print(f"\nOverall (time wins + storage wins combined):")
    print(f"  {label_a}: {score_a}")
    print(f"  {label_b}: {score_b}")
    if score_a > score_b:
        print(f"  -> {label_a} wins overall")
    elif score_b > score_a:
        print(f"  -> {label_b} wins overall")
    else:
        print("  -> overall tie")
    print("=====================================================")


def run_normal_compare(binary_a, binary_b, work_dir, selected_tasks, use_valgrind, label_a, label_b):
    timeout = VALGRIND_TIMEOUT_SEC if use_valgrind else TIMEOUT_SEC
    tally = new_tally()

    for i in range(1, NUM_TESTS + 1):
        case_id = f"case{i:05d}"
        case_dir = work_dir / case_id

        quests_base, map_base, position_base = random_basenames()
        cities = random.randint(MIN_CITIES, MAX_CITIES)
        map_text, edges, links = generate_map(cities, MIN_LINKS, MAX_LINKS)
        if cities >= 1:
            position_text, positions = generate_position(cities, MAX_COORD)
        else:
            position_text, positions = "1 1\n", {}
        quests_text, quest_lines = generate_quests(cities, selected_tasks)

        for side_dir in (case_dir / "A", case_dir / "B"):
            side_dir.mkdir(parents=True, exist_ok=True)
            (side_dir / f"{quests_base}.quests").write_text(quests_text)
            (side_dir / f"{map_base}.map").write_text(map_text)
            (side_dir / f"{position_base}.position").write_text(position_text)

        print(f"[{case_id}] cities={cities} links={links} quests={quest_lines}")
        result_a, result_b, time_winner, storage_winner = compare_one_case(
            binary_a, binary_b, case_dir, quests_base, map_base, position_base,
            use_valgrind, timeout, cities, edges, quest_lines, positions,
            label_a, label_b,
        )
        record_tally(tally, result_a, result_b, time_winner, storage_winner)

        shutil.rmtree(case_dir)

    print_final_summary(tally, label_a, label_b, use_valgrind)


def run_hell_compare(binary_a, binary_b, work_dir, selected_tasks, use_valgrind, label_a, label_b):
    timeout = HELL_VALGRIND_TIMEOUT_SEC if use_valgrind else HELL_TIMEOUT_SEC
    tally = new_tally()

    print("=====================================================")
    print(f"HELL COMPARE: {HELL_REPEATS} huge case(s), all run regardless of failures")
    print(f"  cities target range   : [{HELL_MIN_CITIES}, {HELL_MAX_CITIES}]")
    print(f"  links target range    : [{HELL_MIN_LINKS}, {HELL_MAX_LINKS}]")
    print(f"  coordinate range      : [1, {HELL_MAX_COORD}]")
    print(f"  timeout per binary    : {timeout}s")
    print("=====================================================\n")

    for rep in range(1, HELL_REPEATS + 1):
        case_id = f"hell{rep:02d}"
        case_dir = work_dir / case_id

        cities = random.randint(HELL_MIN_CITIES, HELL_MAX_CITIES)
        quests_base, map_base, position_base = hell_basenames()

        print(f"----- hell case {rep}/{HELL_REPEATS}: generating (cities target ~{cities}) -----")
        map_text, edges, links = generate_map(cities, HELL_MIN_LINKS, HELL_MAX_LINKS)
        position_text, positions = generate_position(cities, HELL_MAX_COORD)
        quests_text, quest_lines = generate_quests(cities, selected_tasks)

        for side_dir in (case_dir / "A", case_dir / "B"):
            side_dir.mkdir(parents=True, exist_ok=True)
            (side_dir / f"{quests_base}.quests").write_text(quests_text)
            (side_dir / f"{map_base}.map").write_text(map_text)
            (side_dir / f"{position_base}.position").write_text(position_text)

        print(f"  cities={cities} links={links}")
        result_a, result_b, time_winner, storage_winner = compare_one_case(
            binary_a, binary_b, case_dir, quests_base, map_base, position_base,
            use_valgrind, timeout, cities, edges, quest_lines, positions,
            label_a, label_b,
        )
        record_tally(tally, result_a, result_b, time_winner, storage_winner)

        shutil.rmtree(case_dir)

    print_final_summary(tally, label_a, label_b, use_valgrind)


def main():
    args = parse_args()

    if SEED is not None:
        random.seed(SEED)

    root = Path(".").resolve()
    source_a = root / SOURCE_FILE_A
    source_b = root / SOURCE_FILE_B
    for sf in (source_a, source_b):
        if not sf.exists():
            print(f"Can't find {sf.name} next to this script.")
            sys.exit(1)

    build_dir = root / BUILD_DIR
    print(f"Compiling {SOURCE_FILE_A} ...")
    binary_a = compile_program(source_a, build_dir, "binary_a")
    print(f"Compiling {SOURCE_FILE_B} ...")
    binary_b = compile_program(source_b, build_dir, "binary_b")
    label_a, label_b = SOURCE_FILE_A, SOURCE_FILE_B

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

    if args.hell:
        run_hell_compare(binary_a, binary_b, work_dir, selected_tasks, use_valgrind, label_a, label_b)
    else:
        print(f"Comparing on {NUM_TESTS} random case(s)...\n")
        run_normal_compare(binary_a, binary_b, work_dir, selected_tasks, use_valgrind, label_a, label_b)

    if work_dir.exists() and not any(work_dir.iterdir()):
        work_dir.rmdir()


if __name__ == "__main__":
    main()
