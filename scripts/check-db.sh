echo "🗄️  Checking Database Connection and Setup"
echo "=========================================="

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
else
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set in .env file"
    exit 1
fi

echo "✅ Environment variables loaded"

# Test database connection using Python
echo "🔌 Testing database connection..."
python3 << EOF
import sys
import os
from sqlalchemy import create_engine, text

try:
    engine = create_engine(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        try:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM catalogue.all_shops_product_data_extended LIMIT 1
            """))
            count = result.fetchone()[0]
            print(f"✅ Materialized view exists with {count:,} records")

        except Exception as e:
            print(f"❌ Materialized view not found: {e}")
            print("Please create the materialized view using the provided SQL")
            sys.exit(1)

        try:
            result = conn.execute(text("""
                SELECT DISTINCT shop_technical_name
                FROM catalogue.all_shops_product_data_extended
                LIMIT 5
            """))
            shops = [row[0] for row in result]
            print(f"✅ Found shops: {', '.join(shops)}")

        except Exception as e:
            print(f"❌ Permission error: {e}")
            sys.exit(1)

except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("Check your DATABASE_URL in .env file")
    sys.exit(1)

print("🎉 Database setup verification complete!")
EOF