echo "📊 Generating Test Coverage Report"
echo "================================="

# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-report=xml

# Open coverage report in browser (optional)
if command -v open &> /dev/null; then
    echo "🌐 Opening coverage report in browser..."
    open htmlcov/index.html
elif command -v xdg-open &> /dev/null; then
    echo "🌐 Opening coverage report in browser..."
    xdg-open htmlcov/index.html
fi

echo "✅ Coverage report generated in htmlcov/"
echo "📊 XML report generated for CI/CD: coverage.xml"