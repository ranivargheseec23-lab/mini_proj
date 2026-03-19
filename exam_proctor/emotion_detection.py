from deepface import DeepFace
import cv2
import time
import json

def start_emotion_detection(duration=3600):  # 60 minutes = 3600 seconds
    cap = cv2.VideoCapture(0)

    start_time = time.time()

    malpractice_count = 0
    stress_count = 0
    confidence_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        elapsed_time = time.time() - start_time
        if elapsed_time > duration:
            break

        try:
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            emotions = result[0]['emotion']

            dominant_emotion = max(emotions, key=emotions.get)

            # Stress emotions
            if dominant_emotion in ['angry', 'fear', 'sad']:
                stress_count += 1

            # Confidence emotions
            if dominant_emotion in ['happy', 'neutral']:
                confidence_count += 1

        except:
            malpractice_count += 1  # Face not detected = malpractice

        cv2.imshow("Exam Monitoring", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Save results
    report = {
        "malpractice_incidents": malpractice_count,
        "stress_events": stress_count,
        "confidence_events": confidence_count
    }

    with open("exam_report.json", "w") as f:
        json.dump(report, f)

    return report
