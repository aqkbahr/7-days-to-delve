$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root 'artifacts/tests/TotemHexTests.exe'
& "$env:WINDIR/Microsoft.NET/Framework64/v4.0.30319/csc.exe" /nologo ('/out:'+$out) (Join-Path $root 'src/Code/TotemHexRules.cs') (Join-Path $root 'src/Code/FirstTierRules.cs') (Join-Path $root 'tests/TotemHexTests.cs')
if($LASTEXITCODE -ne 0){throw 'Totem test compile failed'}
& $out | Tee-Object (Join-Path $root 'artifacts/tests/totem-hex-results.txt')
if($LASTEXITCODE -ne 0){throw 'Totem tests failed'}
