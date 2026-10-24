param([string]$GamePath='D:/Steam/steamapps/common/7 Days To Die')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$output=Join-Path $root 'artifacts/inspection'
New-Item -ItemType Directory -Path $output -Force | Out-Null
Add-Type -Path (Join-Path $GamePath 'Mods/0_TFP_Harmony/Mono.Cecil.dll')
$a=[Mono.Cecil.AssemblyDefinition]::ReadAssembly((Join-Path $GamePath '7DaysToDie_Data/Managed/Assembly-CSharp.dll'))
try {
    @($a.MainModule.GetType('PassiveEffects').Fields | Where-Object HasConstant | ForEach-Object Name) |
        ConvertTo-Json | Set-Content (Join-Path $output 'passive-effects.json') -Encoding utf8
} finally { $a.Dispose() }
