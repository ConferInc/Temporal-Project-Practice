// Example templates
const EXAMPLES = {
    income: {
        income: {
            customer_id: "123e4567-e89b-12d3-a456-426614174000",
            income_type: "salary",
            monthly_amount: 50000
        }
    },
    employment: {
        employment: {
            customer_id: "123e4567-e89b-12d3-a456-426614174000",
            employer_name: "Google",
            employment_type: "full_time"
        }
    },
    asset: {
        asset: {
            customer_id: "123e4567-e89b-12d3-a456-426614174000",
            application_id: "app-123e4567-e89b-12d3-a456-426614174000",
            asset_type: "bank_account",
            asset_value: 100000
        }
    },
    liability: {
        liability: {
            customer_id: "123e4567-e89b-12d3-a456-426614174000",
            application_id: "app-123e4567-e89b-12d3-a456-426614174000",
            liability_type: "loan",
            monthly_payment: 15000
        }
    },
    multi: {
        employment: {
            customer_id: "123e4567-e89b-12d3-a456-426614174000",
            employer_name: "Google",
            employment_type: "full_time"
        },
        income: {
            customer_id: "123e4567-e89b-12d3-a456-426614174000",
            income_type: "salary",
            monthly_amount: 50000
        },
        asset: {
            customer_id: "123e4567-e89b-12d3-a456-426614174000",
            application_id: "app-123e4567-e89b-12d3-a456-426614174000",
            asset_type: "bank_account",
            asset_value: 100000
        }
    }
};

// DOM elements
const jsonInput = document.getElementById('jsonInput');
const submitBtn = document.getElementById('submitBtn');
const responseContainer = document.getElementById('responseContainer');
const exampleBtns = document.querySelectorAll('.example-btn');

// Event listeners
submitBtn.addEventListener('click', handleSubmit);

exampleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const exampleType = btn.getAttribute('data-example');
        jsonInput.value = JSON.stringify(EXAMPLES[exampleType], null, 2);
    });
});

// Handle form submission
async function handleSubmit() {
    const jsonText = jsonInput.value.trim();

    if (!jsonText) {
        displayResponse({ error: 'Please enter JSON data' }, false);
        return;
    }

    // Validate JSON
    let jsonData;
    try {
        jsonData = JSON.parse(jsonText);
    } catch (e) {
        displayResponse({ error: 'Invalid JSON format: ' + e.message }, false);
        return;
    }

    // Disable button and show loading
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    responseContainer.classList.add('loading');

    try {
        const response = await fetch('/api/ingest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(jsonData)
        });

        const result = await response.json();

        if (response.ok) {
            displayResponse(result, true);
        } else {
            displayResponse(result, false);
        }
    } catch (error) {
        displayResponse({ error: 'Network error: ' + error.message }, false);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Data';
        responseContainer.classList.remove('loading');
    }
}

// Display response
function displayResponse(data, isSuccess) {
    responseContainer.innerHTML = '';

    if (isSuccess && data.success) {
        // Success response
        const successDiv = document.createElement('div');
        successDiv.className = 'success';
        successDiv.textContent = '✓ Success!\n\n';
        responseContainer.appendChild(successDiv);

        // Show results for each entity
        if (data.results && data.results.length > 0) {
            data.results.forEach(result => {
                const resultDiv = document.createElement('div');
                resultDiv.style.marginBottom = '15px';

                let resultText = `Entity: ${result.entity}\n`;
                resultText += `Status: ${result.is_update ? 'Updated' : 'Created'}\n`;
                if (result.version_number !== null) {
                    resultText += `Version: ${result.version_number}\n`;
                }
                resultText += `Record ID: ${result.record_id}\n`;

                resultDiv.textContent = resultText;
                responseContainer.appendChild(resultDiv);
            });
        }

        // Show summary
        const summaryDiv = document.createElement('div');
        summaryDiv.style.marginTop = '20px';
        summaryDiv.style.paddingTop = '20px';
        summaryDiv.style.borderTop = '1px solid #ddd';
        summaryDiv.textContent = `Total Processed: ${data.total_processed}`;
        responseContainer.appendChild(summaryDiv);

    } else {
        // Error response
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.textContent = '✗ Error\n\n';
        responseContainer.appendChild(errorDiv);

        if (data.errors && data.errors.length > 0) {
            data.errors.forEach(error => {
                const errorDetail = document.createElement('div');
                errorDetail.style.marginBottom = '10px';
                errorDetail.textContent = `Entity: ${error.entity || 'Unknown'}\nError: ${error.error}`;
                responseContainer.appendChild(errorDetail);
            });
        } else if (data.error) {
            const errorDetail = document.createElement('div');
            errorDetail.textContent = data.error;
            responseContainer.appendChild(errorDetail);
        } else if (data.detail) {
            const errorDetail = document.createElement('div');
            errorDetail.textContent = data.detail;
            responseContainer.appendChild(errorDetail);
        }
    }
}
