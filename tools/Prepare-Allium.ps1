param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die',[switch]$HarnessOnly,
    [ValidateSet('Allium-v0.2','Allium-v0.3','Allium-v0.4','Allium-v0.5','Allium-v0.6')][string]$WorldName='Allium-v0.3',
    [string]$ProfileName='AlliumLocationsFinal')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if ($ProfileName -notmatch '^[A-Za-z0-9_-]+$') { throw 'Invalid profile name' }
$profile=Join-Path $root ('playtest/'+$ProfileName)
if (!$HarnessOnly) {
if (Test-Path (Join-Path $profile ('Saves/'+$WorldName))) { throw 'Allium test save already exists. Use a new world version rather than replacing its terrain.' }
& (Join-Path $PSScriptRoot 'Prepare-Playtest.ps1') -GamePath $GamePath -ProfileName $ProfileName
$destination=Join-Path $profile ('GeneratedWorlds/'+$WorldName)
New-Item -ItemType Directory -Path $destination -Force | Out-Null
Copy-Item (Join-Path $root ('artifacts/maps/'+$WorldName+'/*')) $destination -Recurse -Force
if(Test-Path (Join-Path $root 'src/DelveWayrest')) { Copy-Item (Join-Path $root 'src/DelveWayrest') (Join-Path $profile 'Mods') -Recurse -Force }
}
$mod=Join-Path $profile 'Mods/AlliumTools'
New-Item -ItemType Directory -Path $mod -Force | Out-Null
$WorldName | Set-Content (Join-Path $mod 'world-name.txt')
if(Test-Path (Join-Path $root 'artifacts/wayrest/blueprint.xml')) { Copy-Item (Join-Path $root 'artifacts/wayrest/blueprint.xml') $mod -Force }
'<xml><Name value="AlliumTools"/><DisplayName value="Allium development harness"/><Version value="0.2.0"/><Description value="Isolated map validation"/><Author value="Delve"/></xml>' | Set-Content (Join-Path $mod 'ModInfo.xml')
$managed=Join-Path $GamePath '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll') | ForEach-Object { '/reference:'+(Join-Path $managed $_) }
$refs += '/reference:'+(Join-Path $root 'src/Delve/Delve.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'AlliumTools.dll')) $refs (Get-ChildItem (Join-Path $PSScriptRoot 'allium') -Filter '*.cs' | ForEach-Object FullName)
if ($LASTEXITCODE -ne 0) { throw 'Allium harness compilation failed' }
if ($HarnessOnly) { Write-Host 'Updated development harness only'; return }
[xml]$config=Get-Content (Join-Path $profile 'serverconfig.xml')
$settings=@{GameWorld=$WorldName;GameName='AlliumTerrainValidation';ServerPort='27950';TelnetPort='27959';ServerName='Delve Allium Terrain Test'}
foreach($item in $settings.GetEnumerator()) { $config.SelectSingleNode("/ServerSettings/property[@name='$($item.Key)']").SetAttribute('value',$item.Value) }
$config.Save((Join-Path $profile 'serverconfig.xml'))
Write-Host "Allium prepared at $profile"

