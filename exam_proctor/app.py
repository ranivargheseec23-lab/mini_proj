from flask import Flask, render_template, request, redirect, session, jsonify
from deepface import DeepFace
import base64
import numpy as np
import cv2
import time

app = Flask(__name__)
app.secret_key = "exam_secret"

USER_EMAIL = "student@test.com"
USER_PASSWORD = "1234"

# Load face cascade
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# ================= GLOBAL TRACKING =================
stress_score = 0
confidence_score = 0
malpractice_count = 0
no_face_count = 0
total_frames = 0
looking_away_frames = 0

# NEW: malpractice timeline tracking
malpractice_events = []
exam_start_time = None


# ================= HELPER FUNCTION =================
def log_malpractice(event_type):
    global malpractice_events, exam_start_time

    if exam_start_time:
        elapsed = int(time.time() - exam_start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60

        malpractice_events.append({
            "time": f"{minutes:02d}:{seconds:02d}",
            "event": event_type
        })


# ================= LOGIN PAGE =================
@app.route("/")
def login():
    return render_template("login.html")


# ================= LOGIN ACTION =================
@app.route("/login", methods=["POST"])
def do_login():
    global exam_start_time

    if request.form["email"] == USER_EMAIL and request.form["password"] == USER_PASSWORD:
        session["user"] = USER_EMAIL

        exam_start_time = time.time()   # start exam timer

        reset_scores()

        return redirect("/exam")

    return render_template("login.html", error="Invalid credentials")


# ================= EXAM PAGE =================
@app.route("/exam")
def exam():
    if "user" not in session:
        return redirect("/")
    return render_template("exam.html")


# ================= TAB SWITCH DETECTION =================
@app.route("/tab_switch", methods=["POST"])
def tab_switch():
    global malpractice_count

    malpractice_count += 1

    log_malpractice("Tab Switching Detected")

    return "", 204


# ================= AI FRAME ANALYSIS =================
@app.route("/analyze", methods=["POST"])
def analyze():
    global stress_score, confidence_score
    global malpractice_count, total_frames
    global no_face_count, looking_away_frames

    data = request.json["image"]

    image_data = base64.b64decode(data.split(",")[1])
    np_arr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    total_frames += 1

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )

    # ================= NO FACE =================
    if len(faces) == 0:

        emotion = "no_face"

        malpractice_count += 1
        no_face_count += 1
        looking_away_frames += 1

        log_malpractice("Face Not Detected")

    # ================= MULTIPLE FACES =================
    elif len(faces) > 1:

        emotion = "multiple_faces"

        malpractice_count += 1
        looking_away_frames = 0

        log_malpractice("Multiple Faces Detected")

    else:

        (x, y, w, h) = faces[0]

        face_center_x = x + w // 2
        face_center_y = y + h // 2

        frame_center_x = frame.shape[1] // 2
        frame_center_y = frame.shape[0] // 2

        # ================= LOOKING AWAY =================
        if abs(face_center_x - frame_center_x) > frame.shape[1] * 0.25:
            looking_away_frames += 1

        elif face_center_y > frame.shape[0] * 0.65:
            looking_away_frames += 1

        else:
            looking_away_frames = 0

        if looking_away_frames > 5:

            malpractice_count += 1
            emotion = "looking_away"

            log_malpractice("Looking Away From Screen")

        else:

            # ================= DEEPFACE EMOTION =================
            try:

                result = DeepFace.analyze(
                    frame,
                    actions=["emotion"],
                    enforce_detection=False
                )

                if isinstance(result, list):
                    result = result[0]

                emotion = result["dominant_emotion"]

                if emotion in ["angry", "fear", "sad", "disgust", "confusion"]:
                    stress_score += 1

                elif emotion in ["happy", "neutral", "confident"]:
                    confidence_score += 1

            except:

                emotion = "error"

                malpractice_count += 1

                log_malpractice("Face Analysis Error")

    # ================= CALCULATE PERCENTAGES =================
    if total_frames == 0:

        stress_percent = 0
        confidence_percent = 0

    else:

        stress_percent = round((stress_score / total_frames) * 100, 2)

        confidence_percent = round((confidence_score / total_frames) * 100, 2)

    return jsonify({
        "emotion": emotion,
        "stress": stress_percent,
        "confidence": confidence_percent,
        "malpractice": malpractice_count
    })


# ================= SUBMIT EXAM =================
@app.route("/submit", methods=["POST"])
def submit():
    global stress_score, confidence_score
    global malpractice_count, no_face_count
    global total_frames

    score = int(request.form.get("score", 0))

    if total_frames == 0:
        stress = 0
        confidence = 0
    else:
        stress = round((stress_score / total_frames) * 100, 2)
        confidence = round((confidence_score / total_frames) * 100, 2)

    report = render_template(
        "report.html",
        score=score,
        stress=stress,
        confidence=confidence,
        malpractice=malpractice_count,
        no_face=no_face_count,
        events=malpractice_events
    )

    reset_scores()

    return report


# ================= RESET SYSTEM =================
def reset_scores():
    global stress_score, confidence_score
    global malpractice_count, no_face_count
    global total_frames, malpractice_events
    global looking_away_frames

    stress_score = 0
    confidence_score = 0
    malpractice_count = 0
    no_face_count = 0
    total_frames = 0
    looking_away_frames = 0
    malpractice_events = []


# ================= RUN SERVER =================
if __name__ == "__main__":
    app.run(debug=True)