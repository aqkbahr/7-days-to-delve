param([string]$ProfileName='OreFinal',[ValidateRange(0,4)][int]$Region=0)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$sites=Get-Content (Join-Path $root 'artifacts/maps/Allium-v0.7/resource-sites.json') -Raw | ConvertFrom-Json
$sample=$sites | Where-Object region_index -eq $Region | Group-Object resource | ForEach-Object {$_.Group[0]}
$evidence=Join-Path $root "artifacts/validation/resources/$ProfileName-region-$Region.txt"
foreach($site in $sample) {
    $coords="$($site.x) $($site.y) $($site.z) $($site.index)"
    & (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command "oreverify load $coords" -WaitMilliseconds 2000 | Add-Content $evidence
    $result=& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command "oreverify check $coords" -WaitMilliseconds 1000
    $result | Add-Content $evidence
    if(($result -join "`n") -notmatch '\[Ore\] PASS' -or ($result -join "`n") -match '\[Ore\] FAIL') {throw "Resource validation failed: $result"}
    $result | Select-String '\[Ore\] PASS' | ForEach-Object Line
}
