echo "🚀 Setting up Shopify Analytics Development Environment"
echo "====================================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.9+ required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing production dependencies..."
pip install -r requirements.txt

echo "📦 Installing development dependencies..."
pip install -r requirements-dev.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your database credentials"
fi

# Set up pre-commit hooks
echo "🔧 Setting up pre-commit hooks..."
pre-commit install

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs backups

# Run initial tests to verify setup
echo "🧪 Running initial tests..."
python -c "
try:
    import flask, sqlalchemy, psycopg2, pytest
    print('✅ All required packages imported successfully')
except ImportError as e:
    print(f'❌ Missing package: {e}')
    exit(1)
"

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database credentials"
echo "2. Run 'python -m pytest' to run tests"
echo "3. Run 'python run.py' to start the development server"
echo "4. Visit http://localhost:5000 to see your application"
