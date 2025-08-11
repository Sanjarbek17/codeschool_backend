# CodeSchool Project Flow 🔄

A comprehensive guide explaining the user journey and system flow of the CodeSchool online learning platform.

## 🎯 Project Overview

CodeSchool is an online coding education platform where teachers create lessons, assign coding homework, and students submit solutions that are automatically evaluated through test cases.

## 👥 User Types & Roles

### 🧑‍🏫 Teachers
- Create and manage lessons with video content
- Design homework assignments with coding tasks
- Create test cases for automatic evaluation
- Track student progress and performance
- Review code submissions and provide feedback

### 🎓 Students
- Access assigned lessons and video content
- Complete homework assignments with coding tasks
- Submit code solutions for evaluation
- Track personal progress and test results
- View feedback and performance analytics

### 👨‍💼 Administrators
- Manage all users, teachers, and students
- Oversee course content and assignments
- Monitor platform usage and analytics
- Configure system settings and permissions

## 🔄 Complete User Flow

### 1. Authentication Flow 🔐

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Registration  │───▶│     Login       │───▶│  Token Access   │
│                 │    │                 │    │                 │
│ • Username      │    │ • Username      │    │ • API Token     │
│ • Email         │    │ • Password      │    │ • User Profile  │
│ • Password      │    │                 │    │ • Role Access   │
│ • User Type     │    │                 │    │                 │
│ • Profile Info  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Steps:**
1. **Registration**: Choose user type (Teacher/Student) and provide profile information
2. **Profile Creation**: System automatically creates Teacher or Student profile
3. **Login**: Authenticate with username/password to receive API token
4. **Dashboard Access**: Access role-specific dashboard with appropriate permissions

### 2. Teacher Workflow 🧑‍🏫

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Create Lesson  │───▶│ Create Homework │───▶│  Create Tasks   │
│                 │    │                 │    │                 │
│ • Title         │    │ • Title         │    │ • Task Title    │
│ • Description   │    │ • Description   │    │ • Description   │
│ • Video URL     │    │ • Link to Lesson│    │ • Test Cases    │
│ • Content       │    │                 │    │ • Hidden Tests  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Assign Teachers │    │ Monitor Progress│    │ Review Results  │
│                 │    │                 │    │                 │
│ • Add Teachers  │    │ • Student Stats │    │ • Submissions   │
│ • Manage Access │    │ • Completion %  │    │ • Test Results  │
│                 │    │ • Performance   │    │ • Code Review   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Detailed Teacher Journey:**

1. **Lesson Creation**
   - Create lesson with video content and materials
   - Write comprehensive lesson description and content
   - Assign other teachers as collaborators

2. **Homework Design**
   - Create homework assignments linked to lessons
   - Define learning objectives and requirements
   - Set deadlines and submission guidelines

3. **Task Development**
   - Design individual coding tasks within homework
   - Create test cases for automatic evaluation
   - Set up hidden test cases for comprehensive testing

4. **Student Management**
   - Monitor student progress across all assignments
   - Review submitted code and provide feedback
   - Track performance analytics and completion rates

### 3. Student Workflow 🎓

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Browse Lessons │───▶│   Watch Video   │───▶│ Access Homework │
│                 │    │                 │    │                 │
│ • Available     │    │ • Video Content │    │ • Task List     │
│ • Assigned      │    │ • Take Notes    │    │ • Requirements  │
│ • In Progress   │    │ • Study Material│    │ • Deadlines     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Solve Tasks   │───▶│ Submit Solution │───▶│  View Results   │
│                 │    │                 │    │                 │
│ • Code Editor   │    │ • Upload File   │    │ • Test Results  │
│ • Test Cases    │    │ • Code Text     │    │ • Score/Grade   │
│ • Debug Code    │    │ • Validation    │    │ • Feedback      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Detailed Student Journey:**

1. **Content Access**
   - Browse available lessons and assigned homework
   - Watch instructional videos and study materials
   - Access task requirements and guidelines

2. **Code Development**
   - Use integrated code editor or upload files
   - Write solutions for assigned coding tasks
   - Run local tests to validate solutions

3. **Submission Process**
   - Submit code solutions through the platform
   - Solutions are automatically tested against test cases
   - Receive immediate feedback on test results

4. **Progress Tracking**
   - Monitor completion status across all assignments
   - View performance analytics and improvement areas
   - Track overall learning progress

## 🏗️ System Architecture Flow

### Data Flow Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │───▶│   Django API    │───▶│    Database     │
│                 │    │                 │    │                 │
│ • React/Vue     │    │ • REST APIs     │    │ • SQLite/PG     │
│ • Authentication│    │ • Token Auth    │    │ • User Data     │
│ • Code Editor   │    │ • Permissions   │    │ • Content Data  │
│ • Dashboard     │    │ • Validation    │    │ • Progress Data │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Code Execution │    │  Progress Engine│    │   File Storage  │
│                 │    │                 │    │                 │
│ • Test Runner   │    │ • Tracking      │    │ • Submissions   │
│ • Evaluation    │    │ • Analytics     │    │ • Videos        │
│ • Results       │    │ • Reporting     │    │ • Resources     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 Database Relationships Flow

### Core Entity Relationships

```
User ────────┬─────────► Teacher
             └─────────► Student
                    
Teacher ─────────────► Lessons (Many-to-Many)
                    
Lessons ─────────────► Homework (One-to-Many)
                    
Homework ────────────► Task (One-to-Many)
                    
Task ────────────────► TestCase (One-to-Many)

Student ─────────────► HomeworkProgress (One-to-Many)
                    
Student ─────────────► TaskProgress (One-to-Many)
                    
Student ─────────────► HomeworkSubmission (One-to-Many)
```

## 🔄 API Workflow

### Authentication Endpoints
```
POST /api/auth/register/        # User registration
POST /api/auth/login/           # Get authentication token
GET  /api/auth/profile/         # Get user profile
POST /api/auth/logout/          # Invalidate token
```

### Content Management Endpoints
```
GET  /api/courses/lessons/              # List all lessons
POST /api/courses/lessons/              # Create new lesson
GET  /api/courses/lessons/{id}/         # Get lesson details
GET  /api/courses/lessons/{id}/homework/# Get lesson homework

GET  /api/assignments/homework/         # List homework
POST /api/assignments/homework/         # Create homework
GET  /api/assignments/tasks/            # List tasks
POST /api/assignments/tasks/            # Create task
```

### Progress Tracking Endpoints
```
GET  /api/progress/homework/            # Homework progress
GET  /api/progress/tasks/               # Task progress
POST /api/progress/tasks/               # Update progress

GET  /api/submissions/homework/         # List submissions
POST /api/submissions/homework/         # Submit solution
GET  /api/submissions/homework/{id}/    # Get submission details
```

## 🚀 Development Workflow

### 1. Initial Setup
```bash
# Clone and setup project
git clone <repository>
python -m venv env
source env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
```

### 2. Development Process
```bash
# Start development server
python manage.py runserver

# Access admin interface
http://localhost:8000/admin/

# API documentation
http://localhost:8000/swagger/
```

### 3. Testing Flow
```bash
# Run all tests
python manage.py test

# Test specific app
python manage.py test apps.accounts
```

## 🔧 Integration Points

### Frontend Integration
- **Authentication**: Token-based API authentication
- **Real-time Updates**: WebSocket support for live progress
- **File Uploads**: Code submission with file support
- **Code Editor**: Integration with Monaco/CodeMirror

### External Services
- **Video Hosting**: YouTube/Vimeo integration
- **Code Execution**: Docker containers for safe code running
- **Email Service**: Notifications and password reset
- **Analytics**: Progress tracking and performance metrics

## 📈 Future Enhancements

### Phase 1 (Current)
- ✅ Basic authentication system
- ✅ Lesson and homework management
- ✅ Progress tracking
- ✅ Code submission system

### Phase 2 (Planned)
- 🔄 Real-time code execution
- 🔄 Advanced analytics dashboard
- 🔄 Collaborative code editing
- 🔄 Plagiarism detection

### Phase 3 (Future)
- 📋 AI-powered code review
- 📋 Adaptive learning paths
- 📋 Mobile application
- 📋 Integration with external coding platforms

---

This flow documentation provides a complete understanding of how users interact with the CodeSchool platform, from registration to assignment completion and progress tracking.
