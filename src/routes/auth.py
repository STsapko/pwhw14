from fastapi import Depends, Request, HTTPException, status, APIRouter, BackgroundTasks, Security, UploadFile, File, \
    Form
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm, HTTPAuthorizationCredentials
from fastapi_limiter.depends import RateLimiter
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates

from src.DB.db import get_db

from src.repository import users_repo as user_repository
from src.schemas.User_Schemas import UserCreate, UserCreationResponse, OnLoginResponse, UserDBScheme, RequestEmail
from src.services.authservice import authservice as auth_service
from src.services.email import send_email, send_email_for_reset_pswd


auth_router = APIRouter()
security = HTTPBearer()

templates = Jinja2Templates("src/templates")

@auth_router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserCreationResponse)
async def register(request: Request, bg_task: BackgroundTasks, body: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await user_repository.repo_user_authentication_by_email(body.email, db=db)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists. Try to log in.")

    body.password = auth_service.generate_password_hash(body.password)
    created_user = await user_repository.repo_create_user(body=body, db=db)
    user_response = UserCreationResponse(
        username=created_user.username,
        email=created_user.email,
        created_at=created_user.created_at,
        password=created_user.password,
        avatar=created_user.avatar,
        message="Your account created successfully. Check your email to activate it."
    )
    bg_task.add_task(send_email, created_user.email, created_user.username, request.base_url)

    return user_response


@auth_router.post("/login", status_code=status.HTTP_200_OK, response_model=OnLoginResponse)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await user_repository.repo_user_authentication_by_email(body.username, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.is_activated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user. (Email not confirmed.)")
    if not auth_service.check_password_hash(user.password, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    # Generate tokens
    access_token = await auth_service.create_access_token(data={"sub": user.email}, expires_delta=3600)
    refresh_token_ = await auth_service.create_refresh_token(data={"sub": user.email})
    await user_repository.repo_update_refresh_token(user, refresh_token_, db=db)
    user_data = UserDBScheme(username=user.username, email=user.email, avatar=user.avatar)
    return OnLoginResponse(user=user_data, access_token=access_token, refresh_token=refresh_token_)


@auth_router.get("/refresh_token", response_model=OnLoginResponse)
async def refresh_token(creds: HTTPAuthorizationCredentials = Security(security), db: AsyncSession = Depends(get_db)):
    token = creds.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await user_repository.repo_user_authentication_by_email(email=email, db=db)
    if token != user.refresh_token:
        await user_repository.repo_update_refresh_token(user=user, new_refresh_token=None, db=db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token_ = await auth_service.create_refresh_token(data={"sub": email})
    await user_repository.repo_update_refresh_token(user=user, new_refresh_token=refresh_token_, db=db)
    user_data = UserDBScheme(username=user.username, email=user.email, avatar=user.avatar)
    return OnLoginResponse(user=user_data, access_token=access_token, refresh_token=refresh_token)


@auth_router.get("/email_confirmation/{token}")
async def email_confirmation(token: str, db: AsyncSession = Depends(get_db)):
    email = auth_service.get_email_from_token(token)
    user = await user_repository.repo_user_authentication_by_email(email=email, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.is_activated:
        return {"message": "Your email is already confirmed."}
    await user_repository.confirmed_email(email=email, db=db)
    return {"message": "Email confirmation went good!"}


@auth_router.get("/request_confirmation_email")
async def request_confirmation_email(body: RequestEmail, bg_task: BackgroundTasks, request: Request,
                                     db: AsyncSession = Depends(get_db)):
    user = await user_repository.repo_user_authentication_by_email(email=body.email, db=db)
    if user:
        if user.is_activated:
            return {"message": "Your email is already confirmed."}
        bg_task.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation"}


"""
Test upload image to cloudinary -> WORKING!


@auth_router.patch("/change_avatar")
async def change_avatar():
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret
    )
    cloudinary.uploader.upload("https://upload.wikimedia.org/wikipedia/commons/a/ae/Olympic_flag.jpg",
                                      public_id="test/olympic_flag")
    srcURL = cloudinary.CloudinaryImage("olympic_flag").build_url()

    return {"Message": "Upload Finished", "url": srcURL}
"""


@auth_router.post("/reset_password")
async def reset_password(email: EmailStr, request: Request, bg_tasks: BackgroundTasks,
                         db: AsyncSession = Depends(get_db)):
    user = await user_repository.repo_user_authentication_by_email(email, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User was not found.")
    reset_token = auth_service.create_reset_token({"sub": email})

    await user_repository.add_reset_token_to_db(user, reset_token, db)
    bg_tasks.add_task(send_email_for_reset_pswd, email, user.username, reset_token, request.base_url)

    return {"message": "Email with instructions was sent."}


# TODO: finish set_new_password/
@auth_router.post("/set_new_password/{token}",
                  dependencies=[Depends(RateLimiter(times=1, hours=1))]
                  )
async def set_new_password(token: str, new_password: str = Form(...), db: AsyncSession = Depends(get_db)):
    email = auth_service.get_email_from_reset_token(token)
    user = await user_repository.repo_user_authentication_by_email(email=email, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    new_hashed_password = auth_service.generate_password_hash(new_password)

    user.password = new_hashed_password
    user.reset_token = None
    await db.commit()
    return {"Message": "Password changed successfully"}


@auth_router.get("/set_new_password/{token}",
                 dependencies=[Depends(RateLimiter(times=1, hours=1))]
                 )
async def reset_password_form(request: Request):
    return templates.TemplateResponse("reset_password_form.html", {"request": request})



