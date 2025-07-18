from sqlalchemy import Column, Integer, SmallInteger, Numeric, Date, String, Text, Boolean, ForeignKey
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
    phone = Column(String, unique=True, nullable=True)
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


    conversations = relationship("Participant", back_populates="user")
    messages_sent = relationship("Message", back_populates="sender")


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

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    iso3 = Column(String(3))
    numeric_code = Column(String(3))
    iso2 = Column(String(2))
    phonecode = Column(String(255))
    capital = Column(String(255))
    currency = Column(String(255))
    currency_name = Column(String(255))
    currency_symbol = Column(String(255))
    tld = Column(String(255))
    native = Column(String(255))
    region = Column(String(255))
    # region_id = Column(Integer, ForeignKey("regions.id"), index=True)
    region_id = Column(Integer, index=True)
    subregion = Column(String(255))
    # subregion_id = Column(Integer, ForeignKey("subregions.id"), index=True)
    subregion_id = Column(Integer, index=True)
    nationality = Column(String(255))
    timezones = Column(Text)
    translations = Column(Text)
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    emoji = Column(String(191))
    emojiU = Column(String(191))
    created_at = Column(TIMESTAMP(timezone=False))
    updated_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    flag = Column(SmallInteger, nullable=False, server_default=text("1"))
    wikiDataId = Column(String(255), comment="Rapid API GeoDB Cities")

    # Relationships
    # region = relationship("Region", back_populates="countries")
    # subregion = relationship("Subregion", back_populates="countries")
    cities = relationship("City", back_populates="country") 
    pets = relationship("Pet", back_populates="country") 


class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    state_id = Column(Integer, nullable=False)  # Consider adding ForeignKey if states table exists
    state_code = Column(String(255), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)  # Consider adding ForeignKey if countries table exists
    country_code = Column(String(2), nullable=False)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=text("'2014-01-01 12:01:01'")
    )
    updated_at = Column(
        TIMESTAMP(timezone=False),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    flag = Column(SmallInteger, nullable=False, server_default=text("1"))
    wikiDataId = Column(String(255))

    # Relationships
    country = relationship("Country", back_populates="cities")
    pets = relationship("Pet", back_populates="city")


class Pet(Base):
    __tablename__ = 'pets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # TODO
    nickname = Column(String(50))  # New unique nickname field
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
    is_for_sale = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    country_id = Column(Integer, ForeignKey('countries.id', ondelete="SET NULL"))
    city_id = Column(Integer, ForeignKey('cities.id', ondelete="SET NULL"))
    
    # Relationships
    user = relationship("User", back_populates="pets")
    posts = relationship("Post", back_populates="pet")
    animal_type = relationship("AnimalType", back_populates="pets")
    pet_type = relationship("PetType", back_populates="pets")
    breed_1 = relationship("Breed", back_populates="pets_breed_1", foreign_keys=[breed_1_id])
    breed_2 = relationship("Breed", back_populates="pets_breed_2", foreign_keys=[breed_2_id])
    stories = relationship("Story", back_populates="pet")
    country = relationship("Country", back_populates="pets")
    city = relationship("City", back_populates="pets")


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


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    last_message_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    conversation_type = Column(String(20), nullable=False, server_default='direct')  # direct/group
    name = Column(String(100), nullable=True)  # Group name
    
    # Relationships
    participants = relationship("Participant", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation")

class Participant(Base):
    __tablename__ = "participants"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    joined_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    is_admin = Column(Boolean, default=False)  # For group admins
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    conversation = relationship("Conversation", back_populates="participants")
    read_receipts = relationship("ReadReceipt", back_populates="participant")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text)
    media_url = Column(String)
    media_type = Column(String(30))  # image/video/audio/document
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    read_receipts = relationship("ReadReceipt", back_populates="message")

class ReadReceipt(Base):
    __tablename__ = "read_receipts"
    
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True)
    participant_id = Column(Integer, ForeignKey("participants.id", ondelete="CASCADE"), primary_key=True)
    read_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    
    # Relationships
    message = relationship("Message", back_populates="read_receipts")
    participant = relationship("Participant", back_populates="read_receipts")