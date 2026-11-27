"""
run_all.py: run the whole pipeline in order with the current Python (works on the cluster without uv).

  python code/run_all.py            # everything (download is skipped for years already on disk)
  python code/run_all.py 03 09      # only the listed steps

Needs: duckdb pyarrow pandas numpy scipy matplotlib tabulate requests
       (cluster:  python -m pip install --user duckdb pyarrow pandas numpy scipy matplotlib tabulate requests)
Data location: env var IOWA_DATA_DIR (default ~/mgt634_data/iowa_liquor).
Step 11 needs a free Census API key (env var CENSUS_API_KEY or IOWA_DATA_DIR/census_api_key.txt); without one it is skipped.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ["01_download", "02_build_panel", "03_descriptives", "04_tariff_2019_scotch", "05_demand_first_pass",
         "06_tariff_2025", "07_price_change_events", "08_nested_logit", "09_counterfactuals", "10_slide_figures",
         "11_customs_passthrough"]
wanted = sys.argv[1:]
for step in STEPS:
    if wanted and step[:2] not in wanted:
        continue
    t0 = time.time()
    print(f"\n===== {step} =====", flush=True)
    r = subprocess.run([sys.executable, "-u", os.path.join(HERE, f"{step}.py")])
    print(f"----- {step}: {'OK' if r.returncode == 0 else 'FAILED'} in {time.time() - t0:.0f}s", flush=True)
    if r.returncode != 0:
        sys.exit(r.returncode)
