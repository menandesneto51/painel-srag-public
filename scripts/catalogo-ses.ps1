param(
    [Parameter(Mandatory = $true)][string]$Query,
    [string]$Context = "PAINEL-SRAG-PUBLIC",
    [string]$CatalogRoot = $env:SES_DATA_CATALOG_ROOT,
    [string]$AgentRoot = $env:SES_DATA_CATALOG_AGENT_ROOT,
    [switch]$StrictConfig
)

$ErrorActionPreference = "Stop"
$launcher = Join-Path $PSScriptRoot "catalogo_ses.py"

$argsList = @($launcher, "--query", $Query, "--context", $Context)
if ($CatalogRoot) { $argsList += @("--catalog-root", $CatalogRoot) }
if ($AgentRoot) { $argsList += @("--agent-root", $AgentRoot) }
if ($StrictConfig) { $argsList += "--strict-config" }

if ($env:SES_DATA_CATALOG_PYTHON) {
    & $env:SES_DATA_CATALOG_PYTHON @argsList
    exit $LASTEXITCODE
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    & python @argsList
    exit $LASTEXITCODE
}

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 @argsList
    exit $LASTEXITCODE
}

throw "Python não encontrado. Configure SES_DATA_CATALOG_PYTHON ou disponibilize python/py no PATH."
