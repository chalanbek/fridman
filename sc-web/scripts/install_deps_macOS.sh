#!/usr/bin/env bash
set -eo pipefail

if [ -z "${SC_WEB_PATH}" ];
then
  source "$(cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd)"/set_vars.sh
fi

brew install python3 node

"${SC_WEB_PATH}/scripts/install_deps_npm.sh"
"${SC_WEB_PATH}/scripts/install_deps_python.sh"
