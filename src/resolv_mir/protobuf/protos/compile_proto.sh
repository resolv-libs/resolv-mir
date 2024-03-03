#!/usr/bin/env bash

#
# Script to compile all .proto files in specified ${PROTO_BUFFERS_DIR}.
#

# PROTO_FILES=$(find "./src" -type f -name "*.proto" | sed "s|./src/||")

cd "$(dirname "$0")/../../.." || exit

PROTO_BUFFERS_DIR="./resolv_mir/protobuf/protos"
DESTINATION_DIR="."

for FILE in "${PROTO_BUFFERS_DIR}"/*.proto; do
  protoc --python_out="${DESTINATION_DIR}" --pyi_out="${DESTINATION_DIR}" "${FILE}"
done
