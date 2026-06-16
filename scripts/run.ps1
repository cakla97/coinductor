param(
    [string]$Config = "config.example.toml"
)

$ErrorActionPreference = "Stop"

Set-Location -Path (Split-Path -Parent $PSScriptRoot)
python -m trading_agent --config $Config

