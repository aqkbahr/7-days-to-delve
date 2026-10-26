param([string]$ProfileName='FarmingFirstPass')
$ErrorActionPreference='Stop'
if($ProfileName -notmatch '^[A-Za-z0-9_-]+$'){throw 'Invalid profile name'}
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root ('playtest/'+$ProfileName)
$evidence=Join-Path $root 'artifacts/validation/farming-runtime.txt'
if(!(Test-Path $evidence) -or (Get-Content $evidence -Raw) -notmatch '\[Farming\] PASS '){throw 'Farming engine validation required'}
$release=Join-Path $root ('dist/Delve-Farming-FirstPass-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path (Join-Path $release 'Mods') -Force | Out-Null
# Package the actual isolated test snapshot, excluding its developer harness.
foreach($name in @('Delve','DelveWildlife')) {
    if(Test-Path (Join-Path $profile ('Mods/'+$name))){Copy-Item -LiteralPath (Join-Path $profile ('Mods/'+$name)) -Destination (Join-Path $release 'Mods') -Recurse}
}
foreach($name in @('Play-Delve.cmd','Play-Delve.ps1','Verify-Package.ps1')){Copy-Item -LiteralPath (Join-Path $PSScriptRoot ('package/'+$name)) -Destination $release}
Copy-Item -LiteralPath (Join-Path $root 'docs/farming-first-pass.txt') -Destination (Join-Path $release 'START-HERE.txt')
Copy-Item -LiteralPath $evidence -Destination (Join-Path $release 'VALIDATION.txt')
$manifest=@{name='Delve Farming First Pass';version='0.3-dev-farming';gameVersion='3.3.0 (b18)';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release | Set-Content (Join-Path $root 'dist/latest-farming-release.txt')
Write-Host "Farming playtest: $release"
