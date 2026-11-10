@echo off
cd /d "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results"
echo [%date% %time%] WMI_LAUNCH track=trackA_9800 years=1998 2000 workers=7>> "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_reocr_9800_trackA.log"
"C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u schedule_reocr_from_queue.py --years 1998 2000 --workers 7 --page-workers 2 >> "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_reocr_9800_trackA.log" 2>> "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_reocr_9800_trackA.err.log"
echo [%date% %time%] WMI_EXIT track=trackA_9800 exit=%ERRORLEVEL%>> "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_reocr_9800_trackA.log"
