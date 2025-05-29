from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.ext.associationproxy import association_proxy
from pydantic import BaseModel as PydanticBaseModel # To avoid confusion with SQLAlchemy's Base
from typing import List, Optional as TypingOptional, Dict as TypingDict
from datetime import datetime
import json # For handling list/dict as JSON strings
from flask_bcrypt import generate_password_hash, check_password_hash # Add for DBAuthUser

# Using the application's root directory for the database file
DATABASE_URL = "sqlite:///./main_database.db" 

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}) # check_same_thread for SQLite
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
    __tablename__ = "valuepoints"
    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    vp_type = Column(String) 
    price_usd = Column(Float, nullable=True)
    price_sat = Column(Integer, nullable=True)
    
    _next_vps_json = Column("next", Text, default="[]") 

    @property
    def next(self) -> List[str]:
        return json.loads(self._next_vps_json)

    @next.setter
    def next(self, value: List[str]):
        self._next_vps_json = json.dumps(value)

    expires = Column(DateTime, nullable=True)
    interface = Column(String)
    creditable = Column(Boolean, default=True)
    btc_commit = Column(Boolean, default=False)

    active_for_users = relationship("DBUserContext", secondary=user_active_vps_association, back_populates="active_vps_rels")
    completed_by_users = relationship("DBUserContext", secondary=user_completed_vps_association, back_populates="completed_vps_rels")


class DBUserContext(Base):
    __tablename__ = "usercontexts"
    # This user_id will now typically be the username from DBAuthUser
    user_id = Column(String, primary_key=True, index=True) 
    
    active_vps_rels = relationship("DBValuePoint", secondary=user_active_vps_association, back_populates="active_for_users", lazy="joined")
    completed_vps_rels = relationship("DBValuePoint", secondary=user_completed_vps_association, back_populates="completed_by_users", lazy="joined")

    credits_usd = Column(Float, default=0.0)
    credits_sat = Column(Integer, default=0)
    last_input = Column(String, nullable=True)
    
    _infra_json = Column("infra", Text, default="{}")

    @property
    def infra(self) -> TypingDict:
        if self._infra_json is None: 
            return {}
        return json.loads(self._infra_json)

    @infra.setter
    def infra(self, value: TypingDict):
        self._infra_json = json.dumps(value)

class DBAuthUser(Base):
    __tablename__ = "auth_users"
    id = Column(Integer, primary_key=True, index=True) # Auto-incrementing ID
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Relationship to UserContext (one-to-one: one DBAuthUser to one DBUserContext)
    # The DBUserContext.user_id will store the DBAuthUser.username
    # This relationship helps if you want to navigate from DBAuthUser to DBUserContext directly.
    # user_context = relationship("DBUserContext", back_populates="auth_user", uselist=False, 
    #                             primaryjoin="DBAuthUser.username == DBUserContext.user_id", 
    #                             foreign_keys="[DBUserContext.user_id]")


    def set_password(self, password):
        self.hashed_password = generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

# If you add a back_populates to DBAuthUser.user_context, you'd add this to DBUserContext:
# auth_user = relationship("DBAuthUser", back_populates="user_context", 
#                          primaryjoin="DBUserContext.user_id == DBAuthUser.username",
#                          foreign_keys="[DBUserContext.user_id]")


def create_db_and_tables():
    Base.metadata.create_all(bind=engine)

def get_db(): # Renamed from original get_db_session for consistency with potential FastAPI patterns
    db = SessionLocal()
    try:
        yield db # For use with Depends in FastAPI, or context manager
    finally:
        db.close()
