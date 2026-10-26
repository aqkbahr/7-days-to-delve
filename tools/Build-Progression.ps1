param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die',[switch]$RefreshForestCatalogue)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$python='C:/Users/Michael/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
Push-Location $root
try {
 & $python tools/compile_progression_catalog.py
 if($LASTEXITCODE -ne 0){throw 'Catalog generation failed'}
 & $python tools/build_content.py --game $GamePath
 if($LASTEXITCODE -ne 0){throw 'Content generation failed'}
 & $python tools/build_forest_slice.py
 if($LASTEXITCODE -ne 0){throw 'Strict Forest crafting closure failed'}
 # Processing validation also regenerates live recipe ownership; compile it below.
 & $python tools/validate_processing.py --game $GamePath
 if($LASTEXITCODE -ne 0){throw 'Forest processing validation failed'}
 & $python tools/validate_forged.py --game $GamePath
 if($LASTEXITCODE -ne 0){throw 'Forged equipment validation failed'}
 if($RefreshForestCatalogue) {
  & $python tools/build_forest_catalogue.py --game $GamePath
  if($LASTEXITCODE -ne 0){throw 'Forest catalogue generation failed'}
 }
 & $python tools/build_progression_ui.py --game $GamePath
 if($LASTEXITCODE -ne 0){throw 'Progression UI generation failed'}
 & tools/Build-Code.ps1 -GamePath $GamePath
 & tools/Build-TerrainCompatibility.ps1 -GamePath $GamePath
 & tools/Build-TomeTrading.ps1 -GamePath $GamePath
 & $python tools/validate_content.py --game $GamePath
 if($LASTEXITCODE -ne 0){throw 'Content validation failed'}
 & $python tools/validate_farming.py
 if($LASTEXITCODE -ne 0){throw 'Farming validation failed'}
 & $python tools/validate_starter_equipment.py
 if($LASTEXITCODE -ne 0){throw 'Starter equipment validation failed'}
 & tools/Test-State.ps1
 if($RefreshForestCatalogue) {
  & $python tools/validate_forest_catalogue.py --game $GamePath
  if($LASTEXITCODE -ne 0){throw 'Forest catalogue validation failed'}
 }
 & tools/Test-ForestOwnership.ps1
 & tools/Test-HealingTotem.ps1
 & tools/Test-ForgedSpells.ps1
 & tools/Test-Progression.ps1
 & $python tools/validate_progression_ui.py --game $GamePath
 if($LASTEXITCODE -ne 0){throw 'Progression UI validation failed'}
 & tools/Test-ProgressionUi.ps1
 & tools/Test-FirstTier.ps1
 & $python tools/validate_first_tier.py
 if($LASTEXITCODE -ne 0){throw 'First-tier equipment validation failed'}
 & tools/Test-Rank20.ps1
 if($LASTEXITCODE -ne 0){throw 'Rank-20 rules failed'}
 & $python tools/validate_forest_access.py
 if($LASTEXITCODE -ne 0){throw 'Forest perk and onboarding access failed'}
} finally { Pop-Location }
