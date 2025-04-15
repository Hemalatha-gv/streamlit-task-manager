from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)
    role = Column(String, nullable=False)

    tasks_created = relationship("Task", back_populates="epm", foreign_keys='Task.epm_id')
    tasks_reviewed = relationship("Task", back_populates="reviewer", foreign_keys='Task.reviewer_id')
    tasks_taken = relationship("Task", back_populates="volunteer", foreign_keys='Task.volunteer_id')

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    domain = Column(String)
    description = Column(Text)
    file_path = Column(String)
    status = Column(String, default='Not Done')
    feedback = Column(Text)
    submitted_file_path = Column(String, nullable=True)

    epm_id = Column(Integer, ForeignKey('users.id'))
    reviewer_id = Column(Integer, ForeignKey('users.id'))
    volunteer_id = Column(Integer, ForeignKey('users.id'))

    epm = relationship("User", foreign_keys=[epm_id], back_populates="tasks_created")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="tasks_reviewed")
    volunteer = relationship("User", foreign_keys=[volunteer_id], back_populates="tasks_taken")
