#!/usr/bin/env bash

# Quick and Dirty script to setup the dev environment
# activate a virtualenv before running this script

set -o errexit   # Exit on most errors
set -o errtrace  # Make sure any error trap is inherited
set -o pipefail  # Exit on failures earlier in a pipeline


function init() {
	if [[ -z "$VIRTUAL_ENV" ]]; then
	  printf "please activate your virtualenv before continuing\n"
	  exit 1
	fi

	# paths
	SETUP_SCRIPT="$(realpath "${BASH_SOURCE[0]}")"
	SETUP_DIR="$(dirname "$SETUP_SCRIPT")"
	PROJ_ROOT="$(dirname "$SETUP_DIR")"

	# colours for pretty_print
	typeset -rg ta_none="$(tput sgr0 2> /dev/null || true)"
	typeset -rg ta_bold="$(tput bold || true)"
	typeset -rg fg_cyan="$(tput setaf 6 || true)"
	typeset -rg fg_red="$(tput setaf 1 || true)"
	typeset -rg fg_yellow="$(tput setaf 3 || true)"
}


function pretty_print() {
	local fmt="${2:-$fg_cyan$ta_bold}"
	if [[ "$fmt" = "err" ]]; then
		printf '%b%s%b\n' "$fg_red$ta_bold" "$1" "$ta_none" 1>&2
	else
		printf '%b%s%b\n' "$fmt" "$1" "$ta_none"
	fi
}


function link_precommit_hook() {
	pretty_print "symlinking pre-commit.sh into .git/hook"
	local PRE_COMMIT_HOOK="$PROJ_ROOT/.git/hooks/pre-commit"
	if [[ ! -f "$PRE_COMMIT_HOOK" ]]; then
		ln -s "$SETUP_DIR/pre-commit" "$PRE_COMMIT_HOOK"
		chmod +700 "$PRE_COMMIT_HOOK"  # commit-hooks must be executable
	else
		pretty_print "pre-commit already exists" "$fg_yellow"
	fi
}


function add_pth_to_site_packages() {
	pretty_print "adding test_proj.pth to site-packages"

	local PTH_FILE="$SETUP_DIR/test_proj.pth"
	if [[ ! -f "$PTH_FILE" ]]; then
		cat >"$PTH_FILE" <<-EOF
			$PROJ_ROOT
			$PROJ_ROOT/test_proj
			$PROJ_ROOT/test_proj/apps
			EOF
	fi

	sitepackages=("$VIRTUAL_ENV"/lib/python*/site-packages)
	if ! [[ "${#sitepackages[@]}" -eq 1 ]]; then
		pretty_print "cannot find site-packages at $VIRTUAL_ENV/lib/" "$fg_yellow"
	    exit 1
	fi

	LINK_PATH="${sitepackages[0]}/test_proj.pth"
	if [[ ! -f "$LINK_PATH" ]]; then
	    ln -s "$PTH_FILE" "$LINK_PATH"
	else
		pretty_print "$LINK_PATH already exists" "$fg_yellow"
	fi
}


function install_python_requirements() {
	pretty_print "installing python requirements"
	pip install -qr "$PROJ_ROOT/deps/pip.base"
	pip install -qr "$PROJ_ROOT/deps/pip.dev"
}


function setup_node() {
	pretty_print "setting up node.js"
	npm_path="$(command -v npm)" || ""
	if [[ "$npm_path" != "$VIRTUAL_ENV/bin/npm" ]]; then
		# add node to the virtualenv (nodeenv is a requirement in pip.base)
		python -m nodeenv -p

		# install the node modules
		(cd ../datavalidation/admin && npm install -q)
	else
		pretty_print "node.js already installed in virtual environment" "$fg_yellow"
	fi
}

init
pretty_print "setting up dev environment for django-data-validation..."
link_precommit_hook
add_pth_to_site_packages
install_python_requirements
setup_node
pretty_print "django-data-validation setup complete!"
