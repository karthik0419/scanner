@echo off
cd /d "C:\Users\91814\Desktop\claude\scanner"

echo ============================================
echo   DAILY SWING SCREENER — Enhanced
echo   %date% %time%
echo ============================================
echo.

echo [1/4] Building today's universe (live NSE + momentum)...
python stock_universe.py --top 150
if errorlevel 1 (
    echo ERROR: stock_universe.py failed.
    pause
    exit /b 1
)

echo.
echo [2/4] Running swing screener on today's universe...
python may_screener.py --stocks today_universe.txt --top 15 --min-score 30
if errorlevel 1 (
    echo ERROR: may_screener.py failed.
    pause
    exit /b 1
)

echo.
echo [3/4] Generating charts (Daily + Weekly + Monthly)...
for /f "tokens=*" %%f in ('python -c "import glob; files=sorted(glob.glob('results/results_*.csv'),reverse=True); print(files[0] if files else '')"') do set CHART_CSV=%%f
python -X utf8 -c "
import csv, sys, os
sys.path.insert(0,'.')
import gen_charts
rows = list(csv.DictReader(open(r'%CHART_CSV%', encoding='utf-8')))
gen_charts.STOCKS = [r['symbol'].replace('.NS','') for r in rows if r.get('symbol')]
print(f'Generating charts for {len(gen_charts.STOCKS)} stocks: {gen_charts.STOCKS}')
for s in gen_charts.STOCKS:
    gen_charts.plot(s)
print('Charts done.')
"
if errorlevel 1 (
    echo WARNING: Chart generation failed. Scan results still saved.
)

echo.
echo [4/4] Sending top 5 setups to Telegram...
for /f "tokens=*" %%f in ('python -c "import glob,os; files=sorted(glob.glob('results/results_*.csv'),reverse=True); print(files[0] if files else '')"') do set LATEST_CSV=%%f
for /f %%c in ('python -c "with open(\"today_universe.txt\") as f: lines=[l.strip() for l in f if l.strip() and not l.startswith(\"#\")]; print(len(lines))"') do set SCANNED=%%c

python -X utf8 telegram_notify.py --csv %LATEST_CSV% --top 5 --scanned %SCANNED%
if errorlevel 1 (
    echo WARNING: Telegram notification failed. Results are still saved.
)

echo.
echo ============================================
echo   Done at %date% %time%
echo   Results : %LATEST_CSV%
echo   Charts  : results\charts\daily\   weekly\   monthly\
echo ============================================
echo %date% %time% — Screener completed >> screener_log.txt

pause
