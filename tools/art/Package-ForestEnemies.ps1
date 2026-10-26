$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$art=Join-Path $root 'src\Art\ForestEnemies'
$work=Join-Path $root 'artifacts\forest-enemies'
$render=Join-Path $work 'RenderProfile'
if ((Get-Content "$work\unity-build-result.txt" -First 1) -ne 'PASS' -or (Get-Content "$render\render-result.txt" -First 1) -ne 'PASS') { throw 'Successful build and render reports required' }
foreach($bundle in Get-ChildItem "$work\Bundle\*.unity3d") {if ((Get-Item "$render\render-result.txt").LastWriteTimeUtc -lt $bundle.LastWriteTimeUtc) { throw 'Render evidence predates bundle' }}
$target=Join-Path $root 'dist\Forest-Enemies-Review-0.1.0'
New-Item -ItemType Directory -Path "$target\src\Art\ForestEnemies","$target\tools\art","$target\docs","$target\Previews","$target\artifacts\forest-enemies\InspectProfile","$target\artifacts\forest-enemies\UnityProject","$target\artifacts\forest-enemies\Bundle" -Force|Out-Null
foreach($file in Get-ChildItem $art -Recurse -File | Where-Object {$_.Extension -in '.blend','.fbx','.json','.png','.txt' -and $_.Name -notin 'build-progress.txt','build-error.txt'}) {
 $relative=$file.FullName.Substring($art.Length+1);$dest=Join-Path "$target\src\Art\ForestEnemies" $relative
 New-Item -ItemType Directory -Path (Split-Path $dest) -Force|Out-Null;Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
}
foreach($dir in 'Assets','Packages','ProjectSettings'){Copy-Item -LiteralPath "$work\UnityProject\$dir" -Destination "$target\artifacts\forest-enemies\UnityProject" -Recurse -Force}
Copy-Item "$work\Bundle\*.unity3d","$work\Bundle\*.unity3d.manifest" "$target\artifacts\forest-enemies\Bundle" -Force
Copy-Item "$work\InspectProfile\*-rig.txt" "$target\artifacts\forest-enemies\InspectProfile" -Force
Copy-Item "$work\unity-build-result.txt","$work\source-summary.txt","$render\render-result.txt" "$target\artifacts\forest-enemies" -Force
foreach($file in Get-ChildItem $render -Recurse -File | Where-Object {($_.Extension -eq '.png' -or $_.Name -match 'order|checks|reference-check') -and $_.FullName -notmatch '\\Mods\\'}) {
 $relative=$file.FullName.Substring($render.Length+1);$dest=Join-Path "$target\Previews" $relative
 New-Item -ItemType Directory -Path (Split-Path $dest) -Force|Out-Null;Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
}
foreach($name in 'build_forest_enemies.py','build_thornback.py','BuildForestEnemies.cs','Build-ForestEnemies.ps1','ForestEnemyRenderProbe.cs','Prepare-ForestEnemyRender.ps1','InspectEnemyRigs.cs','Package-ForestEnemies.ps1'){Copy-Item (Join-Path $PSScriptRoot $name) "$target\tools\art" -Force}
Copy-Item (Join-Path $root 'docs\forest-enemy-art-validation.txt') "$target\README.txt" -Force
Copy-Item (Join-Path $root 'docs\forest-enemy-art-validation.txt') "$target\docs" -Force
$files=@(Get-ChildItem $target -Recurse -File | Where-Object {$_.Name -ne 'asset-hashes.json'})
if (@($files|Where-Object{$_.Extension -in '.dll','.exe'}).Count) { throw 'Review kit cannot redistribute runtime binaries' }
if (@($files|Where-Object{$_.Extension -eq '.blend'}).Count -ne 6) { throw 'Expected six editable sources' }
$hashes=@($files|ForEach-Object{@{path=$_.FullName.Substring($target.Length+1).Replace('\','/');bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}})
$hashes|ConvertTo-Json -Depth 4|Set-Content "$target\asset-hashes.json"
Compress-Archive -Path "$target\*" -DestinationPath ($target+'.zip') -Force
Get-Item ($target+'.zip')|Select-Object FullName,Length,LastWriteTime

