$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$art=Join-Path $root 'src\Art\ForestProps'
$work=Join-Path $root 'artifacts\forest-props'
$render=Join-Path $work 'RenderProfile'
if ((Get-Content "$work\unity-build-result.txt" -First 1) -ne 'PASS' -or (Get-Content "$render\render-result.txt" -First 1) -ne 'PASS') { throw 'Fresh successful build and render reports required' }
if ((Get-Item "$render\render-result.txt").LastWriteTimeUtc -lt (Get-Item "$work\Bundle\forestprops.unity3d").LastWriteTimeUtc) { throw 'Render evidence predates the bundle' }
$catalogue=Get-Content "$art\catalogue.json" -Raw|ConvertFrom-Json
if ($catalogue.assets.Count -ne 111) { throw 'Expected complete 111-asset catalogue' }
$target=Join-Path $root 'dist\Forest-Stations-Plants-Items-Review-0.1.0'
New-Item -ItemType Directory -Path "$target\src\Art\ForestProps","$target\tools\art","$target\docs","$target\Previews","$target\artifacts\forest-props\UnityProject","$target\artifacts\forest-props\Bundle" -Force|Out-Null
foreach($file in Get-ChildItem $art -Recurse -File | Where-Object {$_.Extension -in '.blend','.fbx','.json','.png','.txt' -and $_.Name -notin 'progress.txt','build-error.txt'}) {
 $relative=$file.FullName.Substring($art.Length+1);$dest=Join-Path "$target\src\Art\ForestProps" $relative
 New-Item -ItemType Directory -Path (Split-Path $dest) -Force|Out-Null;Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
}
foreach($dir in 'Assets','Packages','ProjectSettings'){Copy-Item -LiteralPath "$work\UnityProject\$dir" -Destination "$target\artifacts\forest-props\UnityProject" -Recurse -Force}
Copy-Item "$work\Bundle\forestprops.unity3d","$work\Bundle\forestprops.unity3d.manifest" "$target\artifacts\forest-props\Bundle" -Force
Copy-Item "$work\unity-build-result.txt","$render\render-result.txt","$work\coverage-check.txt" "$target\artifacts\forest-props" -Force
foreach($file in Get-ChildItem $render -Recurse -File | Where-Object {($_.Extension -eq '.png' -or $_.Name -like '*-order.txt' -or $_.Name -eq 'state-checks.txt') -and $_.FullName -notmatch '\\Mods\\'}) {
 $relative=$file.FullName.Substring($render.Length+1);$dest=Join-Path "$target\Previews" $relative
 New-Item -ItemType Directory -Path (Split-Path $dest) -Force|Out-Null;Copy-Item -LiteralPath $file.FullName -Destination $dest -Force
}
foreach($name in 'build_forest_props.py','build_thornback.py','BuildForestProps.cs','Build-ForestProps.ps1','ForestPropRenderProbe.cs','Prepare-ForestPropRender.ps1','Package-ForestProps.ps1'){Copy-Item (Join-Path $PSScriptRoot $name) "$target\tools\art" -Force}
Copy-Item (Join-Path $root 'docs\forest-props-art-validation.txt') "$target\README.txt" -Force
Copy-Item (Join-Path $root 'docs\forest-props-art-validation.txt') "$target\docs" -Force
$files=@(Get-ChildItem $target -Recurse -File | Where-Object {$_.Name -ne 'asset-hashes.json'})
if (@($files|Where-Object{$_.Extension -in '.dll','.exe'}).Count) { throw 'Review kit must not redistribute runtime binaries' }
if (@($files|Where-Object{$_.Extension -eq '.blend'}).Count -ne 111) { throw 'Expected 111 editable sources' }
$hashes=@($files|ForEach-Object{@{path=$_.FullName.Substring($target.Length+1).Replace('\','/');bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}})
$hashes|ConvertTo-Json -Depth 4|Set-Content "$target\asset-hashes.json"
Compress-Archive -Path "$target\*" -DestinationPath ($target+'.zip') -Force
Get-Item ($target+'.zip')|Select-Object FullName,Length,LastWriteTime
