import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Numeric, Text, Enum
)
from sqlalchemy.orm import relationship
from database import Base


# --- ENUMы ---
class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    superadmin = "superadmin"


class OrderStatus(str, enum.Enum):
    pending = "pending"       # ожидает
    in_progress = "in_progress"  # в работе
    completed = "completed"   # готов
    cancelled = "cancelled"   # отменён


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(70), index=True)
    email = Column(String(50), index=True, unique=True)
    phone_number = Column(String(20), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)

    # Связи
    washstations = relationship("WashStation", back_populates="owner")
    orders = relationship("Order", back_populates="customer")


class WashStation(Base):
    __tablename__ = "washstation"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20))
    description = Column(Text)
    image = Column(String(255))
    address = Column(String(255))
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    user_id = Column(Integer, ForeignKey("users.id"))  # владелец мойки

    # Связи
    owner = relationship("User", back_populates="washstations")
    services = relationship("Service", back_populates="washstation")
    orders = relationship("Order", back_populates="washstation")
    ratings = relationship("Rating", back_populates="washstation")
    employees = relationship("Employ", back_populates="washstation")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    duration_minutes = Column(Integer)
    description = Column(Text)
    wash_id = Column(Integer, ForeignKey("washstation.id"))

    washstation = relationship("WashStation", back_populates="services")


class Car(Base):
    __tablename__ = "car"

    id = Column(Integer, primary_key=True, index=True)
    wash_id = Column(Integer, ForeignKey("washstation.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    employ_id = Column(Integer, ForeignKey("employ.id"))
    car_model = Column(String(100))
    car_number = Column(String(20))
    year = Column(Integer)
    color = Column(String(30))
    entry_time = Column(DateTime)
    exit_time = Column(DateTime)


class Order(Base):
    __tablename__ = "order"

    id = Column(Integer, primary_key=True, index=True)
    wash_id = Column(Integer, ForeignKey("washstation.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)
    date = Column(DateTime)
    total_price = Column(Numeric(10, 2))
    status = Column(Enum(OrderStatus), default=OrderStatus.pending, nullable=False)

    # Связи
    customer = relationship("User", back_populates="orders")
    washstation = relationship("WashStation", back_populates="orders")


class Rating(Base):
    __tablename__ = "rating"

    id = Column(Integer, primary_key=True, index=True)
    wash_id = Column(Integer, ForeignKey("washstation.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    star = Column(Integer)
    comment = Column(Text)

    washstation = relationship("WashStation", back_populates="ratings")


class Employ(Base):
    __tablename__ = "employ"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(70))
    phone_number = Column(String(20))
    role = Column(String(50))
    wash_id = Column(Integer, ForeignKey("washstation.id"))

    washstation = relationship("WashStation", back_populates="employees")
