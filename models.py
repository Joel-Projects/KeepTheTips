from sqlalchemy import Boolean, Column, Float, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata

class Submission(Base):
    __tablename__ = 'submissions'
    __table_args__ = {'schema': 'keepthetips'}
    id = Column(Text, primary_key=True)
    commentid = Column(Text)
    author = Column(String(22))
    submitted_timestamp = Column(TIMESTAMP(True, 4))
    removed_timestamp = Column(TIMESTAMP(True, 4))
    submitted = Column(Float(53))
    submission_removed = Column(Boolean, server_default=text("false"))
    comment_removed = Column(Boolean, server_default=text("false"))
    safe = Column(Boolean, server_default=text("false"))