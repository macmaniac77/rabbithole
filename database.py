from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from pydantic import BaseModel as PydanticBaseModel # To avoid confusion with SQLAlchemy's Base
from typing import List, Optional as TypingOptional, Dict as TypingDict
from datetime import datetime
import json # For handling list/dict as JSON strings
from flask_bcrypt import generate_password_hash, check_password_hash # Add for DBAuthUser

# Using the application's root directory for the database file
DATABASE_URL = "sqlite:///./main_database.db" # Path to the SQLite database file

# The 'connect_args={"check_same_thread": False}' is specific to SQLite.
# It allows the database connection to be shared across multiple threads,
# which is necessary for some web server configurations (like Flask's default)
# where different requests might be handled by different threads.
# For other database systems, this argument may not be needed or applicable.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Association table for UserContext.active_vps (many-to-many)
user_active_vps_association = Table('user_active_vps', Base.metadata,
    Column('user_context_id', String, ForeignKey('usercontexts.user_id'), primary_key=True),
    Column('value_point_id', String, ForeignKey('valuepoints.id'), primary_key=True)
)

# Association table for UserContext.completed_vps (many-to-many)
user_completed_vps_association = Table('user_completed_vps', Base.metadata,
    Column('user_context_id', String, ForeignKey('usercontexts.user_id'), primary_key=True),
    Column('value_point_id', String, ForeignKey('valuepoints.id'), primary_key=True)
)

class DBValuePoint(Base):
    """
    SQLAlchemy ORM model for representing "value points" (VPs) in the system.

    ValuePoints can be tasks, items, services, contractual obligations, or any
    other unit of value or interaction within the application. They have defined
    properties like type, price, and interface, and can be linked to users
    as active or completed items.
    """
    __tablename__ = "valuepoints"
    id = Column(String, primary_key=True, index=True) # Unique identifier for the VP
    title = Column(String, index=True) # Human-readable title or name of the VP
    vp_type = Column(String) # Type of the VP (e.g., "task", "payment", "contract")
    price_usd = Column(Float, nullable=True) # Price in USD, if applicable
    price_sat = Column(Integer, nullable=True) # Price in satoshis, if applicable
    
    # Stores a list of next VP IDs as a JSON string in the database.
    # The 'next' property provides convenient Python list access.
    _next_vps_json = Column("next", Text, default="[]") 

    @property
    def next(self) -> List[str]:
        """Gets the list of next ValuePoint IDs, deserialized from JSON."""
        return json.loads(self._next_vps_json)

    @next.setter
    def next(self, value: List[str]):
        """Sets the list of next ValuePoint IDs, serializing to JSON for storage."""
        self._next_vps_json = json.dumps(value)

    expires = Column(DateTime, nullable=True) # Optional expiration date/time for the VP
    interface = Column(String) # Path or identifier for the UI/markdown file associated with this VP
    creditable = Column(Boolean, default=True) # Whether completing this VP grants credits to the user
    btc_commit = Column(Boolean, default=False) # Whether this VP involves a Bitcoin on-chain commitment

    # Relationship: Users who have this VP in their active list.
    # Populated via the 'user_active_vps_association' table.
    active_for_users = relationship("DBUserContext", secondary=user_active_vps_association, back_populates="active_vps_rels")

    # Relationship: Users who have completed this VP.
    # Populated via the 'user_completed_vps_association' table.
    completed_by_users = relationship("DBUserContext", secondary=user_completed_vps_association, back_populates="completed_vps_rels")


class DBUserContext(Base):
    """
    SQLAlchemy ORM model for storing user-specific data, state, and context.

    This model holds information like user credits, last interactions, and
    references to their active and completed ValuePoints. It also includes
    a flexible 'infra' field for storing other user-related infrastructure details.
    The `user_id` typically corresponds to the username from `DBAuthUser`.
    """
    __tablename__ = "usercontexts"
    user_id = Column(String, primary_key=True, index=True) # User identifier, usually username. Links to DBAuthUser.username.
    
    # Relationship: ValuePoints currently active for this user.
    # `lazy="joined"` means that when a DBUserContext is loaded, its active_vps_rels
    # will be loaded in the same query (using a JOIN). This can be more efficient
    # than the default "select" loading (which issues a separate SELECT per access)
    # if you almost always access the related VPs. However, it can make the initial
    # query heavier if the related VPs are numerous and not always needed.
    active_vps_rels = relationship("DBValuePoint", secondary=user_active_vps_association, back_populates="active_for_users", lazy="joined")

    # Relationship: ValuePoints completed by this user.
    # Similar to active_vps_rels, `lazy="joined"` loads these VPs with the user context.
    completed_vps_rels = relationship("DBValuePoint", secondary=user_completed_vps_association, back_populates="completed_by_users", lazy="joined")

    credits_usd = Column(Float, default=0.0) # User's current balance in USD
    credits_sat = Column(Integer, default=0) # User's current balance in satoshis
    last_input = Column(String, nullable=True) # Stores the last input or action text from the user
    
    # Stores a dictionary of user-specific infrastructure details as a JSON string.
    # The 'infra' property provides convenient Python dict access.
    _infra_json = Column("infra", Text, default="{}")

    @property
    def infra(self) -> TypingDict:
        """Gets the user's infrastructure details, deserialized from JSON."""
        if self._infra_json is None: 
            return {}
        return json.loads(self._infra_json)

    @infra.setter
    def infra(self, value: TypingDict):
        """Sets the user's infrastructure details, serializing to JSON for storage."""
        self._infra_json = json.dumps(value)

class DBAuthUser(Base):
    """
    SQLAlchemy ORM model for user authentication credentials.

    This model stores user identity information, primarily the username and
    a hashed password for secure authentication.
    """
    __tablename__ = "auth_users"
    id = Column(Integer, primary_key=True, index=True) # Auto-incrementing primary key
    username = Column(String, unique=True, index=True, nullable=False) # Unique username for login
    hashed_password = Column(String, nullable=False) # Hashed password for security

    # Relationship to UserContext (one-to-one: one DBAuthUser to one DBUserContext)
    # The DBUserContext.user_id will store the DBAuthUser.username
    # This relationship helps if you want to navigate from DBAuthUser to DBUserContext directly.
    # user_context = relationship("DBUserContext", back_populates="auth_user", uselist=False, 
    #                             primaryjoin="DBAuthUser.username == DBUserContext.user_id", 
    #                             foreign_keys="[DBUserContext.user_id]")


    def set_password(self, password: str):
        """
        Hashes the given password and stores it in `hashed_password`.

        :param password: The plain-text password to hash.
        """
        self.hashed_password = generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """
        Checks if the given plain-text password matches the stored hashed password.

        :param password: The plain-text password to check.
        :return: True if the password matches, False otherwise.
        """
        return check_password_hash(self.hashed_password, password)

# If you add a back_populates to DBAuthUser.user_context, you'd add this to DBUserContext:
# auth_user = relationship("DBAuthUser", back_populates="user_context", 
#                          primaryjoin="DBUserContext.user_id == DBAuthUser.username",
#                          foreign_keys="[DBUserContext.user_id]")


def create_db_and_tables():
    """
    Creates all database tables defined in the SQLAlchemy models.

    This function uses `Base.metadata.create_all(bind=engine)` to issue
    CREATE TABLE statements to the database connected via `engine`.
    It should be called once at application startup to ensure the database
    schema is initialized.
    """
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Provides a SQLAlchemy database session and ensures it's closed after use.

    This function is a generator that yields a database session from `SessionLocal`.
    It's designed to be used as a dependency, for example, with FastAPI's `Depends`
    or within a Python `with` statement (if adapted) to manage the session lifecycle.
    The `finally` block guarantees that the session is closed, releasing resources.

    In a Flask context without FastAPI's dependency injection, this function might
    be called directly, and the session would need to be manually closed, or the
    function adapted for use with Flask's request lifecycle (e.g., using `g` object
    or an application context). The current `yield` pattern is more common with FastAPI.

    :yields: A SQLAlchemy Session object.
    """
    db = SessionLocal()
    try:
        yield db # For use with Depends in FastAPI, or context manager
    finally:
        db.close()
