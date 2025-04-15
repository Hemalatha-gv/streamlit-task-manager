import streamlit as st
import uuid
import pandas as pd
from database import init_db, add_user, get_user_by_username, SessionLocal
from models import User, Task
from sqlalchemy.orm import joinedload


# Initialize DB on app start
init_db()

# ---------- Authentication Logic ----------
def sign_up(username, password, email, role):
    user = get_user_by_username(username)
    if user:
        st.warning("Username already exists.")
    else:
        add_user(username, password, email, role)
        st.success("User registered successfully!")

def sign_in(username, password, role):
    user = get_user_by_username(username)
    if user and user.password == password and user.role.lower() == role.lower():
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.selected_role = role
        st.session_state.page = "dashboard"
        st.success(f"Welcome {username}!")
        st.rerun()
    else:
        st.error("Incorrect username, password, or role.")

def logout():
    st.session_state.logged_in = False
    st.session_state.page = 'home'
    st.session_state.trigger_rerun = True

# ---------- Helper Functions ----------
def save_task_to_db(domain, description, file_path, epm_id, reviewer_id):
    db = SessionLocal()
    new_task = Task(domain=domain, description=description, file_path=file_path, epm_id=epm_id, reviewer_id=reviewer_id)
    db.add(new_task)
    db.commit()
    db.close()

def load_tasks_from_db():
    db = SessionLocal()
    tasks = db.query(Task).options(
        joinedload(Task.volunteer),
        joinedload(Task.reviewer),
        joinedload(Task.epm)
    ).all()
    db.close()
    return tasks

# ---------- Page Functions ----------
def signup_page():
    st.title("Sign Up")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    email = st.text_input("Email")
    role = st.selectbox("Select Role", ["EPM", "Volunteer", "Reviewer"])
    if st.button("Sign Up"):
        if username and password and email and role:
            sign_up(username, password, email, role)
        else:
            st.warning("Please fill in all fields.")

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Select Role", ["EPM", "Volunteer", "Reviewer"])
    if st.button("Login"):
        if username and password and role:
            sign_in(username, password, role)
        else:
            st.warning("Please fill in all fields.")

# ---------- Dashboards ----------
def epm_dashboard():
    st.sidebar.button("Logout", on_click=logout)
    st.title("EPM Dashboard")
    st.write(f"Welcome, {st.session_state.username}")
    st.subheader("Create a New Task")

    task_domain = st.text_input("Task Domain")
    task_description = st.text_area("Task Description")
    uploaded_file = st.file_uploader("Attach File", type=["pdf", "txt", "csv", "docx"])

    db = SessionLocal()
    reviewers = db.query(User).filter_by(role='Reviewer').all()
    reviewer_names = [r.username for r in reviewers]
    selected_reviewer = st.selectbox("Assign Reviewer", reviewer_names) if reviewer_names else None
    db.close()

    if st.button("Create Task"):
        if not selected_reviewer:
            st.error("Please select a reviewer to assign this task.")
        else:
            db = SessionLocal()
            epm = db.query(User).filter_by(username=st.session_state.username).first()
            reviewer = db.query(User).filter_by(username=selected_reviewer).first()
            file_path = uploaded_file.name if uploaded_file else None
            save_task_to_db(task_domain, task_description, file_path, epm.id, reviewer.id)
            db.close()
            st.success("Task created successfully!")
            st.rerun()

    st.subheader("All Tasks")
    tasks = load_tasks_from_db()
    if tasks:
        df = pd.DataFrame([{
            'ID': t.id,
            'Domain': t.domain,
            'Volunteer': t.volunteer.username if t.volunteer else 'Unassigned',
            'Reviewer': t.reviewer.username if t.reviewer else '',
            'Status': t.status
        } for t in tasks])
        st.dataframe(df)

def volunteer_dashboard():
    st.sidebar.button("Logout", on_click=logout)
    st.title("Volunteer Dashboard")
    st.write(f"Welcome, {st.session_state.username}")

    db = SessionLocal()
    user = db.query(User).filter_by(username=st.session_state.username).first()
    available_tasks = db.query(Task).filter_by(volunteer_id=None).all()
    my_tasks = db.query(Task).filter_by(volunteer_id=user.id).all()

    st.subheader("Available Tasks")
    for task in available_tasks:
        st.markdown(f"**Task ID:** {task.id}")
        st.markdown(f"**Domain:** {task.domain}")
        st.markdown(f"**Description:** {task.description}")
        if st.button(f"Take Task {task.id}"):
            task.volunteer_id = user.id
            task.status = 'In Progress'
            db.commit()
            st.success(f"You have taken the task {task.id}")
            st.rerun()

    st.subheader("Your Tasks")
    for task in my_tasks:
        st.markdown(f"**Task ID:** {task.id}")
        st.markdown(f"**Domain:** {task.domain}")
        st.markdown(f"**Status:** {task.status}")
        if task.status == 'In Progress':
            uploaded = st.file_uploader(f"Submit work for Task {task.id}", type=["pdf", "txt", "csv", "docx"])
            if uploaded:
                task.submitted_file_path = uploaded.name
                db.commit()
                st.success(f"Work submitted for Task {task.id}")
    db.close()

def reviewer_dashboard():
    st.sidebar.button("Logout", on_click=logout)
    st.title("Reviewer Dashboard")
    st.write(f"Welcome, {st.session_state.username}")

    db = SessionLocal()
    reviewer = db.query(User).filter_by(username=st.session_state.username).first()
    tasks = db.query(Task).filter_by(reviewer_id=reviewer.id).all()

    st.subheader("Tasks Assigned to You")
    for task in tasks:
        st.markdown(f"**Task ID:** {task.id}")
        st.markdown(f"**Domain:** {task.domain}")
        st.markdown(f"**Volunteer:** {task.volunteer.username if task.volunteer else 'None'}")
        st.markdown(f"**Status:** {task.status}")

        if task.submitted_file_path:
            st.markdown(f"Submitted File: {task.submitted_file_path}")
            feedback_key = f"feedback_{task.id}"
            st.session_state[feedback_key] = st.text_area(
                f"Provide Feedback for Task {task.id}",
                st.session_state.get(feedback_key, task.feedback or "")
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Mark as Done - {task.id}"):
                    task.status = 'Done'
                    task.feedback = st.session_state[feedback_key]
                    db.commit()
                    st.success(f"Task {task.id} marked as Done.")
                    st.rerun()
            with col2:
                if st.button(f"✏️ Needs Changes - {task.id}"):
                    task.status = 'Needs Changes'
                    task.feedback = st.session_state[feedback_key]
                    db.commit()
                    st.info(f"Task {task.id} marked as Needs Changes.")
                    st.rerun()
        else:
            st.write("Work has not been submitted yet.")
    db.close()

def show_dashboard():
    role = st.session_state.selected_role.lower()
    if role == "epm":
        epm_dashboard()
    elif role == "volunteer":
        volunteer_dashboard()
    elif role == "reviewer":
        reviewer_dashboard()
    else:
        st.error("Unknown role!")

# ---------- Main ----------
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "page" not in st.session_state:
        st.session_state.page = "login"

    if not st.session_state.logged_in:
        page = st.sidebar.radio("Navigate", ["Login", "Sign Up"])
        if page == "Login":
            login_page()
        elif page == "Sign Up":
            signup_page()
    else:
        show_dashboard()

    if st.session_state.get("trigger_rerun", False):
        st.session_state.trigger_rerun = False
        st.rerun()

if __name__ == "__main__":
    main()
