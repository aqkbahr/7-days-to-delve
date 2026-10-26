param([string]$ProfileName='FarmingFirstPass',[string]$GamePath='D:/Steam/steamapps/common/7 Days To Die',[switch]$HarnessOnly)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if(!$HarnessOnly){& (Join-Path $PSScriptRoot 'Prepare-Playtest.ps1') -ProfileName $ProfileName -GamePath $GamePath}
$profile=Join-Path $root ('playtest/'+$ProfileName)
$mod=Join-Path $profile 'Mods/FarmingProbe'
New-Item -ItemType Directory -Path $mod -Force | Out-Null
'<xml><Name value="FarmingProbe"/><DisplayName value="Farming validation"/><Version value="1.0.0"/><Description value="Isolated farming verification"/><Author value="Delve"/></xml>' | Set-Content (Join-Path $mod 'ModInfo.xml')
Copy-Item -LiteralPath (Join-Path $root 'artifacts/validation/farming-checks.xml') -Destination $mod -Force
$managed=Join-Path $GamePath '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','netstandard.dll') | ForEach-Object {'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $profile 'Mods/Delve/Delve.dll')
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod 'FarmingProbe.dll')) $refs (Join-Path $PSScriptRoot 'farming/FarmingProbe.cs')
if($LASTEXITCODE -ne 0){throw 'Farming probe compilation failed'}
if($HarnessOnly){return}
[xml]$config=Get-Content (Join-Path $profile 'serverconfig.xml')
foreach($entry in @{ServerPort='28070';TelnetPort='28079';GameName='FarmingFirstPass';ServerName='Delve Farming Test'}.GetEnumerator()) {
    $config.SelectSingleNode("/ServerSettings/property[@name='$($entry.Key)']").SetAttribute('value',$entry.Value)
}
$config.Save((Join-Path $profile 'serverconfig.xml'))
