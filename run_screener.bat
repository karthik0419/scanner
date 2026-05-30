@echo off
cd /d "C:\Users\91814\Desktop\claude\scanner"

echo ============================================
echo   SWING SCREENER v3 — Manual Run
echo   %date% %time%
echo ============================================

echo.
echo [1/3] Building today's universe (live NSE + momentum)...
python stock_universe.py --top 80
if errorlevel 1 (
    echo ERROR: stock_universe.py failed.
    pause
    exit /b 1
)

echo.
echo [2/3] Running swing screener on today's universe...
python may_screener.py --stocks today_universe.txt --top 15 --min-score 30
if errorlevel 1 (
    echo ERROR: may_screener.py failed.
    pause
    exit /b 1
)

echo.
echo [3/3] Sending top 5 setups to Telegram...
for /f "tokens=*" %%f in ('python -c "import glob,os; files=sorted(glob.glob('results_*.csv'),reverse=True); print(files[0] if files else '')"') do set LATEST_CSV=%%f
set SCANNED=0
for /f %%c in ('python -c "with open(\"today_universe.txt\") as f: lines=[l.strip() for l in f if l.strip() and not l.startswith(\"#\")]; print(len(lines))"') do set SCANNED=%%c

python -X utf8 telegram_notify.py --csv %LATEST_CSV% --top 5 --scanned %SCANNED%
if errorlevel 1 (
    echo WARNING: Telegram notification failed. Results are still saved.
)

echo.
echo ============================================
echo   Done at %date% %time%
echo   Results: %LATEST_CSV%
echo ============================================
echo %date% %time% — Screener completed >> screener_log.txt

pause
