@echo off
cd /d "C:\Users\91814\Desktop\claude\scanner"

echo ============================================
echo   DAILY SWING SCREENER — Enhanced + Volume Alert
echo   %date% %time%
echo ============================================
echo.

echo [1/5] Building today's universe (live NSE + momentum)...
python stock_universe.py --top 150
if errorlevel 1 (
    echo ERROR: stock_universe.py failed.
    pause
    exit /b 1
)

echo.
echo [2/5] Running swing screener on today's universe...
python may_screener.py --stocks today_universe.txt --top 15 --min-score 30
if errorlevel 1 (
    echo ERROR: may_screener.py failed.
    pause
    exit /b 1
)

echo.
echo [3/5] Generating charts (Daily + Weekly + Monthly)...
python -X utf8 gen_charts_latest.py
if errorlevel 1 (
    echo WARNING: Chart generation failed. Scan results still saved.
)

echo.
echo [4/5] Checking volume surges on previously flagged stocks...
python -X utf8 volume_alert.py
if errorlevel 1 (
    echo WARNING: Volume alert check failed.
)

echo.
echo [5/5] Sending top 10 setups to Telegram...
python -X utf8 telegram_notify.py --top 10
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
