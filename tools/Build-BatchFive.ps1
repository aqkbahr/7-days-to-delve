$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$base=(Get-Content (Join-Path $root 'artifacts/batch-05/base.txt') -Raw).Trim()
$mod=Join-Path $root 'src/ZZZZZZZZZZZDelveBatch05'
$managed='D:/Steam/steamapps/common/7 Days To Die/7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll')|ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:D:/Steam/steamapps/common/7 Days To Die/Mods/0_TFP_Harmony/0Harmony.dll'
$refs+='/reference:'+(Join-Path $base 'Mods/Delve/Delve.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library /optimize+ ('/out:'+(Join-Path $mod 'DelveBatchFive.dll')) $refs (Get-ChildItem $mod -Filter '*.cs'|ForEach-Object FullName)
if($LASTEXITCODE -ne 0){throw 'Batch 5 compile failed'}
New-Item -ItemType Directory (Join-Path $mod 'Resources'),(Join-Path $mod 'UIAtlases/ItemIconAtlas') -Force|Out-Null
Copy-Item (Join-Path $root 'artifacts/batch-05/art/Bundle/fieldmat.unity3d') (Join-Path $mod 'Resources') -Force
Copy-Item (Join-Path $root 'artifacts/batch-05/art/Preview/delveFieldCraftingMat.png') (Join-Path $mod 'UIAtlases/ItemIconAtlas') -Force
