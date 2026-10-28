#!/bin/sh
# Write the runtime frontend config before nginx starts. The image is built
# once; API_URL is supplied by the deployment (default: same-origin /api).
set -e

api_url="${API_URL:-/api}"

printf 'window.RAGATOUL_CONFIG = { apiUrl: "%s" };\n' "$api_url" \
  > /usr/share/nginx/html/config.js
