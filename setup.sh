set -e

# Define the desired Python version
PYTHON_VERSION="3.12.3"
PYTHON_ALIAS="python3.12"

# Function to install pyenv
install_pyenv() {
    echo "Installing pyenv..."
    curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
    
    # Add pyenv to PATH and initialize it
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv virtualenv-init -)"
    
    # Add pyenv init to shell profile
    echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
    source ~/.bashrc
}

# Check for pyenv and install if not found
if ! command -v pyenv &>/dev/null; then
    install_pyenv
fi

# Install Python version using pyenv if it's not already installed
if ! pyenv versions | grep -q ${PYTHON_VERSION}; then
    pyenv install ${PYTHON_VERSION}
fi

# Set the local Python version for the project
pyenv local ${PYTHON_VERSION}

PROJECT_ROOT=$PWD
VENV_DIR="${PROJECT_ROOT}/.travel-env"

mkdir -p ${VENV_DIR}

# Create a virtual environment using the specific Python version
${PYTHON_ALIAS} -m venv ${VENV_DIR}

source "${VENV_DIR}/bin/activate"

# Install dependencies from the requirements.txt file
pip install -r ${PROJECT_ROOT}/requirements.txt

# Deactivate the virtual environment
deactivate
