param([switch]$Reload,[switch]$SkipFoundation,[string]$ProfileName='CombinedM3',[string]$EvidenceName='combined-m3',[switch]$LatestCore)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=$ProfileName
$evidence=Join-Path $root ('artifacts/validation/'+$EvidenceName)
$deadline=(Get-Date).AddMinutes(10)
while(!(Select-String (Join-Path $root "playtest/$profile/server.log") -Pattern 'StartGame done' -Quiet)){
 if((Get-Date) -gt $deadline){throw 'Server startup timeout'};Start-Sleep -Seconds 3
}
function Run([string]$Command,[string]$Name,[string]$Expected='PASS',[int]$Wait=3000){
 $text=(& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $profile -Command $Command -WaitMilliseconds $Wait|Out-String)
 $text|Set-Content (Join-Path $evidence ($Name+'.txt'))
 if($text -notmatch $Expected -or $text -match '(\] FAIL|HEALING FAIL|FAIL:)'){throw "Failed $Command`n$text"}
 ($text -split "`n"|Where-Object {$_ -match $Expected})
}
if($Reload){
 Run 'delve verify' 'core-reload'
 Run 'processingverify' 'processing-reload'
 Run 'farmingverify' 'farming-reload'
 Run 'pantry verify' 'pantry-reload'
 Run 'healingprobe' 'healing-reload'
 Run 'forestintegrated verify' 'runtime-reload'
 Run 'forgedverify load' 'spell-load-reload' 'Loading' 5000
 Run 'forgedverify delveWarpedBrute' 'forged-reload' 'PASS' 10000
 Run 'forestintegrated restart' 'reload'
 if($LatestCore){Run 'forestready' 'closure-reload';Run 'terrainrace faults' 'decoder-faults-reload' 'PASS' 5000;Run 'terrainrace clone' 'sparse-clone-reload' 'PASS' 5000;Run 'terrainrace channels' 'sparse-channels-reload' 'PASS' 5000}
 try {
  Run 'dungeoncheck load 3' 'dungeon-load-reload' 'Requested' 5000
  $readyLimit=(Get-Date).AddMinutes(2)
  do {
   $ready=& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $profile -Command 'dungeoncheck ready 3' -WaitMilliseconds 1000 | Out-String
   $ready | Set-Content (Join-Path $evidence 'dungeon-ready-reload.txt')
   if($ready -match '\[Dungeons\] PASS ready'){break}
   if($ready -match '\[Dungeons\] FAIL' -or (Get-Date) -gt $readyLimit){throw 'Reloaded dungeon did not finish native initialization'}
   Start-Sleep -Seconds 3
  } while($true)
  Run 'dungeoncheck stress 3 ceiling' 'dungeon-ceiling-reload' 'PASS stress' 30000
 } finally {
  & (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $profile -Command 'dungeoncheck unload' -WaitMilliseconds 1000 | Out-Null
 }
 'PASS combined M3 process reload'
 return
}
if(!$SkipFoundation){
Run 'delve verify' 'core'
Run 'processingverify' 'processing'
Run 'farmingverify' 'farming'
Run 'pantry verify' 'pantry'
Run 'healingprobe' 'healing'
Run 'forestintegrated verify' 'runtime'
if($LatestCore){Run 'forestready' 'closure';Run 'terrainrace' 'decoder-race' 'PASS' 30000;Run 'terrainrace faults' 'decoder-faults' 'PASS' 5000;Run 'terrainrace clone' 'sparse-clone' 'PASS' 5000;Run 'terrainrace channels' 'sparse-channels' 'PASS' 5000}
}
Run 'forestprobe verify' 'roster' 'PASS' 30000
Run 'forgedverify load' 'spell-load' 'Loading' 5000
$roster=@('delveCorruptedWalker','delveImp','delvePossessedSoldier','delveDemonSpawn','delveHellhound','delveWarpedBrute','delveAshboundWarden','delveThornbackBoar','delveGloomcat','delveCrystalStag')
foreach($enemy in $roster){Run "forgedverify $enemy" "forged-$enemy" 'PASS' 5000}
Run 'forestprobe load' 'enemy-load' 'Loading' 5000
Run 'forestprobe heavy' 'heavy'
Run 'forestintegrated damage' 'damage'
Run 'incursionprobe load' 'boss-load' 'Requested' 5000
Run 'forestintegrated horde' 'horde'
Run 'forestintegrated timeline' 'timeline'
Run 'incursionprobe verify' 'warden'
$sites=Get-Content (Join-Path $evidence 'locations.json') -Raw|ConvertFrom-Json
$poiFile=Join-Path $evidence 'pois.txt'
if(Test-Path $poiFile){throw 'POI evidence exists; preserve before rerunning'}
foreach($site in $sites){
 & (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $profile -Command "forestprobe load $($site.x) $($site.z)" -WaitMilliseconds 5000|Out-Null
 $result=& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $profile -Command "forestintegrated poi $($site.x) $($site.z)" -WaitMilliseconds 2000|Out-String
 $result|Add-Content $poiFile
 if($result -notmatch '\[Integrated\] PASS POI' -or $result -match '\] FAIL'){throw "POI failed: $($site.name)`n$result"}
 "PASS POI $($site.name)"
}
& (Join-Path $PSScriptRoot 'Test-Dungeons.ps1') -ProfileName $profile -EvidenceName ($EvidenceName+'-dungeons')
if($LASTEXITCODE -and $LASTEXITCODE -ne 0){throw 'Dungeon command failed'}
'PASS combined M3 initial native suite'
