#!/bin/bash
cd "$(dirname "$0")"
echo "🚀 Updating Founder OS..."
git pull
if [ $? -eq 0 ]; then
    echo "✅ Code updated!"
    echo "📦 Installing dependencies..."
    pip install -q -r requirements.txt
    echo ""
    echo "✅ UPDATE COMPLETE!"
    echo ""
    echo "Please restart Cursor to apply changes."
else
    echo "❌ Update failed. Check your internet connection."
fi

