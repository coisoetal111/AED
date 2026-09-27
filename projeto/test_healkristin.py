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
    python3 test_healkristin.py --hell    one single, gigantic stress case
                                           (tens of thousands of cities,
                                           hundreds of thousands of links,
                                           filenames right at the Windows
                                           255-character filename limit)
                                           instead of NUM_TESTS normal ones
    python3 test_healkristin.py -e        performance sweep: times the binary
                                           across a fixed, growing sequence of
                                           sizes and writes an Excel workbook
                                           of tables/charts (opened for you
                                           when it's done) - see EXEL_* below
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
import re
import shlex
import shutil
import string
import subprocess
import time
import sys
from pathlib import Path

# ============================== CONFIG ==================================

SOURCE_FILE = "healkristin.c"     # path to the C source to compile
BUILD_DIR   = "build"             # where the compiled binary goes
WORK_DIR    = "runs"              # scratch dir, one subfolder per test

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

NUM_TESTS   = 25        # how many random cases to run this session
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
CHECKABLE_TASKS = {1, 2, 3}              # tasks this harness knows how to grade

MIN_TASK_REPEATS = 1   # a selected task line may appear this many times...
MAX_TASK_REPEATS = 3   # ...up to this many times in one .quests file, each
                        # occurrence with its own random argument (e.g. two
                        # different "Task3 <city>" queries in the same run) -
                        # this is legal per the statement and worth fuzzing,
                        # especially for the argument-taking tasks (3/4/6).

# --- --hell mode: one single, absolutely huge case ------------------------
HELL_MIN_CITIES = 20_000    # "tens of thousands of cities"
HELL_MAX_CITIES = 50_000
HELL_MIN_LINKS  = 100_000   # "hundreds of thousands of links"
HELL_MAX_LINKS  = 400_000
HELL_MAX_COORD  = 1_000_000_000  # huge coordinate range -> a much heavier
                                   # .position file (one line per city, with
                                   # up to 10-digit numbers on each line)
HELL_TIMEOUT_SEC = 120            # native run gets a lot more time...
HELL_VALGRIND_TIMEOUT_SEC = 900   # ...and even more under valgrind, which
                                   # will be dramatically slower at this size

# Windows/NTFS allows at most 255 characters in a single filename component
# (this applies per path segment, separately from the older 260-char
# MAX_PATH limit on the full path). Hell mode sizes each basename so the
# resulting filename lands EXACTLY at that limit - as long as a name can
# legally be. The .quests basename also has to leave room for the derived
# ".results" file (8 chars, one longer than ".quests" itself), or the
# .results file the program creates would itself be one character too long.
WINDOWS_MAX_COMPONENT_LEN = 255
EXT_QUESTS, EXT_MAP, EXT_POSITION, EXT_RESULTS = ".quests", ".map", ".position", ".results"

# --- -e/--exel mode: timed performance sweep ------------------------------
# One fixed, growing sequence of sizes (cities == links at every point):
#   10 -> 50   step 5     (10,15,...,50)
#   60 -> 200  step 10    (60,70,...,200)
#   300 -> 1000 step 100  (300,400,...,1000)
#   2000 -> 50000 step 1000 (2000,3000,...,50000)
# The .quests content is fixed (built once from your task selection, with
# every argument-taking task pinned to city 1, which always exists) and
# reused byte-for-byte at every size AND every repeat, and the .map/.position
# content for a given size is also generated only once and reused across
# every repeat - so "run 1", "run 2", ... "run N" are always timing the exact
# same input, isolating run-to-run system noise rather than data variance.
EXEL_MAX_COORD = 1000        # .position plane for the sweep (doesn't need to
                              # be gigantic here - HELL_MAX_COORD covers that)
EXEL_TIMEOUT_SEC = 60         # per-execution timeout during the sweep
EXEL_DEFAULT_REPEATS = 5      # used when the user just presses Enter
EXEL_MAX_OBJECTS_PER_SHEET = 10  # a table + its chart = 2 objects per run,
                                  # so at most 5 runs' worth per sheet/"Page"

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
    parser.add_argument(
        "--hell",
        action="store_true",
        help=(
            "stress-test absolute limits instead of the normal suite: one "
            "single case with tens of thousands of cities, hundreds of "
            "thousands of links, a huge .position file, and filenames sized "
            "right up to the Windows/NTFS 255-character filename limit. "
            "Can be combined with -v, but that will be very slow."
        ),
    )
    parser.add_argument(
        "-e", "--exel",
        action="store_true",
        help=(
            "performance sweep instead of the normal suite: times the binary "
            "across a fixed, growing sequence of sizes (10 up to 50000), "
            "repeated a number of times you choose, and writes an Excel "
            "workbook of per-run tables/charts, opened automatically when "
            "done. Ignores -v (valgrind would swamp the timing)."
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

def run_case(binary_path: Path, case_dir: Path, quests_base, map_base, position_base,
             use_valgrind, timeout_override=None):
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
    if timeout_override is not None:
        timeout = timeout_override

    shell_cmd = " ".join(shlex.quote(a) for a in argv)
    print(f"  $ cd {shlex.quote(str(case_dir))} && {shell_cmd}")

    try:
        t0 = time.perf_counter()
        proc = subprocess.run(
            argv,
            cwd=case_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.perf_counter() - t0
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - t0
        return "TIMEOUT", None, "", "", log_path, elapsed

    if proc.returncode < 0:
        sig = -proc.returncode
        return f"CRASH (signal {sig})", None, proc.stdout, proc.stderr, log_path, elapsed

    if use_valgrind and proc.returncode == VALGRIND_ERROR_EXITCODE:
        return "VALGRIND_ERROR", None, proc.stdout, proc.stderr, log_path, elapsed

    if not results_f.exists():
        return "NO_RESULTS_FILE", None, proc.stdout, proc.stderr, log_path, elapsed

    return "RAN", results_f.read_text(), proc.stdout, proc.stderr, log_path, elapsed


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

def run_and_report_case(binary_path, case_dir, quests_path, map_path, position_path,
                         quests_base, map_base, position_base,
                         cities, edges, quest_lines, positions,
                         use_valgrind, timeout_override=None):
    """Runs one case, prints its outcome, and on anything other than OK
    prints the diagnostic block (diff/location/valgrind log/repro command).
    Returns one of the tally keys: OK / MISMATCH / CRASH / VALGRIND_ERROR /
    TIMEOUT / NO_RESULTS_FILE."""
    status, actual_text, stdout, stderr, log_path, elapsed = run_case(
        binary_path, case_dir, quests_base, map_base, position_base,
        use_valgrind, timeout_override=timeout_override,
    )

    if status.startswith("CRASH") or status == "TIMEOUT":
        kind = "CRASH" if status.startswith("CRASH") else "TIMEOUT"
        print(f"  -> {status}  (time: {elapsed:.4f}s)")
        if stderr.strip():
            print(f"  stderr: {stderr.strip()[:300]}")
        print_valgrind_log(log_path)
        print_failure_location(
            case_dir, quests_path, map_path, position_path, None, binary_path
        )
        return kind

    if status == "VALGRIND_ERROR":
        print(f"  -> VALGRIND_ERROR (memcheck found invalid reads/writes and/or leaks)  (time: {elapsed:.4f}s)")
        print_valgrind_log(log_path)
        print_failure_location(
            case_dir, quests_path, map_path, position_path, None, binary_path
        )
        return "VALGRIND_ERROR"

    if status == "NO_RESULTS_FILE":
        print(f"  -> NO RESULTS FILE produced  (time: {elapsed:.4f}s)")
        print_valgrind_log(log_path)
        print_failure_location(
            case_dir, quests_path, map_path, position_path, None, binary_path
        )
        return "NO_RESULTS_FILE"

    clusters = correct_clusters(cities, edges) if cities >= 1 else []
    verdict, diff, location = check_case(actual_text, quest_lines, clusters, positions, cities)

    if verdict == "OK":
        print(f"  -> OK  (time: {elapsed:.4f}s)")
    else:
        results_path = case_dir / f"{quests_base}.results"
        print(f"  -> MISMATCH  (time: {elapsed:.4f}s)")
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
    return verdict


def run_hell_mode(binary_path, work_dir, selected_tasks, use_valgrind):
    cities = random.randint(HELL_MIN_CITIES, HELL_MAX_CITIES)
    timeout = HELL_VALGRIND_TIMEOUT_SEC if use_valgrind else HELL_TIMEOUT_SEC

    print("=====================================================")
    print("HELL MODE: one absolutely huge case")
    print(f"  cities target range   : [{HELL_MIN_CITIES}, {HELL_MAX_CITIES}]")
    print(f"  links target range    : [{HELL_MIN_LINKS}, {HELL_MAX_LINKS}]")
    print(f"  coordinate range      : [1, {HELL_MAX_COORD}]")
    print(f"  filenames sized to    : {WINDOWS_MAX_COMPONENT_LEN}-char Windows/NTFS limit")
    print(f"  timeout               : {timeout}s")
    print("=====================================================\n")

    case_dir = work_dir / "hell_case"
    case_dir.mkdir()

    quests_base, map_base, position_base = hell_basenames()
    quests_path = case_dir / f"{quests_base}.quests"
    map_path = case_dir / f"{map_base}.map"
    position_path = case_dir / f"{position_base}.position"
    for label, base, path in (
        ("quests", quests_base, quests_path),
        ("map", map_base, map_path),
        ("position", position_base, position_path),
    ):
        print(f"  {label} filename: {len(path.name)} chars -> {path.name}")

    print("\nGenerating map...")
    map_text, edges, links = generate_map(cities, HELL_MIN_LINKS, HELL_MAX_LINKS)
    print("Generating position...")
    position_text, positions = generate_position(cities, HELL_MAX_COORD)
    print("Generating quests...")
    quests_text, quest_lines = generate_quests(cities, selected_tasks)

    map_path.write_text(map_text)
    position_path.write_text(position_text)
    quests_path.write_text(quests_text)
    print(
        f"Actual sizes: cities={cities} links={links} "
        f".map={map_path.stat().st_size:,}B "
        f".position={position_path.stat().st_size:,}B\n"
    )

    verdict = run_and_report_case(
        binary_path, case_dir, quests_path, map_path, position_path,
        quests_base, map_base, position_base,
        cities, edges, quest_lines, positions,
        use_valgrind, timeout_override=timeout,
    )

    print("\n===================== SUMMARY =====================")
    print(f"hell case: {verdict}")
    if verdict == "OK":
        shutil.rmtree(case_dir)
        print(f"Passed - {work_dir} has been cleaned up.")
        if work_dir.exists() and not any(work_dir.iterdir()):
            work_dir.rmdir()
    else:
        print(f"Files kept at: {case_dir}")
    print("=====================================================")


# ------------------------------ -e/--exel mode ------------------------------

def exel_size_sequence():
    """The fixed size sequence swept by --exel (cities == links at each point)."""
    sizes = list(range(10, 51, 5))          # 10, 15, ..., 50
    sizes += list(range(60, 201, 10))       # 60, 70, ..., 200
    sizes += list(range(300, 1001, 100))    # 300, 400, ..., 1000
    sizes += list(range(2000, 50001, 1000)) # 2000, 3000, ..., 50000
    return sizes


def build_fixed_quests_text(selected_tasks):
    """Builds ONE .quests content, reused unchanged at every size and every
    repeat. Argument-taking tasks are pinned to city 1, which exists at
    every size in the sweep (the smallest is 10 cities), so the content
    never needs to change - only the .map/.position vary between sizes."""
    lines = []
    for n in selected_tasks:
        lines.append(f"Task{n} 1" if TASK_NEEDS_ARG[n] else f"Task{n}")
    return "\n".join(lines) + "\n"


def prompt_exel_repeats():
    raw = input(
        f"How many times should the full sweep run? "
        f"(default {EXEL_DEFAULT_REPEATS}, press Enter to accept): "
    ).strip()
    if not raw:
        return EXEL_DEFAULT_REPEATS
    try:
        n = int(raw)
        if n <= 0:
            raise ValueError
        return n
    except ValueError:
        print(f"Not a valid positive number, defaulting to {EXEL_DEFAULT_REPEATS}.")
        return EXEL_DEFAULT_REPEATS


def open_file_in_default_app(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as e:
        print(f"Could not auto-open the workbook ({e}). Open it manually: {path}")


def run_exel_mode(binary_path, work_dir, selected_tasks, root):
    try:
        import openpyxl
        from openpyxl.chart import ScatterChart, Series, Reference
        from openpyxl.styles import Font
        from openpyxl.utils import get_column_letter
    except ImportError:
        print(
            "The --exel/-e flag needs the 'openpyxl' package, which isn't "
            "installed. Install it with:\n    pip install openpyxl\nand run "
            "again."
        )
        sys.exit(1)

    sizes = exel_size_sequence()
    repeats = prompt_exel_repeats()
    quests_text = build_fixed_quests_text(selected_tasks)

    print(
        f"\nSweeping {len(sizes)} sizes (10 -> 50000) x {repeats} repeat(s) "
        f"= {len(sizes) * repeats} runs of the binary. Fixed .quests content:"
    )
    for line in quests_text.splitlines():
        print(f"    {line}")
    print()

    # Generate each size's .map/.position ONCE, reused identically for every
    # repeat, so "run 1" .. f"run {repeats}" all time the exact same input.
    content_cache = {}
    for size in sizes:
        map_text, edges, links = generate_map(size, size, size)
        position_text, positions = generate_position(size, EXEL_MAX_COORD)
        content_cache[size] = (map_text, position_text)

    # run_index -> list of (size, elapsed_seconds_or_None)
    run_results = {r: [] for r in range(1, repeats + 1)}

    for size in sizes:
        map_text, position_text = content_cache[size]
        for run_index in range(1, repeats + 1):
            basename = str(run_index)
            case_dir = work_dir / basename
            case_dir.mkdir(parents=True, exist_ok=True)
            quests_path = case_dir / f"{basename}.quests"
            map_path = case_dir / f"{basename}.map"
            position_path = case_dir / f"{basename}.position"

            quests_path.write_text(quests_text)
            map_path.write_text(map_text)
            position_path.write_text(position_text)

            argv = [str(binary_path.resolve()), quests_path.name, map_path.name, position_path.name]
            print(f"  $ cd {shlex.quote(str(case_dir))} && {' '.join(shlex.quote(a) for a in argv)}")

            elapsed = None
            try:
                t0 = time.perf_counter()
                proc = subprocess.run(
                    argv, cwd=case_dir, capture_output=True, text=True,
                    timeout=EXEL_TIMEOUT_SEC,
                )
                elapsed = time.perf_counter() - t0
            except subprocess.TimeoutExpired:
                print(f"  [run {run_index}] size={size} -> TIMEOUT (> {EXEL_TIMEOUT_SEC}s)")
            else:
                if proc.returncode < 0:
                    print(f"  [run {run_index}] size={size} -> CRASH (signal {-proc.returncode})")
                    elapsed = None
                else:
                    print(f"  [run {run_index}] size={size} -> {elapsed:.4f}s")

            run_results[run_index].append((size, elapsed))

        # this size is done for every repeat - no need to keep its files
        for run_index in range(1, repeats + 1):
            case_dir = work_dir / str(run_index)
            if case_dir.exists():
                shutil.rmtree(case_dir)

    # ------------------------- build the workbook -------------------------
    # One shared table per sheet: column A is the size (Cities = Links),
    # and each run gets its own column right beside it (Run 1, Run 2, ...) -
    # like your reference layout, rather than a separate table per run.
    # Each run also gets its own scatter chart, placed in a row to the right
    # of the table so the charts sit beside each other too. The table
    # counts as 1 object and each chart as 1 more, so at most
    # (EXEL_MAX_OBJECTS_PER_SHEET - 1) runs' worth fit per sheet/"Page"
    # before a new one starts.
    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    header_font = Font(name="Arial", bold=True)
    normal_font = Font(name="Arial")

    runs_per_sheet = max(1, EXEL_MAX_OBJECTS_PER_SHEET - 1)
    run_indices = list(range(1, repeats + 1))
    sheet_groups = [
        run_indices[i:i + runs_per_sheet]
        for i in range(0, len(run_indices), runs_per_sheet)
    ]

    CHART_COL_SPAN = 12  # columns of horizontal spacing between charts
    CHART_WIDTH, CHART_HEIGHT = 16, 9

    for page_num, group in enumerate(sheet_groups, start=1):
        sheet = wb.create_sheet(title=f"Page {page_num}")

        header_row = 1
        first_data_row = 2
        last_data_row = 1 + len(sizes)

        sheet.cell(row=header_row, column=1, value="Cities = Links").font = header_font
        sheet.column_dimensions["A"].width = 16

        for j, run_index in enumerate(group):
            col = 2 + j
            sheet.cell(row=header_row, column=col, value=f"Run {run_index}").font = header_font
            sheet.column_dimensions[get_column_letter(col)].width = 12

        for i, size in enumerate(sizes):
            row = first_data_row + i
            sheet.cell(row=row, column=1, value=size).font = normal_font
            for j, run_index in enumerate(group):
                col = 2 + j
                elapsed = run_results[run_index][i][1]
                if elapsed is not None:
                    sheet.cell(row=row, column=col, value=round(elapsed, 4)).font = normal_font
                # else: leave blank - a failed (crash/timeout) data point

        charts_start_col = 2 + len(group) + 1  # one blank column after the table
        x_ref = Reference(sheet, min_col=1, min_row=first_data_row, max_row=last_data_row)

        for j, run_index in enumerate(group):
            col = 2 + j
            chart = ScatterChart()
            chart.title = f"Run {run_index}: time vs. cities/links"
            chart.x_axis.title = "Cities = Links"
            chart.y_axis.title = "Time (s)"
            chart.style = 13
            chart.displayBlanksAs = "gap"
            chart.width, chart.height = CHART_WIDTH, CHART_HEIGHT

            y_ref = Reference(sheet, min_col=col, min_row=header_row, max_row=last_data_row)
            series = Series(y_ref, x_ref, title_from_data=True)
            series.marker.symbol = "circle"
            series.graphicalProperties.line.noFill = True  # points only, no connecting line
            chart.series.append(series)

            anchor_col = charts_start_col + j * CHART_COL_SPAN
            sheet.add_chart(chart, f"{get_column_letter(anchor_col)}1")

    xlsx_path = root / "exel_results.xlsx"
    try:
        wb.save(xlsx_path)
    except PermissionError:
        # Almost always means the file is still open (e.g. in Excel) and
        # the OS has it locked - very common if you re-run right after
        # opening the previous result. Don't lose this run's data: save
        # under a fresh name instead of crashing.
        print(
            f"\nCouldn't overwrite {xlsx_path.name} - it's likely still open "
            "in Excel (or another program) and locked. Close it and re-run "
            "if you want that exact filename; saving this run under a new "
            "name instead so nothing is lost."
        )
        n = 1
        while True:
            fallback_path = root / f"exel_results_{n}.xlsx"
            try:
                wb.save(fallback_path)
                xlsx_path = fallback_path
                break
            except PermissionError:
                n += 1
                if n > 100:  # extremely unlikely, but don't loop forever
                    print("Could not save the workbook anywhere - giving up.")
                    return
    print(f"\nWorkbook written to: {xlsx_path}")
    print("Opening it now...")
    open_file_in_default_app(xlsx_path)


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

    if args.exel:
        if args.valgrind:
            print("Note: -v/--valgrind is ignored under --exel (it would swamp the timing).\n")
        work_dir = root / WORK_DIR
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir()
        run_exel_mode(binary_path, work_dir, selected_tasks, root)
        if work_dir.exists() and not any(work_dir.iterdir()):
            work_dir.rmdir()
        return

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
        run_hell_mode(binary_path, work_dir, selected_tasks, use_valgrind)
        return

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
        if cities >= 1:
            position_text, positions = generate_position(cities, MAX_COORD)
        else:
            position_text, positions = "1 1\n", {}
        quests_text, quest_lines = generate_quests(cities, selected_tasks)

        map_path.write_text(map_text)
        position_path.write_text(position_text)
        quests_path.write_text(quests_text)

        names_note = (
            f"names: {quests_base}.quests {map_base}.map {position_base}.position"
        )
        print(f"[{case_id}] cities={cities} links={links} quests={quest_lines} ({names_note})")

        verdict = run_and_report_case(
            binary_path, case_dir, quests_path, map_path, position_path,
            quests_base, map_base, position_base,
            cities, edges, quest_lines, positions,
            use_valgrind,
        )
        tally[verdict] += 1

        if verdict == "OK":
            shutil.rmtree(case_dir)  # only successful runs get cleaned up
        else:
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
