# Viva Questions and Answers

## 1. What is the purpose of this project?
This project is designed to help students practice technical interviews in a structured and realistic environment. It combines a practice library, AI-guided mock interviews, automated evaluation, and report generation.

## 2. Why did you choose Streamlit?
I chose Streamlit because it allowed me to quickly build an interactive Python-based frontend, integrate machine learning or AI workflows, and demonstrate the project effectively without needing a separate frontend framework.

## 3. How is data stored in the project?
Data is stored locally in SQLite. The database stores users, interview history, remembered sessions, and practice progress information such as bookmarks and completed questions.

## 4. How does authentication work?
The project uses password hashing with PBKDF2 for secure password storage. After login, a persistent random session token is saved so the user does not need to log in again on the same device.

## 5. How does the interview evaluation work?
The project supports two evaluation modes. If an OpenAI API key is available, AI-based evaluation is used. Otherwise, a local rule-based scoring system evaluates answers using keyword coverage, communication quality, and completeness.

## 6. What is the role of the practice library?
The practice library provides topic-wise interview questions and professional model answers. It helps students prepare before taking the simulated mock interview.

## 7. What makes this project different from a simple Q&A app?
This project includes secure login, persistent user sessions, stored interview history, analytics, voice guidance, practice progress tracking, bookmarks, and report export. It behaves like a small interview-preparation platform rather than a simple question-answer tool.

## 8. What are the main limitations of the current system?
Browser microphone automation is limited by browser security policies. Also, the current project is local-first and not yet deployed to a cloud backend.

## 9. How can this project be improved in the future?
It can be improved by adding cloud deployment, mobile support, better speech-to-text, behavioral interview modules, recruiter dashboards, and multi-user admin management.

## 10. Why is this project suitable as a final year project?
It combines multiple real-world components including authentication, databases, UI/UX, AI-assisted evaluation, reporting, analytics, voice interaction, and system integration. This gives it both technical depth and practical relevance.
