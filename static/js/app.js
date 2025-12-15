/*
app.js
Purpose:
- Handle UI interactions, API calls, and navigation for the landing page.
Main Functions:
- triggerPrediction, handleRateLimitError, populatePills.
Dependent Files:
- Requires inline localization data defined in index.html.
*/

// ========================================================================== 
// Constants
// ==========================================================================
const waitingMessageLoopInterval = 3000; // milliseconds
const OPTION_CLASS = 'option-card';
let challengeCtaButton;

function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

// ==========================================================================
// Utility Functions
// ==========================================================================
function getRandomWaitingMessage() {
    
    if (!getRandomWaitingMessage.counter) {
        getRandomWaitingMessage.counter = 0;
    }

    let message = waitingMessages[getRandomWaitingMessage.counter % waitingMessages.length];

    if (getRandomWaitingMessage.counter === 0) {
        const selectedIndustry = document.querySelector('#listOfIndustries .pill.selected')?.textContent;
        if (selectedIndustry) {
            message = `${message} ${selectedIndustry}`;
        }
    }

    getRandomWaitingMessage.counter++;
    return message;
}

// ==========================================================================
// API Interaction
// ==========================================================================
let isPredictionInProgress = false;

function triggerPrediction() {
    // Prevent issuing additional requests if a prediction is already in progress
    if (isPredictionInProgress) {
        return;
    }

    const noPredictionMessage = document.getElementById('noPredictionMessage');
    if (noPredictionMessage) {
        noPredictionMessage.classList.add('hidden');
    }
    isPredictionInProgress = true;

    const triggerButton = challengeCtaButton || document.querySelector('.trigger-button');
    if (triggerButton) {
        triggerButton.disabled = true;
    }

    const waitingNotificationContainer = document.getElementById('waitingNotificationContainer');
    const predictionContent = document.getElementById('prediction');
    const downloadButton = document.querySelector('.download-button');
    const resultsCtaText = document.querySelector('.results-cta-text');


    // Show waiting message and hide other elements
    waitingNotificationContainer.classList.remove('hidden');
    predictionContent.classList.add('hidden');
    downloadButton.classList.add('hidden');
    resultsCtaText.classList.add('hidden');

    // Start rotating waiting messages
    const waitingMessage = document.getElementById('waitingMessage');
    let message = getRandomWaitingMessage();
    waitingMessage.textContent = message;
    let dotCount = 0;

    const waitingInterval = setInterval(() => {
        if (dotCount < 5) {
            waitingMessage.textContent += '.';
            dotCount++;
        } else {
            message = getRandomWaitingMessage();
            waitingMessage.textContent = message;
            dotCount = 0;
        }
    }, waitingMessageLoopInterval / 6);

    // Record timestamp for rate limiting
    const timestamp = new Date().getTime();
    localStorage.setItem('timestamp', timestamp);
    
    const persona = {
        industry: getSelectedValue('#listOfIndustries'),
        businesProblem: getSelectedValue('#listOfBusinesProblems')
    };
    
    // Validate selections
    if (!persona.industry || !persona.businesProblem) {
        predictionContent.textContent = 'Please select all fields.';
        waitingNotificationContainer.classList.add('hidden');
        predictionContent.classList.remove('hidden');
        // resultsCtaText.classList.remove('hidden');
        clearInterval(waitingInterval);
        isPredictionInProgress = false;
        if (triggerButton) {
            triggerButton.disabled = false;
        }
        return;
    }

    // Make API call
    fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': getCsrfToken()
        },
        body: JSON.stringify(persona)
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw { httpCode: response.status, data };
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.status !== 'success') {
            throw { httpCode: 500, data };
        }
        // Hide waiting message
        waitingNotificationContainer.classList.add('hidden');
        getRandomWaitingMessage.counter = 0;
        clearInterval(waitingInterval);

        // Show prediction and download button
        predictionContent.innerHTML = data.data?.response || '';
        predictionContent.classList.remove('hidden');
        downloadButton.classList.remove('hidden');
        resultsCtaText.classList.remove('hidden');
    })
    .catch(error => {
        waitingNotificationContainer.classList.add('hidden');
        clearInterval(waitingInterval);
        console.error('Error:', error);

        if (error.httpCode === 429) {
            handleRateLimitError();
        } else {
            predictionContent.classList.remove('hidden');
            
            const message = error?.data?.message || 'prediction_error';
            predictionContent.innerHTML = 'Seems like the artificial intelligence run out of steam, please <a id="try-again" href="#" onclick="triggerPrediction()">Try again</a> in 42 seconds.';
            predictionContent.innerHTML += '<br/><br/><br/><small><i>Server responded with `' + message + '`, the technician has been informed.</i></small>';
        }
    })
    .finally(() => {
        isPredictionInProgress = false;
        if (triggerButton) {
            triggerButton.disabled = false;
        }
    });
}

// ==========================================================================
// Error Handling
// ==========================================================================
function handleRateLimitError() {
    const timestamp = localStorage.getItem('timestamp');
    const currentTime = new Date().getTime();
    const timeDifference = currentTime - timestamp;
    let seconds = 60 - Math.floor(timeDifference / 1000);

    const countdown = document.createElement('p');
    countdown.id = 'countdown';
    countdown.textContent = `You have to wait ${seconds} seconds before making another prediction`;
    document.body.appendChild(countdown);

    const interval = setInterval(() => {
        if (seconds <= 0) {
            clearInterval(interval);
            countdown.remove();
        } else {
            seconds--;
            countdown.textContent = `You have to wait ${seconds} seconds before making another prediction`;
        }
    }, 1000);
}

// ==========================================================================
// UI Component: Pills
// ==========================================================================
function populateOptions(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container) {
        return;
    }
    container.innerHTML = '';

    Object.keys(data).forEach((key) => {
        const option = document.createElement('div');
        option.className = OPTION_CLASS;
        option.dataset.value = key;
        option.innerHTML = data[key];
        option.addEventListener('click', () => {
            handleOptionClick(container, option);
        });
        container.appendChild(option);
    });
}

function handleOptionClick(container, option) {
    // Remove previous selection
    const selectedOption = container.querySelector(`.${OPTION_CLASS}.selected`);
    if (selectedOption) {
        selectedOption.classList.remove('selected');
    }

    // Add new selection
    option.classList.add('selected');
    updateChallengeCtaState();
}

function getSelectedValue(containerSelector) {
    return document.querySelector(`${containerSelector} .${OPTION_CLASS}.selected`)?.dataset.value;
}

function updateChallengeCtaState() {
    if (!challengeCtaButton) {
        return;
    }
    const canPredict = Boolean(getSelectedValue('#listOfBusinesProblems') && getSelectedValue('#listOfIndustries'));
    challengeCtaButton.disabled = !canPredict;
}

function initChallengeSection() {
    challengeCtaButton = document.getElementById('challengePrimaryCta');
    if (challengeCtaButton) {
        challengeCtaButton.disabled = true;
        challengeCtaButton.addEventListener('click', triggerPrediction);
    }
    populateOptions('listOfBusinesProblems', businesProblems);
    populateOptions('listOfIndustries', industries);
    populateOptions('listOfDepartments', departments);
    updateChallengeCtaState();
}

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
    initChallengeSection();
});