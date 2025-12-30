#!/bin/bash
# No-op build script when using Dockerfile builds on Render.
# The Dockerfile installs SWI-Prolog and Python deps during image build.

echo "Using Dockerfile for builds. Nothing to do in build.sh"
exit 0


