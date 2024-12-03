from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import database , schemas, models, utils, oauth2

router = APIRouter(
    prefix="/login",
    tags=['Authentication']
)

@router.post('/', response_model=schemas.TokenWithUser)
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # username == phone

    user = db.query(models.User).filter(models.User.phone == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    access_token = oauth2.create_access_token(data = {"user_id": user.id})



    user_out = schemas.UserOut.model_validate(user, from_attributes=True)

    return {"access_token": access_token, 
            "token_type": "bearer",
            "user":  user_out
    }
