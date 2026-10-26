$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$core=Join-Path $root 'dist/Delve-First-Forest-Clean-20261024-224312'
$previous=(Get-Content (Join-Path $root 'dist/latest-combined-m3-candidate.txt') -Raw).Trim()
foreach($package in @($core,$previous)){& (Join-Path $package 'Verify-Package.ps1')}
$release=Join-Path $root ('dist/Delve-Combined-Latest-CANDIDATE-'+(Get-Date -Format yyyyMMdd-HHmmss))
Copy-Item -LiteralPath $core -Destination $release -Recurse
Copy-Item (Join-Path $previous 'Mods/Delve/DelveSpellVisibility.dll') (Join-Path $release 'Mods/Delve')
foreach($file in @('M3-EQUIPMENT-SPELLS.txt','M3-PLAYTEST.txt')){Copy-Item (Join-Path $previous $file) $release}
Copy-Item (Join-Path $previous 'Evidence/SpellVisibilityCompatibility.cs') (Join-Path $release 'Evidence/SpellVisibilityCompatibility.cs')
Copy-Item (Join-Path $core 'START-HERE.txt') (Join-Path $release 'CRAFTING-GUIDE.txt')
Copy-Item (Join-Path $core 'VALIDATION.txt') (Join-Path $release 'Evidence/TerrainCraftingSourceValidation.txt')
'PENDING: combined latest core, terrain decoder and spell compatibility acceptance. Previous evidence is source history.'|Set-Content (Join-Path $release 'START-HERE.txt')
'PENDING combined latest acceptance.'|Set-Content (Join-Path $release 'VALIDATION.txt')
$sources=@{core=$core;m3Original='Delve-Forest-M3-20261024-220158';mapEnemyBase='Delve-Combined-Playtest-20261024-220742';spellSource=$previous;spellCompatibility='Target collider ownership and exception-safe burst-source scope';engineValidation='PENDING integrated latest acceptance';gameTarget='3.3.0 (b18)'}
$sources|ConvertTo-Json|Set-Content (Join-Path $release 'sources.json') -Encoding utf8
$manifest=@{name='Allium Latest Combined Candidate';version='0.7.2-dev-candidate';gameVersion='3.3.0 (b18)';acceptance='PENDING';files=@()}
$manifest.files=@(Get-ChildItem $release -Recurse -File|Where-Object {$_.FullName -ne (Join-Path $release 'manifest.json')}|Sort-Object FullName|ForEach-Object{@{path=$_.FullName.Substring($release.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash}})
$manifest|ConvertTo-Json -Depth 5|Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$release|Set-Content (Join-Path $root 'dist/latest-combined-m3-candidate.txt') -Encoding utf8
Write-Host "Latest combined candidate: $release"
