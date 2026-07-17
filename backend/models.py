from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class UserEntity(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship: 1 User -> M Chats
    # cascade="all, delete-orphan" ensures if a user is deleted, their chats are too
    chats = relationship(
        "ChatEntity", back_populates="user", cascade="all, delete-orphan"
    )


class ChatEntity(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False, default="New Chat")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship: M Chats -> 1 User
    user = relationship("UserEntity", back_populates="chats")

    # Relationship: 1 Chat -> M QAPairs
    qa_pairs = relationship(
        "QAPairEntity", back_populates="chat", cascade="all, delete-orphan"
    )


class QAPairEntity(Base):
    __tablename__ = "qa_pairs"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(
        Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship: M QAPairs -> 1 Chat
    chat = relationship("ChatEntity", back_populates="qa_pairs")

    # Relationship: 1 QAPair -> 1 Question
    # uselist=False forces a 1-to-1 relationship strictly
    question = relationship(
        "QuestionEntity",
        back_populates="qa_pair",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Relationship: 1 QAPair -> 1 Answer
    answer = relationship(
        "AnswerEntity",
        back_populates="qa_pair",
        uselist=False,
        cascade="all, delete-orphan",
    )


class QuestionEntity(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    # unique=True is strictly required at the DB level for a 1-to-1 relationship
    qa_pair_id = Column(
        Integer,
        ForeignKey("qa_pairs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    content = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship: 1 Question -> 1 QAPair
    qa_pair = relationship("QAPairEntity", back_populates="question")


class AnswerEntity(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    # unique=True is strictly required at the DB level for a 1-to-1 relationship
    qa_pair_id = Column(
        Integer,
        ForeignKey("qa_pairs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    content = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship: 1 Answer -> 1 QAPair
    qa_pair = relationship("QAPairEntity", back_populates="answer")
