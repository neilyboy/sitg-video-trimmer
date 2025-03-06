#!/bin/bash

echo "SITG Video Trimmer - macOS Installation Script"
echo "=============================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed."
    echo "Please install Python 3.6 or higher from https://www.python.org/downloads/"
    echo "or use Homebrew: brew install python3"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 6 ]); then
    echo "Python version $PYTHON_VERSION detected."
    echo "SITG Video Trimmer requires Python 3.6 or higher."
    echo "Please upgrade your Python installation."
    exit 1
fi

echo "Python $PYTHON_VERSION detected."

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed."
    echo "Installing pip..."
    python3 -m ensurepip --upgrade
fi

# Install required packages
echo "Installing required Python packages..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Check for FFmpeg
echo
echo "Checking for FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo
    echo "FFmpeg is not installed."
    echo
    echo "Please install FFmpeg using Homebrew:"
    echo "1. Install Homebrew if not already installed:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo "2. Install FFmpeg:"
    echo "   brew install ffmpeg"
    echo
    echo "After installing FFmpeg, run this script again."
    exit 1
fi

echo "FFmpeg is installed."

# Check for Tkinter
echo
echo "Checking for Tkinter..."
if ! python3 -c "import tkinter" &> /dev/null; then
    echo
    echo "Tkinter is not installed."
    echo
    echo "Please install Tkinter using Homebrew:"
    echo "1. Install Homebrew if not already installed:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo "2. Install Python Tkinter:"
    echo "   brew install python-tk"
    echo
    echo "After installing Tkinter, run this script again."
    exit 1
fi

echo "Tkinter is installed."

# Create a wrapper script to run the application
echo "Creating launcher script..."
cat > run_sitg_trimmer.command << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/sitg_video_trimmer_new.py"
EOF

chmod +x run_sitg_trimmer.command

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
echo "./run_sitg_trimmer.command"
echo
echo "Note: On macOS, you may need to right-click the run_sitg_trimmer.command file"
echo "and select 'Open' the first time you run it."
echo

echo "Starting SITG Video Trimmer..."
./run_sitg_trimmer.command
