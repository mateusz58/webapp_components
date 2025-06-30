# Architecture Overview

## System Architecture

### Technology Stack
- **Backend**: Flask with Blueprint architecture
- **Database**: PostgreSQL with custom schema `component_app`
- **Storage**: WebDAV for picture storage
- **Containerization**: Docker-based deployment
- **Frontend**: Bootstrap 5.3.2 + Alpine.js + Lucide icons
- **Testing**: Selenium-based automated testing framework

### Database Schema (`component_app`)
- **Auto-Generated Fields**: SKUs and picture names via PostgreSQL triggers
- **Status Tracking**: Three-stage approval process (Proto/SMS/PPS)
- **Flexible Properties**: JSON-based component attributes
- **Relationships**: Complex many-to-many with brands, categories, keywords

### Key URLs & Endpoints
- **Main Application**: `http://localhost:6002`
- **Picture Storage**: `http://31.182.67.115/webdav/components`
- **Database**: `postgresql://component_user:component_app_123@192.168.100.35:5432/promo_database`

## Application Structure

### Core Models
- `Component` - Main product entity with JSON properties
- `ComponentVariant` - Color variants with auto-generated SKUs
- `ComponentType` - Categories with dynamic properties
- `Supplier` - Supplier management
- `Brand`/`Subbrand` - Brand hierarchy
- `Picture` - Image management with automatic naming
- `Keyword` - Tagging system

### Route Architecture
- **Web Routes** (`app/web/`): User interface endpoints
- **API Routes** (`app/api/`): REST API endpoints
- **Main Routes**: Legacy routes in `app/routes.py`

### Frontend Architecture
- **Templates**: Jinja2 with modular section includes
- **JavaScript**: Modern ES6+ with Alpine.js components
- **CSS**: Modular architecture with component-based styles
- **Icons**: Lucide icon system

## Performance Features

### Database Optimizations
- Comprehensive indexing strategy
- Query optimization with selectinload
- Connection pooling
- Efficient pagination

### Caching System
- Redis integration for performance
- Result caching for autocomplete
- Debounced API requests
- Frontend asset optimization

### File Management
- Image optimization and compression
- Automatic naming conventions
- WebDAV storage integration
- Atomic file operations

## Security Features

### Protection Mechanisms
- CSRF protection via Flask-WTF
- File upload validation
- SQL injection prevention
- Secure file handling
- Input sanitization

### Authentication & Authorization
- Session-based authentication
- Role-based access control
- Secure cookie handling

## Testing Framework

### Automated Testing
- Selenium WebDriver for end-to-end testing
- Page Object Model implementation
- Component-specific test suites
- Critical workflow coverage

### Manual Testing
- Browser compatibility testing
- Performance testing
- User experience validation
- Security testing

## Deployment Architecture

### Docker Configuration
- Multi-container setup
- External PostgreSQL database
- Volume mounts for file storage
- Environment-based configuration

### Monitoring & Logging
- Application logging
- Error tracking
- Performance monitoring
- Database query logging