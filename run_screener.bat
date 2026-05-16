@echo off
cd /d "C:\Users\91814\Desktop\claude\swing-screener-v2"

echo ============================================
echo   SWING SCREENER — Manual Run
echo   %date% %time%
echo ============================================

echo.
echo [1/2] Building today's universe from nifty500...
python stock_universe.py --top 200
if errorlevel 1 (
    echo ERROR: stock_universe.py failed. Check nifty500.txt exists.
    pause
    exit /b 1
)

echo.
echo [2/2] Running swing screener on today's universe...
python may_screener.py --stocks today_universe.txt --top 15 --min-score 30
if errorlevel 1 (
    echo ERROR: may_screener.py failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Done at %date% %time%
echo   Results saved to: results_%date:~-4%-%date:~3,2%-%date:~0,2%.csv
echo ============================================
echo %date% %time% — Screener completed >> screener_log.txt

pause
