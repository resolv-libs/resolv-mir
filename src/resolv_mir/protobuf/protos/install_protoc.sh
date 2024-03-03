#!/bin/bash

#
# Script to install Protocol Buffers compiler on Linux and macOS systems
#

# Detect OS kernel
OS_KERNEL="$(uname -s)"
case "${OS_KERNEL}" in
    Linux*)     kernel="linux";;
    Darwin*)    kernel="darwin";;
    *)          kernel="unsupported"
esac

if [[ "${kernel}" == "unsupported" ]]; then
  echo "Kernel ${OS_KERNEL} not supported."
  exit 1
else
  echo "${OS_KERNEL} kernel detected."
fi

# Install compiler
if [[ "${kernel}" == "linux" ]]; then
  sudo apt install protobuf-compiler
else
  brew install protobuf
fi