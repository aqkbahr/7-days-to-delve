param([string]$ProfileName='AlliumFarming',[string]$BaseRelease='',[string]$FarmingRelease='')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if($ProfileName -notmatch '^[A-Za-z0-9_-]+$'){throw 'Invalid profile name'}
$profile=Join-Path $root ('playtest/'+$ProfileName)
if(Test-Path $profile){throw 'Use a new profile name; existing test saves are preserved'}
if(!$BaseRelease){$BaseRelease=(Get-Content (Join-Path $root 'dist/latest-forest-release.txt') -Raw).Trim()}
if(!$FarmingRelease){$FarmingRelease=(Get-Content (Join-Path $root 'dist/latest-farming-release.txt') -Raw).Trim()}
& (Join-Path $BaseRelease 'Verify-Package.ps1')
& (Join-Path $FarmingRelease 'Verify-Package.ps1')
$world=(Get-Content (Join-Path $BaseRelease 'world-name.txt') -Raw).Trim()
if($world -ne 'Allium-v0.9'){throw 'This integration targets the verified Allium-v0.9 Forest baseline'}
# Prepare the server config and harness, then use only pinned release content.
& (Join-Path $PSScriptRoot 'Prepare-FarmingProbe.ps1') -ProfileName $ProfileName
foreach($mod in Get-ChildItem (Join-Path $BaseRelease 'Mods') -Directory) {
    if($mod.Name -eq 'Delve'){continue}
    Copy-Item -LiteralPath $mod.FullName -Destination (Join-Path $profile 'Mods') -Recurse -Force
}
# Replace the provisional core inside this freshly-created isolated profile.
$target=[IO.Path]::GetFullPath((Join-Path $profile 'Mods/Delve'))
if(!$target.StartsWith([IO.Path]::GetFullPath($profile)+[IO.Path]::DirectorySeparatorChar)){throw 'Invalid core destination'}
Remove-Item -LiteralPath $target -Recurse -Force
Copy-Item -LiteralPath (Join-Path $FarmingRelease 'Mods/Delve') -Destination (Join-Path $profile 'Mods') -Recurse
New-Item -ItemType Directory -Path (Join-Path $profile 'GeneratedWorlds') -Force|Out-Null
Copy-Item -LiteralPath (Join-Path $BaseRelease ('Worlds/'+$world)) -Destination (Join-Path $profile 'GeneratedWorlds') -Recurse
Copy-Item -LiteralPath (Join-Path $root 'src/Code') -Destination (Join-Path $profile 'CodeSnapshot') -Recurse
@{baseRelease=$BaseRelease;farmingRelease=$FarmingRelease;world=$world} | ConvertTo-Json | Set-Content (Join-Path $profile 'integration-sources.json')
[xml]$cfg=Get-Content (Join-Path $profile 'serverconfig.xml')
foreach($entry in @{GameWorld=$world;GameName='AlliumFarming';ServerName='Delve Allium Farming';ServerPort='28230';TelnetPort='28239'}.GetEnumerator()) {
    $cfg.SelectSingleNode("/ServerSettings/property[@name='$($entry.Key)']").SetAttribute('value',$entry.Value)
}
$cfg.Save((Join-Path $profile 'serverconfig.xml'))
Write-Host "Pinned Allium farming profile: $profile"
