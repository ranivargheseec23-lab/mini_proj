// ===================== VARIABLES =====================
let currentIndex = 0;
let answers = [];

// ===================== LOAD QUESTION =====================
function loadQuestion() {
    const box = document.getElementById("questionBox");

    if (!box) {
        console.error("questionBox not found");
        return;
    }

    const q = questions[currentIndex];

    let html = `<h3>Q${currentIndex + 1}. ${q.q}</h3><br>`;

    q.options.forEach((opt, i) => {
        html += `
            <label style="display:block; margin:8px 0;">
                <input type="radio" name="option" value="${i}">
                ${opt}
            </label>
        `;
    });

    box.innerHTML = html;
}

// ===================== NEXT QUESTION =====================
function nextQuestion() {
    const selected = document.querySelector('input[name="option"]:checked');

    if (!selected) {
        alert("Please select an option before proceeding");
        return;
    }

    answers[currentIndex] = parseInt(selected.value);
    currentIndex++;

    if (currentIndex < questions.length) {
        loadQuestion();
    } else {
        document.getElementById("questionBox").innerHTML =
            "<h3>All questions completed. Please submit the exam.</h3>";
    }
}

// ===================== TIMER (1 HOUR) =====================
let time = 60 * 60;

setInterval(() => {
    if (time <= 0) {
        alert("Time up! Exam auto submitted.");
        return;
    }

    let min = Math.floor(time / 60);
    let sec = time % 60;

    document.getElementById("timer").innerText =
        `${min}:${sec < 10 ? "0" + sec : sec}`;

    time--;
}, 1000);

// ===================== WEBCAM =====================
const video = document.getElementById("webcam");
const canvas = document.getElementById("overlay");
const ctx = canvas.getContext("2d");

let stressScore = 0;
let cheatAttempts = 0;
let confidence = 100;

let lookAwayCount = 0;
let mouthOpenCount = 0;
let blinkCount = 0;
let faceLostCount = 0;

const faceMesh = new FaceMesh({
  locateFile: file =>
    `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
});

faceMesh.setOptions({
  maxNumFaces: 1,
  refineLandmarks: true,
  minDetectionConfidence: 0.5,
  minTrackingConfidence: 0.5
});

faceMesh.onResults(onResults);

navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    video.srcObject = stream;
  });

video.addEventListener("loadeddata", () => {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const camera = new Camera(video, {
    onFrame: async () => {
      await faceMesh.send({ image: video });
    },
    width: 640,
    height: 480
  });
  camera.start();
});

function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function onResults(results) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!results.multiFaceLandmarks) {
    faceLostCount++;
    stressScore += 2;
    cheatAttempts += 1;
    updateUI();
    return;
  }

  const landmarks = results.multiFaceLandmarks[0];

  // Draw face mesh
  drawConnectors(ctx, landmarks, FACEMESH_TESSELATION,
    { color: "#00FF00", lineWidth: 0.5 });

  // 👁 Eye movement detection (look away)
  const leftEye = landmarks[33];
  const rightEye = landmarks[263];
  const nose = landmarks[1];

  if (Math.abs(leftEye.x - nose.x) > 0.08 || Math.abs(rightEye.x - nose.x) > 0.08) {
    lookAwayCount++;
    stressScore += 1;
    cheatAttempts += 1;
  }

  // 👄 Mouth open detection
  const upperLip = landmarks[13];
  const lowerLip = landmarks[14];
  if (distance(upperLip, lowerLip) > 0.03) {
    mouthOpenCount++;
    stressScore += 1;
  }

  // 😑 Blink detection
  const eyeTop = landmarks[159];
  const eyeBottom = landmarks[145];
  if (distance(eyeTop, eyeBottom) < 0.01) {
    blinkCount++;
    stressScore += 0.5;
  }

  updateUI();
}

function updateUI() {
  stressScore = Math.min(100, stressScore);
  confidence = Math.max(0, 100 - stressScore);

}