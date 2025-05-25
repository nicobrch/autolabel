#!/bin/bash

# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

# Use either wget or curl to download the checkpoints
if command -v wget &> /dev/null; then
    CMD="wget"
    CMD_INSECURE="wget --no-check-certificate"
elif command -v curl &> /dev/null; then
    CMD="curl -L -O"
    CMD_INSECURE="curl -k -L -O"
else
    echo "Please install wget or curl to download the checkpoints."
    exit 1
fi

# Define the URLs for SAM 2.1 checkpoints
SAM2p1_BASE_URL="https://dl.fbaipublicfiles.com/segment_anything_2/092824"
sam2p1_hiera_t_url="${SAM2p1_BASE_URL}/sam2.1_hiera_tiny.pt"
sam2p1_hiera_s_url="${SAM2p1_BASE_URL}/sam2.1_hiera_small.pt"
sam2p1_hiera_b_plus_url="${SAM2p1_BASE_URL}/sam2.1_hiera_base_plus.pt"
sam2p1_hiera_l_url="${SAM2p1_BASE_URL}/sam2.1_hiera_large.pt"

# Function to download with fallback to insecure if needed
download_with_fallback() {
    url=$1
    echo "Downloading $(basename $url)..."
    $CMD $url || {
        echo "Regular download failed, trying without SSL certificate verification..."
        $CMD_INSECURE $url || {
            echo "Failed to download checkpoint from $url"
            return 1
        }
    }
    return 0
}

# SAM 2.1 checkpoints
download_with_fallback $sam2p1_hiera_t_url || exit 1
download_with_fallback $sam2p1_hiera_s_url || exit 1
download_with_fallback $sam2p1_hiera_b_plus_url || exit 1
download_with_fallback $sam2p1_hiera_l_url || exit 1

echo "All checkpoints are downloaded successfully."
