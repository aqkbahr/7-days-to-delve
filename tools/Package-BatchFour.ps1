param([int[]]$OtherIsolatedTestPids=@())
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if(Get-Process 7DaysToDie -ErrorAction SilentlyContinue|Where-Object {$_.Id -notin $OtherIsolatedTestPids}){throw 'Close playable/test processes before installing; exempt only independently verified isolated profiles'}
$previous=(Get-Content (Join-Path $root 'artifacts/batch-04/previous-release.txt') -Raw).Trim()
if((Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim() -ne $previous){throw 'Active release changed; reconcile before packaging'}
& (Join-Path $previous 'Verify-Package.ps1')
$candidate=Join-Path $root 'artifacts/batch-04/candidate'
$evidence=Join-Path $root 'artifacts/validation/batch04'
foreach($name in @('onboarding','rank20','recipes','core','integration','recruit-definitions','recruit-flow','resurrection','horde','incursion','backend','plants')){
 $result=Get-Content (Join-Path $evidence ($name+'.txt')) -Raw
 if($result -notmatch 'PASS' -or $result -match '\] FAIL|^FAIL'){throw "Acceptance missing: $name"}
}
$log=Get-Content (Join-Path $evidence 'server.log') -Raw
if($log -match 'Exception in thread| EXC |XML loader:| ERR XML'){throw 'Runtime exception in final log'}
$tested=Get-Content (Join-Path $evidence 'tested-mods.json') -Raw|ConvertFrom-Json
foreach($f in $tested){if((Get-FileHash (Join-Path $candidate $f.path)).Hash -ne $f.sha256){throw "Candidate differs from tested files: $($f.path)"}}
$data=(Get-Content (Join-Path $root 'artifacts/batch-04/data-location.txt') -Raw).Trim()
$backup=Join-Path $root 'artifacts/batch-04/preflight'
$save=Join-Path $data 'Saves';$original=Join-Path $backup 'Saves'
$preserved=@(Get-ChildItem $original -Recurse -File|ForEach-Object {@{relative=$_.FullName.Substring($original.Length+1);hash=(Get-FileHash $_.FullName).Hash}})
foreach($f in $preserved){if((Get-FileHash (Join-Path $save $f.relative)).Hash -ne $f.hash){throw "Playable save changed: $($f.relative)"}}
$release=Join-Path $root ('dist/Delve-Batch04-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
Copy-Item $previous $release -Recurse
foreach($m in Get-ChildItem (Join-Path $candidate 'Mods') -Directory){Copy-Item $m.FullName (Join-Path $release 'Mods') -Recurse -Force}
Copy-Item (Join-Path $root 'docs/playtest-batch-04.txt') (Join-Path $release 'BATCH-04.txt')
New-Item -ItemType Directory (Join-Path $release 'Evidence/Batch04') -Force|Out-Null
Copy-Item (Join-Path $evidence '*') (Join-Path $release 'Evidence/Batch04') -Force
Copy-Item (Join-Path $root 'artifacts/batch-04/content-validation.txt') (Join-Path $release 'Evidence/Batch04')
"BATCH 04 - 0.10.6`r`nContinue ForestTest01 in Allium-v0.10. Save data preserved.`r`nRead BATCH-04.txt for changes, validation limits and playtest checks."|Set-Content (Join-Path $release 'START-HERE.txt')
$launcher=Join-Path $release 'Play-Allium.ps1';(Get-Content $launcher -Raw).Replace('Batch 03 installed:','Batch 04 installed:').Replace('Proficiency recipe learning installed:','Batch 04 installed:')|Set-Content $launcher
$mp=Join-Path $release 'manifest.json';$manifest=Get-Content $mp -Raw|ConvertFrom-Json
$manifest.name='Forest Playtest Batch 04';$manifest.version='0.10.6-batch04';$manifest.acceptance='Automated content and native backend acceptance. Hands-on UI acceptance pending; see BATCH-04.txt.'
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object {$_.FullName -ne $mp}|Sort-Object FullName|ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 8|Set-Content $mp
& (Join-Path $release 'Verify-Package.ps1')
foreach($m in Get-ChildItem (Join-Path $release 'Mods') -Directory){Copy-Item $m.FullName (Join-Path $data 'Mods') -Recurse -Force}
foreach($f in $preserved){if((Get-FileHash (Join-Path $save $f.relative)).Hash -ne $f.hash){throw "Save unexpectedly modified: $($f.relative)"}}
Copy-Item (Join-Path $candidate 'Mods/Delve/Delve.dll') (Join-Path $root 'src/Delve/Delve.dll') -Force
$release|Set-Content (Join-Path $root 'dist/latest-first-forest-release.txt')
@{release=$release;preservedSaveFiles=$preserved.Count;version=$manifest.version}|ConvertTo-Json|Set-Content (Join-Path $root 'artifacts/batch-04/installed.json')
Write-Output "Installed Batch 04; preserved all $($preserved.Count) saved files. Release: $release"
