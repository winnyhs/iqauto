<#
(작업 스케줄러 + 바로가기) 스크립트 준비. 더블클릭만으로 UAC 없이 관리자 권한 실행.

- 관리자 PowerShell에서 실행 전제.
- 입력: ExePath, Args, TaskName, ShortcutName.
- 기존 동명 작업 있으면 업데이트(삭제→생성).
- 스케줄러 작업: ONDEMAND, Run with highest privileges, 현재 사용자.
- 바탕화면 바로가기 생성: 대상=schtasks.exe /Run /TN "<TaskName>".
- 검증: 작업 조회, 바로가기 존재 확인.
- 유틸: 제거(-Remove) 지원.
#>

# file: Make-AlwaysAdminShortcut.ps1
<#
Purpose
  - Create a Scheduled Task (Run with highest privileges) and a Desktop shortcut.
  - Double-clicking the shortcut runs the EXE with admin rights WITHOUT UAC prompt.

Usage
  1) Open PowerShell AS ADMIN.
  2) Edit the variables below if needed.
  3) Run: .\Make-AlwaysAdminShortcut.ps1
  4) To remove, run: .\Make-AlwaysAdminShortcut.ps1 -Remove

Why Scheduled Task?
  - UAC policy: silent elevation for normal executables is blocked; Task Scheduler is the supported path.
#>

[CmdletBinding(SupportsShouldProcess)]
param(
  [switch]$Remove
)

# ===== User Settings =====
$ExePath      = "C:\Program Files (x86)\medical\medical.exe"   # target EXE (or python.exe)
$Args         = ""                                             # optional args, e.g. '-m myapp --foo'
$TaskName     = "MedicalElevated"
$ShortcutName = "Medical (Admin).lnk"
# =========================

function Assert-Admin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  $p  = New-Object Security.Principal.WindowsPrincipal($id)
  if (-not $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Run this script in an ELEVATED (Administrator) PowerShell."
  }
}

function Remove-ElevatedTaskAndShortcut {
  param([string]$Name, [string]$LnkName)
  try { schtasks /Delete /TN $Name /F *> $null } catch {}
  $desktop = [Environment]::GetFolderPath("Desktop")
  $lnkPath = Join-Path $desktop $LnkName
  if (Test-Path $lnkPath) { Remove-Item -Force $lnkPath }
  Write-Host "[OK] Removed task '$Name' and shortcut '$lnkPath'"
}

function New-ElevatedTaskAndShortcut {
  param(
    [string]$Exe, [string]$Arguments, [string]$Name, [string]$LnkName
  )
  if (-not (Test-Path $Exe)) { throw "EXE not found: $Exe" }

  # Clean old task (why: ensure idempotency)
  schtasks /Delete /TN $Name /F *> $null

  $user = whoami
  $quotedExe = '"' + $Exe + '"'
  $trValue   = if ($Arguments) { "$quotedExe $Arguments" } else { $quotedExe }

  # Create ON-DEMAND task with highest privileges
  $createCmd = @(
    "/Create",
    "/SC","ONDEMAND",
    "/TN","`"$Name`"",
    "/TR","`"$trValue`"",
    "/RL","HIGHEST",
    "/F",
    "/RU","`"$user`""
  )
  $rc = schtasks $createCmd 2>&1
  if ($LASTEXITCODE -ne 0) { throw "Failed to create task '$Name'. Details: `n$rc" }

  # Desktop shortcut -> runs the task
  $desktop = [Environment]::GetFolderPath("Desktop")
  $lnkPath = Join-Path $desktop $LnkName
  $wsh = New-Object -ComObject WScript.Shell
  $sc  = $wsh.CreateShortcut($lnkPath)
  $sc.TargetPath = "$env:SystemRoot\System32\schtasks.exe"
  $sc.Arguments  = "/Run /TN `"$Name`""
  $sc.WorkingDirectory = Split-Path $Exe
  $sc.IconLocation = "$Exe,0"
  $sc.Save()

  # Validate
  $query = schtasks /Query /TN $Name /FO LIST 2>$null
  if ($LASTEXITCODE -ne 0) { throw "Task '$Name' was not found after creation." }
  if (-not (Test-Path $lnkPath)) { throw "Shortcut was not created: $lnkPath" }

  Write-Host "[OK] Created elevated task '$Name'."
  Write-Host "[OK] Shortcut: $lnkPath"
  Write-Host "Double-click the shortcut to launch WITH admin rights and WITHOUT UAC prompt."
}

try {
  Assert-Admin
  if ($Remove) {
    Remove-ElevatedTaskAndShortcut -Name $TaskName -LnkName $ShortcutName
    return
  }
  New-ElevatedTaskAndShortcut -Exe $ExePath -Arguments $Args -Name $TaskName -LnkName $ShortcutName
}
catch {
  Write-Error $_.Exception.Message
  exit 1
}
