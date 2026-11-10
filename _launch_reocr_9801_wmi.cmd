@echo off
cd /d "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results"
echo [%date% %time%] WMI_LAUNCH>> "_reocr_9801_run.log"
"C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u schedule_reocr_from_queue.py --years 1998 1999 2000 2001 --workers 10 --page-workers 2 >> "_reocr_9801_run.log" 2>> "_reocr_9801_run.err.log"
echo [%date% %time%] WMI_EXIT %ERRORLEVEL%>> "_reocr_9801_run.log"
