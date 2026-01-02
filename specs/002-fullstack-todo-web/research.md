# Research: Phase II - Full-Stack Todo Web Application

**Branch**: `002-fullstack-todo-web`
**Date**: 2026-01-02
**Status**: Complete

---

## 1. Better Auth + FastAPI JWT Integration

### Decision
Use Better Auth on frontend (Next.js) for user management with httpOnly cookies; FastAPI backend verifies JWTs using shared `BETTER_AUTH_SECRET`.

### Rationale
- Better Auth manages the complete authentication lifecycle (signup, signin, signout, session management)
- JWT tokens stored as httpOnly cookies prevent XSS attacks
- Stateless verification: FastAPI decodes JWT with shared secret without database calls
- 30-day token expiration as per spec clarification

### Key Findings
- **Token Storage**: httpOnly, Secure, SameSite cookies set by Better Auth
- **Token Format**: `header.payload.signature` where signature = HMAC(secret, header+payload)
- **Backend Verification**: PyJWT library decodes and verifies using `BETTER_AUTH_SECRET`
- **User ID Extraction**: From JWT payload `sub` claim (subject = user ID)

### Alternatives Rejected
| Alternative | Reason Rejected |
|-------------|-----------------|
| localStorage for tokens | Vulnerable to XSS attacks |
| Session-based auth | Less portable for microservices architecture |
| Backend-issued tokens | Duplicates Better Auth functionality |

---

## 2. SQLModel + Neon Serverless PostgreSQL

### Decision
Use SQLModel with async SQLAlchemy engine, QueuePool with conservative sizing, and transaction-level pooling via Neon's pgbouncer.

### Rationale
- Neon's serverless architecture has connection limits (20 on free tier)
- Transaction pooling (port 6432) returns connections immediately after each transaction
- AsyncSession with FastAPI provides non-blocking database operations
- pool_pre_ping validates connections before use (handles cold starts)

### Key Configuration
```python
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

### Connection String Pattern
```
postgresql+asyncpg://{user}:{password}@{host}:6432/{database}?sslmode=require
```
- Port 6432 = Neon pgbouncer (transaction pooling)
- sslmode=require mandatory for Neon

### Alternatives Rejected
| Alternative | Reason Rejected |
|-------------|-----------------|
| NullPool | 10x slower - new connection per request |
| Large pool (20+) | Exceeds Neon connection limits |
| Session pooling (port 5432) | Higher connection count, not ideal for serverless |

---

## 3. Next.js App Router Patterns

### Decision
Use middleware-based auth protection, Server Components for auth state, and API route handlers as proxies to FastAPI backend.

### Rationale
- Middleware runs at edge before route execution (instant redirects)
- Server Components retrieve session without client exposure
- API route proxies hide backend URL from client and handle CORS server-side

### Route Structure
```
app/
├── middleware.ts                    # Auth checks at edge
├── (auth)/                          # Unprotected auth routes
│   ├── signin/page.tsx
│   └── signup/page.tsx
├── (protected)/                     # Protected app routes
│   ├── layout.tsx                   # Server-side session check
│   └── dashboard/page.tsx
└── api/
    ├── auth/[...auth]/route.ts      # Better Auth handler
    └── tasks/route.ts               # Proxy to FastAPI
```

### Environment Variable Rules
| Variable | Prefix | Exposed to Client |
|----------|--------|-------------------|
| `BETTER_AUTH_SECRET` | None | No |
| `BACKEND_URL` | None | No |
| `DATABASE_URL` | None | No |
| `NEXT_PUBLIC_APP_NAME` | `NEXT_PUBLIC_` | Yes |

### Alternatives Rejected
| Alternative | Reason Rejected |
|-------------|-----------------|
| Client-side redirects | Exposes protected routes briefly |
| Direct fetch to FastAPI | Exposes backend URL, creates CORS issues |
| Global client auth context | Hydration mismatch, session exposed to client |

---

## 4. Migration Strategy

### Decision
Use Alembic for version-controlled schema migrations with explicit review workflow.

### Rationale
- Alembic integrates with SQLAlchemy (SQLModel's foundation)
- Auto-generate migrations from model changes
- Supports rollback for production safety
- Version history enables reproducible deployments

### Workflow
1. Developer: `alembic revision --autogenerate -m "description"`
2. Developer: Review generated migration file
3. Commit migration to git
4. CI/CD: `alembic upgrade head` on staging
5. After approval: Same migration runs on production

### Alternatives Rejected
| Alternative | Reason Rejected |
|-------------|-----------------|
| Manual SQL files | No versioning, error-prone, hard to rollback |
| `Base.metadata.create_all()` | No versioning, can't modify existing tables safely |

---

## 5. CORS Configuration

### Decision
Configure CORS on FastAPI backend for frontend-backend communication; use Next.js API routes as proxy layer.

### Rationale
- API routes eliminate CORS issues between Next.js client and FastAPI
- When direct access needed, FastAPI CORS allows specific origins
- `allow_credentials=True` required for cookie-based auth

### FastAPI CORS Config
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 6. Testing Strategy

### Decision
Use pytest with async fixtures for backend, and Jest/React Testing Library for frontend.

### Rationale
- pytest-asyncio supports async FastAPI testing
- Mock database sessions for unit tests
- Integration tests against Neon staging database
- Frontend component tests with mocked API responses

### Test Structure
```
backend/tests/
├── conftest.py          # Async fixtures
├── test_tasks.py        # API endpoint tests
└── test_auth.py         # JWT verification tests

frontend/__tests__/
├── components/          # Component unit tests
├── hooks/               # Custom hook tests
└── e2e/                 # Playwright E2E tests
```

---

## Research Summary

| Topic | Decision | Confidence |
|-------|----------|------------|
| Authentication | Better Auth + httpOnly cookies | High |
| Backend JWT verification | PyJWT with shared secret | High |
| Database connection | Async SQLModel + QueuePool (5-10) | High |
| Migrations | Alembic with autogenerate | High |
| Frontend routing | Middleware + route groups | High |
| API communication | Next.js API route proxies | High |
| Token expiration | 30 days (per spec) | Confirmed |

---

## Outstanding Questions: None

All technical unknowns have been resolved through research.
