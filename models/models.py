from sqlalchemy import Column, Integer, String, Text, DateTime, LargeBinary
from models.database import Base


class Families(Base):
    __tablename__ = 'families'
    id = Column(Integer, primary_key=True)
    family_id = Column(String(128), unique=True)

    def __init__(self, family_id=None):
        self.family_id = family_id



#以下を追加
class Affiliation(Base):
    __tablename__ = 'affiliation'
    id = Column(Integer, primary_key=True)
    family_id = Column(String(128), unique=False)
    twi_id = Column(String(128))

    def __init__(self, family_id=None, twi_id=None):
        self.family_id = family_id
        self.twi_id = twi_id

class Stocks(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, primary_key=True)
    twi_link = Column(String(255), unique=False)
    family_id = Column(String(128), unique=True)
    twi_img = Column(LargeBinary(), unique=False)

    def __init__(self, twi_link=None, family_id=None, twi_img=None):
        self.twi_link = twi_link
        self.family_id = family_id
        self.twi_img = twi_img
#追加終わり