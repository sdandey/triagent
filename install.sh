#!/usr/bin/env bash
#
# Triagent CLI Installer
# https://github.com/sdandey/triagent
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/sdandey/triagent/main/install.sh | bash
#   curl -sSL https://raw.githubusercontent.com/sdandey/triagent/main/install.sh | bash -s -- --version 0.2.0
#   curl -sSL https://raw.githubusercontent.com/sdandey/triagent/main/install.sh | bash -s -- --no-color
#
# Options:
#   --version VERSION    Install specific version (default: latest)
#   --no-color           Disable colored output
#   --yes/-y             Non-interactive mode (auto-approve)
#   --help               Show help message

set -e

# Configuration
MIN_PYTHON_VERSION="3.11"
PACKAGE_NAME="triagent"

# Global variables
PYTHON_CMD=""
PYTHON_VERSION=""
PIPX_CMD=""
DISABLE_COLOR="${NO_COLOR:-}"

# ============================================================================
# Output and Formatting Functions
# ============================================================================

setup_colors() {
    if [[ -n "${DISABLE_COLOR}" ]] || ! is_tty; then
        RED=""
        GREEN=""
        YELLOW=""
        BLUE=""
        CYAN=""
        BOLD=""
        RESET=""
    else
        RED=$'\033[0;31m'
        GREEN=$'\033[0;32m'
        YELLOW=$'\033[0;33m'
        BLUE=$'\033[0;34m'
        CYAN=$'\033[0;36m'
        BOLD=$'\033[1m'
        RESET=$'\033[0m'
    fi
}

is_tty() {
    test -t 1
}

info() {
    printf "%s[INFO]%s %s\n" "${BLUE}" "${RESET}" "$1"
}

success() {
    printf "%s[OK]%s %s\n" "${GREEN}" "${RESET}" "$1"
}

warn() {
    printf "%s[WARN]%s %s\n" "${YELLOW}" "${RESET}" "$1" >&2
}

error() {
    printf "%s[ERROR]%s %s\n" "${RED}" "${RESET}" "$1" >&2
}

die() {
    error "$1"
    exit 1
}

show_help() {
    cat << EOF
Triagent CLI Installer

Usage:
  curl -sSL https://raw.githubusercontent.com/sdandey/triagent/main/install.sh | bash
  curl -sSL ... | bash -s -- [OPTIONS]

Options:
  --version VERSION    Install specific version (default: latest)
  --no-color           Disable colored output
  -y, --yes            Non-interactive mode (auto-approve all prompts)
  --help               Show this help message

Examples:
  # Install latest version
  curl -sSL https://raw.githubusercontent.com/sdandey/triagent/main/install.sh | bash

  # Install specific version
  curl -sSL ... | bash -s -- --version 0.2.0

  # Non-interactive installation (for CI/CD)
  curl -sSL ... | bash -s -- --yes
EOF
}

# ============================================================================
# Environment Detection Functions
# ============================================================================

detect_os() {
    local os=""
    case "$(uname -s)" in
        Darwin*)   os="macos" ;;
        Linux*)    os="linux" ;;
        MINGW*|MSYS*|CYGWIN*) os="windows" ;;
        *)         os="unknown" ;;
    esac
    echo "$os"
}

detect_arch() {
    local arch=""
    case "$(uname -m)" in
        x86_64|amd64)  arch="x86_64" ;;
        aarch64|arm64) arch="arm64" ;;
        armv7l)        arch="armv7" ;;
        *)             arch="unknown" ;;
    esac
    echo "$arch"
}

detect_linux_distro() {
    if [[ -f /etc/os-release ]]; then
        # shellcheck source=/dev/null
        . /etc/os-release
        echo "${ID:-unknown}"
    elif command -v lsb_release &>/dev/null; then
        lsb_release -si | tr '[:upper:]' '[:lower:]'
    else
        echo "unknown"
    fi
}

is_ci() {
    [[ -n "${CI:-}" ]] || \
    [[ -n "${GITHUB_ACTIONS:-}" ]] || \
    [[ -n "${GITLAB_CI:-}" ]] || \
    [[ -n "${JENKINS_URL:-}" ]] || \
    [[ -n "${AZURE_PIPELINES:-}" ]] || \
    [[ -n "${TF_BUILD:-}" ]] || \
    [[ -n "${CIRCLECI:-}" ]] || \
    [[ -n "${TRAVIS:-}" ]]
}

# ============================================================================
# Version Comparison
# ============================================================================

version_gte() {
    # Returns 0 if $1 >= $2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# ============================================================================
# Python Detection and Installation
# ============================================================================

check_python_version() {
    local python_cmd="$1"
    local version
    version=$("$python_cmd" --version 2>&1 | sed 's/Python //' | cut -d' ' -f1)

    if version_gte "$version" "$MIN_PYTHON_VERSION"; then
        echo "$version"
        return 0
    fi
    return 1
}

find_python() {
    local candidates=("python3.12" "python3.11" "python3" "python")

    for cmd in "${candidates[@]}"; do
        if command -v "$cmd" &>/dev/null; then
            if version=$(check_python_version "$cmd"); then
                PYTHON_CMD="$cmd"
                PYTHON_VERSION="$version"
                return 0
            fi
        fi
    done
    return 1
}

install_python() {
    local os="$1"

    info "Python ${MIN_PYTHON_VERSION}+ not found. Installing..."

    case "$os" in
        macos)
            if command -v brew &>/dev/null; then
                info "Installing Python via Homebrew..."
                brew install python@3.12 || die "Homebrew Python installation failed"
            else
                die "Homebrew not found. Install from https://brew.sh or install Python manually from https://python.org"
            fi
            ;;
        linux)
            local distro
            distro=$(detect_linux_distro)

            case "$distro" in
                ubuntu|debian|pop|linuxmint|elementary)
                    info "Installing Python via apt..."
                    if command -v sudo &>/dev/null; then
                        sudo apt-get update -qq
                        sudo apt-get install -y python3.11 python3.11-venv python3-pip || \
                            sudo apt-get install -y python3 python3-venv python3-pip || \
                            die "apt installation failed"
                    else
                        apt-get update -qq
                        apt-get install -y python3.11 python3.11-venv python3-pip || \
                            apt-get install -y python3 python3-venv python3-pip || \
                            die "apt installation failed"
                    fi
                    ;;
                fedora|rhel|centos|rocky|almalinux)
                    info "Installing Python via dnf..."
                    if command -v sudo &>/dev/null; then
                        sudo dnf install -y python3.11 python3.11-pip || \
                            sudo dnf install -y python3 python3-pip || \
                            die "dnf installation failed"
                    else
                        dnf install -y python3.11 python3.11-pip || \
                            dnf install -y python3 python3-pip || \
                            die "dnf installation failed"
                    fi
                    ;;
                arch|manjaro|endeavouros)
                    info "Installing Python via pacman..."
                    if command -v sudo &>/dev/null; then
                        sudo pacman -Sy --noconfirm python python-pip || die "pacman installation failed"
                    else
                        pacman -Sy --noconfirm python python-pip || die "pacman installation failed"
                    fi
                    ;;
                alpine)
                    info "Installing Python via apk..."
                    apk add --no-cache python3 py3-pip || die "apk installation failed"
                    ;;
                opensuse*|sles)
                    info "Installing Python via zypper..."
                    if command -v sudo &>/dev/null; then
                        sudo zypper install -y python311 python311-pip || die "zypper installation failed"
                    else
                        zypper install -y python311 python311-pip || die "zypper installation failed"
                    fi
                    ;;
                *)
                    die "Unsupported Linux distribution: $distro. Install Python ${MIN_PYTHON_VERSION}+ manually from https://python.org"
                    ;;
            esac
            ;;
        *)
            die "Unsupported OS for automatic Python installation. Install Python ${MIN_PYTHON_VERSION}+ manually from https://python.org"
            ;;
    esac

    # Rehash PATH and verify
    hash -r 2>/dev/null || true
    find_python || die "Python installation succeeded but could not find Python in PATH"

    success "Python ${PYTHON_VERSION} installed"
}

# ============================================================================
# pipx Detection and Installation
# ============================================================================

check_pipx() {
    if command -v pipx &>/dev/null; then
        PIPX_CMD="pipx"
        return 0
    fi
    return 1
}

install_pipx() {
    info "Installing pipx..."

    # Try pip install first (works on all platforms)
    if "$PYTHON_CMD" -m pip install --user pipx 2>/dev/null; then
        # Ensure pipx is in PATH
        "$PYTHON_CMD" -m pipx ensurepath 2>/dev/null || true

        # Update PATH for current session
        export PATH="$HOME/.local/bin:$PATH"

        if check_pipx; then
            success "pipx installed"
            return 0
        fi
    fi

    # Fallback for macOS: use Homebrew
    local os
    os=$(detect_os)
    if [[ "$os" == "macos" ]] && command -v brew &>/dev/null; then
        info "Trying Homebrew for pipx..."
        brew install pipx || die "Homebrew pipx installation failed"
        pipx ensurepath 2>/dev/null || true
        export PATH="$HOME/.local/bin:$PATH"
    fi

    check_pipx || die "pipx installation failed. Install manually: https://pipx.pypa.io/stable/installation/"
    success "pipx installed"
}

# ============================================================================
# Triagent Installation
# ============================================================================

install_triagent() {
    local version="$1"
    local package="$PACKAGE_NAME"

    if [[ -n "$version" ]] && [[ "$version" != "latest" ]]; then
        package="${PACKAGE_NAME}==${version}"
    fi

    info "Installing ${PACKAGE_NAME} via pipx..."

    # Force reinstall if already installed
    if pipx list 2>/dev/null | grep -q "$PACKAGE_NAME"; then
        warn "${PACKAGE_NAME} is already installed. Upgrading..."
        pipx upgrade "$PACKAGE_NAME" 2>/dev/null || \
            (pipx uninstall "$PACKAGE_NAME" 2>/dev/null && pipx install "$package") || \
            die "Failed to upgrade ${PACKAGE_NAME}"
    else
        pipx install "$package" || die "Failed to install ${PACKAGE_NAME}"
    fi

    success "${PACKAGE_NAME} installed"
}

verify_installation() {
    info "Verifying installation..."

    # Refresh PATH
    export PATH="$HOME/.local/bin:$PATH"
    hash -r 2>/dev/null || true

    if command -v "$PACKAGE_NAME" &>/dev/null; then
        local version
        version=$("$PACKAGE_NAME" --version 2>&1 || echo "unknown")
        success "${PACKAGE_NAME} is ready: $version"
        return 0
    fi

    # Check if it's in pipx but not in PATH
    if pipx list 2>/dev/null | grep -q "$PACKAGE_NAME"; then
        warn "${PACKAGE_NAME} installed but not in PATH"
        echo ""
        echo "Add this to your shell profile:"
        echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
        return 0
    fi

    return 1
}

# ============================================================================
# PATH Configuration
# ============================================================================

configure_path() {
    local shell_profile=""
    local path_line='export PATH="$HOME/.local/bin:$PATH"'

    # Check if PATH already includes ~/.local/bin
    if [[ ":$PATH:" == *":$HOME/.local/bin:"* ]]; then
        return 0
    fi

    # In CI, just update current session
    if is_ci; then
        export PATH="$HOME/.local/bin:$PATH"
        return 0
    fi

    # Detect shell and profile file
    case "${SHELL:-}" in
        */bash)
            if [[ -f "$HOME/.bash_profile" ]]; then
                shell_profile="$HOME/.bash_profile"
            elif [[ -f "$HOME/.bashrc" ]]; then
                shell_profile="$HOME/.bashrc"
            else
                shell_profile="$HOME/.bash_profile"
            fi
            ;;
        */zsh)
            shell_profile="$HOME/.zshrc"
            ;;
        */fish)
            shell_profile="$HOME/.config/fish/config.fish"
            path_line='set -gx PATH $HOME/.local/bin $PATH'
            ;;
        *)
            shell_profile="$HOME/.profile"
            ;;
    esac

    # Check if already in profile
    if [[ -f "$shell_profile" ]] && grep -q ".local/bin" "$shell_profile"; then
        return 0
    fi

    info "Adding ~/.local/bin to PATH in $shell_profile"

    # Create profile directory if needed (for fish)
    mkdir -p "$(dirname "$shell_profile")"

    # Add to profile
    {
        echo ""
        echo "# Added by ${PACKAGE_NAME} installer"
        echo "$path_line"
    } >> "$shell_profile"

    # Update current session
    export PATH="$HOME/.local/bin:$PATH"

    success "PATH updated. Run 'source $shell_profile' or start a new terminal."
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    local version=""
    local non_interactive=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --version)
                version="$2"
                shift 2
                ;;
            --no-color)
                DISABLE_COLOR=1
                shift
                ;;
            -y|--yes)
                non_interactive=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                die "Unknown option: $1. Use --help for usage."
                ;;
        esac
    done

    # Initialize colors
    setup_colors

    # Auto-enable non-interactive in CI
    if is_ci; then
        non_interactive=true
    fi

    echo ""
    echo "${BOLD}${CYAN}Triagent CLI Installer${RESET}"
    echo "${CYAN}======================${RESET}"
    echo ""

    local os
    os=$(detect_os)
    local arch
    arch=$(detect_arch)

    info "Detected: $os ($arch)"

    # Step 1: Python
    if find_python; then
        success "Python ${PYTHON_VERSION} found"
    else
        if [[ "$non_interactive" == true ]]; then
            install_python "$os"
        else
            warn "Python ${MIN_PYTHON_VERSION}+ not found"
            read -r -p "Install Python automatically? [Y/n] " response
            if [[ "${response:-y}" =~ ^[Yy]$ ]] || [[ -z "$response" ]]; then
                install_python "$os"
            else
                die "Python ${MIN_PYTHON_VERSION}+ required. Install from https://python.org"
            fi
        fi
    fi

    # Step 2: pipx
    if check_pipx; then
        success "pipx found"
    else
        if [[ "$non_interactive" == true ]]; then
            install_pipx
        else
            warn "pipx not found"
            read -r -p "Install pipx automatically? [Y/n] " response
            if [[ "${response:-y}" =~ ^[Yy]$ ]] || [[ -z "$response" ]]; then
                install_pipx
            else
                die "pipx required. Install from https://pipx.pypa.io"
            fi
        fi
    fi

    # Step 3: Configure PATH
    configure_path

    # Step 4: Install triagent
    install_triagent "$version"

    # Step 5: Verify
    if ! verify_installation; then
        warn "Installation complete but verification failed"
    fi

    echo ""
    echo "${GREEN}${BOLD}Installation Complete!${RESET}"
    echo ""
    echo "Get started:"
    echo "  ${CYAN}${PACKAGE_NAME}${RESET}        # Start interactive chat"
    echo "  ${CYAN}${PACKAGE_NAME} /init${RESET}  # Run setup wizard"
    echo ""

    if ! is_ci && [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo "${YELLOW}Note: You may need to restart your terminal or run:${RESET}"
        echo "  source ~/.bashrc  # or ~/.zshrc"
        echo ""
    fi
}

# Run main
main "$@"
