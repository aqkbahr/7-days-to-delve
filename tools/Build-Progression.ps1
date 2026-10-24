param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$python='python'
Push-Location $root
try {
 & $python tools/compile_progression_catalog.py
 if($LASTEXITCODE -ne 0){throw 'Catalog generation failed'}
 & $python tools/build_content.py --game $GamePath
 if($LASTEXITCODE -ne 0){throw 'Content generation failed'}
 & tools/Build-Code.ps1 -GamePath $GamePath
 & $python tools/validate_content.py --game $GamePath
 if($LASTEXITCODE -ne 0){throw 'Content validation failed'}
 & tools/Test-State.ps1
 & tools/Test-Progression.ps1
} finally { Pop-Location }

