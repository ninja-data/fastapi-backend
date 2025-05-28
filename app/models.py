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
    user = relationship("User", back_populates="posts", foreign_keys=[user_id])
    pet = relationship("Pet", back_populates="posts", foreign_keys=[pet_id])
    parent_post = relationship("Post", remote_side=[id], back_populates="child_posts")
    child_posts = relationship("Post", back_populates="parent_post")  # Added relationship for child posts

    comments = relationship("Comment", back_populates="post")
    likes = relationship("Like", back_populates="post")


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
    private_account = Column(Boolean, default=False) 
    is_premium = Column(Boolean, default=False)
    premium_expires_at = Column(TIMESTAMP, default=None)

    # Relationships
    comments = relationship("Comment", back_populates="user")
    likes = relationship("Like", back_populates="user")
    posts = relationship("Post", back_populates="user")
    pets = relationship("Pet", back_populates="user") 
    stories = relationship("Story", back_populates="user") 


    # New relationships for user relationships
    requested_relationships = relationship(
        "UserRelationship",
        foreign_keys="[UserRelationship.requester_id]",
        back_populates="requester"
    )
    received_relationships = relationship(
        "UserRelationship",
        foreign_keys="[UserRelationship.receiver_id]",
        back_populates="receiver"
    )


class UserRelationship(Base):
    __tablename__ = "user_relationships"

    id = Column(Integer, primary_key=True)
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False, server_default='pending')  # Corrected typo here
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], back_populates='requested_relationships')
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates='received_relationships')


class Like(Base):
    __tablename__ = "likes"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    # Relationships
    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")


class AnimalType(Base):
    __tablename__ = 'animal_types'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    image_url = Column(String, nullable=True)

    # One-to-Many relationship with PetType
    pet_types = relationship("PetType", back_populates="animal_type")
    pets = relationship("Pet", back_populates="animal_type")


class PetType(Base):
    __tablename__ = 'pet_types'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    animal_type_id = Column(Integer, ForeignKey('animal_types.id'), nullable=False)

    # Many-to-One relationship
    animal_type = relationship("AnimalType", back_populates="pet_types")

    breeds = relationship("Breed", back_populates="pet_type")
    pets = relationship("Pet", back_populates="pet_type")



class Breed(Base):
    __tablename__ = 'breeds'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    pet_type_id = Column(Integer, ForeignKey('pet_types.id'), nullable=False)

    pet_type = relationship("PetType", back_populates="breeds")

    # Specify foreign_keys explicitly for relationships
    pets_breed_1 = relationship("Pet", back_populates="breed_1", foreign_keys="[Pet.breed_1_id]")
    pets_breed_2 = relationship("Pet", back_populates="breed_2", foreign_keys="[Pet.breed_2_id]")


# https://github.com/dr5hn/countries-states-cities-database/blob/master/psql/countries.sql
class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    alpha2_code = Column(String(2), unique=True, nullable=False)
    alpha3_code = Column(String(3), unique=True, nullable=False)
    numeric_code = Column(String, nullable=True)
    region_id = Column(Integer, nullable=True)
    subregion_id = Column(Integer, nullable=True)
    flag_url = Column(String, nullable=True)

    # Relationships
    # region = relationship("Region", back_populates="countries")
    # subregion = relationship("Subregion", back_populates="countries")


class Pet(Base):
    __tablename__ = 'pets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    animal_type_id = Column(Integer, ForeignKey('animal_types.id'), nullable=False)  # Type of animal (e.g., Mammal, Bird)
    pet_type_id = Column(Integer, ForeignKey('pet_types.id'), nullable=False)        # Specific pet (e.g., Cat, Dog)
    breed_1_id = Column(Integer, ForeignKey('breeds.id'), nullable=False)            # Breed of the pet (e.g., Persian, Beagle)
    breed_2_id = Column(Integer, ForeignKey('breeds.id'))                            # Breed of the pet (e.g., Persian, Beagle)
    gender = Column(String(1))    # 'M' for male, 'F' for female, 'O' for other
    profile_picture_url = Column(String)
    bio = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    date_of_birth = Column(Date)
    is_active = Column(Boolean, default=True)     # Indicates if the pet profile is active
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="pets")
    posts = relationship("Post", back_populates="pet")
    animal_type = relationship("AnimalType", back_populates="pets")
    pet_type = relationship("PetType", back_populates="pets")
    breed_1 = relationship("Breed", back_populates="pets_breed_1", foreign_keys=[breed_1_id])
    breed_2 = relationship("Breed", back_populates="pets_breed_2", foreign_keys=[breed_2_id])
    stories = relationship("Story", back_populates="pet")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id", ondelete="CASCADE"), nullable=False)
    media_url = Column(String, nullable=True)
    media_type = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP + INTERVAL '1 day'"))


    user = relationship("User", back_populates="stories")
    pet = relationship("Pet", back_populates="stories")