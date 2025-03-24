let taskCounter = 1;

window.onload = function () {
    // Set today's date as the default value for the date input
    const today = new Date();
    const formattedDate = today.toISOString().split('T')[0]; // Format as YYYY-MM-DD
    document.getElementById('entry_date').value = formattedDate;

    // Initialize the first task
    initializeTask(document.querySelector('.task-container'));

    // Set up event listener for the "Add Another Task" button
    document.getElementById('add-task-btn').addEventListener('click', addTask);

    // Set up event listener for the total hours input
    document.getElementById('hours').addEventListener('input', updateAllSliders);

    // Set up event listener for the time balance checkbox
    document.getElementById('time_balance').addEventListener('change', function () {
        updateAllSliders();
    });

    // Initialize category dropdowns
    document.querySelectorAll('.category-select').forEach(function (select) {
        select.addEventListener('change', function () {
            updateProjectOptions(select);
        });
    });

    // Convert project selects to datalist/input components
    convertProjectSelectsToDatalist();

    // IMPORTANT FIX: Initialize all sliders to set initial hours values
    updateAllSliders();
};

// Function to convert all project selects to datalist/input components
function convertProjectSelectsToDatalist() {
    // Create a single datalist element to be used by all project inputs
    if (!document.getElementById('project-list')) {
        const datalist = document.createElement('datalist');
        datalist.id = 'project-list';

        // Add options from the global projects array
        if (window.allProjects && window.allProjects.length > 0) {
            window.allProjects.forEach(project => {
                if (project && project.trim() !== '') {
                    const option = document.createElement('option');
                    option.value = project;
                    datalist.appendChild(option);
                }
            });
        }

        document.body.appendChild(datalist);
    }

    // Convert all project select elements to text inputs with datalist
    document.querySelectorAll('.project-select').forEach(projectSelect => {
        // Create container div to maintain the layout
        const container = document.createElement('div');
        container.className = 'project-input-container';
        container.style.display = 'inline-block';
        container.style.width = '100%';

        // Create text input
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'project-input';
        input.name = projectSelect.name;
        input.id = projectSelect.id;
        input.setAttribute('list', 'project-list');
        input.placeholder = 'Select or type project';

        // Copy the current value
        if (projectSelect.value) {
            input.value = projectSelect.value;
        }

        // Replace select with input
        projectSelect.parentNode.insertBefore(container, projectSelect);
        container.appendChild(input);
        projectSelect.remove();
    });
}

function initializeTask(taskContainer) {
    const taskId = taskContainer.getAttribute('data-task-id');
    const slider = taskContainer.querySelector('.task-slider');
    const hoursInput = taskContainer.querySelector('.hours-input');
    const percentDisplay = taskContainer.querySelector('.percent-display');
    const categorySelect = taskContainer.querySelector('.category-select');
    const productFamilySelect = taskContainer.querySelector('.product-family-select');

    // Set up event listeners for the slider
    slider.addEventListener('input', function () {
        updateSliderValue(slider);
        if (document.getElementById('time_balance').checked) {
            balanceOtherSliders(slider);
        }
    });

    // Set up event listeners for the hours input
    hoursInput.addEventListener('input', function () {
        lockSlider(hoursInput);
    });

    // Initial setup of dropdowns - populate them on page load
    updateProjectOptions(categorySelect);

    // Add debug message to show values
    console.log("Initial values - Category:", categorySelect.value,
        "Product Family:", productFamilySelect.value);
}

function addTask() {
    taskCounter++;
    const tasksContainer = document.getElementById('tasks-container');
    const taskTemplate = document.querySelector('.task-container');
    const newTask = taskTemplate.cloneNode(true);

    // Update the new task's ID and name attributes
    newTask.setAttribute('data-task-id', taskCounter);

    const categorySelect = newTask.querySelector('.category-select');
    categorySelect.id = 'category-' + taskCounter;
    categorySelect.name = 'tasks[' + (taskCounter - 1) + '][category]';
    categorySelect.value = '';

    // Reset the product family dropdown
    const productFamilySelect = newTask.querySelector('.product-family-select');
    productFamilySelect.id = 'product-family-' + taskCounter;
    productFamilySelect.name = 'tasks[' + (taskCounter - 1) + '][product_family]';
    productFamilySelect.value = '';

    // Handle project input (if it's an input with datalist)
    const projectInput = newTask.querySelector('.project-input');
    if (projectInput) {
        projectInput.id = 'project-' + taskCounter;
        projectInput.name = 'tasks[' + (taskCounter - 1) + '][project]';
        projectInput.value = '';
    } else {
        // Handle if it's still a select (fallback)
        const projectSelect = newTask.querySelector('.project-select');
        if (projectSelect) {
            projectSelect.id = 'project-' + taskCounter;
            projectSelect.name = 'tasks[' + (taskCounter - 1) + '][project]';
            projectSelect.value = '';
        }
    }

    const hoursInput = newTask.querySelector('.hours-input');
    hoursInput.name = 'tasks[' + (taskCounter - 1) + '][hours]';
    hoursInput.value = '';

    const commentBox = newTask.querySelector('.comment-box');
    commentBox.name = 'tasks[' + (taskCounter - 1) + '][comment]';
    commentBox.value = '';

    // Reset the slider to 0
    const slider = newTask.querySelector('.task-slider');
    slider.value = 0;

    // Update percentage display
    newTask.querySelector('.percent-display').textContent = '0%';

    // Show the remove button for additional tasks
    const removeBtn = newTask.querySelector('.remove-task-btn');
    removeBtn.style.display = 'block';

    // Add the new task to the container
    tasksContainer.appendChild(newTask);

    // Set up event listeners for the new task
    initializeTask(newTask);

    // Update all sliders to balance the percentages
    updateAllSliders();

    // Convert project select to datalist/input if it's still a select
    const projectSelect = newTask.querySelector('.project-select');
    if (projectSelect) {
        convertProjectSelectsToDatalist();
    }
}

function removeTask(button) {
    const taskContainer = button.closest('.task-container');

    // Only allow removal if there's more than one task
    if (document.querySelectorAll('.task-container').length > 1) {
        taskContainer.remove();
        updateAllSliders();
    }
}

function updateProjectOptions(categorySelect) {
    const taskContainer = categorySelect.closest('.task-container');
    const productFamilySelect = taskContainer.querySelector('.product-family-select');

    // Find project input - could be either select or input with datalist
    const projectInput = taskContainer.querySelector('.project-input');
    const projectSelect = taskContainer.querySelector('.project-select');

    // Remember the currently selected project if there is one
    const currentProject = projectInput ? projectInput.value : (projectSelect ? projectSelect.value : '');

    // Make sure both dropdowns are visible regardless of selection
    productFamilySelect.style.display = 'block';

    // If we still have a select element (not converted yet), show it
    if (projectSelect) {
        projectSelect.style.display = 'block';

        // Clear the current options in project dropdown
        projectSelect.innerHTML = '<option value="">Select Project</option>';

        // Add all available projects from the global array
        if (window.allProjects && window.allProjects.length > 0) {
            console.log(`Adding ${window.allProjects.length} projects to dropdown`);

            window.allProjects.forEach(project => {
                if (project && project.trim() !== '') {
                    const option = document.createElement('option');
                    option.value = project;
                    option.textContent = project;
                    projectSelect.appendChild(option);
                }
            });

            // Try to restore previously selected project if it exists in the new options
            if (currentProject) {
                // Check if the option still exists
                const exists = Array.from(projectSelect.options).some(option => option.value === currentProject);
                if (exists) {
                    projectSelect.value = currentProject;
                }
            }
        } else {
            console.warn("No projects available to populate dropdown");
        }
    }
    // If we have an input with datalist, set its value
    else if (projectInput && currentProject) {
        projectInput.value = currentProject;
    }
}

function lockSlider(hoursInput) {
    const taskContainer = hoursInput.closest('.task-container');
    const slider = taskContainer.querySelector('.task-slider');
    const percentDisplay = taskContainer.querySelector('.percent-display');
    const totalHours = parseFloat(document.getElementById('hours').value);
    const inputHours = parseFloat(hoursInput.value);

    hoursInput.classList.remove('invalid', 'valid');

    if (isNaN(inputHours) || inputHours < 0) {
        hoursInput.classList.add('invalid');
        hoursInput.value = '';
    } else if (inputHours > totalHours) {
        hoursInput.classList.add('invalid');
        hoursInput.value = totalHours;
    } else {
        hoursInput.classList.add('valid');
        const percentage = (inputHours / totalHours) * 100;
        slider.value = percentage;
        percentDisplay.textContent = percentage.toFixed(0) + '%';

        if (document.getElementById('time_balance').checked) {
            balanceOtherSliders(slider);
        }
    }
}

function updateSliderValue(slider) {
    const taskContainer = slider.closest('.task-container');
    const hoursInput = taskContainer.querySelector('.hours-input');
    const percentDisplay = taskContainer.querySelector('.percent-display');
    const totalHours = parseFloat(document.getElementById('hours').value);

    const percentage = parseFloat(slider.value);
    const hours = (percentage / 100) * totalHours;

    hoursInput.value = hours.toFixed(1);
    percentDisplay.textContent = percentage.toFixed(0) + '%';
}

function balanceOtherSliders(changedSlider) {
    if (!document.getElementById('time_balance').checked) return;

    const sliders = Array.from(document.querySelectorAll('.task-slider'));
    if (sliders.length <= 1) return;

    const changedValue = parseFloat(changedSlider.value);
    const totalHours = parseFloat(document.getElementById('hours').value);

    // Calculate the sum of all slider values
    let sum = sliders.reduce((acc, slider) => acc + parseFloat(slider.value), 0);

    // Calculate the difference from 100%
    const diff = 100 - sum;

    if (Math.abs(diff) < 0.1) return; // Already balanced

    // Get all sliders except the one that was changed
    const otherSliders = sliders.filter(slider => slider !== changedSlider);

    // Get unlocked sliders (those that can be adjusted)
    const adjustableSliders = otherSliders.filter(slider => {
        const taskContainer = slider.closest('.task-container');
        const hoursInput = taskContainer.querySelector('.hours-input');
        return !hoursInput.classList.contains('valid');
    });

    if (adjustableSliders.length === 0) return;

    // Calculate the total value of adjustable sliders
    const adjustableSum = adjustableSliders.reduce((acc, slider) => acc + parseFloat(slider.value), 0);

    if (adjustableSum === 0 && diff < 0) {
        // If adjustable sliders are all at 0 and we need to decrease, nothing to do
        return;
    }

    // Distribute the difference proportionally
    adjustableSliders.forEach(slider => {
        const currentValue = parseFloat(slider.value);
        let newValue;

        if (adjustableSum === 0) {
            // If all adjustable sliders are at 0, distribute the difference equally
            newValue = diff / adjustableSliders.length;
        } else {
            // Otherwise distribute proportionally
            const proportion = currentValue / adjustableSum;
            newValue = currentValue + (diff * proportion);
        }

        // Ensure the new value is not negative
        newValue = Math.max(0, newValue);

        slider.value = newValue;

        // Update the corresponding hours input and percentage display
        updateSliderValue(slider);
    });
}

function updateAllSliders() {
    const sliders = Array.from(document.querySelectorAll('.task-slider'));
    const totalHours = parseFloat(document.getElementById('hours').value);

    if (document.getElementById('time_balance').checked && sliders.length > 0) {
        // If time balance is checked, distribute hours evenly among tasks with 0 hours
        const emptySliders = sliders.filter(slider => {
            const taskContainer = slider.closest('.task-container');
            const hoursInput = taskContainer.querySelector('.hours-input');
            return !hoursInput.classList.contains('valid') && parseFloat(slider.value) === 0;
        });

        const filledSliders = sliders.filter(slider => !emptySliders.includes(slider));
        const filledSum = filledSliders.reduce((acc, slider) => acc + parseFloat(slider.value), 0);

        if (emptySliders.length > 0 && filledSum < 100) {
            const remainingPercentage = 100 - filledSum;
            const percentPerEmpty = remainingPercentage / emptySliders.length;

            emptySliders.forEach(slider => {
                slider.value = percentPerEmpty;
                updateSliderValue(slider);
            });
        }
    }

    // Update all sliders and inputs
    sliders.forEach(slider => {
        updateSliderValue(slider);
    });
}

// Updated form validation to require Product Family field
document.getElementById('time-tracking-form').addEventListener('submit', function (event) {
    // Prevent the form from submitting by default
    event.preventDefault();

    let isValid = true;
    let errorMessage = '';

    // Check if team member is selected
    const teamMember = document.getElementById('team_member').value;
    if (!teamMember) {
        isValid = false;
        errorMessage += 'Please select a team member.<br>';
    }

    // Check if date is selected
    const entryDate = document.getElementById('entry_date').value;
    if (!entryDate) {
        isValid = false;
        errorMessage += 'Please select a date.<br>';
    }

    // Check if total hours is valid
    const totalHours = parseFloat(document.getElementById('hours').value);
    if (isNaN(totalHours) || totalHours <= 0) {
        isValid = false;
        errorMessage += 'Please enter a valid number of hours.<br>';
    }

    // Validate each task
    const taskContainers = document.querySelectorAll('.task-container');
    let tasksWithCategory = 0;

    taskContainers.forEach((taskContainer, index) => {
        const categorySelect = taskContainer.querySelector('.category-select');
        const productFamilySelect = taskContainer.querySelector('.product-family-select');
        const hoursInput = taskContainer.querySelector('.hours-input');

        // Check if category is selected (required)
        if (!categorySelect.value) {
            isValid = false;
            errorMessage += `Task ${index + 1}: Please select a category.<br>`;
        } else {
            tasksWithCategory++;
        }

        // Check if product family is selected (required)
        if (!productFamilySelect.value) {
            isValid = false;
            errorMessage += `Task ${index + 1}: Please select a product family.<br>`;
        }

        // Check if hours is filled and valid
        const hours = parseFloat(hoursInput.value);
        if (isNaN(hours) || hours <= 0) {
            isValid = false;
            errorMessage += `Task ${index + 1}: Please enter valid hours (must be greater than 0).<br>`;
        }
    });

    // Ensure at least one task has a category
    if (tasksWithCategory === 0) {
        isValid = false;
        errorMessage += 'At least one task must have a category selected.<br>';
    }

    // Show error message or submit the form
    if (!isValid) {
        // Display error message
        showValidationErrors(errorMessage);
    } else {
        // Remove any existing error messages
        hideValidationErrors();

        // Submit the form
        this.submit();
    }
});

// Function to show validation errors
function showValidationErrors(message) {
    // Check if error container already exists
    let errorContainer = document.getElementById('validation-errors');

    if (!errorContainer) {
        // Create container for error messages
        errorContainer = document.createElement('div');
        errorContainer.id = 'validation-errors';
        errorContainer.className = 'error-message';

        // Insert before the form
        const form = document.getElementById('time-tracking-form');
        form.parentNode.insertBefore(errorContainer, form);
    }

    // Set error message content
    errorContainer.innerHTML = `
        <h3>Please fix the following errors:</h3>
        ${message}
    `;

    // Scroll to error message
    errorContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Function to hide validation errors
function hideValidationErrors() {
    const errorContainer = document.getElementById('validation-errors');
    if (errorContainer) {
        errorContainer.remove();
    }
}

// Add CSS for the validation errors
document.addEventListener('DOMContentLoaded', function () {
    const style = document.createElement('style');
    style.textContent = `
        .error-message {
            background-color: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border: 1px solid #f5c6cb;
        }
        
        .error-message h3 {
            margin-top: 0;
            font-size: 16px;
        }
        
        .project-input {
            width: 100%;
            padding: 4px 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-family: 'Roboto', sans-serif;
        }
    `;
    document.head.appendChild(style);
});