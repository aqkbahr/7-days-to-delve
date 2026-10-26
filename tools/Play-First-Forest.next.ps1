param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die',[switch]$InstallOnly)
$ErrorActionPreference='Stop'
# Resolve both the physical D: project and the preserved C: junction to the
# same authoritative release. Old migration copies cannot select Batch 5 again.
$root='D:/Projects/ChatGPT/7 days to delve'
$selection=Get-Content (Join-Path $root 'dist/active-playtest-release.json') -Raw | ConvertFrom-Json
$release=[IO.Path]::GetFullPath($selection.release)
$allowed=[IO.Path]::GetFullPath((Join-Path $root 'dist'))+[IO.Path]::DirectorySeparatorChar
if(!$release.StartsWith($allowed,[StringComparison]::OrdinalIgnoreCase)){throw 'Selected release is outside the active D: project.'}
if(!(Test-Path (Join-Path $release 'manifest.json'))){throw 'The selected Delve release is missing. Do not fall back to an older package.'}
& (Join-Path $release 'Play-Allium.ps1') -GamePath $GamePath -InstallOnly:$InstallOnly
