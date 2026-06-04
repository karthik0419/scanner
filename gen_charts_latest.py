"""Auto-generate charts from the latest scan results CSV."""
import csv, sys, os, glob, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_charts

files = sorted([f for f in glob.glob("results/results_*.csv") if "_all" not in f], reverse=True)
if not files:
    print("No results CSV found.")
    sys.exit(0)

f = files[0]
print(f"Reading: {f}")
rows = list(csv.DictReader(open(f, encoding="utf-8")))
gen_charts.STOCKS = [r["symbol"].replace(".NS","") for r in rows if r.get("symbol")]
print(f"Generating charts for {len(gen_charts.STOCKS)} stocks")
for s in gen_charts.STOCKS:
    gen_charts.plot(s)
print("Charts done.")
