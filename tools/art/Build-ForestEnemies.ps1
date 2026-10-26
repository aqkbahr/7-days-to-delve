$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$project=Join-Path $root 'artifacts\forest-enemies\UnityProject'
New-Item -ItemType Directory -Path "$project\Assets\Editor","$project\ProjectSettings","$project\Packages" -Force|Out-Null
if (!(Test-Path "$project\Packages\manifest.json")) {
 '{"dependencies":{"com.unity.modules.animation":"1.0.0","com.unity.modules.assetbundle":"1.0.0","com.unity.modules.imageconversion":"1.0.0","com.unity.modules.physics":"1.0.0","com.unity.modules.jsonserialize":"1.0.0","com.unity.modules.imgui":"1.0.0"}}'|Set-Content "$project\Packages\manifest.json"
}
if (!(Test-Path "$project\ProjectSettings\ProjectVersion.txt")) { 'm_EditorVersion: 2022.3.62f2'|Set-Content "$project\ProjectSettings\ProjectVersion.txt" }
'BUILDING'|Set-Content (Join-Path $root 'artifacts\forest-enemies\unity-build-result.txt')
foreach($id in @('delveCorruptedWalker','delveImp','delvePossessedSoldier','delveDemonSpawn','delveWarpedBrute','delveAshboundWarden')){
 $destination=Join-Path $project "Assets\Creatures\$id"
 New-Item -ItemType Directory -Path $destination -Force|Out-Null
 Copy-Item (Join-Path $root "src\Art\ForestEnemies\$id\$id.fbx"),(Join-Path $root "src\Art\ForestEnemies\$id\Albedo.png"),(Join-Path $root "src\Art\ForestEnemies\$id\Emission.png") $destination -Force
}
Copy-Item (Join-Path $PSScriptRoot 'BuildForestEnemies.cs') (Join-Path $project 'Assets\Editor') -Force
$args=@('-batchmode','-nographics','-projectPath',('"'+$project+'"'),'-executeMethod','BuildForestEnemies.Run','-logFile',('"'+(Join-Path $root 'artifacts\forest-enemies\unity-build.log')+'"'))
$p=Start-Process 'D:\Unity\Hub\Editor\2022.3.62f2\Editor\Unity.exe' -ArgumentList $args -WindowStyle Hidden -PassThru
Write-Output ('Unity Forest build process '+$p.Id)

