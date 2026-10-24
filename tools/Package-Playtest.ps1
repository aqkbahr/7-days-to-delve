param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$release=Join-Path $root ('dist/Delve-0.2.0-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path (Join-Path $release 'Mods') -Force | Out-Null
Copy-Item (Join-Path $root 'src/Delve') (Join-Path $release 'Mods') -Recurse
Copy-Item (Join-Path $PSScriptRoot 'package/*') $release
Copy-Item (Join-Path $root 'docs/playtest-guide.txt') (Join-Path $release 'START-HERE.txt')
Copy-Item (Join-Path $root 'docs/playtest-validation.txt') (Join-Path $release 'VALIDATION.txt')
Copy-Item (Join-Path $root 'docs/progression-framework.txt') $release
Copy-Item (Join-Path $root 'docs/progression-validation.txt') $release
$manifest=@{
    name='7 Days to Delve - Living Border'; version='0.2.0'; gameVersion='3.3.0 (b18)';
    steamBuild='25661859'; requires='Bundled TFP_Harmony 1.1.0.4; launch without EAC';
    files=@()
}
$manifest.files=@(Get-ChildItem $release -Recurse -File | Sort-Object FullName | ForEach-Object {
    @{path=$_.FullName.Substring($release.Length+1).Replace('\','/'); sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash}
})
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $release 'manifest.json') -Encoding utf8
& (Join-Path $release 'Verify-Package.ps1')
$zip=$release+'.zip'
Compress-Archive -LiteralPath $release -DestinationPath $zip
(Get-FileHash $zip -Algorithm SHA256).Hash+'  '+(Split-Path $zip -Leaf) | Set-Content ($zip+'.sha256') -Encoding ascii
$release | Set-Content (Join-Path $root 'dist/latest-release.txt') -Encoding utf8
Write-Host "Ready folder: $release"
Write-Host "Share package: $zip"
