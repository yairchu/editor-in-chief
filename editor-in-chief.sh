#!/bin/bash

wait_args=()
line=""
column=""
while [[ $# -gt 1 ]]; do
    if [[ "$1" == "--wait" ]]; then
        wait_args=(--wait)
    elif [[ "$1" =~ ^\+([0-9]+)(:([0-9]+))?$ ]]; then
        # Position in the vi/emacs style: +line or +line:column
        line="${BASH_REMATCH[1]}"
        column="${BASH_REMATCH[3]}"
    else
        break
    fi
    shift
done

if [ "$1" == "" ] || [ "$1" == "--help" ]; then
    echo "Usage: $0 [--wait] [+line[:column]] <file>[:line[:column]]"
    echo
    echo "editor-in-chief.sh opens the file in Xcode if it is in an open Xcode project,"
    echo "otherwise it opens the file in Visual Studio Code."
    echo "Xcode supports line selection; Visual Studio Code supports line and column."
    echo "Use --wait to wait until the file is closed before returning."
    exit 1
fi

file="$1"
# Prefer a literal existing filename when its suffix looks like a position.
if [[ -z "$line" && ! -e "$file" ]]; then
    if [[ "$file" =~ ^(.+):([0-9]+):([0-9]+)$ ]]; then
        file="${BASH_REMATCH[1]}"
        line="${BASH_REMATCH[2]}"
        column="${BASH_REMATCH[3]}"
    elif [[ "$file" =~ ^(.+):([0-9]+)$ ]]; then
        file="${BASH_REMATCH[1]}"
        line="${BASH_REMATCH[2]}"
    fi
fi
abs_file_path=$(realpath "$file") || exit 1

open_xcode_projects=$( osascript -e '
tell application "Xcode"
    set res to {}
    repeat with w in windows
        try
            set end of res to path of document of w
        end try
    end repeat
    set text item delimiters of AppleScript to linefeed
    return res as text
end tell
')

while IFS= read -r proj_file; do
    [[ -n "$proj_file" ]] || continue
    proj_dir=$(dirname "$proj_file")
    if [[ $(basename "$proj_dir") == "build" ]]; then
        # Probably a cmake build directory
        proj_dir=$(dirname "$proj_dir")
    elif [[ $(basename "$proj_dir") == "MacOSX" ]]; then
        # Looks like a JUCE projucer generated project
        parent_dir=$(dirname "$proj_dir")
        if [[ $(basename "$parent_dir") == "Builds" ]]; then
            # Yep, it's a JUCE projucer project
            proj_dir=$(dirname "$parent_dir")
        fi
    fi
    proj_dir=$(cd "$proj_dir" && pwd -P) || continue

    if [[ "$abs_file_path" == "$proj_dir/"* ]]; then
        if [[ -n "$line" ]]; then
            exec xed "${wait_args[@]}" --line "$line" "$abs_file_path"
        fi
        exec xed "${wait_args[@]}" "$abs_file_path"
    fi
done <<< "$open_xcode_projects"

if [[ -n "$line" ]]; then
    position="$abs_file_path:$line"
    [[ -z "$column" ]] || position="$position:$column"
    exec code "${wait_args[@]}" --goto "$position"
fi
exec code "${wait_args[@]}" "$abs_file_path"
