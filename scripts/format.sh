echo "🎨 Formatting Shopify Analytics Code"
echo "=================================="

# Format Python code with Black
echo "🎨 Formatting code with Black..."
black app/ tests/

# Sort imports with isort
echo "📦 Sorting imports with isort..."
isort app/ tests/

# Run linting check
echo "🔍 Checking code style with flake8..."
flake8 app/ tests/

echo "✅ Code formatting complete!"