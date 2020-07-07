#!/usr/bin/env bash

# Quick and Dirty script to setup the dev environment
# activate a virtualenv before running this script
SETUP_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
PROJ_ROOT="$(dirname "$SETUP_DIR")"

if [[ -z "$VIRTUAL_ENV" ]]; then
  printf "please activate your virtualenv before continuing"
  return 1
fi

# add project paths to site-packages
pypths="$SETUP_DIR/test_proj.pth"
cat >"$pypths" <<-EOF
	$PROJ_ROOT
	$PROJ_ROOT/test_proj
	$PROJ_ROOT/test_proj/apps
	EOF

sitepackages=("$VIRTUAL_ENV"/lib/python*/site-packages/)
if ! [[ "${#sitepackages[@]}" -eq 1 ]]; then
	printf "cannot find site-packages at %s\n" "$VIRTUAL_ENV/lib/python"
  exit 1
elif ! [[ -e "${sitepackages[0]}/test_proj.pth" ]]; then
  ln -s "$pypths" "${sitepackages[0]}"
fi
unset pypths

# symlink datavalidation app into tests
# pycharm recommendation: right click and mark the symlink as excluded
ln -s "$PROJ_ROOT/datavalidation/" "$PROJ_ROOT/test_proj/apps/"

# install requirements
pip install -r "$PROJ_ROOT/deps/pip.base"

# add node to the virtualenv
nodeenv -p

# install the node modules
cd datavalidation/admin || exit
npm install