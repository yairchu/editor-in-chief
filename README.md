# editor-in-chief

Open files in Xcode when they belong to an open Xcode project, otherwise in
Visual Studio Code. Recognizes CMake `build` and JUCE `Builds/MacOSX` layouts.
Requires macOS and the `xed`, `code`, and `realpath` commands.

Set the script as your editor using its absolute path:

```sh
export EDITOR='/absolute/path/to/editor-in-chief.sh'
```

If you also set `VISUAL`, tools may prefer that setting over `EDITOR`.

The script accepts `file`, `file:line`, and `file:line:column`, including the
format passed by the Rust `editor-command` crate's `Editor::open_at` method.
It selects the line in Xcode, or the line and column in VS Code. Both editors
wait until the file is closed before the script returns.

Paths containing spaces and colons are supported. If the entire argument names
an existing file, it is treated literally, even when it ends in `:42` or `:42:5`.
Otherwise, trailing numeric components are interpreted as a position.

Run the routing tests without launching either editor:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```
