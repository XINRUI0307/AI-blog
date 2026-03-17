# Photo Blog System Specification
AI-Assisted Version (Claude Code)

This project is a Photo Blog platform with role-based access control.  
It extends a previously developed manual blog system and adds photo management and additional features.

The goal is to compare **manual development vs AI-assisted development**.

---

# 1. System Roles

The system contains four roles.

### Admin
Platform administrator with full control.

Permissions:
- Approve or reject contributor membership applications
- Edit or delete any blog post
- Remove inappropriate comments
- Send messages to contributors
- Manage sidebar content
- Manage user accounts

---

### Contributor
Registered users who can create blog posts.

Permissions:
- Create blog posts
- Upload photos to blog posts
- Edit their own posts
- Delete their own posts
- Manage their personal profile
- Report inappropriate comments to admin

Restrictions:
- Maximum **10 blog posts per contributor**
- Posts older than **18 months are automatically deleted**

---

### Reader
Users who can read and interact with blog posts but cannot publish content.

Permissions:
- View blog posts
- Comment on blog posts
- Receive notifications of new posts
- View contributor profiles
- Rate blog posts (star rating)

---

### Guest (Public User)
Users who are not logged in.

Permissions:
- View blog summaries
- Read limited blog content
- Search blog posts
- Apply for membership (reader or contributor)

---

# 2. Core System Features

## 2.1 Authentication System

The system must include:

- User registration
- Login and logout
- Session management

Security requirements:

- Passwords must be stored using **hashed passwords**
- Use **salted hashing**
- Do not store plaintext passwords.

---

## 2.2 Role-Based Access Control (RBAC)

Access control must be enforced **on the server side**.

Roles:

- Admin
- Contributor
- Reader

Example restrictions:

- Only contributors can create blog posts
- Only admins can approve new members
- Only admins can delete inappropriate comments

---

# 3. Blog Post System

Blog posts are the core entity of the system.

Each blog post contains:

- Title
- Description
- Photo(s)
- Location (optional)
- Author
- Date created

Functions:

- Create post
- Edit post
- Delete post
- View post
- Search posts

System rules:

- Each contributor can publish **maximum 10 posts**
- Posts older than **18 months are automatically deleted**

---

# 4. Photo Upload System

Blog posts must support photo uploads.

Requirements:

- Maximum file size: **10 MB**
- Maximum resolution: **1200 x 800**
- Multiple photos per post allowed
- Photos stored in server storage

Optional:

- Image search
- Image download options

---

# 5. Comment System

Users can comment on blog posts.

Functions:

- Add comment
- Delete comment
- Report comment

Permissions:

- Readers and contributors can comment
- Admin can delete any comment
- Users can report inappropriate comments

---

# 6. Membership System

Users can apply to become members.

Types:

- Reader
- Contributor

Process:

1. User submits application
2. Admin reviews application
3. Admin approves or rejects request

---

# 7. User Profile System

Contributors can manage personal profiles.

Profile data:

- Username
- Email
- Profile description
- Uploaded avatar photo

Users can:

- Edit profile
- Update personal information

---

# 8. Search System

Users should be able to search blog posts.

Search options:

- By title
- By location
- By author

---

# 9. Admin Moderation Tools

Admin dashboard should allow:

- Approve or reject membership
- Remove comments
- Edit blog posts
- Manage users

---

# 10. Notifications

Optional feature.

Readers can:

- Receive notification of new blog posts

---

# 11. Database Requirements

The system must contain relational tables such as:

Users
Posts
Images
Comments
Membership Applications

Relationships must use:

- Primary Keys
- Foreign Keys

---

# 12. Technical Requirements

Suggested stack:

Backend:
Python (Flask or FastAPI)

Database:
SQLite or PostgreSQL

Frontend:
HTML templates + CSS

Image Storage:
Local server storage

---

# 13. Development Goal

This project is part of an academic comparison study.

The AI-generated system will be compared with a previously developed **manual blog system**.

Evaluation criteria include:

- Development time
- Code complexity
- AI errors
- Required human intervention"# blog-ai" 
# 14. System Architecture

Suggested project structure:

project_root/

app.py  
models.py  
auth.py  
routes/  
templates/  
static/  
uploads/  
database.db  
