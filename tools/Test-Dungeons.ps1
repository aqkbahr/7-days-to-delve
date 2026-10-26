param([string]$ProfileName='DungeonFinal',[string]$EvidenceName='dungeons',[ValidateRange(1,15)][int]$StartupTimeoutMinutes=4,[ValidateRange(0,3)][int]$StartIndex=0)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if($EvidenceName -notmatch '^[A-Za-z0-9_-]+$'){throw 'Invalid evidence folder name'}
$evidence=Join-Path $root ('artifacts/validation/'+$EvidenceName)
New-Item -ItemType Directory $evidence -Force | Out-Null
$deadline=(Get-Date).AddMinutes($StartupTimeoutMinutes)
$log=Join-Path $root "playtest/$ProfileName/server.log"
while(!(Test-Path $log) -or !(Select-String -LiteralPath $log -Pattern 'StartGame done' -Quiet)) {
    if((Get-Date) -gt $deadline){throw 'Server did not finish starting'}
    Start-Sleep -Seconds 3
}
function Run([string]$Command,[string]$Name,[string]$Expected,[int]$Wait=1000){
    $result=(& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command $Command -WaitMilliseconds $Wait | Out-String)
    $result | Set-Content (Join-Path $evidence ($Name+'.txt'))
    if($result -notmatch $Expected -or $result -match '\[Dungeons\] FAIL'){throw "Dungeon check failed: $Command`n$result"}
    $result
}
function Wait-Ready([int]$Index,[string]$Name){
    $limit=(Get-Date).AddMinutes(2)
    do {
        $state=(& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command "dungeoncheck ready $Index" -WaitMilliseconds 1000 | Out-String)
        $state | Set-Content (Join-Path $evidence ($Name+'.txt'))
        if($state -match '\[Dungeons\] PASS ready'){return}
        if($state -match '\[Dungeons\] FAIL' -or (Get-Date) -gt $limit){throw "Dungeon native initialization incomplete: $state"}
        Start-Sleep -Seconds 3
    } while($true)
}
Run 'dungeoncheck flora' 'flora' '\[Dungeons\] PASS flora'
Run 'dungeoncheck registry' 'registry' '\[Dungeons\] PASS registry'
try {
foreach($i in $StartIndex..3){
    Run "dungeoncheck load $i" "load-$i" '\[Dungeons\] Requested' | Out-Null
    Wait-Ready $i "ready-$i"
    Run "dungeoncheck check $i" "carving-$i" '\[Dungeons\] PASS generated'
    if($i -eq 3){Run 'dungeoncheck stress 3 ceiling' 'ceiling-generated' '\[Dungeons\] PASS stress' 30000}
    Run "dungeoncheck stress $i" "floor-stress-$i" '\[Dungeons\] PASS stress' 30000
    Run "dungeoncheck reset $i" "reset-$i" '\[Dungeons\] PASS native reset' 10000
    Wait-Ready $i "ready-after-reset-$i"
    Run "dungeoncheck check $i" "after-reset-$i" '\[Dungeons\] PASS generated'
    if($i -eq 1){Run 'dungeoncheck stress 1' 'smuggler-after-reset-stress' '\[Dungeons\] PASS stress' 30000}
    Run "dungeoncheck guardian $i" "guardian-$i" '\[Dungeons\] PASS guardian' 10000
    if($i -eq 3){Run 'dungeoncheck stress 3 ceiling' 'ceiling-regression' '\[Dungeons\] PASS stress' 30000}
}
& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command 'alliumprobe -2680 -2132 load' -WaitMilliseconds 1000 | Out-Null
Start-Sleep -Seconds 5
Run 'dungeoncheck board' 'board' '\[Dungeons\] PASS board' 10000
} finally {
    & (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command 'dungeoncheck unload' -WaitMilliseconds 1000 | Out-Null
}
