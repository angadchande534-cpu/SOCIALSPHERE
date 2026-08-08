from pathlib import Path
from tempfile import template

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from app.database import Base, engine
from app.routes import auth, calls, messages, notifications, posts, reels, social, stories, users

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOAD_DIR = BASE_DIR / "uploads"
custom_page = FRONTEND_DIR / "404.html"

for folder in ("profiles", "posts", "stories", "messages", "reels", "covers"):
    UPLOAD_DIR.joinpath(folder).mkdir(parents=True, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SocialSphere API",
    description="Instagram-style SocialSphere with photo/video posts, stories, messages, likes, comments and notifications.",
    version="5.0.0",
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

custom_page = FRONTEND_DIR / "404.html"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
if (FRONTEND_DIR / "images").exists():
    app.mount("/images", StaticFiles(directory=str(FRONTEND_DIR / "images")), name="images")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(stories.router)
app.include_router(social.router)
app.include_router(messages.router)
app.include_router(notifications.router)
app.include_router(reels.router)
app.include_router(calls.router)

PAGES = {
    "/": "index.html",
    "/login": "login.html",
    "/login-page": "login.html",
    "/signup": "signup.html",
    "/signup-page": "signup.html",
    "/feed": "feed.html",
    "/feed-page": "feed.html",
    "/create-post": "create_post.html",
    "/create-post-page": "create_post.html",
    "/profile": "profile.html",
    "/profile-page": "profile.html",
    "/edit-profile": "edit_profile.html",
    "/edit-profile-page": "edit_profile.html",
    "/search": "search.html",
    "/search-page": "search.html",
    "/bookmarks": "bookmark.html",
    "/bookmark-page": "bookmark.html",
    "/about": "about.html",
    "/about-page": "about.html",
    "/contact": "contact.html",
    "/contact-page": "contact.html",
    "/explore": "explore.html",
    "/friends": "friends.html",
    "/messages": "message.html",
    "/notifications": "notification.html",
    "/settings": "setting.html",
    "/reels": "reels.html",
    "/create-reel": "create_reel.html",
    "/call": "call.html",
    "/privacy": "privacy.html",
    "/terms": "terms.html",
}


def page_response(filename: str):
    target = FRONTEND_DIR / filename
    if not target.is_file():
        return JSONResponse({"detail": f"Page {filename} is missing"}, status_code=404)
    return FileResponse(target)

for route, filename in PAGES.items():
    async def page(filename: str = filename):
        return page_response(filename)

    app.add_api_route(
        route,
        page,
        methods=["GET"],
        include_in_schema=False
    )
@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "message": "SocialSphere backend is running", "version": "5.0.0"}


@app.exception_handler(404)
async def not_found(request: Request, exc):
    if custom_page.is_file():
        return FileResponse(custom_page, status_code=404)

    return JSONResponse(
        {"detail": "Not found"},
        status_code=404
    )


@app.get("/video-call", response_class=HTMLResponse)
async def video_call(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="video_call.html",
        context={}
    )
@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "SocialSphere backend is running",
        "version": "5.0.0"
    }


# ===============================
# VIDEO CALL PAGE
# ===============================

@app.get("/video-call", response_class=HTMLResponse)
async def video_call(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="video_call.html",
        context={}
    )