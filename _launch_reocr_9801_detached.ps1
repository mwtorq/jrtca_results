$ErrorActionPreference = "Continue"
$repo = "C:\Users\mw\OneDrive - timberwilde.net\repos\jrtca_results"
$py = "C:\Users\mw\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$log = Join-Path $repo "_reocr_9801_run.log"
$err = Join-Path $repo "_reocr_9801_run.err.log"
Set-Location $repo
$stamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
Add-Content -Path $log -Encoding utf8 -Value "[$stamp] DETACHED_LAUNCH host=schtasks pid_launcher=$PID years=1998-2001 workers=10 page_workers=2"
& $py -u schedule_reocr_from_queue.py --years 1998 1999 2000 2001 --workers 10 --page-workers 2 *>> $log 2>> $err
$ec = $LASTEXITCODE
$stamp2 = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssK")
Add-Content -Path $log -Encoding utf8 -Value "[$stamp2] DETACHED_EXIT exit=$ec"
