<#
.SYNOPSIS
    Weekly JRTCA trial collection: download new results, then load -> normalize -> compare
    -> normalize -> compare into TrialResults.sResults.

.DESCRIPTION
    Wraps the existing jrtca_results pipeline.

      1. scrape_trial_results_fixed.py pulls the JRTCA Yearbook and JRTCC sources.
         Neither needs a login, and it skips files already downloaded. Two bounds keep
         it to new work: --web-only skips re-parsing the ~3,500 already-downloaded local
         files (they only fed a dedup set the website walk never consults), and
         --min-year stops it following every archive year the sites link, which reached
         back to the 1990s. Use -RescanLocalFiles to rebuild the full report, and -Years
         to widen the window.
      2. populate_trialresults_fixed.py loads new trial files. It skips trials already
         in the database. With --normalize-at-end it defers normalization until the whole
         batch is loaded, then runs run_normalize_verify_cycle with passes=2, which is the
         normalize -> compare -> normalize -> compare sequence.
      3. Trial Vault is handled last because it is the only source that requires a login.

    Shared helpers live outside this repo because all three result-collection repos
    use them. Override the location with the RESULTS_AUTOMATION_HOME environment
    variable. Logs and run state are written there, not into this repo.

.EXAMPLE
    .\Run-JrtcaResults.ps1
    .\Run-JrtcaResults.ps1 -Years 2026 -IncludeTrialVault:$false
#>
[CmdletBinding()]
param(
    [string]$Python,
    [string]$Years,
    [switch]$SkipDownload,
    [switch]$RescanLocalFiles,
    [bool]$IncludeTrialVault = $true,
    [switch]$DryRun
)

$AutomationHome = if ($env:RESULTS_AUTOMATION_HOME) { $env:RESULTS_AUTOMATION_HOME } else { 'C:\Users\mw\ResultsAutomation' }
$CommonPath     = Join-Path $AutomationHome 'Common.ps1'
if (-not (Test-Path -LiteralPath $CommonPath)) {
    throw "Shared helpers not found at $CommonPath. Set RESULTS_AUTOMATION_HOME to the folder holding Common.ps1."
}

. $CommonPath
$script:AutomationDryRun = [bool]$DryRun

$Repo     = Split-Path -Parent $PSScriptRoot
$Server   = 'localhost\SQLEXPRESS'
$Database = 'TrialResults'

$run = Start-RunLog -Name 'jrtca_results'

try {
    $py = Resolve-PythonPath -Preferred $Python
    Write-Log "Python: $py"
    Write-Log "Repo:   $Repo"

    if (-not (Test-Path -LiteralPath (Join-Path $Repo 'populate_trialresults_fixed.py'))) {
        throw "jrtca_results scripts not found under $Repo"
    }

    # Prior year included because late-posted results land in that year's folder.
    $yearList = ConvertTo-YearList -Value $Years -Default @((Get-Date).Year, ((Get-Date).Year - 1))
    Write-Log ("Target year(s): {0}" -f ($yearList -join ', '))

    # Every source links its whole archive, so bound all three walks to the years loaded.
    $minYear = ($yearList | Measure-Object -Minimum).Minimum

    $trialsBefore     = Get-DbCount -Python $py -Server $Server -Database $Database -Query 'SELECT COUNT(*) FROM sResults.TrialList'
    $placementsBefore = Get-DbCount -Python $py -Server $Server -Database $Database -Query 'SELECT COUNT(*) FROM sResults.TrialPlacements'
    Write-Log "Baseline: $trialsBefore trials, $placementsBefore placements"

    if (-not $SkipDownload) {
        $scrapeArgs = @('scrape_trial_results_fixed.py', '--min-year', "$minYear")
        if (-not $RescanLocalFiles) { $scrapeArgs += '--web-only' }

        Invoke-Step -Name "Download new Yearbook and JRTCC results ($minYear onward)" `
            -Exe $py -WorkingDirectory $Repo `
            -Arguments $scrapeArgs | Out-Null
    }

    foreach ($year in $yearList) {
        $populateLog = Join-Path $script:LogRoot ("jrtca_populate_{0}_{1}.log" -f $year, (Get-Date -Format 'yyyy-MM-dd'))
        Invoke-Step -Name "Load $year, then normalize/compare twice" `
            -Exe $py -WorkingDirectory $Repo `
            -Arguments @(
                'populate_trialresults_fixed.py',
                '--year', "$year",
                '--normalize-at-end',
                '--log-file', $populateLog
            ) | Out-Null
    }

    # Trial Vault is the one source behind a login, so it runs last, after everything else
    # is committed. --trialvault-new walks the event catalog itself, so no per-event URL is
    # needed, and the stored credential means no prompt. The loader skips trials already
    # present for the year, so offering it the whole catalog cannot duplicate anything.
    if ($IncludeTrialVault) {
        $credential = Get-TrialVaultCredential

        if (-not $credential) {
            Request-Attention ('Trial Vault (https://v3.trialvault.dog) was skipped: no stored credential. ' +
                'Create one once with: powershell -File "' + (Join-Path $AutomationHome 'Save-TrialVaultCredential.ps1') + '"')
        }
        else {
            Write-Log ("Trial Vault: using stored credential for {0}" -f $credential.UserName)
            $tvBefore = Get-DbCount -Python $py -Server $Server -Database $Database -Query 'SELECT COUNT(*) FROM sResults.TrialList'

            # Passed as environment variables so the password never appears in a command
            # line, where any other user could read it out of the process list.
            $tvOk = Invoke-Step -Name "Import new Trial Vault events ($minYear onward)" `
                -Exe $py -WorkingDirectory $Repo `
                -Arguments @('scrape_trial_results_fixed.py', '--trialvault-new', '--min-year', "$minYear") `
                -Environment @{
                    TRIALVAULT_EMAIL    = $credential.UserName
                    TRIALVAULT_PASSWORD = $credential.GetNetworkCredential().Password
                }

            $tvAfter = Get-DbCount -Python $py -Server $Server -Database $Database -Query 'SELECT COUNT(*) FROM sResults.TrialList'
            $tvNew   = if ($null -ne $tvBefore -and $null -ne $tvAfter) { $tvAfter - $tvBefore } else { $null }

            if (-not $tvOk) {
                Request-Attention 'The Trial Vault import failed. Check the log; if the login was rejected, re-save the credential with Save-TrialVaultCredential.ps1.'
            }
            elseif ($tvNew -gt 0) {
                Write-Log "Trial Vault added $tvNew trial(s); re-running normalize/compare."
                foreach ($year in $yearList) {
                    Invoke-Step -Name "Re-run normalize/compare for $year after Trial Vault" `
                        -Exe $py -WorkingDirectory $Repo `
                        -Arguments @('verify_trial_normalization.py', '--year', "$year", '--passes', '2') | Out-Null
                }
            }
            else {
                Write-Log 'Trial Vault had no new events, so no re-normalization is needed.'
            }
        }
    }

    $trialsAfter     = Get-DbCount -Python $py -Server $Server -Database $Database -Query 'SELECT COUNT(*) FROM sResults.TrialList'
    $placementsAfter = Get-DbCount -Python $py -Server $Server -Database $Database -Query 'SELECT COUNT(*) FROM sResults.TrialPlacements'
    Add-Metric -Label 'sResults.TrialList'       -Before $trialsBefore     -After $trialsAfter
    Add-Metric -Label 'sResults.TrialPlacements' -Before $placementsBefore -After $placementsAfter
}
catch {
    Write-Log ("Unhandled error: {0}" -f $_.Exception.Message) 'ERROR'
    Write-Log ($_.ScriptStackTrace) 'ERROR'
    $run.Steps.Add([pscustomobject]@{ Name = 'runner'; Status = 'FAILED'; ExitCode = 1; Seconds = 0 })
}

exit (Complete-RunLog)
