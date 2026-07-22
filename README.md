# E-Noticeboard

## 📌 Project Overview

E-Noticeboard is a web-based notice management system developed to provide a simple and convenient platform for publishing, managing, and viewing college notices digitally.

The system allows administrators to manage notices and users to access important announcements through an online noticeboard. It helps reduce dependency on traditional physical noticeboards and makes important information easier to access.

## 🎯 Objectives

- To develop a digital platform for managing college notices.
- To allow administrators to add, edit, and manage notices.
- To provide users with easy access to important announcements.
- To reduce the use of physical noticeboards and paper-based notices.
- To make notice management faster, organized, and accessible.

## 🛠️ Technologies Used

- Python
- Flask
- HTML
- CSS
- SQLite
- Jinja2
- Pandas
- Excel

## ✨ Features

- User Registration and Signup
- User Login
- Admin Login
- Admin Dashboard
- Add and Manage Notices
- Edit Notices
- View Notices
- Forgot Password
- Reset Password
- Database Management
- File and Image Upload Support
- Responsive Web Interface

## ⚙️ Project Workflow

1. User opens the E-Noticeboard web application.
2. Users can register or log in to the system.
3. Administrators can access the admin login.
4. Admin can manage notices through the admin dashboard.
5. Notices can be added and edited when required.
6. Users can view available notices through the online noticeboard.
7. User and notice information is stored in the database.

## 📂 Project Structure

```text
e_noticeboard/
│
├── app.py
├── config.py
├── requirements.txt
├── database.db
├── noticeboard.db
├── list.xlsx
│
├── templates/
│   ├── index.html
│   ├── admin_dashboard.html
│   ├── signup.html
│   ├── forgot_password.html
│   ├── login.html
│   ├── edit_notice.html
│   ├── admin_login.html
│   ├── reset_password.html
│   └── notices.html
│
└── static/
    ├── css/
    │   └── style.css
    ├── images/
    │   └── college_banner.jpg
    └── uploads/
```

## 🚀 How to Run the Project

### Step 1: Clone the Repository

```bash
git clone <your-github-repository-link>
```

### Step 2: Open the Project Folder

```bash
cd e_noticeboard
```

### Step 3: Install Required Libraries

```bash
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
python app.py
```

### Step 5: Open in Browser

After running the application, open the local URL displayed in the terminal in your web browser.

## 🗄️ Database

The project uses a database to store and manage application-related information such as users and notices.

Database-related files included in the project are:

- `database.db`
- `noticeboard.db`

## 📁 Files Description

| File/Folder | Description |
|------|-------------|
| `app.py` | Main Flask application |
| `config.py` | Application configuration |
| `requirements.txt` | Required Python libraries |
| `database.db` | Database file |
| `noticeboard.db` | Noticeboard database |
| `list.xlsx` | Excel file used in the project |
| `templates/` | Contains HTML templates |
| `static/css/` | Contains CSS styling files |
| `static/images/` | Contains application images |
| `static/uploads/` | Contains uploaded files and images |

## 🔮 Future Scope

- Add email notifications for new notices.
- Add role-based access control.
- Add search and filter functionality.
- Add notice categories and priority levels.
- Add online hosting and deployment.
- Improve security and authentication.
- Add mobile-friendly features.
- Add automatic notice expiry and archiving.

## 👩‍💻 Author

**Pradnya Patil**

## 📜 License

This project is created for educational and learning purposes.

