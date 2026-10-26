function Get-DelveFileHash {
    param([Parameter(Mandatory=$true)][string]$LiteralPath,[string]$Algorithm='SHA256')
    if($Algorithm -ne 'SHA256'){throw 'Only SHA256 is supported.'}
    $stream=[IO.File]::OpenRead($LiteralPath)
    $sha=[Security.Cryptography.SHA256]::Create()
    try { [pscustomobject]@{Hash=([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-','')} }
    finally {$stream.Dispose();$sha.Dispose()}
}
