$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$project=Join-Path $root 'artifacts\forest-quadrupeds\UnityProject'
foreach($id in @('delveHellhound','delveGloomcat','delveCrystalStag')){
 $destination=Join-Path $project "Assets\Creatures\$id"
 New-Item -ItemType Directory -Path $destination -Force|Out-Null
 Copy-Item (Join-Path $root "src\Art\$id\$id.fbx"),(Join-Path $root "src\Art\$id\Albedo.png") $destination -Force
}
Copy-Item (Join-Path $PSScriptRoot 'BuildForestQuadrupeds.cs') (Join-Path $project 'Assets\Editor') -Force
$args=@('-batchmode','-nographics','-projectPath',('"'+$project+'"'),'-executeMethod','BuildForestQuadrupeds.Run','-logFile',('"'+(Join-Path $root 'artifacts\forest-quadrupeds\unity-build.log')+'"'))
$p=Start-Process 'D:\Unity\Hub\Editor\2022.3.62f2\Editor\Unity.exe' -ArgumentList $args -WindowStyle Hidden -PassThru
Write-Output ('Unity Forest build process '+$p.Id)
