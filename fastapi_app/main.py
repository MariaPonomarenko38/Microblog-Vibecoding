from fastapi import Response

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from pymongo import MongoClient
from bson.objectid import ObjectId
from .models import UserCreate, UserProfile
import os

app = FastAPI()

# Static and template setup
app.mount("/static", StaticFiles(directory="fastapi_app/static"), name="static")
templates = Jinja2Templates(directory="fastapi_app/templates")

# MongoDB setup
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
client = MongoClient(MONGO_URI)
db = client['microblog']
users_collection = db['users']

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_username(username: str):
    user = users_collection.find_one({"username": username})
    return user

@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup", response_model=UserProfile)
def signup(user: UserCreate):
    if get_user_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    password = user.password
    if len(password) > 72:
        raise HTTPException(status_code=400, detail="Password must be at most 72 characters.")
    hashed_password = get_password_hash(password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    result = users_collection.insert_one(user_dict)
    return UserProfile(id=str(result.inserted_id), username=user.username, email=user.email)

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"access_token": str(user["_id"]), "token_type": "bearer"}

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/profile_page/{user_id}", response_class=HTMLResponse)
def profile_page(user_id: str, request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/profile/{user_id}", response_model=UserProfile)
def get_profile(user_id: str, token: str = Depends(oauth2_scheme)):
    # Only allow access if token matches user_id
    if token != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this profile.")
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(id=str(user["_id"]), username=user["username"], email=user["email"])

@app.get("/all_users")
def get_all_users():
    users = users_collection.find({}, {"_id": 1, "username": 1})
    result = []
    for user in users:
        result.append({"id": str(user["_id"]), "username": user["username"]})
    return result
