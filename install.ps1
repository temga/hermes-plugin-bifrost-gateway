# install.ps1 — Bifrost Gateway plugin pack installer for Hermes Agent (Windows)
#
# Installs five plugins into the correct Hermes plugin directories:
#   1. model-providers/bifrost  — LLM provider (one sk-bf-* key for all models)
#   2. image_gen/bifrost        — image generation via gateway
#   3. web/bifrost              — web search + extract via gateway MCP
#   4. transcription/bifrost    — STT (whisper, gigaam) via gateway
#   5. tts/bifrost              — TTS (espeech, qwen3) via Bifrost → tts-proxy → NeuralDeep
#
# Usage:
#   .\install.ps1                  # install all five
#   .\install.ps1 -Uninstall       # remove all five
#
# After install:
#   1. Add to ~/.hermes/.env:
#      BIFROST_API_KEY=sk-bf-...
#      # Optional: BIFROST_BASE_URL=https://router.rove-ai.ru/v1
#   2. Enable plugins in config.yaml (or use hermes plugins)
#   3. Restart: hermes gateway restart (or new session in CLI)

param(
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$HermesPlugins = if ($env:HERMES_PLUGINS_DIR) { $env:HERMES_PLUGINS_DIR } else { Join-Path $env:USERPROFILE ".hermes\plugins" }
$ScriptDir = $PSScriptRoot

# Plugin definitions: source_dir → target_dir
$Plugins = @(
    "model-providers/bifrost"
    "image_gen/bifrost"
    "web/bifrost"
    "transcription/bifrost"
    "tts/bifrost"
)

function Info($msg)  { Write-Host "✓ $msg" -ForegroundColor Green }
function Warn($msg)  { Write-Host "⚠ $msg" -ForegroundColor Yellow }
function ErrorMsg($msg) { Write-Host "✗ $msg" -ForegroundColor Red }

if ($Uninstall) {
    Write-Host "Uninstalling Bifrost Gateway plugins..."
    foreach ($target in $Plugins) {
        $dir = Join-Path $HermesPlugins $target
        if (Test-Path $dir) {
            Remove-Item -Recurse -Force $dir
            Info "Removed: $target"
        } else {
            Warn "Not found: $target"
        }
    }
    Write-Host ""
    Write-Host "Plugins removed. Edit ~/.hermes/config.yaml to remove 'bifrost' from plugins.enabled."
    exit 0
}

Write-Host "Installing Bifrost Gateway plugin pack..."
Write-Host "  Target: $HermesPlugins"
Write-Host ""

# Create category directories
foreach ($cat in @("model-providers", "image_gen", "web", "transcription", "tts")) {
    $catDir = Join-Path $HermesPlugins $cat
    if (-not (Test-Path $catDir)) {
        New-Item -ItemType Directory -Path $catDir -Force | Out-Null
    }
}

foreach ($src in $Plugins) {
    $srcDir = Join-Path $ScriptDir $src
    $destDir = Join-Path $HermesPlugins $src

    $yamlFile = Join-Path $srcDir "plugin.yaml"
    if (-not (Test-Path $yamlFile)) {
        ErrorMsg "Source not found: $yamlFile"
        exit 1
    }

    # Remove old install if exists
    if (Test-Path $destDir) {
        Remove-Item -Recurse -Force $destDir
    }

    # Copy plugin files
    Copy-Item -Recurse -Force $srcDir $destDir
    Info "Installed: $src"
}

Write-Host ""
Write-Host "Next steps:"
Write-Host ""
Write-Host "  1. Add your Bifrost key to ~/.hermes/.env:"
Write-Host "     BIFROST_API_KEY=sk-bf-..."
Write-Host ""
Write-Host "  2. Enable plugins in config.yaml (plugins.enabled):"
Write-Host "     plugins:"
Write-Host "       enabled:"
Write-Host "         - model-providers/bifrost"
Write-Host "         - image_gen/bifrost"
Write-Host "         - web/bifrost"
Write-Host "         - transcription/bifrost"
Write-Host "         - tts/bifrost"
Write-Host ""
Write-Host "  3. Set active providers:"
Write-Host "     model:"
Write-Host "       provider: bifrost"
Write-Host "       default: neuraldeep/gpt-oss-120b"
Write-Host "     image_gen:"
Write-Host "       provider: bifrost"
Write-Host "     web:"
Write-Host "       search_backend: bifrost"
Write-Host "       extract_backend: bifrost"
Write-Host "     stt:"
Write-Host "       provider: bifrost"
Write-Host "       bifrost:"
Write-Host "         model: neuraldeep/whisper-podlodka-turbo"
Write-Host "     tts:"
Write-Host "       provider: bifrost"
Write-Host "       bifrost:"
Write-Host "         model: espeech-tts"
Write-Host ""
Write-Host "  Note: TTS routes through Bifrost → tts-proxy (localhost:8090) → NeuralDeep API."
Write-Host "        All five services use a single BIFROST_API_KEY (sk-bf-*)."
Write-Host ""
Write-Host "  4. Restart Hermes:"
Write-Host "     hermes gateway restart   # gateway"
Write-Host "     # or start a new session in CLI"
Write-Host ""
Info "Done! One key (sk-bf-*) — LLM + image gen + web search + STT + TTS."
