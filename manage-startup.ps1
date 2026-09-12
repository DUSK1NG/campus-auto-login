param([ValidateSet('Install','Remove')][string]$Action = 'Install', [switch]$ValidateOnly)
$ErrorActionPreference = 'Stop'
$appExe = Join-Path $PSScriptRoot 'campus-auto-login.exe'
$configFile = Join-Path $PSScriptRoot '.env'
$startupDir = [Environment]::GetFolderPath('Startup')
$shortcutFile = Join-Path $startupDir 'Campus Auto Login.lnk'
$shellObject = New-Object -ComObject WScript.Shell
if ($Action -eq 'Remove') {
    if (Test-Path -LiteralPath $shortcutFile) {
        $existing = $shellObject.CreateShortcut($shortcutFile)
        if ($existing.TargetPath -ne $appExe) { throw 'Shortcut belongs to another installation. Run removal from that folder.' }
        if (-not $ValidateOnly) { Remove-Item -LiteralPath $shortcutFile }
    }
    Write-Host 'Startup disabled (or already absent). Running application is not stopped.'
    exit 0
}
if (-not (Test-Path -LiteralPath $appExe)) { throw 'Extract the Windows ZIP first; campus-auto-login.exe is missing.' }
if (-not (Test-Path -LiteralPath $configFile)) { throw 'Run configure.cmd and fill in .env first.' }
if (Test-Path -LiteralPath $shortcutFile) {
    $existing = $shellObject.CreateShortcut($shortcutFile)
    if ($existing.TargetPath -ne $appExe) { throw 'Another installation owns this startup shortcut. Remove it from that folder first.' }
}
if ($ValidateOnly) { Write-Host 'Startup paths validated; no changes made.'; exit 0 }
$shortcut = $shellObject.CreateShortcut($shortcutFile)
$shortcut.TargetPath = $appExe
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.Description = 'Campus network authentication for the current Windows user'
$shortcut.Save()
$check = $shellObject.CreateShortcut($shortcutFile)
if ($check.TargetPath -ne $appExe -or $check.WorkingDirectory -ne $PSScriptRoot) { throw 'Shortcut verification failed.' }
Write-Host 'Installed for this Windows user. Starts at next sign-in; administrator rights are not required.'
Write-Host 'Keep this folder in place. Logs: logs\campus.log'
