from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup
engine = create_engine("sqlite:///task_manager.db", connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Initialize database
def init_db():
    from models import User, Task  # Import models only here to avoid circular import
    Base.metadata.create_all(bind=engine)

# Helper functions
def get_user_by_username(username):
    from models import User
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    return user

def add_user(username, password, email, role):
    from models import User
    db = SessionLocal()
    new_user = User(username=username, password=password, email=email, role=role)
    db.add(new_user)
    db.commit()
    db.close()

def save_task_to_db(task):
    from models import Task, User
    db = SessionLocal()
    epm = db.query(User).filter_by(username=task['epm']).first()
    reviewer = db.query(User).filter_by(username=task['reviewer']).first()
    volunteer = db.query(User).filter_by(username=task['volunteer']).first() if task['volunteer'] else None

    new_task = Task(
        domain=task['domain'],
        description=task['description'],
        file_path=task['file_path'],
        status=task['status'],
        feedback=task['feedback'],
        submitted_file_path=task['submitted_file_path'],
        epm_id=epm.id,
        reviewer_id=reviewer.id,
        volunteer_id=volunteer.id if volunteer else None
    )
    db.add(new_task)
    db.commit()
    db.close()
    
def load_tasks_from_db():
    from models import Task, User
    db = SessionLocal()
    tasks = []
    for t in db.query(Task).all():
        tasks.append({
            'task_id': t.id,
            'domain': t.domain,
            'description': t.description,
            'file_path': t.file_path,
            'status': t.status,
            'feedback': t.feedback,
            'submitted_file_path': t.submitted_file_path,
            'epm': db.query(User).filter_by(id=t.epm_id).first().username,
            'reviewer': db.query(User).filter_by(id=t.reviewer_id).first().username,
            'volunteer': db.query(User).filter_by(id=t.volunteer_id).first().username if t.volunteer_id else None
        })
    db.close()
    return tasks


