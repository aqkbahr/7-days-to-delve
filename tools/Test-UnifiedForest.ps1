param([ValidateSet('core','enemies','dungeon','pois','board','reload')][string]$Phase='core',[int]$Index=0,[string]$ProfileName='ForestUnifiedM3')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$evidence=Join-Path $root 'artifacts/validation/forest-unified-m3'
function Run([string]$Name,[string]$Command,[int]$Wait=3000,[bool]$RequirePass=$true) {
 $output=(& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command $Command -WaitMilliseconds $Wait | Out-String)
 $output | Set-Content (Join-Path $evidence ($Name+'.txt'))
 Write-Host $output
 if($output -match '\] FAIL|HEALING FAIL|Exception' -or ($RequirePass -and $output -notmatch 'PASS')){throw "Check failed/incomplete: $Name"}
}
if($Phase -eq 'core') {
 Run 'core' 'delve verify'
 Run 'forged-load' 'forgedverify load' 5000 $false
 Run 'forged' 'forgedverify' 15000
 Run 'processing' 'processingverify'
 Run 'farming' 'farmingverify'
 Run 'pantry' 'pantry verify'
 Run 'healing' 'healingprobe'
 Run 'registry' 'dungeoncheck registry'
}
if($Phase -eq 'enemies') {
 Run 'incursion-load' 'incursionprobe load' 10000 $false
 Run 'runtime' 'forestintegrated verify'
 Run 'roster' 'forestprobe verify' 5000
 Run 'damage' 'forestintegrated damage' 5000
 Run 'heavy' 'forestprobe heavy' 5000
 Run 'horde' 'forestintegrated horde' 5000
 Run 'timeline' 'forestintegrated timeline' 5000
 Run 'warden' 'incursionprobe verify' 5000
}
if($Phase -eq 'dungeon') {
 if($Index -lt 0 -or $Index -gt 3){throw 'Dungeon index must be 0-3'}
 Run "load-$Index" "dungeoncheck load $Index" 10000 $false
 Run "carving-$Index" "dungeoncheck check $Index" 5000
 if($Index -eq 3){Run 'ceiling-generated' 'dungeoncheck stress 3 ceiling' 30000}
 Run "floor-stress-$Index" "dungeoncheck stress $Index" 30000
 Run "reset-$Index" "dungeoncheck reset $Index" 15000
 Run "after-reset-$Index" "dungeoncheck check $Index" 5000
 Run "guardian-$Index" "dungeoncheck guardian $Index" 5000
 if($Index -eq 3){Run 'ceiling-regression' 'dungeoncheck stress 3 ceiling' 30000}
 if($Index -eq 1){Run 'smuggler-after-reset-stress' 'dungeoncheck stress 1' 30000}
}
if($Phase -eq 'pois') {
 $locations=Get-Content (Join-Path $evidence 'locations.json') -Raw | ConvertFrom-Json
 $location=$locations[$Index]
 if(!$location){throw 'Invalid surface POI index'}
 Run "poi-load-$Index" "forestprobe load $($location.x) $($location.z)" 6000 $false
 Run "poi-$Index" "forestintegrated poi $($location.x) $($location.z)" 3000
}
if($Phase -eq 'board') {
 Run 'wayrest-load' 'forestprobe load -2681 -2152' 10000 $false
 Run 'board' 'dungeoncheck board' 5000
}
if($Phase -eq 'reload') {
 Run 'reload-core' 'delve verify'
 Run 'reload-forged-load' 'forgedverify load' 5000 $false
 Run 'reload-forged' 'forgedverify' 10000
 Run 'reload-processing' 'processingverify'
 Run 'reload-runtime' 'forestintegrated verify'
 Run 'reload' 'forestintegrated restart'
 Run 'reload-registry' 'dungeoncheck registry'
 foreach($enemy in @('delveCorruptedWalker','delveImp','delvePossessedSoldier','delveDemonSpawn','delveHellhound','delveWarpedBrute')){Run "spell-$enemy" "forgedverify $enemy" 5000}
}
