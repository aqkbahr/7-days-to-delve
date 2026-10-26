$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$project=Join-Path $root 'artifacts\forest-armor\UnityProject'
New-Item -ItemType Directory -Path "$project\Assets\Editor","$project\Assets\Models","$project\ProjectSettings","$project\Packages" -Force|Out-Null
if (!(Test-Path "$project\Packages\manifest.json")) {
 '{"dependencies":{"com.unity.modules.animation":"1.0.0","com.unity.modules.assetbundle":"1.0.0","com.unity.modules.imageconversion":"1.0.0","com.unity.modules.physics":"1.0.0","com.unity.modules.jsonserialize":"1.0.0","com.unity.modules.imgui":"1.0.0"}}'|Set-Content "$project\Packages\manifest.json"
}
if (!(Test-Path "$project\ProjectSettings\ProjectVersion.txt")) { 'm_EditorVersion: 2022.3.62f2'|Set-Content "$project\ProjectSettings\ProjectVersion.txt" }
Copy-Item (Join-Path $PSScriptRoot 'BuildForestArmor.cs') "$project\Assets\Editor" -Force
$catalogue=Get-Content (Join-Path $root 'src\Art\ForestArmor\catalogue.json') -Raw|ConvertFrom-Json
$assets=@();foreach($asset in $catalogue.armor){
 Copy-Item (Join-Path $root "src\Art\ForestArmor\$($asset.id)\$($asset.id).fbx") "$project\Assets\Models" -Force
 $states=@($asset.animations.PSObject.Properties)
 $assets+=@{id=$asset.id;family=$asset.family;slot=$asset.slot;set=$asset.set;clips=$states.Count;loops=@($states|Where-Object {$_.Value.loop}|ForEach-Object {$_.Name})}
}
@{assets=$assets}|ConvertTo-Json -Depth 8|Set-Content "$project\Assets\build-input.json"
Copy-Item (Join-Path $root 'src\Art\ForestArmor\ForestArmorAtlas.png') "$project\Assets" -Force
$args=@('-batchmode','-nographics','-projectPath',('"'+$project+'"'),'-executeMethod','BuildForestArmor.Run','-logFile',('"'+(Join-Path $root 'artifacts\forest-armor\unity-build.log')+'"'))
'BUILDING'|Set-Content (Join-Path $root 'artifacts\forest-armor\unity-build-result.txt')
$p=Start-Process 'D:\Unity\Hub\Editor\2022.3.62f2\Editor\Unity.exe' -ArgumentList $args -WindowStyle Hidden -PassThru
Write-Output ('Forest armor Unity build '+$p.Id)

