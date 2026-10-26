param([string]$ProfileName='PantryFinal')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=Join-Path $root "playtest/$ProfileName"
$evidence=Join-Path $root 'artifacts/validation/pantry-runtime.txt'
if(!(Test-Path $evidence) -or (Get-Content $evidence -Raw) -notmatch '\[Pantry\] PASS 22') {throw 'Pantry runtime verification required'}
$runtime=Get-Content $evidence -Raw
if(([regex]::Matches($runtime,'PASS world garden')).Count -ne 3 -or $runtime -match '\[Pantry\] FAIL') {throw 'All three generated gardens must pass'}
$snapshot=Get-Content (Join-Path $root 'artifacts/validation/pantry-tested-mods.json') -Raw | ConvertFrom-Json
foreach($entry in $snapshot) {
    if((Get-FileHash (Join-Path $profile ('Mods/'+$entry.path))).Hash -ne $entry.sha256) {throw "Validated mod changed: $($entry.path)"}
}
$release=Join-Path $root ('dist/Delve-Forest-Pantry-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path (Join-Path $release 'Mods'),(Join-Path $release 'Worlds') -Force | Out-Null
foreach($mod in Get-ChildItem (Join-Path $profile 'Mods') -Directory) {
    if($mod.Name -eq 'AlliumTools'){continue}
    Copy-Item -LiteralPath $mod.FullName -Destination (Join-Path $release 'Mods') -Recurse
}
Copy-Item -LiteralPath (Join-Path $root 'artifacts/maps/Allium-v0.9') -Destination (Join-Path $release 'Worlds') -Recurse
Copy-Item -LiteralPath (Join-Path $profile 'GeneratedWorlds/Allium-v0.9/main.ttw') -Destination (Join-Path $release 'Worlds/Allium-v0.9/main.ttw')
Copy-Item (Join-Path $PSScriptRoot 'package/*') $release
'Allium-v0.9' | Set-Content (Join-Path $release 'world-name.txt')
Copy-Item -LiteralPath (Join-Path $root 'docs/forest-pantry-playtest.txt') -Destination (Join-Path $release 'START-HERE.txt')
Copy-Item -LiteralPath $evidence -Destination (Join-Path $release 'VALIDATION.txt')
$manifest=@{name='Delve Forest Pantry';version='0.3.3-dev-pantry';gameVersion='3.3.0 (b18)';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash}})
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release | Set-Content (Join-Path $root 'dist/latest-pantry-release.txt')
Write-Host "Forest pantry playtest: $release"
