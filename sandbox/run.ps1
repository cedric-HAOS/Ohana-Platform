param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $SandboxArgs
)

$ErrorActionPreference = "Stop"

$SandboxDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PlatformDir = Split-Path -Parent $SandboxDir
$WorkspaceDir = Split-Path -Parent $PlatformDir

$AgentDir = Join-Path $WorkspaceDir "Ohana-Agent"
$VenvDir = Join-Path $SandboxDir ".venv"
$Python = Join-Path $VenvDir "Scripts\python.exe"
$Marker = Join-Path $VenvDir ".ohana-sandbox-ready"

if (-not (Test-Path $AgentDir)) {
    Write-Host "ERROR: Ohana-Agent introuvable : $AgentDir"
    exit 1
}

$PyProject = Join-Path $AgentDir "pyproject.toml"

if (-not (Test-Path $PyProject)) {
    Write-Host "ERROR: pyproject.toml Ohana-Agent introuvable."
    exit 1
}

if (-not (Test-Path $Python)) {
    Write-Host "Initialisation du Ohana Sandbox..."
    Write-Host "Creation de l'environnement Python..."

    py -3.13 -m venv $VenvDir

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Impossible de creer l'environnement Python."
        exit $LASTEXITCODE
    }
}

if (-not (Test-Path $Marker)) {
    Write-Host "Installation des dependances Ohana-Agent..."

    & $Python -m pip install --upgrade pip

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    $AgentSpec = "${AgentDir}[development]"

    & $Python -m pip install -e $AgentSpec

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Installation de Ohana-Agent impossible."
        exit $LASTEXITCODE
    }

    New-Item -ItemType File -Path $Marker -Force | Out-Null

    Write-Host "Sandbox pret."
    Write-Host ""
}

$Runner = Join-Path $SandboxDir "runner.py"

# Le parcours de développement et les scénarios de journaux utilisent aussi le
# code et les dépendances Katsuyu.
$NeedsKatsuyu = ($SandboxArgs -contains "--exercise-logs") -or ($SandboxArgs -contains "all") -or ($SandboxArgs -contains "recurring-log-review")
if (($SandboxArgs -contains "run") -and $NeedsKatsuyu) {
    $KatsuyuDir = Join-Path $WorkspaceDir "Ohana-Katsuyu"
    $KatsuyuIndex = [Array]::IndexOf($SandboxArgs, "--katsuyu")
    if ($KatsuyuIndex -ge 0 -and $KatsuyuIndex + 1 -lt $SandboxArgs.Count) {
        $KatsuyuDir = $SandboxArgs[$KatsuyuIndex + 1]
    }
    & $Python -m pip install -e $KatsuyuDir --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

# The runner's exit code carries the verdict. Windows asyncio may print a
# harmless connection reset on stderr when the browser reloads; with Stop it
# aborted a passing run when the output was redirected.
$ErrorActionPreference = "Continue"
& $Python -X utf8 $Runner @SandboxArgs

exit $LASTEXITCODE
