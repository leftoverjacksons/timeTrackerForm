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

    // Log subfields for debugging
    console.log("Subfields structure:", window.subfields);
    console.log("NPI subfields:", window.npiSubfields);
    console.log("Sustaining subfields:", window.sustainingSubfields);

    // Initialize category dropdowns
    document.querySelectorAll('.category-select').forEach(function (select) {
        select.addEventListener('change', function () {
            updateProjectOptions(select);
        });
    });
};

function initializeTask(taskContainer) {
    const taskId = taskContainer.getAttribute('data-task-id');
    const slider = taskContainer.querySelector('.task-slider');
    const hoursInput = taskContainer.querySelector('.hours-input');
    const percentDisplay = taskContainer.querySelector('.percent-display');
    const categorySelect = taskContainer.querySelector('.category-select');

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

    // Set up event listeners for the category select
    categorySelect.addEventListener('change', function () {
        console.log("Category changed to:", categorySelect.value);
        updateProjectOptions(categorySelect);
    });

    // Initialize project options based on current category selection
    if (categorySelect.value) {
        updateProjectOptions(categorySelect);
    }
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

    // Clear and reset the project dropdown
    const projectSelect = newTask.querySelector('.project-select');
    projectSelect.id = 'project-' + taskCounter;
    projectSelect.name = 'tasks[' + (taskCounter - 1) + '][project]';
    projectSelect.value = '';
    projectSelect.innerHTML = '<option value="">Select Project</option>';

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
    categorySelect.addEventListener('change', function () {
        console.log(`Category changed for task ${taskCounter} to:`, categorySelect.value);
        updateProjectOptions(categorySelect);
    });

    // Initialize the new task
    initializeTask(newTask);

    // Update all sliders to balance the percentages
    updateAllSliders();
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
    const projectSelect = taskContainer.querySelector('.project-select');
    const category = categorySelect.value;

    // Clear the current options
    projectSelect.innerHTML = '<option value="">Select Project</option>';

    // Skip if no category is selected
    if (!category) {
        return;
    }

    console.log("Updating projects for category:", category);

    // Always use all available subfields regardless of category
    const subfields = window.allSubfields || [];
    console.log(`Using ${subfields.length} subfields for ${category}`);

    // Add the subfields as options
    subfields.forEach(subfield => {
        if (subfield && subfield.trim() !== '') {
            const option = document.createElement('option');
            option.value = subfield;
            option.textContent = subfield;
            projectSelect.appendChild(option);
        }
    });

    // Show the project dropdown
    projectSelect.style.display = 'block';
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