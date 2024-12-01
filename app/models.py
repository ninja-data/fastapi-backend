from sqlalchemy import Column, Integer, Date, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from .database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    published = Column(Boolean, server_default='TRUE', nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    owner = relationship("User", backref='posts')


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    surname = Column(String)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    profile_picture = Column(String)
    bio = Column(Text)
    location = Column(String)
    date_of_birth = Column(Date)
    gender = Column(String(1))  # Added gender field (e.g., M, F, O for other)
    role = Column(String, default='user')
    is_active = Column(Boolean, default=True) 
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    last_login = Column(TIMESTAMP, default=None)
    two_factor_enabled = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    premium_expires_at = Column(TIMESTAMP, default=None)


class Vote(Base):
    __tablename__ = "votes"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)

    
class Pet(Base):
    __tablename__ = 'pets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    animal_type = Column(String, nullable=False)  # Type of animal (e.g., Mammal, Bird)
    pet_type = Column(String, nullable=False)     # Specific pet (e.g., Cat, Dog)
    breed_1 = Column(String, nullable=False)                        # Breed of the pet (e.g., Persian, Beagle)
    breed_2 = Column(String)                        # Breed of the pet (e.g., Persian, Beagle)
    gender = Column(String(1), nullable=False)    # 'M' for male, 'F' for female, 'O' for other
    profile_picture = Column(String)
    bio = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    date_of_birth = Column(Date)
    is_active = Column(Boolean, default=True)     # Indicates if the pet profile is active
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationship to Users table
    owner = relationship("User", backref="pets")

    

