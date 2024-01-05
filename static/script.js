window.onload = function () {
    var sliders = document.querySelectorAll('input[type="range"]');
    var hourInputs = document.querySelectorAll('.hours-input');

    // Attach event listeners and set initial states
    sliders.forEach(function (slider, index) {
        slider.addEventListener('input', function () {
            if (!slider.disabled) {
                updateSliderValues(slider);
            }
        });

        hourInputs[index].addEventListener('input', function () {
            lockSlider(hourInputs[index]);
        });

        // Initialize sliders as unlocked
        slider.disabled = hourInputs[index].value.trim() !== '';
    });

    // Set initial slider values
    updateSliderValues(sliders[0]);
};


function lockSlider(inputElement) {
    var sliderId = inputElement.nextElementSibling.nextElementSibling.id;
    var slider = document.getElementById(sliderId);
    var totalHoursInput = document.getElementById('hours');
    var totalHours = parseFloat(totalHoursInput.value);
    var inputHours = parseFloat(inputElement.value);

    // Clear any previously set styles
    inputElement.classList.remove('invalid', 'valid');
    slider.disabled = false; // Ensure sliders start as unlocked

    if (inputHours > totalHours || isNaN(inputHours)) {
        inputElement.classList.add('invalid');
        inputElement.value = '';  // Clear the invalid input
        slider.disabled = false;  // Ensure slider is unlocked
    } else if (inputElement.value.trim() !== '') {
        inputElement.classList.add('valid');
        slider.value = (inputHours / totalHours) * 100;
        slider.disabled = true;  // Lock the slider
    }

    updateSliderValues(slider);  // Update the sliders and hours display
}

// Existing updateSliderValues function
// Add your existing function here, making sure to include the disabling logic

function updateSliderValues(changedSlider) {
    var sliders = document.querySelectorAll('input[type="range"]');
    var lockedSliders = Array.from(document.querySelectorAll('.hours-input.valid'));
    var totalHours = parseFloat(document.getElementById('hours').value);
    var allocatedHours = getAllocatedHours(lockedSliders);
    var remainingHours = totalHours - allocatedHours;
    var remainingPercentage = (remainingHours / totalHours) * 100;
    var totalUnlockedPercentage = getTotalPercentage(sliders, lockedSliders);

    // Find all unlocked and non-zero sliders
    var activeSliders = Array.from(sliders).filter(function (slider) {
        return !slider.disabled && parseFloat(slider.value) !== 0;
    });

    // If there is only one active slider left and it's the one being changed
    if (activeSliders.length === 1 && activeSliders[0] === changedSlider) {
        // Set this slider to the remaining percentage but not above it
        changedSlider.value = Math.min(parseFloat(changedSlider.value), remainingPercentage).toString();
        updateHoursDisplay(changedSlider, totalHours); // Update the hours display for this slider
    } else {
        // If there are other sliders, distribute the remaining percentage among them
        if (totalUnlockedPercentage !== 100) {
            distributeRemainingPercentage(sliders, changedSlider, totalUnlockedPercentage, lockedSliders);
        }
        // Update the hours display for all sliders
        sliders.forEach(slider => updateHoursDisplay(slider, totalHours));
    }
}

// Helper function to update the hours display for a slider
function updateHoursDisplay(slider, totalHours) {
    var sliderPercentage = parseFloat(slider.value);
    var sliderHours = (sliderPercentage / 100) * totalHours;
    var correspondingInput = slider.previousElementSibling.previousElementSibling;
    if (correspondingInput && correspondingInput.value.trim() === '') {
        correspondingInput.placeholder = sliderHours.toFixed(1) + 'h';
    }
}

// Helper function to get the total allocated hours from locked sliders
function getAllocatedHours(lockedSliders) {
    return lockedSliders.reduce((total, input) => total + parseFloat(input.value || 0), 0);
}

// ... rest of the existing script.js functions ...


// This function now also receives lockedSliders as an argument
function getTotalPercentage(sliders, lockedSliders) {
    var totalPercentage = 0;
    sliders.forEach(function (slider) {
        // Check if slider is not locked
        if (!lockedSliders.includes(slider.previousElementSibling.previousElementSibling)) {
            totalPercentage += parseFloat(slider.value);
        }
    });
    return totalPercentage;
}

// This function now also receives lockedSliders as an argument
function distributeRemainingPercentage(sliders, changedSlider, totalPercentage, lockedSliders) {
    var unlockedSliders = Array.from(sliders).filter(function (slider) {
        return !slider.disabled &&
            !lockedSliders.includes(slider.previousElementSibling.previousElementSibling);
    });

    // Exclude sliders that are manually set to 0% unless it's the changed slider
    var slidersToAdjust = unlockedSliders.filter(function (slider) {
        return slider.value !== '0' || slider === changedSlider;
    });

    if (slidersToAdjust.length <= 1) {
        return; // No need to adjust if there's only one unlocked slider
    }

    var remainingHours = getRemainingHours(lockedSliders);
    var remainingPercentage = (remainingHours / parseFloat(document.getElementById('hours').value)) * 100;
    var adjustment = remainingPercentage - totalPercentage;

    // Calculate the adjustment per slider
    var adjustmentPerSlider = adjustment / slidersToAdjust.length;

    // Adjust the other unlocked sliders, ensuring no slider value becomes negative
    slidersToAdjust.forEach(function (slider) {
        if (slider !== changedSlider) {
            let newValue = parseFloat(slider.value) + adjustmentPerSlider;
            slider.value = Math.max(newValue, 0); // Ensure slider does not go below 0
        }
    });
}

function getRemainingHours(lockedSliders) {
    var totalHours = parseFloat(document.getElementById('hours').value);
    var allocatedHours = 0;

    // Calculate the total hours allocated by locked sliders
    lockedSliders.forEach(function (input) {
        allocatedHours += parseFloat(input.value) || 0;
    });

    return totalHours - allocatedHours; // Remaining hours for unlocked sliders
}


// This new function updates the placeholders for the hour input fields
function updateHourInputs(sliders, totalHours) {
    sliders.forEach(function (slider) {
        // Find the corresponding hour input
        let hourInput = slider.previousElementSibling.previousElementSibling;
        if (hourInput && hourInput.value.trim() === '') {
            // Calculate the hours based on the slider's percentage
            let sliderPercentage = parseFloat(slider.value);
            let sliderHours = (sliderPercentage / 100) * totalHours;
            // Set the placeholder to the calculated hours
            hourInput.placeholder = sliderHours.toFixed(1) + 'h';
        }
    });
    // Update the hour input placeholders when a value is locked
    updateHourInputs(Array.from(document.querySelectorAll('input[type="range"]')), parseFloat(document.getElementById('hours').value));
}

// Add the event listener to the total hours input
document.getElementById('hours').addEventListener('input', function () {
    var sliders = document.querySelectorAll('input[type="range"]');
    updateSliderValues(sliders[0]);
});

// Ensure that the sliders are unlocked if the corresponding hour input is empty
document.querySelectorAll('.hours-input').forEach(function (input) {
    if (input.value.trim() === '') {
        var sliderId = input.nextElementSibling.nextElementSibling.id;
        var slider = document.getElementById(sliderId);
        slider.disabled = false;
    }
});