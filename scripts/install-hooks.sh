#!/bin/bash

# Install Pre-commit Hooks for Pro Team Care
echo "🔧 Installing pre-commit hooks for Pro Team Care..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not detected. Activating..."
    source venv/bin/activate || {
        echo "❌ Virtual environment not found. Creating..."
        python3 -m venv venv
        source venv/bin/activate
    }
fi

# Install pre-commit if not installed
pip install pre-commit

# Install the git hook scripts
pre-commit install

# Install commit message hook
pre-commit install --hook-type commit-msg

# Run hooks against all files (optional - for first time setup)
echo "🧹 Running hooks against all files..."
pre-commit run --all-files || {
    echo "⚠️  Some hooks failed. This is normal on first run."
    echo "💡 Files have been auto-fixed. Please review and commit changes."
}

# Create secrets baseline for detect-secrets
echo "🔐 Creating secrets detection baseline..."
detect-secrets scan --baseline .secrets.baseline

echo ""
echo "✅ Pre-commit hooks installed successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Review any auto-fixed files"
echo "   2. Commit changes: git add . && git commit -m 'chore: setup pre-commit hooks'"
echo "   3. All future commits will be automatically checked"
echo ""
echo "🔧 Available commands:"
echo "   - pre-commit run --all-files  # Run all hooks manually"
echo "   - pre-commit run <hook-name>  # Run specific hook"
echo "   - pre-commit update           # Update hook versions"