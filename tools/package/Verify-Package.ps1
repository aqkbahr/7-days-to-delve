$ErrorActionPreference='Stop'
$manifest=Get-Content (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
foreach($entry in $manifest.files) {
    $file=Join-Path $PSScriptRoot $entry.path
    if (!(Test-Path -LiteralPath $file)) { throw "Missing package file: $($entry.path)" }
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $entry.sha256) { throw "Package file differs: $($entry.path)" }
}
Write-Host "Package verified: $($manifest.version), target $($manifest.gameVersion)."
