$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$project=Join-Path $root 'artifacts\forest-weapons\UnityProject'
New-Item -ItemType Directory -Path "$project\Assets\Editor","$project\Assets\Models","$project\ProjectSettings","$project\Packages" -Force|Out-Null
Copy-Item (Join-Path $root 'artifacts\thornback\UnityProject\Packages\manifest.json') "$project\Packages" -Force
Copy-Item (Join-Path $root 'artifacts\thornback\UnityProject\ProjectSettings\ProjectVersion.txt') "$project\ProjectSettings" -Force
Copy-Item (Join-Path $PSScriptRoot 'BuildForestWeapons.cs') "$project\Assets\Editor" -Force
Copy-Item (Join-Path $PSScriptRoot 'WeaponQualityReview.cs') "$project\Assets\Editor" -Force
$catalogue=Get-Content (Join-Path $root 'src\Art\ForestWeapons\catalogue.json') -Raw|ConvertFrom-Json
$assets=@();foreach($asset in $catalogue.weapons){
 Copy-Item (Join-Path $root "src\Art\ForestWeapons\$($asset.id)\$($asset.id).fbx") "$project\Assets\Models" -Force
 $states=@($asset.animations.PSObject.Properties)
 $assets+=@{id=$asset.id;family=$asset.family;clips=$states.Count;loops=@($states|Where-Object {$_.Value.loop}|ForEach-Object {$_.Name})}
}
@{assets=$assets}|ConvertTo-Json -Depth 8|Set-Content "$project\Assets\build-input.json"
Copy-Item (Join-Path $root 'src\Art\ForestWeapons\ForestWeapon*.png') "$project\Assets" -Force
if(@($catalogue.weapons|Where-Object {$_.art_revision -like 'WeaponRebuild*'}).Count -gt 0){
 Copy-Item (Join-Path $PSScriptRoot 'WeaponSurface.shader') "$project\Assets" -Force
 Copy-Item (Join-Path $root 'src\Art\ForestWeapons\catalogue.json') "$project\Assets\weapon-rebuild.json" -Force
 Copy-Item (Join-Path $PSScriptRoot 'plant_unity_packages.json') "$project\Packages\manifest.json" -Force
}
$args=@('-batchmode','-nographics','-projectPath',('"'+$project+'"'),'-executeMethod','BuildForestWeapons.Run','-logFile',('"'+(Join-Path $root 'artifacts\forest-weapons\unity-build.log')+'"'))
$p=Start-Process 'D:\Unity\Hub\Editor\2022.3.62f2\Editor\Unity.exe' -ArgumentList $args -WindowStyle Hidden -PassThru
Write-Output ('Forest weapon Unity build '+$p.Id)
