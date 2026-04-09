param(
    [Parameter(Mandatory=$true)][string]$TargetRepo,
    [Parameter(Mandatory=$true)][string]$SkillRepo,
    [ValidateSet("symlink","junction","copy")][string]$Mode = "junction"
)

$TargetRepo = (Resolve-Path $TargetRepo).Path
$SkillRepo  = (Resolve-Path $SkillRepo).Path
$SkillLink  = Join-Path $TargetRepo ".agents\skills\codex-autoresearch"

New-Item -ItemType Directory -Force (Split-Path $SkillLink -Parent) | Out-Null

if (Test-Path $SkillLink) {
    Remove-Item $SkillLink -Recurse -Force
}

switch ($Mode) {
    "symlink" {
        New-Item -ItemType SymbolicLink -Path $SkillLink -Target $SkillRepo | Out-Null
    }
    "junction" {
        cmd /c "mklink /J `"$SkillLink`" `"$SkillRepo`"" | Out-Null
    }
    "copy" {
        Copy-Item -Recurse $SkillRepo $SkillLink
    }
}

Write-Host "Installed codex-autoresearch skill:"
Write-Host "  target repo: $TargetRepo"
Write-Host "  skill repo : $SkillRepo"
Write-Host "  mode       : $Mode"
Write-Host ""
Write-Host "Next:"
Write-Host "  1) cd $TargetRepo"
Write-Host "  2) codex"
Write-Host "  3) invoke: `$codex-autoresearch"
