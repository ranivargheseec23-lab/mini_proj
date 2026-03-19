function nextQuestion() {
    let selected = document.querySelector('input[name="opt"]:checked');

    if (!selected) {
        alert("Please select an option");
        return;
    }

    if (selected.value === questions[index].ans) {
        score++;
    }

    selected.checked = false;   // 🔥 FIX

    index++;

    if (index < questions.length) {
        loadQuestion();
    } else {
        submitExam();
    }
}