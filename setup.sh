#!/bin/bash

# Nano Codec Data Pipeline - Setup Script
# This script installs all dependencies and sets up the environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Clear screen for a clean start
clear

# Print the NINENINESIX logo with colors
echo -e "${CYAN}${BOLD}"
echo "==============================================="
echo "          N I N E N I N E S I X  😼"
echo "==============================================="
echo ""
echo -e "${MAGENTA}"
echo "          /\\_/\\  "
echo "         ( -.- )───┐"
echo "          > ^ <    │"
echo -e "${CYAN}"
echo "==============================================="
echo -e "${NC}"
echo ""
echo -e "${GREEN}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║   Nano Codec Data Pipeline - Setup Script                  ║${NC}"
echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# 1. Check Python version
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Checking Python version"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed!"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

print_info "Found Python $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
    print_success "Python version is compatible (3.10+)"
else
    print_error "Python 3.10 or higher is required!"
    print_info "Current version: $PYTHON_VERSION"
    exit 1
fi

# 2. Install system dependencies based on Python version
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Installing Python development packages"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

print_info "Updating package lists..."
sudo apt update

if [ "$PYTHON_MINOR" -eq 12 ]; then
    print_info "Installing Python 3.12 development packages..."
    sudo apt install -y python3.12-dev libpython3.12-dev
    print_success "Python 3.12 development packages installed"
elif [ "$PYTHON_MINOR" -eq 11 ]; then
    print_info "Installing Python 3.11 development packages..."
    sudo apt install -y python3.11-dev libpython3.11-dev
    print_success "Python 3.11 development packages installed"
elif [ "$PYTHON_MINOR" -eq 10 ]; then
    print_info "Installing Python 3.10 development packages..."
    sudo apt install -y python3.10-dev libpython3.10-dev
    print_success "Python 3.10 development packages installed"
else
    print_info "Installing generic Python 3 development packages..."
    sudo apt install -y python3-dev libpython3-dev
    print_success "Python development packages installed"
fi

# 3. Install libsndfile1
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Installing libsndfile1 (audio library)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if dpkg -l | grep -q libsndfile1; then
    print_success "libsndfile1 is already installed"
else
    print_info "Installing libsndfile1..."
    sudo apt-get update
    sudo apt-get install -y libsndfile1

    if dpkg -l | grep -q libsndfile1; then
        print_success "libsndfile1 installed successfully"
    else
        print_error "Failed to install libsndfile1"
        exit 1
    fi
fi

# 4. Create virtual environment
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Creating virtual environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    print_info "Virtual environment already exists at ./$VENV_DIR"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
        print_info "Creating new virtual environment..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment recreated"
    else
        print_info "Using existing virtual environment"
    fi
else
    print_info "Creating virtual environment at ./$VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created"
fi

# 5. Install Python packages
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Installing Python dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

print_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

print_info "Upgrading pip..."
pip install --upgrade pip

print_info "Installing requirements from requirements.txt..."
print_info "This may take several minutes..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    print_success "All Python packages installed successfully"
else
    print_error "Failed to install some packages"
    exit 1
fi

# 6. Optional: HuggingFace authentication
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: HuggingFace Authentication (Optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

print_info "To download and upload datasets, you need to login to HuggingFace."
echo ""
read -p "Do you want to login to HuggingFace now? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Configuring git credential storage..."
    git config --global credential.helper store

    print_info "Launching HuggingFace login..."
    print_info "You'll need your HuggingFace token from: https://huggingface.co/settings/tokens"
    echo ""

    hf auth login

    if [ $? -eq 0 ]; then
        print_success "Successfully logged in to HuggingFace!"
    else
        print_error "HuggingFace login failed. You can run 'huggingface-cli login' manually later."
    fi
else
    print_info "Skipped HuggingFace login. You can login later with:"
    echo -e "     ${GREEN}git config --global credential.helper store${NC}"
    echo -e "     ${GREEN}hf auth login${NC}"
fi

# Final summary
echo ""
echo ""
echo -e "${GREEN}${BOLD}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║                  Setup Complete! 🎉                        ║${NC}"
echo -e "${GREEN}${BOLD}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
print_success "All dependencies installed successfully!"
echo ""

# Print logo again at the end
echo -e "${CYAN}${BOLD}"
echo "==============================================="
echo "          N I N E N I N E S I X  😼"
echo "==============================================="
echo -e "${NC}"
echo ""

echo -e "${BOLD}Next steps:${NC}"
echo ""
echo -e "  ${YELLOW}1.${NC} Activate the virtual environment:"
echo -e "     ${GREEN}source venv/bin/activate${NC}"
echo ""
echo -e "  ${YELLOW}2.${NC} Login to HuggingFace (if you skipped it):"
echo -e "     ${GREEN}git config --global credential.helper store${NC}"
echo -e "     ${GREEN}hf auth login${NC}"
echo ""
echo -e "  ${YELLOW}3.${NC} Configure your pipeline:"
echo -e "     ${GREEN}nano config.yaml${NC}"
echo ""
echo -e "  ${YELLOW}4.${NC} Run the pipeline:"
echo -e "     ${GREEN}python main.py${NC}"
echo ""
print_info "Documentation: See README.md for usage guide"
print_info "              See CLAUDE.md for technical details"
echo ""
