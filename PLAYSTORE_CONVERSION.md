# Play Store Conversion Plan

## Honest Status

This current project is not directly publishable to the Play Store because it is a Python + Streamlit app. Play Store requires an Android app package (`.aab` or `.apk`) built with a mobile framework.

## What Is Already Ready

- Full interview logic
- Question bank and practice library
- Evaluation engine
- SQLite-backed storage logic
- Authentication and persistent sessions
- Mobile-ready backend API scaffold in `mobile_api.py`

## Best Conversion Path

### Option Recommended
- Frontend: Flutter
- Backend API: FastAPI using `mobile_api.py`
- Database: SQLite for demo, PostgreSQL/MySQL for production

## What You Need To Install

1. Flutter SDK
2. Android Studio
3. Android SDK
4. Java JDK

## Recommended Project Split

- `mobile_api.py`
  Backend for login, topics, practice, interview start, evaluation, and history
- Flutter app
  Screens:
  - Splash / login
  - Practice library
  - Interview session
  - History
  - Profile

## Mobile Screens To Build

1. Login screen
2. Register screen
3. Dashboard screen
4. Practice questions screen
5. Interview screen
6. Result screen
7. History screen

## API Endpoints Already Prepared

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /topics`
- `GET /practice/{topic}`
- `POST /interview/start`
- `POST /interview/evaluate`
- `GET /history/{user_id}`

## Launch Sequence

1. Run backend locally:

```powershell
uvicorn mobile_api:app --reload
```

2. Build Flutter frontend
3. Connect frontend to API
4. Test on Android emulator / physical device
5. Build Android App Bundle:

```powershell
flutter build appbundle
```

6. Upload `.aab` to Google Play Console

## Final Conclusion

Yes, this project can be converted for Play Store launch, but it requires building a mobile frontend. The backend preparation is now started inside this repo so the project is closer to mobile conversion than before.
