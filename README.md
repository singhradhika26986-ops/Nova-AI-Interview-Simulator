# Nova AI Interview Simulator

Nova AI Interview Simulator is a final year project built with Python and Streamlit. It provides secure login, remembered sessions, a 500-question interview practice library, voice-guided mock interviews, interview history tracking, and downloadable assessment reports.

## Features

- Secure login and remembered device session
- Student and admin roles
- 500 professional practice questions with answers
- Topic-based interview simulation
- Voice-guided recruiter-style interview flow
- AI and local rule-based answer evaluation
- Practice bookmarks and completion tracking
- Daily random practice set
- Interview history and downloadable reports
- Admin analytics dashboard

## Main Modules

- `app.py` - Main application
- `launcher.py` - Desktop app launcher
- `auth.py` - Authentication and persistent sessions
- `database.py` - SQLite storage
- `qa_dataset.py` - Practice and interview question banks
- `question_generator.py` - Question generation helpers
- `answer_evaluator.py` - Evaluation logic
- `report_export.py` - Text and PDF report export
- `dashboard.py` - Analytics charts

## Run Locally

```powershell
cd C:\Users\ASUS\Desktop\AI_Interview_Simulator
pip install -r requirements.txt
streamlit run app.py
```

## Build Windows App

This project can be packaged as a Windows desktop app using PyInstaller.

```powershell
cd C:\Users\ASUS\Desktop\AI_Interview_Simulator
.\build_exe.ps1
```

After build:

- Executable path:
  `dist\NovaInterviewSimulator\NovaInterviewSimulator.exe`

## Mobile / Play Store Path

This project is not directly uploadable to the Play Store in its current Streamlit form.
For Play Store conversion:

- Use `mobile_api.py` as the backend API layer
- Build an Android frontend using Flutter
- See [PLAYSTORE_CONVERSION.md](C:\Users\ASUS\Desktop\AI_Interview_Simulator\PLAYSTORE_CONVERSION.md)

## Login Behavior

- Users log in once
- Session is remembered on the same device
- Logout clears the remembered session

## Deliverables Added

- [RESUME_POINTS.md](C:\Users\ASUS\Desktop\AI_Interview_Simulator\RESUME_POINTS.md)
- [PROJECT_SYNOPSIS.md](C:\Users\ASUS\Desktop\AI_Interview_Simulator\PROJECT_SYNOPSIS.md)
- [PPT_CONTENT.md](C:\Users\ASUS\Desktop\AI_Interview_Simulator\PPT_CONTENT.md)
- [VIVA_QA.md](C:\Users\ASUS\Desktop\AI_Interview_Simulator\VIVA_QA.md)

## Admin Demo Account

- Email: `admin@interviewsimulator.local`
- Password: `Admin@123`

## Notes

- Interview data is stored locally in `interview_simulator.db`
- Remembered login is stored locally in `remembered_session.json`
- Browser microphone auto-start is limited by browser security rules
