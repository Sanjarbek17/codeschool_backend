# Admin Registration Endpoints

This document describes the new admin registration endpoints for creating student and teacher accounts with auto-generated credentials.

## Overview

The admin panel now includes dedicated endpoints for administrators to register new students and teachers. These endpoints automatically generate usernames and passwords, making the registration process simple for admins. The generated credentials are provided in the response so admins can share them with students/teachers.

## Endpoints

### 1. Student Registration
**URL:** `POST /api/admin-panel/register/student/`  
**Permission:** Admin only  
**Purpose:** Create a new student account with auto-generated username and password

### 2. Teacher Registration  
**URL:** `POST /api/admin-panel/register/teacher/`  
**Permission:** Admin only  
**Purpose:** Create a new teacher account with auto-generated username and password

## Request Format

### Student Registration Request
```json
{
    "email": "student@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "parents_phone_number": "+1234567899",
    "groups": [1, 2]  // Optional: Array of group IDs
}
```

### Teacher Registration Request
```json
{
    "email": "teacher@example.com", 
    "first_name": "Jane",
    "last_name": "Smith",
    "phone_number": "+1234567890"
}
```

## Auto-Generated Credentials

### Username Generation
- Based on the `first_name` field
- Converted to lowercase, spaces removed
- If username exists, numbers are appended (e.g., `john`, `john1`, `john2`)
- Examples: `john`, `alice`, `muhammad1`

### Password Generation  
- Simple pattern: `firstname + current_year + !`
- Examples: `john2025!`, `alice2025!`, `maria2025!`
- Meets Django's password validation requirements
- Students/teachers can change passwords later

## Response Format

### Successful Student Registration (201 Created)
```json
{
    "message": "Student registered successfully",
    "credentials": {
        "username": "john",
        "password": "john2025!",
        "note": "Please provide these credentials to the student. They can change them later."
    },
    "user": {
        "id": 1,
        "username": "john",
        "email": "student@example.com"
    },
    "student": {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890",
        "parents_phone_number": "+1234567899",
        "groups": [1, 2]
    }
}
```

### Successful Teacher Registration (201 Created)
```json
{
    "message": "Teacher registered successfully",
    "credentials": {
        "username": "jane",
        "password": "jane2025!",
        "note": "Please provide these credentials to the teacher. They can change them later."
    },
    "user": {
        "id": 2,
        "username": "jane",
        "email": "teacher@example.com"
    },
    "teacher": {
        "id": 1,
        "first_name": "Jane",
        "last_name": "Smith",
        "phone_number": "+1234567890"
    }
}
```

### Error Response (400 Bad Request)
```json
{
    "email": ["Enter a valid email address."],
    "first_name": ["This field is required."]
}
```
```

## Features

### Student Registration Features:
- **Auto-generated username** based on first name (e.g., `john`, `alice1`)
- **Auto-generated password** with simple pattern (e.g., `john2025!`)
- Creates User account with authentication token
- Creates Student profile with all required fields
- Optionally assigns student to groups during registration
- Returns generated credentials in response for admin to share

### Teacher Registration Features:
- **Auto-generated username** based on first name (e.g., `jane`, `bob2`)
- **Auto-generated password** with simple pattern (e.g., `jane2025!`)
- Creates User account with authentication token  
- Creates Teacher profile with all required fields
- Returns generated credentials in response for admin to share

### Security Features:
- Admin-only access via `IsAdminUser` permission
- Automatic token generation for new users
- Simple but secure passwords that meet Django validation
- Unique username generation with automatic numbering
- Users can change their credentials after first login

### Credential Management:
- **Simplified registration**: No need for admins to create usernames/passwords
- **Clear credential sharing**: Generated credentials included in API response
- **User flexibility**: Students/teachers can change credentials later
- **Unique usernames**: Automatic handling of duplicate names

## Usage Example

### Using curl to register a student:
```bash
curl -X POST http://localhost:8000/api/admin-panel/register/student/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_ADMIN_TOKEN" \
  -d '{
    "email": "newstudent@example.com",
    "first_name": "Alice",
    "last_name": "Johnson",
    "phone_number": "+1234567890",
    "parents_phone_number": "+1234567899"
  }'
```

### Using curl to register a teacher:
```bash
curl -X POST http://localhost:8000/api/admin-panel/register/teacher/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_ADMIN_TOKEN" \
  -d '{
    "email": "newteacher@example.com",
    "first_name": "Bob",
    "last_name": "Wilson",
    "phone_number": "+1234567890"
  }'
```

## Admin Workflow

1. **Registration**: Admin fills out basic information (name, email, phone)
2. **Auto-generation**: System creates username and password automatically
3. **Response**: Admin receives generated credentials in API response
4. **Distribution**: Admin provides credentials to student/teacher
5. **First Login**: Student/teacher logs in with provided credentials
6. **Password Change**: User can change password through profile settings

## Integration with Existing Admin Panel

These endpoints are part of the admin panel module and follow the same permission patterns as other admin endpoints. They complement the existing `StudentManagementViewSet` and `TeacherManagementViewSet` which handle CRUD operations for existing users, while these new endpoints specifically handle the initial registration process with automatic credential generation.