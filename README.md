# SARA - AI Interview Simulator

SARA is a final year project built using Python, Streamlit, and SQLite to help students prepare for technical interviews in a realistic and structured way. The platform includes secure login, a large interview practice library, performance analytics, exportable reports, and a voice-guided AI interviewer named Nova.

## Live Demo

[Open the live app](https://nova-ai-interview-simulator-xrcdue6mbfnh2zvsn5x4qg.streamlit.app)

## Project Overview

SARA is designed as an interview preparation platform for students who want to practice technical interviews before placements. It combines guided mock interviews, AI-style evaluation, saved progress, and interview history into one system.

The app supports topic-based mock interviews across core computer science areas and gives structured feedback to help users improve clarity, confidence, and technical explanation.

## Key Features

- Secure login with remembered session on the same device
- Student and admin access modes
- 500+ interview practice questions with model answers
- Topic-based mock interviews in Python, DSA, DBMS, and OOP
- Voice-guided AI interviewer experience through Nova
- Smart answer evaluation with feedback and scoring
- Performance analytics dashboard
- Interview history tracking
- Downloadable text and PDF interview reports
- Practice bookmarks, completion tracking, and daily random question sets

## Tech Stack

- Python
- Streamlit
- SQLite
- SpeechRecognition
- ReportLab

## Main Modules

- `app.py` - Main Streamlit application
- `auth.py` - Authentication and remembered login support
- `database.py` - SQLite database operations
- `qa_dataset.py` - Interview and practice question bank
- `question_generator.py` - Topic-based question utilities
- `answer_evaluator.py` - AI/local evaluation logic
- `dashboard.py` - Performance analytics display
- `report_export.py` - Text and PDF report generation
- `face_detection.py` - Browser camera and face check support
- `voice_input.py` - Voice input utilities
- `launcher.py` - Desktop launcher helper

## Run Locally

```powershell
cd C:\Users\ASUS\Desktop\AI_Interview_Simulator
pip install -r requirements.txt
streamlit run app.py
```

## Deployment

This project is deployed on Streamlit Community Cloud and can also be run locally for demo or development.

## Build as a Windows App

You can package the project as a Windows executable using PyInstaller.

```powershell
cd C:\Users\ASUS\Desktop\AI_Interview_Simulator
.\build_exe.ps1
```

Expected output:

- `dist\NovaInterviewSimulator\NovaInterviewSimulator.exe`

## Login Behavior

- Users log in once and the session is remembered on the same device
- Logout clears the remembered session
- Interview and progress data are stored locally in SQLite

## Admin Demo Account

- Email: `admin@interviewsimulator.local`
- Password: `Admin@123`

## Project Deliverables

- `RESUME_POINTS.md`
- `PROJECT_SYNOPSIS.md`
- `PPT_CONTENT.md`
- `VIVA_QA.md`
- `PLAYSTORE_CONVERSION.md`

## Notes

- Interview data is stored in `interview_simulator.db`
- Remembered login is stored in `remembered_session.json`
- Browser microphone auto-start is limited by browser security policies
- Direct Play Store upload is not supported for the current Streamlit version without a separate mobile frontend

## Future Scope

- More interview domains and advanced question sets
- Better adaptive evaluation logic
- Cloud database integration
- Recruiter panel with centralized candidate review
- Mobile app version using Flutter + backend API
