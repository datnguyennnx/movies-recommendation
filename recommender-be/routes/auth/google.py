import logging
import requests
from fastapi import APIRouter, HTTPException, Response, Cookie, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt, JWTError
from datetime import datetime, timedelta
from config.settings import settings
from sqlalchemy.orm import Session
from db.database import get_db
from models.models import User, Session as UserSession
import uuid
from pytz import UTC

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_access_token(data: dict, db: Session):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # Create a new session in the database
    db_session = UserSession(
        user_id=uuid.UUID(to_encode["sub"]),
        issued_at=datetime.now(UTC),
        expires_at=expire,
        client_id=settings.GOOGLE_CLIENT_ID
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return encoded_jwt, db_session.id

@router.get("/google")
async def google_auth():
    if not settings.GOOGLE_CLIENT_ID:
        logger.error("GOOGLE_CLIENT_ID is not set")
        raise HTTPException(status_code=500, detail="Server configuration error")
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_REDIRECT_URI}&scope=openid%20email%20profile"
    logger.info(f"Initiating Google auth with client ID: {settings.GOOGLE_CLIENT_ID} and redirect URI: {settings.GOOGLE_REDIRECT_URI}")
    return {"auth_url": auth_url}

@router.get("/callback")
async def auth_callback(code: str, db: Session = Depends(get_db)):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    try:
        logger.info(f"Attempting to exchange code for token with redirect URI: {settings.GOOGLE_REDIRECT_URI}")
        token_response = requests.post(token_url, data=data)
        token_response.raise_for_status()
        token_data = token_response.json()
        id_token_value = token_data["id_token"]


        try: 
            # Verify the ID token
            idinfo = id_token.verify_oauth2_token(id_token_value, google_requests.Request(), settings.GOOGLE_CLIENT_ID)
            
            if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
                raise ValueError("Wrong issuer.")
            
            # Check if user exists, if not create a new user
            user = db.query(User).filter(User.google_id == idinfo["sub"]).first()
            if not user:
                user = User(
                    google_id=idinfo["sub"],
                    name=idinfo.get("name"),
                    email=idinfo["email"],
                    picture=idinfo.get("picture")
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            access_token, session_id = create_access_token({"sub": str(user.id), "email": user.email}, db)
            
            redirect_url = f"{settings.FRONTEND_URL}?token={access_token}"
            response = RedirectResponse(url=redirect_url)
            
            # Set the cookie as well for added security
            response.set_cookie(
                key="token",
                value=access_token,
                httponly=True,
                secure=settings.COOKIE_SECURE,
                samesite="lax",
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60000,
                path="/"
            )
            
            return response
        except ValueError as ve:
            if "Token used too early" in str(ve):
                logger.error(f"Time synchronization error: {str(ve)}")
                raise HTTPException(status_code=400, detail="Server time is out of sync. Please try again in a few moments.")
            else:
                logger.error(f"Value error during Google authentication: {str(ve)}")
                raise HTTPException(status_code=400, detail=f"Error during Google authentication: {str(ve)}")
    except Exception as e:
        logger.error(f"Error during Google authentication: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error during Google authentication: {str(e)}")

def verify_token(token: str, db: Session):
    logger.info(f"Verifying token: {token[:10]}...")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logger.info(f"Token decoded successfully. Payload: {payload}")
        
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Token payload does not contain 'sub' field")
            return {"valid": False}
        
        session = db.query(UserSession).filter(UserSession.user_id == uuid.UUID(user_id)).first()
        if not session:
            logger.warning(f"No session found for user_id: {user_id}")
            return {"valid": False}
        
        if session.expires_at < datetime.now(UTC):
            logger.warning(f"Session expired for user_id: {user_id}")
            return {"valid": False}
        
        logger.info(f"Token verified successfully for user_id: {user_id}")
        return {"valid": True, "user": payload}
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return {"valid": False}
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return {"valid": False}
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {str(e)}")
        return {"valid": False}
   

@router.get("/protected")
async def protected_route(token: str = Cookie(None), db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=401, detail="Token not provided")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        session = db.query(UserSession).filter(UserSession.user_id == uuid.UUID(payload["sub"])).first()
        if not session or session.expires_at < datetime.now(UTC):
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return {"message": "This is a protected route", "user": payload}
    except JWTError as e:
        logger.error(f"JWT verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/logout")
async def logout(response: Response, token: str = Cookie(None), db: Session = Depends(get_db)):
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            db.query(UserSession).filter(UserSession.user_id == uuid.UUID(payload["sub"])).delete()
            db.commit()
            logger.info(f"User logged out: {payload.get('email')}")
        except JWTError as e:
            logger.error(f"Error during logout: {str(e)}")
    response.delete_cookie(key="token", path="/")
    return {"message": "Logged out successfully"}

@router.get("/verify")
async def verify_auth(token: str = Cookie(None), db: Session = Depends(get_db)):
    if not token:
        return JSONResponse(status_code=401, content={"authenticated": False, "message": "No token provided"})
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        session = db.query(UserSession).filter(UserSession.user_id == uuid.UUID(payload["sub"])).first()
        if not session or session.expires_at < datetime.now(UTC):
            return JSONResponse(status_code=401, content={"authenticated": False, "message": "Invalid or expired token"})
        
        user = db.query(User).filter(User.id == uuid.UUID(payload["sub"])).first()
        if not user:
            return JSONResponse(status_code=401, content={"authenticated": False, "message": "User not found"})
        
        return JSONResponse(content={
            "authenticated": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "picture": user.picture
            }
        })
    except JWTError as e:
        logger.error(f"JWT verification failed: {str(e)}")
        return JSONResponse(status_code=401, content={"authenticated": False, "message": "Invalid token"})
