param([string]$ProfileName='ArborFinal',[int]$StartIndex=0)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$evidence=Join-Path $root 'artifacts/validation/arbor'
New-Item -ItemType Directory -Path $evidence -Force | Out-Null
function Check([string]$Command,[string]$File) {
    $wait=if($Command -eq 'arborverify jobs'){5000}else{1000}
    $result=(& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command $Command -WaitMilliseconds $wait | Out-String)
    $result | Set-Content (Join-Path $evidence $File)
    if($result -notmatch '\[Arbor\] PASS' -or $result -match '\[Arbor\] FAIL') {throw "Runtime validation failed: $Command`n$result"}
    $result
}
Check 'arborverify registry' 'registry.txt'
$records=Get-Content (Join-Path $root 'artifacts/maps/Allium-v0.8/locations.json') -Raw | ConvertFrom-Json
$samples=@('cabin_03','cabin_17','farm_16','farm_02','oldwest_business_08','oldwest_strip_01','cemetery_02','rural_church_01','remnant_burnt_01','remnant_farm_03','remnant_oldwest_07','ranger_station_01')
foreach($sample in ($samples | Select-Object -Skip $StartIndex)) {
    $r=$records | Where-Object prefab -eq ('delve_arbor_'+$sample) | Select-Object -First 1
    if(!$r){throw "Missing sample $sample"}
    $argsText="$($r.prefab) $($r.position[0]) $($r.position[1]) $($r.position[2])"
    $loaded=(& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command "arborverify load $argsText" -WaitMilliseconds 1000 | Out-String)
    if($loaded -notmatch '\[Arbor\] Requested chunks'){throw "Load request not acknowledged: $sample`n$loaded"}
    Start-Sleep -Seconds 6
    Check "arborverify sample $argsText" ($sample+'.txt')
}
& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command 'alliumprobe -513 -1423 load' -WaitMilliseconds 1000 | Out-Null
Start-Sleep -Seconds 6
Check 'arborverify jobs' 'jobs.txt'
