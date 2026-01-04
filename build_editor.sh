#!/bin/bash
set -e

# Check if running from root
if [ ! -d "src/pyergonomics" ]; then
    echo "Error: Please run this script from the project root directory."
    exit 1
fi

# Add src to PYTHONPATH so Nuitka can find the pyergonomics package
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

echo "Starting Nuitka build for Editor..."

# Build command
# Note: We use command line flags instead of a config file for compatibility
python -m nuitka \
    --standalone \
    --macos-create-app-bundle \
    --enable-plugin=pyside6 \
    --include-qt-plugins=qml \
    --include-package=pyergonomics \
    --include-package-data=pyergonomics \
    --include-data-dir=src/pyergonomics/ui/qml=pyergonomics/ui/qml \
    --include-data-file=app/editor/editor.qml=editor.qml \
    --nofollow-import-to=scipy \
    --nofollow-import-to=torch \
    --nofollow-import-to=matplotlib \
    --nofollow-import-to=k3d \
    --nofollow-import-to=ipywidgets \
    --nofollow-import-to=ultralytics \
    --nofollow-import-to=pandas \
    --output-dir=build \
    --output-filename=Editor \
    --macos-app-name="Editor" \
    app/editor/editor.py

echo "Build complete!"
echo "App bundle location: build/editor.dist/Editor.app"
echo ""
echo "Note: Since the app requires a project path argument, you should run the binary directly from the terminal:"
echo "  ./build/editor.dist/Editor.app/Contents/MacOS/Editor <path_to_project>"
