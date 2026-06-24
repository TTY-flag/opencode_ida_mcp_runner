# IDA Feeds 

> Manage FLIRT signatures and generate Rust signatures on demand.

# Notes

Can be run as a standalone app (`python feeds_app`) using IDALIB or as an IDAPython plugin.

# Install

The packages should be installed in the interpreter that IDA is using

- `python3 -m pip install -r requirements.txt`

Set the path to your platform's flair tools bin directory e.g. `/flair90/bin/x64linux`

- `cp config.sample.json config.json` and set the variables

## Other dependencies

- `git`
- `idalib`
- `idapro`
- `sigmake` / flair

## Linux & OSX

`ln -s $(pwd) $HOME/.idapro/plugins/ida_feeds`

## Windows

`mklink /D "%APPDATA%\Hex-Rays\IDA Pro\plugins\ida_feeds" "%cd%"`
