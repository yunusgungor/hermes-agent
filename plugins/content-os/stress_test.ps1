# Content OS Master Stress Test Script
# Purpose: Test all combinations of content lifecycle, state sync, and edge cases.

$ErrorActionPreference = "Stop"
$slug = "stress-test-content-2026"
$console_width = 80

$hermes_home = "C:\Users\ASUS\AppData\Local\hermes"
$plugin_root = "$hermes_home\plugins\content-os"
$active_runs_path = "$plugin_root\runs\active"

function Log($msg) {
    Write-Host "`n[TEST] $msg" -ForegroundColor Cyan
}

function Assert($condition, $msg) {
    if (-not $condition) {
        Write-Host "[FAIL] $msg" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "[PASS] $msg" -ForegroundColor Green
    }
}

Log "Step 1: Environment Cleanup"
if (Test-Path "$active_runs_path\$slug") { Remove-Item -Path "$active_runs_path\$slug" -Recurse -Force }
if (Test-Path "$plugin_root\runs_backup") { Remove-Item -Path "$plugin_root\runs_backup" -Recurse -Force }

Log "Step 2: Testing 'new' with weird characters"
$weird_idea = "A very weird Idea! with @#$ characters & Türkçe şİğÜç"
$res = hermes content new $weird_idea --slug $slug
Assert ($res -match "Created new run") "Should create run even with weird idea"

Log "Step 3: State Sync - Initial (Captured)"
$status = hermes content status
Assert ($status -match "$slug.*captured") "New run should start in 'captured' state"

Log "Step 4: State Sync - Brief Addition"
"Sample brief" | Out-File -FilePath "$active_runs_path\$slug\brief.md" -Encoding utf8
$status = hermes content status
Assert ($status -match "$slug.*briefed") "Should sync to 'briefed' when brief.md exists"

Log "Step 5: State Sync - Draft Addition (Priority Check)"
"Groundbreaking draft utilizes AI" | Out-File -FilePath "$active_runs_path\$slug\draft-package.md" -Encoding utf8
$status = hermes content status
Assert ($status -match "$slug.*drafted") "Should sync to 'drafted' when draft exists (priority over brief)"

Log "Step 6: State Sync - Recovery (Deleting content-object.md)"
Remove-Item "$active_runs_path\$slug\content-object.md"
$status = hermes content status
Assert ($status -match "$slug.*drafted") "Should recover and sync even if meta-file is deleted"

Log "Step 7: Slop Scan - High Slop Detection"
$scan = hermes content scan $slug
Assert ($scan -match "REJECT" -or $scan -match "REVISE") "Should detect slop in the sample draft"

Log "Step 8: Slop Scan - Zero Slop Test"
"This is a clean technical document about kernel optimization. It provides data and results." | Out-File -FilePath "$active_runs_path\$slug\draft-package.md" -Encoding utf8
$scan = hermes content scan $slug
Assert ($scan -match "Score: PASS") "Clean text should result in PASS"

Log "Step 9: Audit Test"
$audit = hermes content audit
Assert ($audit -match "All systems nominal") "Audit should pass when all directories exist"

Log "Step 10: Signal Source Test"
$signal = hermes content signal rss
Assert ($signal -match "RSS:") "Should fetch RSS signals correctly"

Log "Step 12: Scale Test (50 Runs)"
$startTime = Get-Date
for ($i = 1; $i -le 50; $i++) {
    $null = hermes content new "Scale Test Idea $i" --slug "scale-test-$i"
}
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds
Assert ($duration -lt 90) "Should create 50 runs in under 90 seconds (Actual: $duration s)"

Log "Step 17: Directory Corruption Recovery"
$old_name = "$plugin_root\runs_backup"
Rename-Item -Path "$plugin_root\runs" -NewName "runs_backup"
$audit = hermes content audit
Assert ($audit -match "❌") "Audit should detect missing critical directory"
# Restore
Rename-Item -Path $old_name -NewName "runs"
Log "Directory restored."

Log "Step 18: File Content Integrity (Zero-Byte File)"
$zero_slug = "zero-byte-test"
$null = hermes content new "Zero Byte" --slug $zero_slug
"" | Out-File -FilePath "$active_runs_path\$zero_slug\content-object.md" -Encoding utf8
$status = hermes content status
Assert ($status -match "$zero_slug.*captured") "Should handle empty content-object.md gracefully"

Log "Step 19: Bulk Cleanup"
Log "Cleaning up remaining test runs..."
for ($i = 1; $i -le 50; $i++) {
    $r = "$active_runs_path\scale-test-$i"
    if (Test-Path $r) { Remove-Item -Path $r -Recurse -Force }
}
if (Test-Path "$active_runs_path\$zero_slug") { Remove-Item -Path "$active_runs_path\$zero_slug" -Recurse -Force }
if (Test-Path "$active_runs_path\$slug") { Remove-Item -Path "$active_runs_path\$slug" -Recurse -Force }

Write-Host "`n🚀 LEVEL 3 COMPLETE: SYSTEM IS BATTLE-HARDENED 🚀" -ForegroundColor Cyan
