param([string]$ProfileName='HealingTotem')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$baseRelease=(Get-Content (Join-Path $root "playtest/$ProfileName/base-release.txt") -Raw).Trim()
$release=Join-Path $root ('dist/Delve-Starter-Equipment-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
$runtime=Join-Path $root 'artifacts/validation/starter-runtime.txt'
if(!(Test-Path $runtime) -or (Get-Content $runtime -Raw) -notmatch 'PASS: 544') {throw 'Starter runtime verification must pass first'}
$healingEvidence=Join-Path $root 'artifacts/validation/healing-runtime.txt'
if(!(Test-Path $healingEvidence) -or (Get-Content $healingEvidence -Raw) -notmatch 'HEALING PASS:') {throw 'Healing runtime fixture must pass first'}
$testedMods=Join-Path $root "playtest/$ProfileName/Mods"
$snapshot=Get-Content (Join-Path $root 'artifacts/validation/starter-tested-mods.json') -Raw | ConvertFrom-Json
foreach($entry in $snapshot){if((Get-FileHash (Join-Path $testedMods $entry.path)).Hash -ne $entry.sha256){throw "Validated profile changed: $($entry.path)"}}
New-Item -ItemType Directory -Path (Join-Path $release 'Mods') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $baseRelease 'Worlds') -Destination $release -Recurse
foreach($mod in Get-ChildItem $testedMods -Directory) {
    if($mod.Name -eq 'HealingProbe'){continue}
    Copy-Item -LiteralPath $mod.FullName -Destination (Join-Path $release 'Mods') -Recurse
}
Copy-Item (Join-Path $PSScriptRoot 'package/*') $release
Copy-Item -LiteralPath (Join-Path $baseRelease 'world-name.txt') -Destination $release
Copy-Item -LiteralPath (Join-Path $root 'docs/starter-equipment-playtest.txt') -Destination (Join-Path $release 'START-HERE.txt')
Copy-Item -LiteralPath $runtime -Destination (Join-Path $release 'VALIDATION.txt')
Copy-Item -LiteralPath $healingEvidence -Destination (Join-Path $release 'HEALING-VALIDATION.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/wayrest-campaign-playtest.txt') -Destination (Join-Path $release 'FOREST-CAMPAIGN.txt')
$manifest=@{name='Delve starter equipment with healing';version='0.3.2-dev-healing';gameVersion='3.3.0 (b18)';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object { @{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash} })
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release | Set-Content (Join-Path $root 'dist/latest-starter-release.txt')
Write-Host "Starter playtest: $release"
