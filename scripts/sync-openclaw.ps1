$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Resolve-RepoRoot {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StartPath
    )

    try {
        $gitRoot = (& git -C $StartPath rev-parse --show-toplevel 2>$null).Trim()
        if ($LASTEXITCODE -eq 0 -and $gitRoot) {
            $candidate = (Resolve-Path -Path $gitRoot).Path
            if (Test-Path (Join-Path $candidate "pyproject.toml")) {
                return $candidate
            }
        }
    }
    catch {
    }

    $cursor = (Resolve-Path -Path $StartPath).Path
    while ($true) {
        $hasPyproject = Test-Path (Join-Path $cursor "pyproject.toml")
        $hasSkills = Test-Path (Join-Path $cursor "skills")
        $hasSource = Test-Path (Join-Path $cursor "src\hunter_agent")

        if ($hasPyproject -and $hasSkills -and $hasSource) {
            return $cursor
        }

        $parent = Split-Path -Parent $cursor
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $cursor) {
            break
        }
        $cursor = $parent
    }

    throw "Failed to detect repo root automatically. Ensure this script is inside the repo and repo has pyproject.toml, skills, and src/hunter_agent."
}

function Remove-IfExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PathToRemove,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    if (Test-Path $PathToRemove) {
        Remove-Item -Recurse -Force $PathToRemove
        Write-Host "Removed $Label : $PathToRemove"
    }
    else {
        Write-Host "Skip remove (not found) $Label : $PathToRemove"
    }
}

$repoRoot = Resolve-RepoRoot -StartPath $PSScriptRoot
$openClawWorkspace = Join-Path $HOME ".openclaw\workspace"
$openClawSkillsRoot = Join-Path $openClawWorkspace "skills"
$openClawSrcRoot = Join-Path $openClawWorkspace "src"

$skillNames = @(
    "arxiv-robotics-daily",
    "talent-db-sync"
)

$packageName = "hunter_agent"
$sourceSkillsRoot = Join-Path $repoRoot "skills"
$sourcePackagePath = Join-Path $repoRoot ("src\" + $packageName)

if (-not (Test-Path $sourcePackagePath)) {
    throw "Source package folder not found: $sourcePackagePath"
}

foreach ($skill in $skillNames) {
    $srcSkill = Join-Path $sourceSkillsRoot $skill
    if (-not (Test-Path $srcSkill)) {
        throw "Source skill folder not found: $srcSkill"
    }
}

New-Item -ItemType Directory -Force -Path $openClawSkillsRoot | Out-Null
New-Item -ItemType Directory -Force -Path $openClawSrcRoot | Out-Null

Write-Host "Repo root: $repoRoot"
Write-Host "OpenClaw workspace: $openClawWorkspace"

Write-Host ""
Write-Host "[1/4] Clean old folders"
foreach ($skill in $skillNames) {
    $targetSkillPath = Join-Path $openClawSkillsRoot $skill
    Remove-IfExists -PathToRemove $targetSkillPath -Label "skill"
}
$targetPackagePath = Join-Path $openClawSrcRoot $packageName
Remove-IfExists -PathToRemove $targetPackagePath -Label "source"

Write-Host ""
Write-Host "[2/4] Copy latest skills"
foreach ($skill in $skillNames) {
    $srcSkill = Join-Path $sourceSkillsRoot $skill
    Copy-Item -Recurse -Force -Path $srcSkill -Destination $openClawSkillsRoot
    Write-Host "Copied skill: $skill"
}

Write-Host ""
Write-Host "[3/4] Copy latest source package"
Copy-Item -Recurse -Force -Path $sourcePackagePath -Destination $openClawSrcRoot
Write-Host "Copied source package: $packageName"

Write-Host ""
Write-Host "[4/4] Reinstall dependencies via pip"
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    throw "python command not found. Install Python and ensure python is on PATH."
}

& $pythonCommand.Source -m pip install --upgrade --force-reinstall -e $repoRoot
if ($LASTEXITCODE -ne 0) {
    throw "pip reinstall failed with exit code: $LASTEXITCODE"
}

Write-Host ""
Write-Host "Sync completed."
Write-Host "Skills => $openClawSkillsRoot"
Write-Host "Source => $targetPackagePath"
