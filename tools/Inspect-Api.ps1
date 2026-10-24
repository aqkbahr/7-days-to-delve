param(
    [string]$GamePath = 'D:/Steam/steamapps/common/7 Days To Die',
    [string[]]$Types = @('IModApi'),
    [string]$Method = '',
    [switch]$IL
)
$ErrorActionPreference = 'Stop'
Add-Type -Path (Join-Path $GamePath 'Mods/0_TFP_Harmony/Mono.Cecil.dll')
$assembly = [Mono.Cecil.AssemblyDefinition]::ReadAssembly((Join-Path $GamePath '7DaysToDie_Data/Managed/Assembly-CSharp.dll'))
try {
    foreach ($name in $Types) {
        $type = $assembly.MainModule.GetType($name)
        if (!$type) { throw "Type not found: $name" }
        "TYPE $($type.FullName)"
        if (!$Method) {
            $type.Fields | Where-Object { !$_.Name.StartsWith('Prop') } | ForEach-Object { $_.FullName }
        }
        $type.Methods | Where-Object { !$Method -or $_.Name -match $Method } | ForEach-Object {
            $_.FullName
            if ($IL -and $_.HasBody) { $_.Body.Instructions | ForEach-Object { $_.ToString() } }
        }
    }
} finally { $assembly.Dispose() }
