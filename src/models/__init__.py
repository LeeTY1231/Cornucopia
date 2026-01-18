from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, Date, UUID, BigInteger, DECIMAL
from sqlalchemy.sql import func
from datetime import datetime, timezone

ModelBase = declarative_base()
