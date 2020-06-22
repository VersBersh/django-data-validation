#!/usr/bin/env bash

# Quick and Dirty script to setup the dev environment
# activate a virtualenv before running this script

SETUP_DIR="$(dirname "${BASH_SOURCE[0]}")"
PROJ_ROOT="$(dirname "$SETUP_DIR")"

if [[ -z "$VIRTUAL_ENV" ]]; then
  printf "please activate your virtualenv before continuing"
  return 1
fi

# add project paths to site-packages
pypths="$SETUP_DIR/test_proj.pth"
cat >"$pypths" <<-EOF
	$PROJ_ROOT/tests/
	$PROJ_ROOT/tests/test_proj
	$PROJ_ROOT/tests/test_proj/apps
	EOF

sitepackages="$VIRTUAL_ENV/lib/python*/site-packages"
if [[ -d "$sitepackages" ]]; then
  ln -s "$pypths" .
else
  printf "cannot find site-packages at %s" "$sitepackages"
  return 1
fi
unset pypths

# symlink datavalidation app into tests
# pycharm recommendation: right click and mark the symlink as excluded
ln -s "$PROJ_ROOT/datavalidation/" "$PROJ_ROOT/tests/test_proj/apps/"

# install requirements
pip install -r "$PROJ_ROOT/deps/pip.base"

# add node to the virtualenv
nodeenv -p

# install the node modules
npm install