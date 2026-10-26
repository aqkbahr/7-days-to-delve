param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die',[switch]$HarnessOnly,
    [ValidateSet('Allium-v0.2','Allium-v0.3','Allium-v0.4','Allium-v0.5','Allium-v0.6','Allium-v0.7','Allium-v0.8','Allium-v0.9','Allium-v0.10')][string]$WorldName='Allium-v0.3',
    [string]$ProfileName='AlliumLocationsFinal',[string]$BaseDelveRelease='', [string[]]$ExcludeHarnessSources=@(),[switch]$IncludeM3Harness,[switch]$IncludeReadinessHarness)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if ($ProfileName -notmatch '^[A-Za-z0-9_-]+$') { throw 'Invalid profile name' }
$profile=Join-Path $root ('playtest/'+$ProfileName)
if (!$HarnessOnly) {
if (Test-Path (Join-Path $profile ('Saves/'+$WorldName))) { throw 'Allium test save already exists. Use a new world version rather than replacing its terrain.' }
& (Join-Path $PSScriptRoot 'Prepare-Playtest.ps1') -GamePath $GamePath -ProfileName $ProfileName
if($BaseDelveRelease) {
    $baseMod=Join-Path (Resolve-Path -LiteralPath $BaseDelveRelease).Path 'Mods/Delve'
    if(!(Test-Path (Join-Path $baseMod 'Delve.dll'))) {throw 'Base release has no Delve DLL'}
    $targetMod=[IO.Path]::GetFullPath((Join-Path $profile 'Mods/Delve'))
    $profileRoot=[IO.Path]::GetFullPath($profile)+[IO.Path]::DirectorySeparatorChar
    if(!$targetMod.StartsWith($profileRoot)){throw 'Invalid isolated mod destination'}
    Remove-Item -LiteralPath $targetMod -Recurse -Force
    Copy-Item -LiteralPath $baseMod -Destination (Join-Path $profile 'Mods') -Recurse
}
$destination=Join-Path $profile ('GeneratedWorlds/'+$WorldName)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
Copy-Item (Join-Path $root ('artifacts/maps/'+$WorldName+'/*')) $destination -Recurse -Force
if(Test-Path (Join-Path $root 'src/DelveWayrest')) { Copy-Item (Join-Path $root 'src/DelveWayrest') (Join-Path $profile 'Mods') -Recurse -Force }
}
if(!$HarnessOnly) {
    if($BaseDelveRelease) {
        Get-ChildItem (Join-Path (Resolve-Path -LiteralPath $BaseDelveRelease).Path 'Mods') -Directory | Where-Object Name -notin @('Delve','DelveWayrest','DelveWildlife','ZDelveDungeons') | ForEach-Object {Copy-Item $_.FullName (Join-Path $profile 'Mods') -Recurse -Force}
    }
    if($WorldName -eq 'Allium-v0.10'){Copy-Item (Join-Path $root 'src/ZDelveDungeons') (Join-Path $profile 'Mods') -Recurse -Force}
}
$mod=Join-Path $profile 'Mods/AlliumTools'
New-Item -ItemType Directory -Path $mod -Force | Out-Null
$WorldName | Set-Content (Join-Path $mod 'world-name.txt')
if($WorldName -eq 'Allium-v0.10') {
    $sites=New-Object Xml.XmlDocument
    $sites.AppendChild($sites.CreateElement('dungeons')) | Out-Null
    foreach($site in (Get-Content (Join-Path $root "artifacts/maps/$WorldName/dungeons.json") -Raw | ConvertFrom-Json)) {
        $node=$sites.CreateElement('poi')
        $node.SetAttribute('name',$site.prefab)
        $node.SetAttribute('x',[string]$site.position[0])
        $node.SetAttribute('y',[string]$site.position[1])
        $node.SetAttribute('z',[string]$site.position[2])
        $sites.DocumentElement.AppendChild($node) | Out-Null
    }
    $sites.Save((Join-Path $mod 'dungeon-sites.xml'))
}
if(Test-Path (Join-Path $root 'artifacts/wayrest/blueprint.xml')) { Copy-Item (Join-Path $root 'artifacts/wayrest/blueprint.xml') $mod -Force }
'<xml><Name value="AlliumTools"/><DisplayName value="Allium development harness"/><Version value="0.2.0"/><Description value="Isolated map validation"/><Author value="Delve"/></xml>' | Set-Content (Join-Path $mod 'ModInfo.xml')
$managed=Join-Path $GamePath '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','MemoryPack.dll','netstandard.dll') | ForEach-Object { '/reference:'+(Join-Path $managed $_) }
$refs += '/reference:'+(Join-Path $managed 'UnityEngine.PhysicsModule.dll')
$refs += '/reference:'+(Join-Path $profile 'Mods/Delve/Delve.dll')
$harnessSources=Get-ChildItem (Join-Path $PSScriptRoot 'allium') -Filter '*.cs'
$harnessSources=$harnessSources | Where-Object Name -notin $ExcludeHarnessSources
if($BaseDelveRelease){
 $allowed=@('AlliumTools.cs','ArborVerify.cs','ForestArt.cs','ForestArtVerify.cs','OreTools.cs','WayrestBuilder.cs','WayrestCampaignProbe.cs','DungeonVerify.cs')
 if($IncludeM3Harness){$allowed+=@('ForgedProbe.cs','ProcessingProbe.cs','PantryTools.cs')}
 if($IncludeReadinessHarness){$allowed+='ForestReadinessProbe.cs'}
 $harnessSources=$harnessSources | Where-Object Name -in $allowed
}
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'AlliumTools.dll')) $refs ($harnessSources | ForEach-Object FullName)
if ($LASTEXITCODE -ne 0) { throw 'Allium harness compilation failed' }
if ($HarnessOnly) { Write-Host 'Updated development harness only'; return }
[xml]$config=Get-Content (Join-Path $profile 'serverconfig.xml')
$settings=@{GameWorld=$WorldName;GameName='AlliumTerrainValidation';ServerPort='27950';TelnetPort='27959';ServerName='Delve Allium Terrain Test'}
foreach($item in $settings.GetEnumerator()) { $config.SelectSingleNode("/ServerSettings/property[@name='$($item.Key)']").SetAttribute('value',$item.Value) }
$config.Save((Join-Path $profile 'serverconfig.xml'))
Write-Host "Allium prepared at $profile"


