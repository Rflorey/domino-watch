#requires -Version 5.1
# Daily brief runner. Wire this up via Task Scheduler.
# It assumes the venv exists and .env contains ANTHROPIC_API_KEY.

$ErrorActionPreference = 'Stop'
$repo = 'C:\Users\russf\Source\Repos\domino_watch'
Set-Location $repo

# Pull any remote changes first so we don't hit merge conflicts
git pull --ff-only

# Generate, commit on branch, open + merge PR via gh-less flow in run_brief.py
& "$repo\venv\Scripts\python.exe" "$repo\scripts\run_brief.py" --commit --merge

# Optional log line
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Add-Content -Path "$repo\scripts\daily.log" -Value "$stamp OK"
