document.addEventListener('DOMContentLoaded', () => {
    const partSelect = document.getElementById('part');
    const questionsContainer = document.getElementById('questions-list');
    const questions = {
        part1: [
            "Do you prefer to take photos of yourself or other things?",
            "Do you like animals?",
            "What is your favorite animal?",
            "Do you have any animals in your home?"
        ],
        part2: [
            "Describe a time when you helped someone.",
            "Talk about a place you would like to visit.",
            "Describe an event that made you happy."
        ],
        part3: [
            "What are the advantages and disadvantages of working from home?",
            "How do you think technology will change the way we work in the future?",
            "What skills are important for success in the workplace?"
        ]
    };

    function loadQuestions(part) {
        questionsContainer.innerHTML = '';
        questions[part].forEach(question => {
            const li = document.createElement('li');
            li.textContent = question;
            questionsContainer.appendChild(li);
        });
    }

    partSelect.addEventListener('change', () => {
        const selectedPart = partSelect.value;
        loadQuestions(selectedPart);
    });

    document.getElementById('upload-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);

        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        if (response.ok) {
            document.getElementById('transcription').textContent = result.transcription;

            const feedback = {
                fluency: parseFloat(result.fluency_feedback.split(' ')[1]),
                grammar: parseFloat(result.grammar_feedback.split(' ')[1]),
                lexical: parseFloat(result.lexical_feedback.split(' ')[1]),
                pronunciation: parseFloat(result.pronunciation_feedback.split(' ')[1])
            };
            feedback.overall = (feedback.fluency + feedback.grammar + feedback.lexical + feedback.pronunciation) / 4;

            const createChart = (ctx, data) => {
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Score', 'Remaining'],
                        datasets: [{
                            data: [data, 9 - data],
                            backgroundColor: ['rgba(54, 162, 235, 0.7)', 'rgba(200, 200, 200, 0.3)'],
                            borderColor: ['rgba(54, 162, 235, 1)', 'rgba(200, 200, 200, 1)'],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                enabled: false
                            }
                        },
                        cutout: '70%'
                    }
                });
            };

            const ctxFluency = document.getElementById('fluencyChart').getContext('2d');
            const ctxGrammar = document.getElementById('grammarChart').getContext('2d');
            const ctxLexical = document.getElementById('lexicalChart').getContext('2d');
            const ctxPronunciation = document.getElementById('pronunciationChart').getContext('2d');
            const ctxOverall = document.getElementById('overallChart').getContext('2d');

            createChart(ctxFluency, feedback.fluency);
            createChart(ctxGrammar, feedback.grammar);
            createChart(ctxLexical, feedback.lexical);
            createChart(ctxPronunciation, feedback.pronunciation);
            createChart(ctxOverall, feedback.overall);

            document.getElementById('fluency-feedback').textContent = result.fluency_feedback;
            document.getElementById('grammar-feedback').textContent = result.grammar_feedback;
            document.getElementById('lexical-feedback').textContent = result.lexical_feedback;
            document.getElementById('pronunciation-feedback').textContent = result.pronunciation_feedback;
            document.getElementById('overall-feedback').textContent = `Overall Score: ${feedback.overall.toFixed(2)}`;

            document.getElementById('results').style.display = 'block';
        } else {
            alert('Error: ' + result.error);
        }
    });

    // Trigger change event to load questions for the default selected part
    loadQuestions(partSelect.value);
});
