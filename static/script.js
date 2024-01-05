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
    // Convert NodeList to Array for locked sliders
    var lockedSliders = Array.from(document.querySelectorAll('.hours-input.valid'));
    var totalHours = parseFloat(document.getElementById('hours').value);
    var totalPercentage = getTotalPercentage(sliders, lockedSliders); // Define totalPercentage

    // If total is exactly 100 or no unlocked sliders, just update the hours
    if (totalPercentage === 100 || lockedSliders.length === sliders.length) {
        updateHours(sliders, totalHours);
        return;
    }

    // Distribute the remaining percentage to other unlocked sliders
    distributeRemainingPercentage(sliders, changedSlider, totalPercentage, lockedSliders);

    // Update hours after adjusting the sliders
    updateHours(sliders, totalHours);
}

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
    var totalHours = parseFloat(document.getElementById('hours').value);
    var allocatedHours = 0;

    // Calculate the total hours allocated by locked sliders
    lockedSliders.forEach(function (input) {
        allocatedHours += parseFloat(input.value);
    });

    var remainingHours = totalHours - allocatedHours; // Hours available for unlocked sliders
    var remainingPercentage = (remainingHours / totalHours) * 100; // Convert to percentage

    var unlockedSliders = Array.from(sliders).filter(function (slider) {
        return !slider.disabled &&
            !lockedSliders.includes(slider.previousElementSibling.previousElementSibling);
    });

    if (unlockedSliders.length <= 1) {
        return; // No need to adjust if there is only one unlocked slider
    }

    var totalUnlockedPercentage = getTotalPercentage(unlockedSliders, []);
    var adjustment = remainingPercentage - totalUnlockedPercentage;

    // Calculate the adjustment per slider
    var adjustmentPerSlider = adjustment / unlockedSliders.length;

    var excess = 0; // This will capture any rounding excess

    // Adjust the other unlocked sliders
    unlockedSliders.forEach(function (slider, index) {
        // Don't adjust the slider that was just changed
        if (slider === changedSlider) {
            return;
        }

        let currentPercentage = parseFloat(slider.value);
        let newPercentage = currentPercentage + adjustmentPerSlider + excess;

        // Make sure we don't go below 0
        newPercentage = Math.max(newPercentage, 0);

        // Calculate and accumulate any excess due to rounding
        excess += currentPercentage + adjustmentPerSlider - newPercentage;

        // Update the slider with the new percentage
        slider.value = newPercentage;
    });

    // After adjustment, recalculate to ensure we haven't exceeded the remaining percentage due to rounding
    var postAdjustmentTotal = getTotalPercentage(unlockedSliders, []);
    if (postAdjustmentTotal > remainingPercentage) {
        unlockedSliders.forEach(function (slider) {
            if (slider !== changedSlider) {
                slider.value -= postAdjustmentTotal - remainingPercentage; // Adjust down slightly
            }
        });
    }
}

function updateHours(sliders, totalHours) {
    sliders.forEach(function (slider) {
        let sliderPercentage = parseFloat(slider.value);
        let sliderHours = (sliderPercentage / 100) * totalHours;
        document.getElementById(slider.name + '_value').textContent = Math.round(sliderPercentage) + '%';
        document.getElementById(slider.name + '_hours').textContent = sliderHours.toFixed(1) + 'h';
    });
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