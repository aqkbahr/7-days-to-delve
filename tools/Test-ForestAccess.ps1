param([string]$ProfileName='ForestAccess20',[string]$EvidenceName='forest-access20',[switch]$Reload)
$ErrorActionPreference='Stop'
if($ProfileName -notmatch '^[A-Za-z0-9_-]+$' -or $EvidenceName -notmatch '^[A-Za-z0-9_-]+$'){throw 'Invalid profile/evidence name'}
$root=Split-Path $PSScriptRoot -Parent
$evidence=Join-Path $root ('artifacts/validation/'+$EvidenceName)
New-Item -ItemType Directory -Path $evidence -Force|Out-Null
if(!(Select-String (Join-Path $root "playtest/$ProfileName/server.log") -Pattern 'StartGame done' -Quiet)){throw 'Wait for the isolated world to finish loading'}
$profile=Join-Path $root "playtest/$ProfileName"
$process=Get-Process -Id ([int](Get-Content (Join-Path $profile 'server.pid') -Raw)) -ErrorAction Stop
$production=@('Delve','DelveWayrest','DelveWildlife','ZDelveDungeons','ZDelveForest','ZDelveRecruits','ZDelvePresentation','ZZZDelveBatch01','ZZZZDelveBatch02','ZZZZZDelvePitch','ZZZZZZDelveBatch03','ZZZZZZZDelveBatch04','ZZZZZZZZDelveRecipeLearning')
$files=@(foreach($module in $production){$directory=Join-Path $profile "Mods/$module";if(Test-Path $directory){Get-ChildItem $directory -Recurse -File}})
if($files|Where-Object {$_.LastWriteTime -gt $process.StartTime}){throw 'Production files changed after server launch; restart before acceptance'}
$hashes=@($files|Sort-Object FullName|ForEach-Object {@{path=$_.FullName.Substring($profile.Length+1).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})
$suffix=if($Reload){'-reload'}else{''}
foreach($test in @(@('onboardingverify','onboarding'),@('rank20verify','rank20'),@('forestready','recipes'),@('delve verify','core'),@('forestintegrated verify','integration'))){
 $result=& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command $test[0] -WaitMilliseconds 3000|Out-String
 $result|Set-Content (Join-Path $evidence ($test[1]+$suffix+'.txt'))
 if($result -notmatch 'PASS' -or $result -match '\] FAIL|Exception:|ERROR:'){throw "Failed $($test[0]): $result"}
 ($result -split "`n"|Where-Object {$_ -match 'PASS'})
}
if($Reload){
 $result=& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command 'forestintegrated restart' -WaitMilliseconds 2000|Out-String
 $result|Set-Content (Join-Path $evidence 'persistence-reload.txt')
 if($result -notmatch 'PASS' -or $result -match '\] FAIL'){throw "Persistence failed: $result"}
}
& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command 'incursionprobe load' -WaitMilliseconds 1000 | Out-Null
& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command 'recruitprobe load' -WaitMilliseconds 1000 | Out-Null
foreach($test in @(@('recruitprobe','recruit-definitions'),@('recruitprobe flow','recruit-flow'),@('recruitprobe resurrection','resurrection'),@('forestintegrated horde','horde'),@('incursionprobe verify','incursion'))){
 $result=& (Join-Path $PSScriptRoot 'Server-Command.ps1') -ProfileName $ProfileName -Command $test[0] -WaitMilliseconds 4000|Out-String
 $result|Set-Content (Join-Path $evidence ($test[1]+$suffix+'.txt'))
 if($result -notmatch 'PASS' -or $result -match '\] FAIL|Exception:|ERROR:'){throw "Failed $($test[0]): $result"}
 ($result -split "`n"|Where-Object {$_ -match 'PASS'})
}
Copy-Item (Join-Path $root "playtest/$ProfileName/server.log") (Join-Path $evidence ('server'+$suffix+'.log')) -Force
foreach($file in $hashes){if((Get-FileHash -LiteralPath (Join-Path $profile $file.path)).Hash -ne $file.sha256){throw "Production file changed during acceptance: $($file.path)"}}
$hashes|ConvertTo-Json -Depth 4|Set-Content (Join-Path $evidence ('tested-mods'+$suffix+'.json'))
Write-Host 'PASS Forest access native suite' 




