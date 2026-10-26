param(
 [Parameter(Mandatory=$true)][string]$ProductionProfile,
 [Parameter(Mandatory=$true)][string]$EvidenceDirectory,
 [Parameter(Mandatory=$true)][string]$ValidationFile,
 [switch]$IncludePresentation
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$profile=(Resolve-Path -LiteralPath $ProductionProfile).Path
$base=Join-Path $root 'dist/Delve-Combined-Playtest-20261024-233416'
& (Join-Path $base 'Verify-Package.ps1')
$catalogue=Join-Path $profile 'AcceptanceCatalogue'
foreach($file in @('first-playtest.json','forest-ready-catalogue.txt')){if(!(Test-Path (Join-Path $catalogue $file))){throw 'Missing frozen acceptance catalogue'}}
if(!(Test-Path -LiteralPath $ValidationFile)){throw 'Missing validation record'}
$modules=@('Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest','ZDelveRecruits')
if($IncludePresentation){$modules+='ZDelvePresentation'}
foreach($name in $modules){if(!(Test-Path (Join-Path $profile "Mods/$name/ModInfo.xml"))){throw "Missing production module $name"}}
$testedFile=Get-ChildItem -LiteralPath $EvidenceDirectory -Filter 'tested-mods*.json'|Sort-Object LastWriteTime -Descending|Select-Object -First 1
if(!$testedFile){throw 'No passing native suite file hashes found'}
$tested=Get-Content -LiteralPath $testedFile.FullName -Raw|ConvertFrom-Json
foreach($name in $modules){
 foreach($file in Get-ChildItem (Join-Path $profile "Mods/$name") -Recurse -File){
  $relative=$file.FullName.Substring($profile.Length+1).Replace('\','/')
  $entry=@($tested|Where-Object path -eq $relative)
  if($entry.Count -ne 1 -or (Get-FileHash -LiteralPath $file.FullName).Hash -ne $entry[0].sha256){throw "Untested production file: $relative"}
 }
}
$release=Join-Path $root ('dist/Delve-Forest-Access-'+(Get-Date -Format yyyyMMdd-HHmmss))
if(Test-Path $release){throw 'Candidate already exists'}
New-Item -ItemType Directory -Path $release,(Join-Path $release 'Mods'),(Join-Path $release 'Evidence'),(Join-Path $release 'Catalogue')|Out-Null
foreach($file in Get-ChildItem $base -File){if($file.Name -ne 'manifest.json'){Copy-Item -LiteralPath $file.FullName -Destination $release}}
Copy-Item (Join-Path $base 'Worlds') $release -Recurse
foreach($name in $modules){Copy-Item -LiteralPath (Join-Path $profile "Mods/$name") -Destination (Join-Path $release 'Mods') -Recurse}
Copy-Item (Join-Path $catalogue '*') (Join-Path $release 'Catalogue') -Recurse
Copy-Item -LiteralPath (Resolve-Path $EvidenceDirectory).Path -Destination (Join-Path $release 'Evidence/ForestAccessAcceptance') -Recurse
Copy-Item -LiteralPath $ValidationFile -Destination (Join-Path $release 'VALIDATION.txt')
Copy-Item (Join-Path $root 'docs/forest-access-playtest.txt') (Join-Path $release 'START-HERE.txt')
Copy-Item (Join-Path $root 'docs/forest-access-playtest.txt') (Join-Path $release 'ACCESS-GUIDE.txt')
Copy-Item (Join-Path $root 'docs/forest-first-playthrough.txt') (Join-Path $release 'FIRST-PLAYTHROUGH.txt')
Copy-Item (Join-Path $root 'docs/wayrest-recruits-playtest.txt') (Join-Path $release 'RECRUITMENT.txt')
Copy-Item (Join-Path $root 'docs/wayrest-recruits-validation.txt') (Join-Path $release 'RECRUITMENT-VALIDATION.txt')
Copy-Item (Join-Path $root 'docs/shrine-resurrection-playtest.txt') (Join-Path $release 'RESURRECTION.txt')
Copy-Item (Join-Path $root 'docs/shrine-resurrection-validation.txt') (Join-Path $release 'RESURRECTION-VALIDATION.txt')
$craftGuide=Join-Path $release 'CRAFTING-GUIDE.txt'
(Get-Content $craftGuide -Raw).Replace('All 208 enabled','All 218 enabled')|Set-Content $craftGuide -Encoding UTF8
$m3=Join-Path $release 'M3-EQUIPMENT-SPELLS.txt'
(Get-Content $m3 -Raw) -replace '(?s)The Arbor environmental-protection draught and proficiency-20 talent behavior.*?unfinished talent trees\.', 'Arbor protection and all proficiency-20 branch entries are included in this update. See ACCESS-GUIDE.txt and VALIDATION.txt; higher unfinished talents remain locked.'|Set-Content $m3 -Encoding UTF8
$m3=Join-Path $release 'M3-PLAYTEST.txt'
(Get-Content $m3 -Raw) -replace '(?s)This build covers M0-M3 equipment and supply chains\..*?those experiences\.', 'This update includes M0-M3 equipment, supply chains, early perks and Arbor protection. See ACCESS-GUIDE.txt and VALIDATION.txt for the combined scope and exact automated evidence. Human pacing, balance, visual fit and general multiplayer acceptance remain.'|Set-Content $m3 -Encoding UTF8
$sources=@{baseline=$base;testedProfile=$profile;world='Allium-v0.10';modules=$modules;scope='100 early perks, Forest onboarding and supply access';presentation=[bool]$IncludePresentation}
$sources|ConvertTo-Json -Depth 4|Set-Content (Join-Path $release 'sources.json') -Encoding UTF8
$manifest=@{name='Forest Access Playtest';version='0.10.0-playtest';gameVersion='3.3.0 (b18)';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object {$_.Name -ne 'manifest.json'}|Sort-Object FullName|ForEach-Object {@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding UTF8
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $root 'artifacts/forest-access-candidate.txt') -Encoding UTF8
Write-Host "Candidate created without changing any release pointer: $release"


