param([string]$GamePath='')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Hash-File.ps1')
$root=[IO.Path]::GetFullPath($PSScriptRoot)+[IO.Path]::DirectorySeparatorChar
$manifest=Get-Content -LiteralPath (Join-Path $root 'manifest.json') -Raw | ConvertFrom-Json
$seen=@{}
foreach($entry in $manifest.files){
    $path=[IO.Path]::GetFullPath((Join-Path $root $entry.path))
    if(!$path.StartsWith($root,[StringComparison]::OrdinalIgnoreCase) -or $seen.ContainsKey($path)){throw "Invalid manifest path: $($entry.path)"}
    $seen[$path]=$true
    if(!(Test-Path -LiteralPath $path -PathType Leaf)){throw "Missing file: $($entry.path)"}
    if((Get-DelveFileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $entry.sha256){throw "File verification failed: $($entry.path)"}
}
if($GamePath){
    $api=Join-Path $GamePath '7DaysToDie_Data/Managed/Assembly-CSharp.dll'
    if(!(Test-Path -LiteralPath $api) -or (Get-DelveFileHash -LiteralPath $api -Algorithm SHA256).Hash -ne $manifest.gameAssemblySha256){throw "This release requires the tested game build $($manifest.gameVersion). Installed game binaries differ; do not load your save until compatibility is resolved."}
    if(!(Test-Path -LiteralPath (Join-Path $GamePath 'Mods/0_TFP_Harmony/ModInfo.xml'))){throw 'The game installation is missing its bundled TFP Harmony mod.'}
}
Write-Host "Verified $($manifest.displayVersion): $($manifest.files.Count) files; game $($manifest.gameVersion)."
