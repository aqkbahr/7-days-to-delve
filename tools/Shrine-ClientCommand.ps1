param([Parameter(Mandatory=$true)][string]$Command)
$ErrorActionPreference='Stop'
$profile=Join-Path (Split-Path $PSScriptRoot -Parent) 'playtest/ShrineClient'
$pending=Join-Path $profile 'client-command.txt'
if(Test-Path $pending){throw 'A shrine client command is still pending'}
$result=Join-Path $profile 'client-result.txt'
$previous=if(Test-Path $result){(Get-Item $result).LastWriteTimeUtc}else{[DateTime]::MinValue}
Set-Content -LiteralPath $pending -Value $Command
for($attempt=0;$attempt -lt 30;$attempt++){
 Start-Sleep -Milliseconds 500
 if((Test-Path $result) -and (Get-Item $result).LastWriteTimeUtc -gt $previous){Get-Content -LiteralPath $result;return}
}
throw 'No fixture response within 15 seconds; inspect client.log before retrying.'
