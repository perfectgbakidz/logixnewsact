# Logic NewsAct - Backend API

A secure and scalable FastAPI backend for the Logic NewsAct news platform.

## Features

- **Posts Management**: Create, read, update, delete news articles
- **Regions & Sub-zones**: Organize content by geopolitical zones
- **Admin Authentication**: JWT-based secure authentication
- **File Storage**: Upload images to Supabase Storage or local filesystem
- **Analytics**: Site-wide statistics and metrics
- **Security**: Rate limiting, CORS, XSS protection, SQL injection prevention

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (with asyncpg) or **Supabase**
- **Storage**: Supabase Storage or local filesystem
- **ORM**: SQLAlchemy 2.0 (async)
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **Rate Limiting**: slowapi
- **HTML Sanitization**: bleach

## Project Structure

```
logic_newsact_backend/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── posts.py        # Posts CRUD endpoints
│   │   │   ├── regions.py      # Regions & zones endpoints
│   │   │   └── analytics.py    # Analytics endpoints
│   │   ├── deps.py             # Authentication dependencies
│   │   └── api.py              # API router configuration
│   ├── core/
│   │   ├── config.py           # Application settings
│   │   └── security.py         # Password & JWT utilities
│   ├── db/
│   │   └── database.py         # Database configuration
│   ├── models/
│   │   └── models.py           # SQLAlchemy models
│   ├── schemas/
│   │   └── schemas.py          # Pydantic schemas
│   ├── services/
│   │   └── crud.py             # CRUD operations
│   └── main.py                 # Application entry point
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
├── seed_data.py               # Database seeding script
└── README.md                  # This file
```

## Quick Start

### 1. Clone and Setup

```bash
cd logic_newsact_backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials and secret keys
```

### 3. Setup Database

#### Option A: Local PostgreSQL

Ensure PostgreSQL is running and create a database:

```sql
CREATE DATABASE logic_newsact;
```

#### Option B: Supabase (Recommended for Production)

1. **Create a Supabase account** at [supabase.com](https://supabase.com)

2. **Create a new project** and wait for it to be ready

3. **Get your database connection string:**
   - Go to Project Settings → Database
   - Under "Connection String", select "URI"
   - Copy the connection string
   - Replace `[YOUR-PASSWORD]` with your database password

4. **Update your `.env` file:**
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:your-password@db.your-project-ref.supabase.co:5432/postgres
   ```

5. **Important: Connection Pool Settings for Supabase**
   
   Supabase free tier has a connection limit (~60). The app is configured with connection pooling:
   ```env
   DB_POOL_SIZE=5
   DB_MAX_OVERFLOW=10
   ```

6. **Enable Row Level Security (optional but recommended):**
   
   In Supabase SQL Editor, run:
   ```sql
   -- Tables will be created automatically by the app
   -- You can add RLS policies later for additional security
   ```

### 4. Seed Database (Optional)

```bash
python seed_data.py
```

This creates:
- Initial admin user (username: `admin`, password: `admin123`)
- Sample regions (IbileLogic, ArewaLogic, NaijaLogic, NigerDeltaLogic)
- Sub-zones for each region
- Sample news posts

### 5. Run the Application

```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## API Documentation

- **Swagger UI**: `http://localhost:8000/docs` (development only)
- **ReDoc**: `http://localhost:8000/redoc` (development only)

## API Endpoints

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/posts` | List all posts (with filters) |
| GET | `/api/posts/{id}` | Get single post |
| POST | `/api/posts/{id}/view` | Increment view count |
| GET | `/api/regions` | List all regions with zones |
| GET | `/api/regions/{id}` | Get single region |

### Admin Endpoints (Protected)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Admin login |
| GET | `/api/auth/me` | Get current admin profile |
| PUT | `/api/auth/profile` | Update admin profile |
| POST | `/api/posts` | Create new post |
| PUT | `/api/posts/{id}` | Update post |
| DELETE | `/api/posts/{id}` | Delete post |
| POST | `/api/regions` | Create new region |
| PUT | `/api/regions/{id}` | Update region |
| DELETE | `/api/regions/{id}` | Delete region |
| POST | `/api/regions/{id}/zones` | Add sub-zone to region |
| DELETE | `/api/regions/{id}/zones/{zone_id}` | Delete sub-zone |
| GET | `/api/analytics` | Get site analytics |
| POST | `/api/upload` | Upload file (Admin) |
| POST | `/api/upload/avatar` | Upload avatar (Admin) |
| POST | `/api/upload/post-image` | Upload post image (Admin) |
| DELETE | `/api/upload/delete` | Delete file (Admin) |

## Authentication

The API uses JWT Bearer tokens for authentication.

### Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### Using the Token

Include the token in the Authorization header:

```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

## File Storage

The backend supports file uploads for images (posts, avatars, region images).

### Storage Options

#### Option A: Supabase Storage (Recommended)

1. Enable Storage in your Supabase project
2. Create a bucket (default: `public`)
3. Set bucket to public access
4. Configure environment variables:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your-service-role-key
   SUPABASE_STORAGE_BUCKET=public
   ```

#### Option B: Local File Storage

If Supabase credentials are not provided, files are stored locally in the `uploads/` directory and served from `/static/uploads`.

### Upload Endpoints (Admin Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload image file (max 5MB, jpeg/png/webp) |
| POST | `/api/upload/avatar` | Upload admin avatar (max 2MB) |
| POST | `/api/upload/post-image` | Upload post image (max 5MB) |
| DELETE | `/api/upload/delete?url=` | Delete a file |

### Example Upload

```bash
curl -X POST "http://localhost:8000/api/upload/post-image" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@image.jpg"
```

Response:
```json
{
  "success": true,
  "image_url": "https://your-project.supabase.co/storage/v1/object/public/public/posts/20240115_120000_a1b2c3d4.jpg",
  "path": "posts/20240115_120000_a1b2c3d4.jpg",
  "bucket": "public",
  "provider": "supabase"
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (local or Supabase) | `postgresql+asyncpg://user:pass@localhost:5432/logic_newsact` |
| `SUPABASE_URL` | Supabase project URL (optional) | - |
| `SUPABASE_KEY` | Supabase anon key (optional) | - |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (for storage) | - |
| `SUPABASE_STORAGE_BUCKET` | Default storage bucket | `public` |
| `DB_POOL_SIZE` | Database connection pool size | `5` |
| `DB_MAX_OVERFLOW` | Max overflow connections | `10` |
| `SECRET_KEY` | JWT signing key | Generate a secure random key |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `1440` (24 hours) |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |
| `TRUSTED_HOSTS` | Allowed host headers in production | `localhost,127.0.0.1` |
| `DEBUG` | Debug mode | `False` |

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt with salt
- **Rate Limiting**: Prevents brute force and DoS attacks
- **CORS**: Configurable cross-origin resource sharing
- **XSS Protection**: HTML sanitization with bleach
- **SQL Injection Prevention**: ORM query builders
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, CSP

## Database Schema

### Tables

- **admins**: Administrator accounts
- **regions**: Geopolitical zones
- **sub_zones**: States/zones within regions
- **posts**: News articles

See `BACKEND_DOCUMENTATION.md` for detailed schema.

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
```

### Type Checking

```bash
mypy app/
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Checklist

- [ ] Change default admin password
- [ ] Set strong `SECRET_KEY`
- [ ] Configure `ALLOWED_ORIGINS` for production
- [ ] Set `DEBUG=False`
- [ ] Use HTTPS
- [ ] Configure proper logging
- [ ] Set up monitoring

### Supabase Deployment Notes

When deploying with Supabase:

1. **Connection Limits**: Supabase free tier allows ~60 concurrent connections. The app uses connection pooling (default: 5 pool + 10 overflow = 15 max).

2. **Connection String Format**:
   ```
   postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
   ```
   The app also accepts `postgresql://...` (for Render) and auto-converts it to `postgresql+asyncpg://...`.

3. **IPv4 Addon**: If deploying to a platform without IPv6 support (like some VPS), enable the "IPv4" addon in Supabase Dashboard → Database → Network Restrictions.

4. **Database Migrations**: Tables are auto-created on first run (`init_db()`). For production, consider using Alembic for migrations.

5. **Row Level Security**: Enable RLS on tables for additional security:
   ```sql
   ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
   ALTER TABLE regions ENABLE ROW LEVEL SECURITY;
   ALTER TABLE sub_zones ENABLE ROW LEVEL SECURITY;
   ```

## License

MIT License

## Support

For issues and feature requests, please contact the development team.
