#!/usr/bin/env python3
# usage: run_imt.py <outdir> <passes> <nom binary>
# Times the variations in <outdir>/rates.csv (bench,variation,slow_calls_per_s)
# in base, trans and trans-sync mode, and checks each run against expected.txt.
# Writes <outdir>/raw/<bench>/<variation>.p<pass>.csv, one line per run:
#   variation,mode,pass,exit,ok,seconds
# which scripts/python/make_tables.py reads. An existing .csv is skipped, so a
# stopped run can be resumed. Four workers run at a time, each pinned to two
# P-cores (the second for the async IMT compiler), because on this hybrid CPU
# more parallel runs make timings noisy. A variation's modes all run on the
# same worker and their order rotates per pass.
import csv, glob, os, queue, subprocess, sys, threading

G = "/data/workspace/monnom/gtp-benchmark-monnom"
OUT, PASSES, NOM = sys.argv[1], int(sys.argv[2]), sys.argv[3]
MODES = [("base", []), ("trans", ["--trans"]),
         ("trans-sync", ["--trans", "--sync"])]
CPUS = ["0,1", "2,3", "4,5", "6,7"]
TIMEOUT = 300


def run_one(cpus, bench, project, cdir, flags):
    cmd = ["taskset", "-c", cpus, NOM, "-p", cdir, "-o3"] + flags + [project]
    try:
        r = subprocess.run(cmd, cwd=cdir, capture_output=True, text=True,
                           timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return 124, 0, ""
    lines = r.stdout.split("\n")
    expected = open("%s/%s/expected.txt" % (G, bench)).read()
    ok = int("\n".join(lines[2:]) == expected)
    words = lines[0].split()
    return r.returncode, ok, words[0] if words else ""


def worker(cpus, jobs, npass):
    while True:
        try:
            bench, name = jobs.get_nowait()
        except queue.Empty:
            return
        path = "%s/raw/%s/%s.p%d.csv" % (OUT, bench, name, npass)
        if os.path.exists(path):
            continue
        d = "%s/%s" % (G, bench)
        project = os.path.basename(glob.glob(d + "/*.mnp")[0])[:-4]
        cdir = "%s/.BM_%s" % (d, name)
        rows = []
        for i in range(3):
            mode, flags = MODES[(i + npass) % 3]
            code, ok, secs = run_one(cpus, bench, project, cdir, flags)
            rows.append([name, mode, npass, code, ok, secs])
        with open(path + ".tmp", "w") as f:
            csv.writer(f).writerows(rows)
        os.rename(path + ".tmp", path)


selected = [(r[0], r[1]) for r in csv.reader(open(OUT + "/rates.csv"))]
for bench in {b for b, _ in selected}:
    os.makedirs("%s/raw/%s" % (OUT, bench), exist_ok=True)
for npass in range(1, PASSES + 1):
    for bench in sorted({b for b, _ in selected}):
        jobs = queue.Queue()
        for b, name in selected:
            if b == bench:
                jobs.put((b, name))
        threads = [threading.Thread(target=worker, args=(c, jobs, npass))
                   for c in CPUS]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        print("pass %d: %s done" % (npass, bench), flush=True)
    subprocess.run([sys.executable, "/data/workspace/monnom/scripts/python/make_tables.py", OUT])
    print("#### pass %d done" % npass, flush=True)
print("#### imt done", flush=True)
