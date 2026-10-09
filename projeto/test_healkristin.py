#!/usr/bin/env python3
"""
test_healkristin.py

Randomised test harness for the "HealkrISTin" project (AED, IST Lisboa).

What it does, each run:
  1. Builds the project with `make` (once) - not a hardcoded gcc command,
     so it picks up the real makefile's sources (healkristin.c, tasks.c,
     funcMan.c), flags, and target name exactly as the project defines
     them. See PROJECT_DIR / MAKEFILE_NAMES / MAKE_TARGET / BINARY_NAME
     below if your layout differs from the default.
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
         see USE_VALGRIND below), timing it AND tracking its peak RAM
         usage ("peak storage") the whole way, printed next to the time
         on every run. Above STORAGE_WARN_MB (90) prints a loud warning;
         above STORAGE_ERROR_MB (100) counts as its own error type,
         STORAGE_ERROR - except in --hell mode, where pushing memory hard
         is expected, so only the warning applies there, never the error.
       - computes the CORRECT answer itself (independent union-find,
         following the rules in the project statement) for every task
         it knows how to check (currently Task1-4)
       - compares the program's .results file against that correct
         answer and reports OK / MISMATCH / CRASH / VALGRIND_ERROR /
         STORAGE_ERROR / NO OUTPUT
  3. Prints a summary. Files for a test case are deleted automatically
     if and only if that case passed; every non-OK case's files are left
     on disk under ./runs/<case>/ so you can inspect or replay them.

Only Task1-4 are checked for correctness (CHECKABLE_TASKS below). You'll
be asked at startup which tasks (1-6) to include in the generated .quests
files; Task5/6 still get generated (with a random city argument) and run,
purely to fuzz for crashes - their output isn't graded until you extend
`build_expected`. Task3/4's tie-break rule (when multiple cities are
equally close, the correct answer is the one with the lowest city
number) isn't written in the enunciado but was confirmed separately.

Usage:
    python3 test_healkristin.py           run without valgrind (default)
    python3 test_healkristin.py -v        also run every case under valgrind
    python3 test_healkristin.py --hell    up to HELL_REPEATS (default 10)
                                           gigantic stress cases (tens of
                                           thousands of cities, hundreds of
                                           thousands of links, filenames
                                           right at the Windows 255-char
                                           filename limit), stopping at the
                                           first non-OK one - instead of
                                           NUM_TESTS normal ones
    python3 test_healkristin.py -e        performance sweep: times the binary
                                           across a fixed, growing sequence of
                                           sizes and writes an Excel workbook
                                           of tables/charts (opened for you
                                           when it's done) - see EXEL_* below
    python3 test_healkristin.py -r        re-run the most recently failed
                                           case under ./runs with its exact
                                           original files AND settings (e.g.
                                           valgrind on/off), no flags needed
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
import signal
import string
import subprocess
import time
import sys
from datetime import datetime
from pathlib import Path

# ============================== CONFIG ==================================

MAKEFILE_NAMES = ["makefile", "Makefile"]  # tried in this order in PROJECT_DIR
PROJECT_DIR = "."       # directory containing the makefile and all .c/.h
                         # files - defaults to wherever this script itself
                         # sits, which is normally right
MAKE_TARGET = None      # which make target to build; None = make's default
                         # target (first one in the makefile, usually "all")
BINARY_NAME = "healkristin"  # must match the makefile's $(TARGET)/binary
                              # name, since that's what gets run afterwards
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

DIVERGENCE_LINE_THRESHOLD = 201  # the "First divergence" expected/actual
DIVERGENCE_WINDOW = 100          # lines are shown in full up to this many
                                  # characters; past that, only this many
                                  # characters before/after the exact
                                  # differing character are shown (a single
                                  # Task2 cluster line can run to tens of
                                  # thousands of characters in --hell mode,
                                  # which would otherwise flood the terminal)

USE_VALGRIND_DEFAULT = False  # overridden by the -v/--valgrind CLI flag
VALGRIND_TIMEOUT_SEC = 20    # valgrind is much slower than a native run
VALGRIND_ERROR_EXITCODE = 99 # sentinel exit code valgrind returns when it
                              # found errors (invalid reads/writes, leaks, ...)
VALGRIND_LOG_CHARS = 4000    # truncate a very long valgrind report when printing

ALL_TASKS = [1, 2, 3, 4, 5, 6]           # tasks defined in the statement
TASK_NEEDS_ARG = {1: False, 2: False, 3: True, 4: True, 5: False, 6: True}
CHECKABLE_TASKS = {1, 2, 3, 4}           # tasks this harness knows how to grade

MIN_TASK_REPEATS = 1   # a selected task line may appear this many times...
MAX_TASK_REPEATS = 3   # ...up to this many times in one .quests file, each
                        # occurrence with its own random argument (e.g. two
                        # different "Task3 <city>" queries in the same run) -
                        # this is legal per the statement and worth fuzzing,
                        # especially for the argument-taking tasks (3/4/6).

# --- --hell mode: absolutely huge cases ------------------------------------
HELL_REPEATS = 10           # how many fresh huge cases to run (each its own
                             # random size/content); stops at the first
                             # non-OK result, same as normal mode - edit
                             # this to run more or fewer
HELL_MIN_CITIES = 20_000    # "tens of thousands of cities"
HELL_MAX_CITIES = 50_000
HELL_MIN_LINKS  = 100_000   # "hundreds of thousands of links"
HELL_MAX_LINKS  = 400_000
HELL_MAX_COORD  = 30_000    # still a much heavier .position file than
                             # normal mode's MAX_COORD=50 (5-digit numbers
                             # on every line, at tens of thousands of
                             # lines) - but capped so dx*dx+dy*dy can't
                             # overflow a 32-bit int even in the worst
                             # case (two cities at opposite corners), so
                             # Task3/Task4 checks at hell scale test real
                             # algorithmic correctness instead of being
                             # swamped by unavoidable int-overflow noise.
                             # sqrt(INT_MAX/2) =~ 32,767 is the hard
                             # ceiling for that; this leaves some margin.
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
EXEL_OUTPUT_DIR = "exel_reports"  # sibling of WORK_DIR - every -e session
                                    # gets its own timestamped workbook
                                    # here, so nothing is overwritten
EXEL_TIMESTAMP_FORMAT = "%S.%M.%H.%d-%m-%Y"  # second.minute.hour.date

# --- peak storage (peak RAM footprint) tracking ----------------------------
# "Storage" here means the process's peak resident memory (what the OS
# reports as the most RAM it ever held at once), read straight from the
# kernel via /proc/<pid>/status (Linux/WSL only - gracefully reports
# "n/a" elsewhere, since there's no portable equivalent without extra
# dependencies). Under -v/--valgrind this reflects valgrind's own memory
# (instrumentation overhead), not the target program alone - that's noted
# wherever it's printed.
STORAGE_WARN_MB = 90    # prints an attention-grabbing warning above this
STORAGE_ERROR_MB = 100  # counts as a new error type above this (except in
                         # --hell mode, where only the warning applies -
                         # hell mode is expected to push memory hard on
                         # purpose, so that alone shouldn't fail the run).
                         # BOTH the warning and the error are skipped
                         # entirely under -v/--valgrind, since valgrind's
                         # own overhead makes the number meaningless as a
                         # measure of the target program.
TIMEOUT_POLL_INTERVAL = 0.001  # how often we check whether a case has
                                # finished yet, to enforce our own timeout
                                # (the actual peak-RSS reading itself is a
                                # single exact value from the kernel at
                                # reap time, via os.wait4 - no sampling)

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
            "stress-test absolute limits instead of the normal suite: "
            "up to HELL_REPEATS (default 10) cases, each with tens of "
            "thousands of cities, hundreds of thousands of links, a huge "
            ".position file, and filenames sized right up to the "
            "Windows/NTFS 255-character filename limit - stopping at the "
            "first non-OK case, same as normal mode. Can be combined with "
            "-v, but that will be very slow."
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
    parser.add_argument(
        "-r", "--rerun",
        action="store_true",
        help=(
            "instead of generating new random cases, re-run the most "
            "recently failed case saved under ./runs (from normal mode or "
            "--hell), using its exact same files AND the exact same "
            "settings it failed with (e.g. valgrind on/off) - no need to "
            "pass -v again if that's how it failed. Reads the case's "
            ".parameters file. Mutually exclusive with --hell/--exel."
        ),
    )
    # -h/--help is added automatically by argparse: it prints the flags
    # above and exits immediately, before anything is compiled or run.
    args = parser.parse_args()
    if sum([args.hell, args.exel, args.rerun]) > 1:
        parser.error("--hell, -e/--exel and -r/--rerun are mutually exclusive.")
    return args


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
            "aren't graded by this harness yet, so they'll be generated "
            "and run (to fuzz for crashes) but their output isn't checked."
        )
    return chosen


# ---------------------------- Compilation --------------------------------

def find_makefile(project_dir: Path):
    for name in MAKEFILE_NAMES:
        candidate = project_dir / name
        if candidate.exists():
            return candidate
    return None


def compile_program(project_dir: Path) -> Path:
    """Builds the project with `make` - no manual gcc invocation. This
    matters because the real build isn't just healkristin.c: the
    makefile's SRCS also pulls in tasks.c and funcMan.c, and uses the
    project's own CFLAGS/LDFLAGS, none of which a hardcoded single-file
    gcc command would have respected."""
    makefile = find_makefile(project_dir)
    if makefile is None:
        tried = " or ".join(MAKEFILE_NAMES)
        print(f"Can't find a makefile ({tried}) in {project_dir}.")
        sys.exit(1)

    cmd = ["make", "-C", str(project_dir)]
    if MAKE_TARGET:
        cmd.append(MAKE_TARGET)
    print(f"  $ {' '.join(shlex.quote(a) for a in cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr:
        print(proc.stderr)
    if proc.returncode != 0:
        print("make failed - fix the C code (or the makefile) before testing.")
        sys.exit(1)

    binary_path = project_dir / BINARY_NAME
    if not binary_path.exists():
        print(
            f"make succeeded but {BINARY_NAME} wasn't produced in {project_dir}. "
            "Check that BINARY_NAME matches the makefile's $(TARGET), and that "
            "MAKE_TARGET (if set) actually builds it."
        )
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
        lines.append("Cluster: " + " ".join(str(c) for c in cl))
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
    cluster in the whole map). Ties are broken by smallest city id - not
    stated in the written enunciado, but confirmed separately - which
    matches the natural result of scanning candidate cities in increasing
    order and only replacing the best candidate on a strictly smaller
    distance (a single source city, so this alone is enough; Task4 below
    needs more care, see its docstring)."""
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


def closest_outside_cluster_for_whole_cluster(cities, clusters, positions, ref):
    """Reference solution for Task4: nearest city NOT in ref's cluster,
    where "nearest" is measured to the WHOLE cluster (closest to any
    member), not just to `ref` itself. Same -2 cases as Task3. Ties are
    broken by smallest EXTERNAL city id - confirmed separately, same rule
    as Task3 - but unlike Task3 this needs explicit care: Task4 has
    MULTIPLE source cities (every cluster member), so a naive "first
    strictly-better candidate wins" scan - iterating cluster members
    outer, candidates inner, which is what both C implementations given
    to this harness actually do - does NOT reliably pick the lowest
    external id on a tie; whichever member happens to be scanned first
    can lock in a higher-numbered candidate before a lower-numbered one
    from a different member is even considered. To get the tie-break
    right regardless of iteration order, this scans candidate EXTERNAL
    cities in increasing order (so ties naturally resolve to the lowest
    one, exactly like Task3), computing each candidate's distance to its
    closest cluster member."""
    if ref < 1 or ref > cities:
        return -2
    cluster_of = city_to_cluster_map(clusters)
    ref_cluster = cluster_of[ref]
    members = [c for c in range(1, cities + 1) if cluster_of[c] == ref_cluster]
    best_city, best_dist2 = None, None
    for cand in range(1, cities + 1):
        if cluster_of[cand] == ref_cluster:
            continue
        cx, cy = positions[cand]
        cand_dist2 = min((cx - positions[m][0]) ** 2 + (cy - positions[m][1]) ** 2 for m in members)
        if best_dist2 is None or cand_dist2 < best_dist2:
            best_dist2 = cand_dist2
            best_city = cand
    return best_city if best_city is not None else -2


def expected_block_task4(clusters, positions, cities, arg):
    ans = closest_outside_cluster_for_whole_cluster(cities, clusters, positions, arg)
    return f"Task4 {arg} {ans}"


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

    # Per an enunciado clarification: ANY termination - success or a
    # deliberate early exit() for invalid input, in main() or anywhere
    # else - MUST return 0. A non-zero, non-crash exit is graded by the
    # submissions site as "Erro de Execução" (zero points for that test),
    # independent of whatever the program did or didn't produce. This
    # check is unconditional - even a program that writes a perfectly
    # correct .results file still fails this if its exit code isn't 0.
    if returncode != 0:
        return f"EXEC_ERROR (exit code {returncode})", None, stdout, stderr, log_path, elapsed, peak_mb

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
    (Task1-4), in the order they appear in the .quests file,
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
        elif name == "Task4":
            arg = int(parts[1])
            blocks.append(expected_block_task4(clusters, positions, cities, arg))
        # Task5/6: not implemented yet, nothing to check.
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


def truncate_around_diff(exp_line, act_line, threshold=DIVERGENCE_LINE_THRESHOLD,
                          window=DIVERGENCE_WINDOW):
    """If either line is longer than `threshold` characters, returns both
    lines cut down to `window` characters before and after the exact
    character where they first differ (not just which LINE differs -
    within that line too), with '...' markers wherever text was cut.
    Otherwise returns them unchanged. None lines (one side missing a
    line entirely) pass through as-is."""
    if exp_line is None or act_line is None:
        return exp_line, act_line
    if len(exp_line) <= threshold and len(act_line) <= threshold:
        return exp_line, act_line

    min_len = min(len(exp_line), len(act_line))
    diff_idx = min_len
    for i in range(min_len):
        if exp_line[i] != act_line[i]:
            diff_idx = i
            break

    def window_around(s):
        start = max(0, diff_idx - window)
        end = min(len(s), diff_idx + window)
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(s) else ""
        return prefix + s[start:end] + suffix

    return window_around(exp_line), window_around(act_line)


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
    Only Task1-4 (CHECKABLE_TASKS) are graded. A program that
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


def run_and_report_case(binary_path, case_dir, quests_path, map_path, position_path,
                         quests_base, map_base, position_base,
                         cities, edges, quest_lines, positions,
                         use_valgrind, timeout_override=None, count_storage_error=True):
    """Runs one case, prints its outcome, and on anything other than OK
    prints the diagnostic block (diff/location/valgrind log/repro command).
    Returns one of the tally keys: OK / MISMATCH / CRASH / VALGRIND_ERROR /
    EXEC_ERROR / STORAGE_ERROR / TIMEOUT / NO_RESULTS_FILE. STORAGE_ERROR
    is only ever returned when count_storage_error is True (--hell mode
    passes False, since pushing memory hard there is expected, not a
    bug). EXEC_ERROR applies everywhere, always - a non-zero exit code is
    never acceptable regardless of mode or input scale."""
    effective_timeout = timeout_override
    if effective_timeout is None:
        effective_timeout = VALGRIND_TIMEOUT_SEC if use_valgrind else TIMEOUT_SEC

    status, actual_text, stdout, stderr, log_path, elapsed, peak_mb = run_case(
        binary_path, case_dir, quests_base, map_base, position_base,
        use_valgrind, timeout_override=timeout_override,
    )
    storage_suffix = format_storage_suffix(peak_mb, use_valgrind)

    if status.startswith("CRASH") or status == "TIMEOUT":
        kind = "CRASH" if status.startswith("CRASH") else "TIMEOUT"
        print(f"  -> {status}  (time: {elapsed:.4f}s, {storage_suffix})")
        print_storage_warning(peak_mb, use_valgrind)
        if stderr.strip():
            print(f"  stderr: {stderr.strip()[:300]}")
        print_valgrind_log(log_path)
        print_failure_location(
            case_dir, quests_path, map_path, position_path, None, binary_path,
            use_valgrind, effective_timeout, count_storage_error,
        )
        return kind

    if status == "VALGRIND_ERROR":
        print(f"  -> VALGRIND_ERROR (memcheck found invalid reads/writes and/or leaks)  (time: {elapsed:.4f}s, {storage_suffix})")
        print_storage_warning(peak_mb, use_valgrind)
        print_valgrind_log(log_path)
        print_failure_location(
            case_dir, quests_path, map_path, position_path, None, binary_path,
            use_valgrind, effective_timeout, count_storage_error,
        )
        return "VALGRIND_ERROR"

    if status.startswith("EXEC_ERROR"):
        print(f"  -> {status}  (time: {elapsed:.4f}s, {storage_suffix})")
        print("  " + "!" * 62)
        print("  !!! Any program termination - success or a deliberate   !!!")
        print("  !!! early exit() for invalid input - must return exit  !!!")
        print("  !!! code 0, or the submissions site grades this test   !!!")
        print("  !!! as \"Erro de Execução\" (zero points), regardless    !!!")
        print("  !!! of what the program did or didn't produce.         !!!")
        print("  " + "!" * 62)
        print_storage_warning(peak_mb, use_valgrind)
        if stderr.strip():
            print(f"  stderr: {stderr.strip()[:300]}")
        print_valgrind_log(log_path)
        print_failure_location(
            case_dir, quests_path, map_path, position_path, None, binary_path,
            use_valgrind, effective_timeout, count_storage_error,
        )
        return "EXEC_ERROR"

    if status == "NO_RESULTS_FILE":
        print(f"  -> NO RESULTS FILE produced  (time: {elapsed:.4f}s, {storage_suffix})")
        print_storage_warning(peak_mb, use_valgrind)
        print_valgrind_log(log_path)
        print_failure_location(
            case_dir, quests_path, map_path, position_path, None, binary_path,
            use_valgrind, effective_timeout, count_storage_error,
        )
        return "NO_RESULTS_FILE"

    # A completed run with a .results file: check the storage limit before
    # correctness, same priority VALGRIND_ERROR already gets over MISMATCH.
    if count_storage_error and not use_valgrind and peak_mb is not None and peak_mb > STORAGE_ERROR_MB:
        print(f"  -> STORAGE_ERROR  (time: {elapsed:.4f}s, {storage_suffix})")
        print("  " + "!" * 62)
        print(f"  !!! peak storage usage {peak_mb:.2f} MB exceeds the "
              f"{STORAGE_ERROR_MB} MB limit - counted as an error !!!")
        print("  " + "!" * 62)
        results_path = case_dir / f"{quests_base}.results"
        print_valgrind_log(log_path)
        print_failure_location(
            case_dir, quests_path, map_path, position_path, results_path, binary_path,
            use_valgrind, effective_timeout, count_storage_error,
        )
        return "STORAGE_ERROR"

    clusters = correct_clusters(cities, edges) if cities >= 1 else []
    verdict, diff, location = check_case(actual_text, quest_lines, clusters, positions, cities)

    if verdict == "OK":
        print(f"  -> OK  (time: {elapsed:.4f}s, {storage_suffix})")
        print_storage_warning(peak_mb, use_valgrind)
    else:
        results_path = case_dir / f"{quests_base}.results"
        print(f"  -> MISMATCH  (time: {elapsed:.4f}s, {storage_suffix})")
        print_storage_warning(peak_mb, use_valgrind)
        if VERBOSE_DIFF:
            print(diff)
        if location and location[0] is not None:
            line_no, exp_line, act_line = location
            exp_shown, act_shown = truncate_around_diff(exp_line, act_line)
            print(f"\n  First divergence at output line {line_no}:")
            print(f"    expected: {exp_shown!r}")
            print(f"    actual:   {act_shown!r}")
        print_valgrind_log(log_path)
        print_failure_location(
            case_dir, quests_path, map_path, position_path, results_path, binary_path,
            use_valgrind, effective_timeout, count_storage_error,
        )
    return verdict


def run_hell_mode(binary_path, work_dir, selected_tasks, use_valgrind):
    timeout = HELL_VALGRIND_TIMEOUT_SEC if use_valgrind else HELL_TIMEOUT_SEC

    print("=====================================================")
    print(f"HELL MODE: up to {HELL_REPEATS} absolutely huge case(s)")
    print(f"  cities target range   : [{HELL_MIN_CITIES}, {HELL_MAX_CITIES}]")
    print(f"  links target range    : [{HELL_MIN_LINKS}, {HELL_MAX_LINKS}]")
    print(f"  coordinate range      : [1, {HELL_MAX_COORD}]")
    print(f"  filenames sized to    : {WINDOWS_MAX_COMPONENT_LEN}-char Windows/NTFS limit")
    print(f"  timeout per case      : {timeout}s")
    print("=====================================================\n")

    stopped_early = False
    repeats_run = 0

    for rep in range(1, HELL_REPEATS + 1):
        repeats_run = rep
        print(f"----- hell case {rep}/{HELL_REPEATS} -----")
        cities = random.randint(HELL_MIN_CITIES, HELL_MAX_CITIES)

        case_dir = work_dir / f"hell_case_{rep:02d}"
        case_dir.mkdir()

        quests_base, map_base, position_base = hell_basenames()
        quests_path = case_dir / f"{quests_base}.quests"
        map_path = case_dir / f"{map_base}.map"
        position_path = case_dir / f"{position_base}.position"
        for label, path in (
            ("quests", quests_path), ("map", map_path), ("position", position_path),
        ):
            print(f"  {label} filename: {len(path.name)} chars -> {path.name}")

        print("  Generating map...")
        map_text, edges, links = generate_map(cities, HELL_MIN_LINKS, HELL_MAX_LINKS)
        print("  Generating position...")
        position_text, positions = generate_position(cities, HELL_MAX_COORD)
        print("  Generating quests...")
        quests_text, quest_lines = generate_quests(cities, selected_tasks)

        map_path.write_text(map_text)
        position_path.write_text(position_text)
        quests_path.write_text(quests_text)
        print(
            f"  Actual sizes: cities={cities} links={links} "
            f".map={map_path.stat().st_size:,}B "
            f".position={position_path.stat().st_size:,}B\n"
        )

        verdict = run_and_report_case(
            binary_path, case_dir, quests_path, map_path, position_path,
            quests_base, map_base, position_base,
            cities, edges, quest_lines, positions,
            use_valgrind, timeout_override=timeout, count_storage_error=False,
        )
        print(f"  hell case {rep}/{HELL_REPEATS}: {verdict}\n")

        if verdict == "OK":
            shutil.rmtree(case_dir)
        else:
            stopped_early = True
            break

    print("===================== SUMMARY =====================")
    if stopped_early:
        print(f"Stopped at hell case {repeats_run}/{HELL_REPEATS} (see details above).")
    else:
        print(f"All {repeats_run}/{HELL_REPEATS} hell case(s) passed.")
        if work_dir.exists() and not any(work_dir.iterdir()):
            work_dir.rmdir()
    print("=====================================================")


# ------------------------------ -r/--rerun mode -----------------------------

def parse_map_file(path):
    """Reads a .map file back into (cities, edges), the same structures
    correct_clusters() expects - parsed the same loose way the C program
    itself reads it (fscanf-style: whitespace-separated ints, layout not
    line-sensitive)."""
    nums = [int(t) for t in path.read_text().split()]
    cities, links = nums[0], nums[1]
    edges = []
    idx = 2
    for _ in range(links):
        edges.append((nums[idx], nums[idx + 1]))
        idx += 2
    return cities, edges


def parse_position_file(path):
    """Reads a .position file back into the {city: (x, y)} dict the Task3
    reference needs."""
    nums = [int(t) for t in path.read_text().split()]
    positions = {}
    idx = 2  # skip Xmax Ymax
    while idx + 2 <= len(nums):
        _id, x, y = nums[idx], nums[idx + 1], nums[idx + 2]
        positions[_id] = (x, y)
        idx += 3
    return positions


def parse_quests_file(path):
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]


def parse_parameters_file(path):
    params = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        params[key] = value
    return {
        "quests_base": params.get("quests_base"),
        "map_base": params.get("map_base"),
        "position_base": params.get("position_base"),
        "use_valgrind": params.get("use_valgrind") == "True",
        "timeout": float(params["timeout"]) if "timeout" in params else None,
        # defaults to True for .parameters files saved before this field
        # existed, matching normal mode's original behaviour
        "count_storage_error": params.get("count_storage_error", "True") == "True",
    }


def run_rerun_mode(binary_path, work_dir):
    if not work_dir.exists():
        print(f"No {work_dir} folder found - nothing to rerun. Run the "
              "harness normally first to produce a failing case.")
        sys.exit(1)

    param_files = sorted(
        work_dir.glob("*/.parameters"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not param_files:
        print(f"No saved failing case (.parameters file) found under {work_dir} "
              "to rerun. Run the harness normally (or with --hell) first.")
        sys.exit(1)

    param_path = param_files[0]
    case_dir = param_path.parent
    params = parse_parameters_file(param_path)
    print(f"Re-running the failing case at: {case_dir}")
    print(f"  quests_base={params['quests_base']} map_base={params['map_base']} "
          f"position_base={params['position_base']} use_valgrind={params['use_valgrind']} "
          f"timeout={params['timeout']}\n")

    quests_path = case_dir / f"{params['quests_base']}.quests"
    map_path = case_dir / f"{params['map_base']}.map"
    position_path = case_dir / f"{params['position_base']}.position"
    for p in (quests_path, map_path, position_path):
        if not p.exists():
            print(f"Missing expected file: {p} - can't rerun this case.")
            sys.exit(1)

    cities, edges = parse_map_file(map_path)
    positions = parse_position_file(position_path)
    quest_lines = parse_quests_file(quests_path)

    use_valgrind = params["use_valgrind"]
    if use_valgrind and shutil.which("valgrind") is None:
        print("Note: this case was recorded as using valgrind, but valgrind "
              "isn't installed here - rerunning without it.\n")
        use_valgrind = False

    verdict = run_and_report_case(
        binary_path, case_dir, quests_path, map_path, position_path,
        params["quests_base"], params["map_base"], params["position_base"],
        cities, edges, quest_lines, positions,
        use_valgrind, timeout_override=params["timeout"],
        count_storage_error=params["count_storage_error"],
    )

    print("\n===================== RERUN RESULT =====================")
    print(f"verdict: {verdict}")
    if verdict == "OK":
        print("This case now passes - cleaning it up.")
        shutil.rmtree(case_dir)
    else:
        print(f"Still failing. Files remain at: {case_dir}")
    print("==========================================================")


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


def run_timed_with_peak_memory(argv, cwd, timeout):
    """Lightweight run+time+peak-RSS measurement for the --exel sweep (no
    valgrind, no diagnostic file-keeping - just the numbers). Returns
    (elapsed_seconds_or_None, peak_mb_or_None, failure), where failure is
    None on a normal exit, "timeout", or a short crash description. Uses
    the same exact os.wait4()-based measurement as run_case()."""
    t0 = time.perf_counter()
    devnull = Path(os.devnull)

    if FORK_AVAILABLE:
        returncode, peak_kb, timed_out = fork_exec_with_rusage(argv, cwd, timeout, devnull, devnull)
    else:
        try:
            proc = subprocess.run(
                argv, cwd=cwd, timeout=timeout,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            returncode, peak_kb, timed_out = proc.returncode, None, False
        except subprocess.TimeoutExpired:
            returncode, peak_kb, timed_out = None, None, True

    peak_mb = peak_kb / 1024 if peak_kb is not None else None
    if timed_out:
        return None, peak_mb, "timeout"
    if returncode < 0:
        return None, peak_mb, f"CRASH (signal {-returncode})"
    return time.perf_counter() - t0, peak_mb, None


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

            elapsed, peak_mb, failure = run_timed_with_peak_memory(
                argv, case_dir, EXEL_TIMEOUT_SEC
            )
            storage_bit = format_storage_suffix(peak_mb, use_valgrind=False)
            if failure == "timeout":
                print(f"  [run {run_index}] size={size} -> TIMEOUT (> {EXEL_TIMEOUT_SEC}s), {storage_bit}")
            elif failure is not None:
                print(f"  [run {run_index}] size={size} -> {failure}, {storage_bit}")
            else:
                print(f"  [run {run_index}] size={size} -> {elapsed:.4f}s, {storage_bit}")
            print_storage_warning(peak_mb, use_valgrind=False)

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

    output_dir = root / EXEL_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime(EXEL_TIMESTAMP_FORMAT)
    xlsx_path = output_dir / f"{timestamp}.xlsx"
    try:
        wb.save(xlsx_path)
    except PermissionError:
        # Extremely unlikely now that every run gets its own timestamped
        # name, but still handle a locked target gracefully rather than
        # losing this run's data.
        print(
            f"\nCouldn't write {xlsx_path.name} - it's likely open in Excel "
            "(or another program) and locked. Saving under a new name "
            "instead so nothing is lost."
        )
        n = 1
        while True:
            fallback_path = output_dir / f"{timestamp}_{n}.xlsx"
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
    project_dir = (root / PROJECT_DIR).resolve()

    binary_path = compile_program(project_dir)

    if args.rerun:
        if args.valgrind:
            print("Note: -v/--valgrind is ignored under -r/--rerun - the case's "
                  "own recorded settings are used instead.\n")
        run_rerun_mode(binary_path, root / WORK_DIR)
        return

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
        "EXEC_ERROR": 0,
        "STORAGE_ERROR": 0,
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


def build_argv(binary_path, quests_f, map_f, position_f, use_valgrind, log_path=None):
    """Builds the exact argv used to run a case - shared by run_case() and
    the .parameters writer, so the two can never drift apart."""
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


def write_parameters_file(case_dir, quests_base, map_base, position_base,
                           use_valgrind, timeout, binary_path, count_storage_error=True):
    """Saved alongside every failing case so -r/--rerun can replay it later
    with the exact same settings (e.g. valgrind on/off, and whether peak
    storage counts as an error - False for a --hell case) without the user
    needing to remember or re-specify any flags."""
    argv = build_argv(
        binary_path, f"{quests_base}.quests", f"{map_base}.map", f"{position_base}.position",
        use_valgrind,
    )
    lines = [
        "# Saved automatically when this case failed.",
        "# Re-run this exact case (same files, same settings) with:",
        "#     python3 test_healkristin.py -r",
        "",
        f"quests_base={quests_base}",
        f"map_base={map_base}",
        f"position_base={position_base}",
        f"use_valgrind={use_valgrind}",
        f"timeout={timeout}",
        f"count_storage_error={count_storage_error}",
        "",
        "# exact command that was run:",
        f"cd {case_dir} && {' '.join(shlex.quote(a) for a in argv)}",
    ]
    (case_dir / ".parameters").write_text("\n".join(lines) + "\n")


def print_failure_location(case_dir, quests_path, map_path, position_path, results_path,
                            binary_path, use_valgrind=False, timeout=None, count_storage_error=True):
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
    quests_base = quests_path.stem
    map_base = map_path.stem
    position_base = position_path.stem
    write_parameters_file(
        case_dir, quests_base, map_base, position_base, use_valgrind, timeout, binary_path,
        count_storage_error,
    )
    print(f"  (settings saved to {case_dir / '.parameters'} - replay with: python3 test_healkristin.py -r)")


if __name__ == "__main__":
    main()
