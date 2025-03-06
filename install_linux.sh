#!/bin/bash

echo "SITG Video Trimmer - Linux Installation Script (Direct Install)"
echo "======================================================"
echo

# Function to check if running with sudo
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        return 1
    else
        return 0
    fi
}

# Function to install packages
install_packages() {
    local packages=("$@")
    
    if check_sudo; then
        apt update
        apt install -y "${packages[@]}"
    else
        echo "Installing required system packages. You may be prompted for your password."
        sudo apt update
        sudo apt install -y "${packages[@]}"
    fi
    
    # Check if installation was successful
    for pkg in "${packages[@]}"; do
        if ! dpkg -l | grep -q "$pkg"; then
            echo "Failed to install $pkg. Please install it manually and run this script again."
            return 1
        fi
    done
    
    return 0
}

# Check for and install Python if needed
echo "Checking for Python..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Installing Python 3..."
    if ! install_packages python3; then
        exit 1
    fi
fi

# Get Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
python_major=$(echo "$python_version" | cut -d. -f1)
python_minor=$(echo "$python_version" | cut -d. -f2)

echo "Found Python $python_version"

# Check for and install pip if needed
echo "Checking for pip..."
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Installing python3-pip..."
    if ! install_packages python3-pip; then
        exit 1
    fi
fi

# Check for and install python-tk if needed
echo "Checking for Python Tk..."
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "Python Tkinter is not installed. Installing python3-tk..."
    if ! install_packages python3-tk; then
        exit 1
    fi
fi

# Check for and install FFmpeg if needed
echo "Checking for FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "FFmpeg is not installed. Installing ffmpeg..."
    if ! install_packages ffmpeg; then
        exit 1
    fi
fi

# Install Python packages directly
echo "Installing required Python packages..."

# Read packages from requirements.txt and install them
echo "Installing: $(cat requirements.txt | tr '\n' ' ')"

# Use pip3 to install packages (with --user flag for non-root installation)
if check_sudo; then
    pip3 install $(cat requirements.txt)
else
    pip3 install --user $(cat requirements.txt)
fi

# Check if installation was successful
for pkg in $(cat requirements.txt); do
    if ! python3 -c "import $pkg" &> /dev/null && [ "$pkg" != "opencv-python" ]; then
        if [ "$pkg" = "tk" ]; then
            # Special case for tk which is imported as tkinter
            if ! python3 -c "import tkinter" &> /dev/null; then
                echo "Failed to install $pkg. Please install it manually."
                exit 1
            fi
        elif [ "$pkg" = "pillow" ]; then
            # Special case for pillow which is imported as PIL
            if ! python3 -c "import PIL" &> /dev/null; then
                echo "Failed to install $pkg. Please install it manually."
                exit 1
            fi
        else
            echo "Failed to install $pkg. Please install it manually."
            exit 1
        fi
    fi
done

# Special check for opencv-python
if ! python3 -c "import cv2" &> /dev/null; then
    echo "Failed to install opencv-python. Please install it manually."
    exit 1
fi

# Create a wrapper script to run the application
echo "Creating launcher script..."
cat > run_sitg_trimmer.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/sitg_video_trimmer_new.py"
EOF

chmod +x run_sitg_trimmer.sh

# Clean up old files that are no longer needed
echo "Cleaning up old files..."
if [ -f "sitg_video_trimmer.py" ]; then
    echo "Backing up original monolithic version to sitg_video_trimmer_original.py"
    mv sitg_video_trimmer.py sitg_video_trimmer_original.py
fi

echo
echo "Installation complete!"
echo
echo "To run SITG Video Trimmer, use:"
echo "./run_sitg_trimmer.sh"
echo

echo "Starting SITG Video Trimmer..."
./run_sitg_trimmer.sh
