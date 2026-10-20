# editor-in-chief

Open files in Xcode when they belong to an open Xcode project, otherwise in
Visual Studio Code. Recognizes CMake `build` and JUCE `Builds/MacOSX` layouts.
Requires macOS and the `xed`, `code`, and `realpath` commands. Check that they
are available:

```sh
command -v xed code realpath
```

If `code` is missing, open VS Code's Command Palette and run
**Shell Command: Install 'code' command in PATH**. The `xed` command comes with
Xcode; make sure Xcode is installed and its command-line tools are configured.

## Install

From the repository directory, copy the script into your user executable directory:

```sh
mkdir -p "$HOME/.local/bin"
install -m 755 editor-in-chief.sh "$HOME/.local/bin/editor-in-chief"
```

Add these lines to `~/.zshrc` (or the startup file for your shell):

```sh
export PATH="$HOME/.local/bin:$PATH"
export EDITOR=editor-in-chief
export VISUAL=editor-in-chief
```

Set both variables because some tools prefer `VISUAL` over `EDITOR`. Open a new
terminal or run `source ~/.zshrc` to apply the settings to your current terminal.
Verify the command is available with `command -v editor-in-chief`.

To update an installed copy, run the `install` command again after updating this
repository. Alternatively, use a symlink so repository changes take effect
immediately (keep the repository at the same location):

```sh
ln -s "$PWD/editor-in-chief.sh" "$HOME/.local/bin/editor-in-chief"
```

Use the symlink instead of copying the script; if you already installed a copy,
remove that copy before creating the symlink.

## Usage

```sh
editor-in-chief path/to/file.cpp:42:5
```

The script accepts `file`, `file:line`, and `file:line:column`, including the
format passed by the Rust `editor-command` crate's `Editor::open_at` method.
It also accepts the vi/emacs-style `+line` or `+line:column` argument before the
file, as passed by tools such as `git-mediate`:

```sh
editor-in-chief +42 path/to/file.cpp
```

It selects the line in Xcode, or the line and column in VS Code. By default,
the script returns after opening the file. Pass `--wait` before the file argument
to wait until the file is closed:

```sh
editor-in-chief --wait path/to/file.cpp:42:5
```

For tools that need editing to finish before continuing, such as Git when editing
a commit message, include `--wait` in the editor setting:

```sh
export EDITOR='editor-in-chief --wait'
export VISUAL='editor-in-chief --wait'
```

To keep the default editor setting without waiting and enable waiting only for
Git, use:

```sh
git config --global core.editor 'editor-in-chief --wait'
```

Paths containing spaces and colons are supported. If the entire argument names
an existing file, it is treated literally, even when it ends in `:42` or `:42:5`.
Otherwise, trailing numeric components are interpreted as a position.

## Tests

Run the routing tests without launching either editor:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```
