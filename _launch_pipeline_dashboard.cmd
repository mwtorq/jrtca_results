@echo off
cd /d "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results"
"C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe" -u dashboard\serve_pipeline_dashboard.py --port 8765 --host 127.0.0.1 >> "_pipeline_dashboard_serve.log" 2>> "_pipeline_dashboard_serve.err.log"
