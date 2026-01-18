from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, Date, BigInteger, JSON
from sqlalchemy.sql import func
from datetime import datetime

ModelBase = declarative_base()
