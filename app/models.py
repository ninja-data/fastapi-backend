from sqlalchemy import Column, Integer, Date, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from .database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    media_url = Column(String, nullable=False)
    media_type = Column(String, nullable=True)
    visibility = Column(String, nullable=False, server_default="public")
    is_active = Column(Boolean, nullable=False, server_default="TRUE", comment="Indicates if the post is active")
    tags = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    likes_count = Column(Integer, nullable=False, server_default="0")
    comments_count = Column(Integer, nullable=False, server_default="0")
    parent_post_id = Column(Integer, ForeignKey("posts.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    edited_at = Column(TIMESTAMP(timezone=True), nullable=True)

   # Relationships
    user = relationship("User", backref="posts", foreign_keys=[user_id])
    pet = relationship("Pet", backref="posts", foreign_keys=[pet_id])
    parent_post = relationship("Post", remote_side=[id], backref="child_posts")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    surname = Column(String)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    profile_picture_url = Column(String)
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


class Like(Base):
    __tablename__ = "likes"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

   # Relationships
    user = relationship("User", backref="likes", foreign_keys=[user_id])
    post = relationship("Post", backref="likes", foreign_keys=[post_id])


class Pet(Base):
    __tablename__ = 'pets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    animal_type = Column(String, nullable=False)  # Type of animal (e.g., Mammal, Bird)
    pet_type = Column(String, nullable=False)     # Specific pet (e.g., Cat, Dog)
    breed_1 = Column(String, nullable=False)                        # Breed of the pet (e.g., Persian, Beagle)
    breed_2 = Column(String)                        # Breed of the pet (e.g., Persian, Beagle)
    gender = Column(String(1), nullable=False)    # 'M' for male, 'F' for female, 'O' for other
    profile_picture_url = Column(String)
    bio = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    date_of_birth = Column(Date)
    is_active = Column(Boolean, default=True)     # Indicates if the pet profile is active
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationship
    user = relationship("User", backref="pets", foreign_keys=[user_id])
