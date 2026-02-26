from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, UUID, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as pgUUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    preferences = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_url = Column(String, nullable=False)
    source_name = Column(String(20), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    price_eur = Column(Float, nullable=False)
    region = Column(String(50))
    city = Column(String(50))
    condition = Column(String(20), nullable=False)
    year = Column(Integer)
    brand = Column(String(100))
    category = Column(String(50), nullable=False)
    shipping_cost = Column(Float, default=0.0)
    metadata_ = Column("metadata", JSONB, default={})
    updated_at = Column(DateTime, default=datetime.utcnow)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    verified = Column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint('source_url', 'source_name', name='unique_source'),
    )


class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(pgUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    product_id = Column(pgUUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    score = Column(Float, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='recommendations')
    product = relationship('Product', back_populates='recommendations')


User.recommendations = relationship('Recommendation', order_by=Recommendation.generated_at, back_populates='user')
Product.recommendations = relationship('Recommendation', order_by=Recommendation.generated_at, back_populates='product')

def get_database_url():
    import os
    return os.getenv('DATABASE_URL', 'postgresql://piranha:pass@localhost:5432/piranha')

def get_engine():
    return create_engine(get_database_url())

def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def create_tables():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    create_tables()