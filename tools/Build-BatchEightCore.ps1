$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$base=(Get-Content (Join-Path $root 'artifacts/batch-08/base.txt') -Raw).Trim()
$target=Join-Path $root 'artifacts/batch-08/Delve.dll'
Add-Type -Path 'D:/Steam/steamapps/common/7 Days To Die/Mods/0_TFP_Harmony/Mono.Cecil.dll'
$assembly=[Mono.Cecil.AssemblyDefinition]::ReadAssembly((Join-Path $base 'Mods/Delve/Delve.dll'))
try {
 $count=0
 foreach($method in $assembly.MainModule.GetType('Delve.XUiC_ProgressionScreen').Methods | Where-Object Name -in 'Refresh','Buy') {
  foreach($il in $method.Body.Instructions) {
   if($il.OpCode.Code -eq 'Ldfld' -and $il.Operand.Name -eq 'tab' -and $il.Next.OpCode.Code -eq 'Ldc_I4_M1') {
    $il.Next.OpCode=[Mono.Cecil.Cil.OpCodes]::Ldc_I4_0; $count++
   }
  }
 }
 if($count -ne 4){throw "Expected four erroneous attribute-tab comparisons; found $count"}
 $assembly.Write($target)
 "PASS: repaired four attribute-tab comparisons in the tested baseline assembly; all other methods retained." | Set-Content (Join-Path $root 'artifacts/batch-08/core-patch.txt')
}finally{$assembly.Dispose()}
$source=Join-Path $root 'src/Code/ProgressionScreen.cs'
$text=[IO.File]::ReadAllText($source)
if(([regex]::Matches($text,'tab==-1')).Count -ne 4){throw 'Unexpected source revision'}
[IO.File]::WriteAllText($source,$text.Replace('tab==-1','tab==0'))
