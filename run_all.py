"""Run the whole NorthGrid pipeline: python run_all.py [--data PATH] [--team TEAM07] [--from N]"""
import argparse
import os
import sys
import time

p = argparse.ArgumentParser()
p.add_argument("--data", help="folder holding the extract (searched recursively)")
p.add_argument("--team", help="team id for predictions_<TEAM>.csv, e.g. TEAM07")
p.add_argument("--from", dest="start", type=int, default=1, help="start at step N (1-8), reusing earlier results")
p.add_argument("--mem", help="DuckDB memory limit, e.g. 6GB")
a = p.parse_args()
if a.data:
    os.environ["NG_DATA"] = a.data
team_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "team.txt")
if not a.team and os.path.exists(team_file):
    a.team = open(team_file).read().strip() or None
if a.team:
    os.environ["NG_TEAM"] = a.team.upper().replace(" ", "")
else:
    print("WARNING: no --team given, the submission will be named predictions_TEAMxx.csv. "
          "Use: python run_all.py --team TEAM07 (or put TEAM07 in team.txt)")
if a.mem:
    os.environ["NG_MEM"] = a.mem

from ng import (s01_load, s02_losses, s03_loadshed, s04_theft_model, s05_insider, s06_answers,  # noqa: E402
                s07_detective, s08_network)

steps = [s01_load, s02_losses, s03_loadshed, s04_theft_model, s05_insider, s07_detective, s08_network, s06_answers]
for i, mod in enumerate(steps, 1):
    if i < a.start:
        continue
    t = time.time()
    print(f"\n===== STEP {i}: {mod.__name__} =====")
    sys.argv = [sys.argv[0]]
    mod.main()
    print(f"----- step {i} done in {time.time() - t:.0f}s")
print("\nAll done. Open outputs/ANSWERS.md, then run:  streamlit run dashboard.py")
