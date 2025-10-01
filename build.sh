#!/usr/bin/env bash
# exit on error
set -o errexit

# Install build tools
apt-get update
apt-get install -y build-essential cmake

# Install python dependencies
pip install -r requirements.txt
