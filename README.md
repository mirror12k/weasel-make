# Weasel Make

Weasel Make is a Makefile-compatible build tool that hides the output of your commands if it executed successfully.
Very useful when executing `make build deploy` over and over again.

## Features

- Bash auto-completions - Just press tab after the `weasel` command to see the list of available actions.
- Output folding - Hides output of successful commands, or shows it if the command failed.
- Secrets obfuscation - Any line of text that looks like it might be sensitive secrets information gets replaced with `***`

## Installation

Install easily with `pip install weasel-make`. If you are installing without `sudo`, make sure to add python to your `PATH` by executing:

```bash
echo 'export PATH=$(python3 -m site --user-base)/bin:$PATH' >> ~/.bashrc
```

## Usage

To execute targets from your Makefile with Weasel Make, use the `weasel` command followed by your target names:
```bash
weasel build deploy
```
This will run the `build` and `deploy` targets as specified in your `Makefile`.

## Makefile Compatibility

Weasel Make is designed to be compatible with standard Makefiles, so you should be able to run your existing Makefiles without any modifications.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or create issues if you encounter any problems or have suggestions for new features.
