from sqlalchemy.orm import declarative_base

Base = declarative_base()
from app.db.models import Document, Chunk, Conversation, Message, Job