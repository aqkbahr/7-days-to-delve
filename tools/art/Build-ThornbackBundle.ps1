$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$project=Join-Path $root 'artifacts\thornback\UnityProject'
Copy-Item (Join-Path $PSScriptRoot 'BuildThornbackBundle.cs') (Join-Path $project 'Assets\Editor\BuildThornbackBundle.cs')
Copy-Item (Join-Path $root 'src\Art\delveThornbackBoar\delveThornbackBoar.fbx'),(Join-Path $root 'src\Art\delveThornbackBoar\Thornback_Albedo.png') (Join-Path $project 'Assets\Thornback')
$arguments=@('-batchmode','-nographics','-projectPath',('"'+$project+'"'),'-executeMethod','BuildThornbackBundle.Run','-logFile',('"'+(Join-Path $root 'artifacts\thornback\unity-final-build.log')+'"'))
$p=Start-Process 'D:\Unity\Hub\Editor\2022.3.62f2\Editor\Unity.exe' -ArgumentList $arguments -WindowStyle Hidden -PassThru
Write-Output ('Unity build process '+$p.Id)
