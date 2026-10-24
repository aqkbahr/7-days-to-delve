param([string]$ProfileName='AlliumLocationsFinal')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$evidence=Join-Path $root 'artifacts/validation/allium-v0.3'
New-Item -ItemType Directory -Path $evidence -Force | Out-Null
$output=@()
$pois= & (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command 'alliumprobe pois'
$output += $pois
if (($pois -join "`n") -notmatch 'POI count=20') { throw 'Expected exactly 20 loaded POIs; inspect runtime output.' }
$checks=@(
    @('-2621 -2212','height=65 biome=pine_forest water=False'),
    @('-573 -1393','height=76 biome=burnt_forest water=False'),
    @('-1556 901','height=98 biome=desert water=False'),
    @('-2785 2908','height=132 biome=snow water=False'),
    @('2376 2089','height=100 biome=wasteland water=False'),
    @('614 -82','height=42 biome=desert water=True')
)
foreach($check in $checks) {
    $result= & (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command ('alliumprobe '+$check[0])
    $output += $result
    if(($result -join "`n") -notmatch [regex]::Escape($check[1])) { throw ('Runtime map probe failed: '+$check[0]) }
}
$result= & (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command 'delve verify'
$output += $result
if(($result -join "`n") -notmatch 'PASS: 71') { throw 'Loaded Delve definition check failed' }
$output | Set-Content (Join-Path $evidence 'runtime-probes.txt')
Write-Host 'PASS: 20 registered POIs, all five hubs, lake water and 71 Delve checks.'
