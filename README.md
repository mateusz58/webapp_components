### Quick Setup for Production Database:

1. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env with your database credentials:**
   ```bash
   # Your production database
   DATABASE_URL=postgresql://username:password@your-host:5432/database
   DB_HOST=your-database-host.com
   DB_PORT=5432
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_NAME=your_database_name
   ```

3. **Test Database Connection:**
   ```bash
   ./scripts/check-db.sh
   ```

4. **Start Application:**
   ```bash
   docker-compose up --build
   ```

### Supported Database Providers:

✅ **AWS RDS PostgreSQL**
✅ **Google Cloud SQL**
✅ **Azure Database for PostgreSQL**
✅ **DigitalOcean Managed Databases**
✅ **Heroku Postgres**
✅ **Self-hosted PostgreSQL**

### Database Requirements:

- PostgreSQL 12+
- Network access from your Docker host
- Materialized view `catalogue.all_shops_product_data_extended` exists
- Read permissions for your application user

### Security Notes:

- Use SSL/TLS connections in production
- Restrict database access by IP if possible
- Use strong passwords and consider rotating them
- Monitor database access logs

---

# Quick Commands Summary:

# Test database connection
./scripts/check-db.sh

# Start development with external DB
docker-compose up --build

# Start production with external DB
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose logs -f web

# Stop services
docker-compose down