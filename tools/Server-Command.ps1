param([Parameter(Mandatory=$true)][string]$Command,[string]$ProfileName='LivingBorder',[ValidateRange(800,30000)][int]$WaitMilliseconds=800)
$ErrorActionPreference='Stop'
if ($ProfileName -notmatch '^[A-Za-z0-9_-]+$') { throw 'Invalid profile name.' }
$root=Split-Path $PSScriptRoot -Parent
[xml]$config=Get-Content (Join-Path $root "playtest/$ProfileName/serverconfig.xml")
$port=[int]$config.SelectSingleNode('/ServerSettings/property[@name="TelnetPort"]').value
$password=$config.SelectSingleNode('/ServerSettings/property[@name="TelnetPassword"]').value
$client=[Net.Sockets.TcpClient]::new()
try {
    $client.Connect('127.0.0.1',$port)
    $stream=$client.GetStream(); $stream.ReadTimeout=4000
    $writer=[IO.StreamWriter]::new($stream); $writer.NewLine="`r`n"; $writer.AutoFlush=$true
    $buffer=New-Object byte[] 65536
    Start-Sleep -Milliseconds 300
    if ($stream.DataAvailable) { $null=$stream.Read($buffer,0,$buffer.Length) }
    $writer.WriteLine($password)
    Start-Sleep -Milliseconds 300
    if ($stream.DataAvailable) { $null=$stream.Read($buffer,0,$buffer.Length) }
    $writer.WriteLine($Command)
    Start-Sleep -Milliseconds $WaitMilliseconds
    while ($stream.DataAvailable) {
        $count=$stream.Read($buffer,0,$buffer.Length)
        [Text.Encoding]::UTF8.GetString($buffer,0,$count)
        Start-Sleep -Milliseconds 100
    }
} finally { $client.Dispose() }
