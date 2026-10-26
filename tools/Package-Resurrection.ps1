# Upgrade package content in place; leave its live PlaytestData and saves untouched.
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$release=[IO.Path]::GetFullPath((Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim())
$dist=[IO.Path]::GetFullPath((Join-Path $root 'dist'))+[IO.Path]::DirectorySeparatorChar
if(!$release.StartsWith($dist,[StringComparison]::OrdinalIgnoreCase)){throw 'Expected a workspace distribution package.'}
& (Join-Path $release 'Verify-Package.ps1')
$flow=Get-Content (Join-Path $root 'artifacts/tests/resurrection-native-flow.txt') -Raw
if($flow -notmatch '\[Resurrection\] PASS native' -or $flow -match '\[Recruits\] FAIL'){throw 'Native resurrection fixture must pass before packaging.'}
$overlay=[ordered]@{
 'Mods/Delve/Delve.dll'=(Join-Path $root 'src/Delve/Delve.dll')
 'RESURRECTION.txt'=(Join-Path $root 'docs/shrine-resurrection-playtest.txt')
 'RESURRECTION-VALIDATION.txt'=(Join-Path $root 'docs/shrine-resurrection-validation.txt')
 'RECRUITMENT.txt'=(Join-Path $root 'docs/wayrest-recruits-playtest.txt')
 'RECRUITMENT-VALIDATION.txt'=(Join-Path $root 'docs/wayrest-recruits-validation.txt')
}
$module=Join-Path $root 'src/ZDelveRecruits'
foreach($file in Get-ChildItem -LiteralPath $module -Recurse -File){$relative=$file.FullName.Substring($module.Length+1).Replace('\','/');$overlay['Mods/ZDelveRecruits/'+$relative]=$file.FullName}
foreach($name in @('resurrection-results.txt','resurrection-native-flow.txt','resurrection-native-definitions.txt')){$overlay['Evidence/Resurrection/'+$name]=Join-Path $root ('artifacts/tests/'+$name)}
foreach($source in $overlay.Values){if(!(Test-Path -LiteralPath $source -PathType Leaf)){throw "Missing update file: $source"}}
$backup=Join-Path $root ('artifacts/resurrection-upgrade-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
$changed=@($overlay.Keys)+@('START-HERE.txt','sources.json','manifest.json')
foreach($relative in $changed){
 $existing=Join-Path $release $relative
 if(Test-Path -LiteralPath $existing){$copy=Join-Path $backup $relative;New-Item -ItemType Directory -Path (Split-Path $copy) -Force|Out-Null;Copy-Item -LiteralPath $existing -Destination $copy}
}
foreach($relative in $overlay.Keys){$destination=Join-Path $release $relative;New-Item -ItemType Directory -Path (Split-Path $destination) -Force|Out-Null;Copy-Item -LiteralPath $overlay[$relative] -Destination $destination -Force}
$start=Join-Path $release 'START-HERE.txt'
$heading="SHRINE RESURRECTION UPDATE - 0.9.0`r`nRestart through Play-First-Forest.cmd. Existing saves and fallen records remain compatible.`r`nCraft a Shrine of Return; read RESURRECTION.txt and RESURRECTION-VALIDATION.txt.`r`nOne in-game hour, no priest or payment. Same recruit identity and tier; full-health reserve.`r`nPlaytestData is unchanged by this package update. All multiplayer clients need this version.`r`n`r`nPRIOR PACKAGE NOTES`r`n"
$heading+(Get-Content $start -Raw)|Set-Content $start -Encoding utf8
$sourcesPath=Join-Path $release 'sources.json'
if(Test-Path $sourcesPath){$sources=Get-Content $sourcesPath -Raw|ConvertFrom-Json;$sources|Add-Member -NotePropertyName resurrection -NotePropertyValue 'Workspace RecruitRecords/RecruitRuntime/RecruitScreen and ZDelveRecruits v0.2; 2026-10-25' -Force;$sources|ConvertTo-Json -Depth 8|Set-Content $sourcesPath -Encoding utf8}
$manifestPath=Join-Path $release 'manifest.json'
$manifest=Get-Content $manifestPath -Raw|ConvertFrom-Json
$manifest.name='Allium Shrine Resurrection Playtest';$manifest.version='0.9.0-resurrection'
$manifest.acceptance='Compiled, unit persistence and native shrine flow checked. Rendered UI, natural ritual timing and remote multiplayer acceptance pending.'
$files=@{};foreach($entry in $manifest.files){$files[$entry.path]=$entry.sha256}
foreach($relative in ($changed|Where-Object {$_ -ne 'manifest.json'})){
 $path=Join-Path $release $relative
 if(Test-Path -LiteralPath $path -PathType Leaf){$files[$relative]=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash}
}
$manifest.files=@($files.Keys|Sort-Object|ForEach-Object {@{path=$_;sha256=$files[$_]}})
$manifest|ConvertTo-Json -Depth 8|Set-Content $manifestPath -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $root 'dist/latest-resurrection-release.txt')
$backup|Set-Content (Join-Path $root 'artifacts/latest-resurrection-backup.txt')
Write-Host "Updated package: $release"
Write-Host "Original package files backed up: $backup"
