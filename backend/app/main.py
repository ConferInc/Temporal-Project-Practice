from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

# Import New Modular Components
from app.core import config, database, security
from app.models.sql import User
from app.services import files
from app.api.routes import auth, applications

app = FastAPI(title="Moxi Mortgage API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
app.mount("/static", StaticFiles(directory=files.get_upload_root()), name="static")

# Include Routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(applications.router, tags=["Applications"]) # Paths like /apply, /applications are root-level or near root

# Startup Event (Database & Seeding)
@app.on_event("startup")
def on_startup():
    database.init_db()
    # Admin Seeding
    try:
        session = next(database.get_session())
        admin_email = "admin@gmail.com"
        existing_admin = session.query(User).filter(User.email == admin_email).first()
        if not existing_admin:
            print(f"Seeding Admin User: {admin_email}")
            admin_user = User(
                email=admin_email,
                password_hash=security.get_password_hash("admin1234"),
                role="manager"
            )
            session.add(admin_user)
            session.commit()
    except Exception as e:
        print(f"Admin seeding failed: {e}")
