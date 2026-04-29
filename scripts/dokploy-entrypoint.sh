#!/bin/bash
set -e

echo "🚀 Starting North Seattle Beer App..."

# Run the scraper initially to ensure we have data
echo "🔍 Running initial scraper..."
uv run around-the-grounds --preview

# Copy the generated data to the build output so the frontend can see it immediately
# Note: Nuxt static builds serve from .output/public
if [ -d "frontend/.output/public" ]; then
    echo "📋 Copying data.json to build output..."
    cp frontend/public/data.json frontend/.output/public/data.json
fi

# Start a background loop to update data every 9 hours
(
    while true; do
        sleep 32400 # 9 hours
        echo "🔄 Updating data..."
        uv run around-the-grounds --preview
        if [ -d "frontend/.output/public" ]; then
            cp frontend/public/data.json frontend/.output/public/data.json
        fi
        echo "✅ Data update complete."
    done
) &

# Start the web server
echo "🌐 Starting web server..."
cd frontend
# Use environment variables and explicit path to avoid argument confusion
export NITRO_HOST=0.0.0.0
export NITRO_PORT=3000
exec npx nuxi preview .
