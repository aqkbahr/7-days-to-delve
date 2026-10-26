$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$game='D:/Steam/steamapps/common/7 Days To Die'
$release=(Get-Content (Join-Path $root 'dist/latest-first-forest-release.txt') -Raw).Trim()
$client=Join-Path $root 'playtest/ShrineClient'
$server=Join-Path $root 'playtest/WayrestRecruits'
foreach($pair in @(@{Path=$client;Pid='client.pid'},@{Path=$server;Pid='server.pid'})){
 $pidFile=Join-Path $pair.Path $pair.Pid
 if(Test-Path $pidFile){$testPid=[int](Get-Content $pidFile);$running=Get-Process -Id $testPid -ErrorAction SilentlyContinue;if($running -and $running.ProcessName -eq '7DaysToDie'){throw 'Stop the isolated shrine client and server before preparing their files.'}}
}
New-Item -ItemType Directory -Path (Join-Path $client 'Mods') -Force | Out-Null
Copy-Item (Join-Path $release 'Mods/*') (Join-Path $client 'Mods') -Recurse -Force
& (Join-Path $PSScriptRoot 'Prepare-RecruitProbe.ps1') -HarnessOnly
Copy-Item (Join-Path $server 'Mods/Delve/Delve.dll') (Join-Path $client 'Mods/Delve/Delve.dll') -Force
Copy-Item (Join-Path $root 'src/ZDelveRecruits') (Join-Path $client 'Mods') -Recurse -Force
New-Item -ItemType Directory -Path (Join-Path $client 'GeneratedWorlds') -Force | Out-Null
Copy-Item (Join-Path $server 'GeneratedWorlds/*') (Join-Path $client 'GeneratedWorlds') -Recurse -Force
$managed=Join-Path $game '7DaysToDie_Data/Managed'
$refs=@('mscorlib.dll','System.dll','System.Core.dll','System.Xml.dll','Assembly-CSharp.dll','UnityEngine.CoreModule.dll','UnityEngine.dll','LogLibrary.dll','MemoryPack.dll','netstandard.dll')|ForEach-Object{'/reference:'+(Join-Path $managed $_)}
$refs+='/reference:'+(Join-Path $client 'Mods/Delve/Delve.dll')
foreach($side in @(@{Path=$client;Name='ShrineClientDriver';Source='ShrineClientDriver.cs'},@{Path=$server;Name='ShrineAcceptance';Source='ShrineAcceptance.cs'})) {
 $mod=Join-Path $side.Path ('Mods/'+$side.Name)
 New-Item -ItemType Directory -Path $mod -Force | Out-Null
 ('<xml><Name value="'+$side.Name+'"/><DisplayName value="Disposable shrine acceptance"/><Version value="0.1.0"/><Author value="Delve"/></xml>')|Set-Content (Join-Path $mod 'ModInfo.xml')
 & "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo /noconfig /nostdlib+ /target:library ('/out:'+(Join-Path $mod ($side.Name+'.dll'))) $refs (Join-Path $PSScriptRoot $side.Source)
 if($LASTEXITCODE -ne 0){throw 'Shrine acceptance fixture compilation failed'}
}
