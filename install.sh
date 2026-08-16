#!/usr/bin/env bash
# install.sh — Bifrost Gateway plugin pack installer for Hermes Agent
#
# Installs three plugins into the correct Hermes plugin directories:
#   1. model-providers/bifrost  — LLM provider (one sk-bf-* key for all models)
#   2. image_gen/bifrost        — image generation via gateway
#   3. web/bifrost              — web search + extract via gateway MCP
#
# Usage:
#   ./install.sh                  # install all three
#   ./install.sh --uninstall      # remove all three
#
# After install:
#   1. Add to ~/.hermes/.env:
#      BIFROST_API_KEY=sk-bf-...
#      # Optional: BIFROST_BASE_URL=http://127.0.0.1:8082/v1
#   2. Enable plugins in config.yaml (or use hermes plugins)
#   3. Restart: hermes gateway restart (or new session in CLI)

set -euo pipefail

HERMES_PLUGINS="${HERMES_PLUGINS_DIR:-$HOME/.hermes/plugins}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; }

# Plugin definitions: source_dir → target_dir
declare -A PLUGINS=(
    ["model-providers/bifrost"]="model-providers/bifrost"
    ["image_gen/bifrost"]="image_gen/bifrost"
    ["web/bifrost"]="web/bifrost"
)

uninstall=false
if [[ "${1:-}" == "--uninstall" ]]; then
    uninstall=true
fi

if $uninstall; then
    echo "Uninstalling Bifrost Gateway plugins..."
    for target in "${PLUGINS[@]}"; do
        dir="$HERMES_PLUGINS/$target"
        if [[ -d "$dir" ]]; then
            rm -rf "$dir"
            info "Removed: $target"
        else
            warn "Not found: $target"
        fi
    done
    echo ""
    echo "Plugins removed. Edit ~/.hermes/config.yaml to remove 'bifrost' from plugins.enabled."
    exit 0
fi

echo "Installing Bifrost Gateway plugin pack..."
echo "  Target: $HERMES_PLUGINS"
echo ""

# Create category directories
mkdir -p "$HERMES_PLUGINS/model-providers"
mkdir -p "$HERMES_PLUGINS/image_gen"
mkdir -p "$HERMES_PLUGINS/web"

for src in "${!PLUGINS[@]}"; do
    target="${PLUGINS[$src]}"
    src_dir="$SCRIPT_DIR/$src"
    dest_dir="$HERMES_PLUGINS/$target"

    if [[ ! -f "$src_dir/plugin.yaml" ]]; then
        error "Source not found: $src_dir/plugin.yaml"
        exit 1
    fi

    # Remove old install if exists
    if [[ -d "$dest_dir" ]]; then
        rm -rf "$dest_dir"
    fi

    # Copy plugin files
    cp -r "$src_dir" "$dest_dir"
    info "Installed: $target"
done

echo ""
echo "Next steps:"
echo ""
echo "  1. Add your Bifrost key to ~/.hermes/.env:"
echo "     BIFROST_API_KEY=sk-bf-..."
echo ""
echo "  2. Enable plugins in config.yaml (plugins.enabled):"
echo "     plugins:"
echo "       enabled:"
echo "         - bifrost-provider"
echo "         - bifrost"
echo "         - bifrost-web"
echo ""
echo "  3. Set active providers:"
echo "     image_gen:"
echo "       provider: bifrost"
echo "     web:"
echo "       search_backend: bifrost"
echo "       extract_backend: bifrost"
echo ""
echo "  4. Restart Hermes:"
echo "     hermes gateway restart   # gateway"
echo "     # or start a new session in CLI"
echo ""
info "Done! One key (sk-bf-*) — LLM + image gen + web search."
