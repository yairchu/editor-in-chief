#!/bin/bash

if [ "$1" == "" ] || [ "$1" == "--help" ]; then
    echo "Usage: $0 <file>"
    echo
    echo "editor-in-chief.sh opens the file in Xcode if it is in an open Xcode project,"
    echo "otherwise it opens the file in Visual Studio Code."
    exit 1
fi

file="$1"
abs_file_path=$(realpath "$file")

open_xcode_projects=$( osascript -e '
tell application "Xcode"
    set res to {}
    repeat with w in windows
        try
            set end of res to path of document of w
        end try
    end repeat
    return res
end tell
')
echo "open_xcode_projects: $open_xcode_projects"

for proj_file in $open_xcode_projects; do
    proj_dir=$(dirname "$proj_file")
    if [[ $(basename "$proj_dir") == "build" ]]; then
        # Probably a cmake build directory
        proj_dir=$(dirname "$proj_dir")
    elif [[ $(basename "$proj_dir") == "MacOSX" ]]; then
        # Looks like a JUCE projucer generated project
        parent_dir=$(dirname "$proj_dir")
        if [[ $(basename "$proj_dir") == "Builds" ]]; then
            # Yep, it's a JUCE projucer project
            proj_dir=$(dirname "$parent_dir")
        fi
    fi
    echo "xcode project folder: $proj_dir"

    if [[ "$abs_file_path" == "$proj_dir"* ]]; then
        xed "$abs_file_path"
        exit 0
    fi
done

code "$abs_file_path"
