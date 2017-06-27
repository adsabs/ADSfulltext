# -*- coding: utf-8 -*-

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP

Base = declarative_base()

class KeyValue(Base):
    """Example model, it stores key/value pairs - a persistent configuration"""
    __tablename__ = 'storage'
    key = Column(String(255), primary_key=True)
    value = Column(Text)
    
    def toJSON(self):
        return {'key': self.key, 'value': self.value } 
