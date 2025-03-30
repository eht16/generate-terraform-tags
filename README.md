# Generate Terraform tags

Generate tags files using u-ctags for various Terraform providers.
To be used with Geany or other tools which can process tags files.

## Requirements

- Python3
- pyhcl Python package (https://pypi.org/project/pyhcl/)
- ctags 6.1 or later (https://github.com/universal-ctags/ctags)
- up to 1 GB of disk space or even more depending on the providers configured below

## Usage

Edit `WORKING_DIRECTORY`, `CTAGS_COMMAND`, `TERRAFORM_COMMAND` and `TERRAFORM_PROVIDERS_SCRIPT`
according to your environment and then start the script.

## License

Licensed under the GPLv2 or later.

## Author

Enrico Tröger <enrico.troeger@uvena.de>
