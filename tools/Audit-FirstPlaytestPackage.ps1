param(
 [Parameter(Mandatory=$true)][string]$Package,
 [Parameter(Mandatory=$true)][string]$CoreBaseline,
 [string]$TerrainCompatibilityBaseline,
 [string]$TerrainCompatibilitySha256
)
$ErrorActionPreference='Stop'
$packageRoot=(Resolve-Path -LiteralPath $Package).Path
$baseRoot=(Resolve-Path -LiteralPath $CoreBaseline).Path
$terrainRelative='Mods/Delve/DelveTerrainCompatibility.dll'
$terrainReference=Join-Path $baseRoot $terrainRelative
if($TerrainCompatibilityBaseline){
 if($TerrainCompatibilitySha256 -notmatch '^[A-Fa-f0-9]{64}$'){throw 'An explicit terrain replacement requires its approved SHA256'}
 $terrainReference=(Resolve-Path -LiteralPath $TerrainCompatibilityBaseline).Path
 if((Get-FileHash -LiteralPath $terrainReference -Algorithm SHA256).Hash -ne $TerrainCompatibilitySha256){throw 'Terrain reference differs from its approved SHA256'}
} elseif($TerrainCompatibilitySha256){throw 'Terrain SHA256 requires an explicit reference DLL'}
& (Join-Path $packageRoot 'Verify-Package.ps1')
$expected=@('Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest')
$actual=@(Get-ChildItem (Join-Path $packageRoot 'Mods') -Directory | ForEach-Object Name)
if(Compare-Object $expected $actual){throw 'Missing production module or unexpected developer harness'}
if((Get-Content (Join-Path $packageRoot 'world-name.txt') -Raw).Trim() -ne 'Allium-v0.10'){throw 'Wrong world target'}
$core='Mods/Delve/Delve.dll'
if((Get-FileHash (Join-Path $packageRoot $core)).Hash -ne (Get-FileHash (Join-Path $baseRoot $core)).Hash){throw 'Final core differs from the approved crafting baseline'}
# All approved crafting configuration must survive integration byte-for-byte.
foreach($file in Get-ChildItem (Join-Path $baseRoot 'Mods/Delve/Config') -Recurse -File){
 $relative=$file.FullName.Substring($baseRoot.Length+1)
 if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $packageRoot $relative)).Hash){throw "Crafting data changed: $relative"}
}
foreach($folder in @('Mods','Worlds','Catalogue')){
 foreach($file in Get-ChildItem (Join-Path $baseRoot $folder) -Recurse -File){
  $relative=$file.FullName.Substring($baseRoot.Length+1)
  if($TerrainCompatibilityBaseline -and $relative.Replace('\','/') -eq $terrainRelative){continue}
  if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $packageRoot $relative)).Hash){throw "Approved baseline asset changed: $relative"}
 }
}
$baseModFiles=@(Get-ChildItem (Join-Path $baseRoot 'Mods') -Recurse -File)
$finalModFiles=@(Get-ChildItem (Join-Path $packageRoot 'Mods') -Recurse -File)
if($finalModFiles.Count -ne $baseModFiles.Count+1){throw 'Expected only one extra production file: spell compatibility DLL'}
Add-Type -Path 'D:/Steam/steamapps/common/7 Days To Die/Mods/0_TFP_Harmony/Mono.Cecil.dll'
$spellOwners=@();$terrainOwners=@()
foreach($file in Get-ChildItem (Join-Path $packageRoot 'Mods') -Recurse -Filter '*.dll'){
 $assembly=[Mono.Cecil.AssemblyDefinition]::ReadAssembly($file.FullName)
 try {
  if($assembly.MainModule.GetType('DelveNativeModelVisibility')){$spellOwners+=$file.FullName}
  if($assembly.MainModule.GetType('DelveTerrainCompatibility.PrefabDecoderGate')){$terrainOwners+=$file.FullName}
 } finally {$assembly.Dispose()}
}
if($spellOwners.Count -ne 1){throw 'Expected exactly one spell compatibility implementation'}
if($terrainOwners.Count -ne 1){throw 'Expected exactly one terrain decoder fix'}
if($terrainOwners[0] -ne (Join-Path $packageRoot $terrainRelative)){throw 'Terrain compatibility implementation is outside its approved module path'}
if((Get-FileHash $terrainOwners[0]).Hash -ne (Get-FileHash -LiteralPath $terrainReference).Hash){throw 'Terrain compatibility differs from validated baseline'}
foreach($name in @('Play-Allium.cmd','Play-Allium.ps1','START-HERE.txt','VALIDATION.txt','dungeons-atlas.png','resource-atlas.png')){if(!(Test-Path (Join-Path $packageRoot $name))){throw "Missing player artifact: $name"}}
if(Test-Path (Join-Path $packageRoot 'PlaytestData')){throw 'Player package contains a used test profile'}
Write-Host 'INDEPENDENT PACKAGE AUDIT PASS: integrity, five production modules, byte-identical approved core/configuration/world/catalogue and baseline assets except any explicit terrain replacement, only one added spell DLL, validated terrain compatibility, v0.10 target, player launch/docs and no test profile.'
if($TerrainCompatibilityBaseline){Write-Host "Approved terrain replacement: $terrainReference SHA256=$TerrainCompatibilitySha256"}
