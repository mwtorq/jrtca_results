@echo off
cd /d "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results"
echo [%date% %time%] WMI_LAUNCH track=trackB_9901 years=1999 2001 workers=7>> "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_reocr_9901_trackB.log"
"C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u schedule_reocr_from_queue.py --years 1999 2001 --workers 7 --page-workers 2 >> "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_reocr_9901_trackB.log" 2>> "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_reocr_9901_trackB.err.log"
echo [%date% %time%] WMI_EXIT track=trackB_9901 exit=%ERRORLEVEL%>> "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results\_reocr_9901_trackB.log"
