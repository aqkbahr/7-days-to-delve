param(
    [string]$GamePath='D:/Steam/steamapps/common/7 Days To Die',
    [string]$ProfileName='LivingBorder'
)
$ErrorActionPreference='Stop'
if ($ProfileName -notmatch '^[A-Za-z0-9_-]+$') { throw 'Use letters, digits, hyphens and underscores for profile name.' }
$root=Split-Path $PSScriptRoot -Parent
$profilePath=Join-Path $root ('playtest/'+$ProfileName)
$mods=Join-Path $profilePath 'Mods'
New-Item -ItemType Directory -Path $mods -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $root 'src/Delve') -Destination $mods -Recurse -Force
[xml]$config=Get-Content -LiteralPath (Join-Path $GamePath 'serverconfig.xml')
$settings=@{
    ServerName='Delve Living Border Playtest'; ServerDescription='Private Delve prototype test';
    ServerVisibility='0'; ServerIP='127.0.0.1'; ServerPort='27930';
    ServerPassword='delve-local-test'; ServerMaxPlayerCount='4';
    ServerAllowCrossplay='false'; EACEnabled='false';
    GameWorld='Navezgane'; GameName='DelveLivingBorder';
    UserDataFolder=$profilePath; LandClaimCount='2';
    TelnetEnabled='true'; TelnetPort='27939';
    TelnetPassword=[Guid]::NewGuid().ToString('N');
    WebDashboardEnabled='false'; TerminalWindowEnabled='false'
}
foreach($entry in $settings.GetEnumerator()) {
    $p=$config.SelectSingleNode("/ServerSettings/property[@name='$($entry.Key)']")
    if (!$p) { $p=$config.CreateElement('property'); $p.SetAttribute('name',$entry.Key); $null=$config.DocumentElement.AppendChild($p) }
    $p.SetAttribute('value',$entry.Value)
}
$config.Save((Join-Path $profilePath 'serverconfig.xml'))
@{ GamePath=$GamePath; ProfilePath=$profilePath; Prepared=(Get-Date).ToString('o') } |
    ConvertTo-Json | Set-Content (Join-Path $profilePath 'profile.json') -Encoding utf8
Write-Host "Prepared isolated profile: $profilePath"
Write-Host 'Native game installation and regular saves were not modified.'
