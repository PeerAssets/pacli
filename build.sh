#!/bin/bash

# Compile the binary using nuitka static compiler, results in a single-file binary

echo "Starting complilation."

python3 -m nuitka --recurse-on --python-version=3.6 --lto pacli/__main__.py
