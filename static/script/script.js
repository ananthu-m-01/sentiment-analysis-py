// Function to fetch and render the survey data
async function fetchAndRenderSurvey() {
  try {
    // Fetch the survey data from the Flask backend
    const response = await fetch('/get-data');
    const data = await response.json();

    const surveyContainer = document.getElementById('survey-container');
    
    // Clear previous content if the survey is re-rendered
    surveyContainer.innerHTML = '';

    // Set the survey title
    const titleElement = document.createElement('h1');
    titleElement.className = 'survey-title';
    titleElement.textContent = data.survey_title; // Assuming 'survey_title' is part of the JSON
    surveyContainer.appendChild(titleElement);

    // Render each question and its options
    data.questions.forEach((question, index) => {
      const questionDiv = document.createElement('div');
      questionDiv.className = 'question';

      // Add question title
      const questionTitle = document.createElement('div');
      questionTitle.className = 'question-title';
      questionTitle.textContent = `${index + 1}. ${question.question}`;
      questionDiv.appendChild(questionTitle);

      // Add options
      const optionsList = document.createElement('ul');
      optionsList.className = 'options';
      Object.entries(question.options).forEach(([key, option]) => {
        const optionItem = document.createElement('li');

        // Create the radio input for options
        const radioInput = document.createElement('input');
        radioInput.type = 'radio';
        radioInput.name = `question-${index}`;
        radioInput.value = option;

        // Create a label for the radio button
        const label = document.createElement('label');
        label.textContent = option;
        label.style.marginLeft = '8px';

        // Append radio button and label to the list item
        optionItem.appendChild(radioInput);
        optionItem.appendChild(label);
        optionsList.appendChild(optionItem);
      });

      // Append the options list to the question div
      questionDiv.appendChild(optionsList);
      surveyContainer.appendChild(questionDiv);
    });
  } catch (error) {
    console.error('Error fetching or rendering survey:', error);
  }
}

// Function to handle survey submission
async function submitSurvey(event) {
  event.preventDefault(); // Prevent default form submission

  // Disable the submit button to prevent multiple submissions
  const submitButton = document.querySelector('.submit-btn');
  if (submitButton) {
    submitButton.disabled = true;
  }

  const surveyResponses = [];
  const questions = document.querySelectorAll('.question');

  // Collect the responses for each question
  questions.forEach((question, index) => {
    const selectedOption = document.querySelector(`input[name="question-${index}"]:checked`);
    if (selectedOption) {
      surveyResponses.push({
        questionId: index + 1, // Use index or the actual question id if present in the JSON
        userResponse: selectedOption.value,
      });
    }
  });

  // If no responses, alert the user
  if (surveyResponses.length === 0) {
    alert("Please answer all the questions.");
    if (submitButton) {
      submitButton.disabled = false; // Enable the submit button again if no response is selected
    }
    return;
  }

  try {
    // Send the survey responses to the server
    const response = await fetch('/submit-survey', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ responses: surveyResponses }),
    });

    const result = await response.json();
    if (response.ok && result.redirect) {
      // Redirect to thank you page
      window.location.href = result.redirect;
    } else {
      alert(`Error: ${result.message}`);
    }
  } catch (error) {
    console.error('Error submitting survey:', error);
  } finally {
    // Re-enable the submit button after submission (even if an error occurs)
    if (submitButton) {
      submitButton.disabled = false;
    }
  }
}

// Load the survey on page load
document.addEventListener('DOMContentLoaded', () => {
  fetchAndRenderSurvey();

  // Set up the submit button click event
  const submitButton = document.querySelector('.submit-btn');
  if (submitButton) {
    submitButton.addEventListener('click', submitSurvey);
  }
});
