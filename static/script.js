window.onload = function () {
    var sliders = document.querySelectorAll('input[type="range"]');
    var hourInputs = document.querySelectorAll('.hours-input');

    sliders.forEach(function (slider, index) {
        slider.addEventListener('input', function () {
            if (!slider.disabled) {
                updateSliderValues(slider);
            }
        });

        hourInputs[index].addEventListener('input', function () {
            lockSlider(hourInputs[index]);
        });

        slider.disabled = hourInputs[index].value.trim() !== '';
    });

    updateSliderValues(sliders[0]);
};

function lockSlider(inputElement) {
    var sliderId = inputElement.nextElementSibling.nextElementSibling.id;
    var slider = document.getElementById(sliderId);
    var totalHoursInput = document.getElementById('hours');
    var totalHours = parseFloat(totalHoursInput.value);
    var inputHours = parseFloat(inputElement.value);

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
    // Call the function to update the placeholders for the hour inputs
    updateHourInputs(document.querySelectorAll('input[type="range"]'), totalHours);
}

function updateSliderValues(changedSlider) {
    var sliders = document.querySelectorAll('input[type="range"]');
    var lockedSliders = Array.from(document.querySelectorAll('.hours-input.valid'));
    var totalHours = parseFloat(document.getElementById('hours').value);
    var remainingHours = getRemainingHours(lockedSliders);
    var remainingPercentage = (remainingHours / totalHours) * 100;

    // Find all unlocked and non-zero sliders
    var activeSliders = Array.from(sliders).filter(function (slider) {
        return !slider.disabled && parseFloat(slider.value) !== 0;
    });

    // If there is only one active slider left and it's the one being changed
    if (activeSliders.length === 1 && activeSliders[0] === changedSlider) {
        changedSlider.value = Math.min(parseFloat(changedSlider.value), remainingPercentage).toString();
    } else if (activeSliders.length === 1) {
        activeSliders[0].value = remainingPercentage.toString();
    } else {
        distributeRemainingPercentage(sliders, changedSlider, remainingPercentage, lockedSliders);
    }

    // Update the hours display for all sliders
    updateHours(sliders, totalHours);
    // Call the function to update the placeholders for the hour inputs
    updateHourInputs(sliders, totalHours);

    // Show or hide the subfield dropdowns for NPI and Sustaining
    sliders.forEach(function (slider) {
        if (slider.id === 'npi' || slider.id === 'sustaining') {
            let sliderValue = parseFloat(slider.value);
            let subfieldDropdown = document.getElementById(slider.id + '_subfield');
            if (subfieldDropdown) {
                subfieldDropdown.style.display = sliderValue > 0 ? 'block' : 'none';
            } else {
                console.error('Dropdown with ID ' + slider.id + '_subfield not found.');
            }
        }
    });
}



function updateHourInputs(sliders, totalHours) {
    console.log('Updating hour inputs placeholders'); // For debugging
    sliders.forEach(function (slider) {
        let hourInput = slider.previousElementSibling.previousElementSibling;
        console.log(`Current slider value for ${slider.id}:`, slider.value); // For debugging
        if (hourInput && hourInput.value.trim() === '') {
            let sliderPercentage = parseFloat(slider.value);
            let sliderHours = (sliderPercentage / 100) * totalHours;
            console.log(`Setting placeholder for ${hourInput.id}:`, sliderHours.toFixed(1) + 'h'); // For debugging
            hourInput.placeholder = sliderHours.toFixed(1) + 'h';
        }
    });
}

function distributeRemainingPercentage(sliders, changedSlider, remainingPercentage, lockedSliders) {
    var unlockedSliders = Array.from(sliders).filter(function (slider) {
        return !slider.disabled &&
            !lockedSliders.includes(slider.previousElementSibling.previousElementSibling) &&
            parseFloat(slider.value) !== 0; // Exclude sliders that are set to 0
    });

    if (unlockedSliders.length <= 1) return; // No need to adjust if there's only one unlocked slider

    var adjustment = remainingPercentage - getTotalPercentage(unlockedSliders, []);
    var adjustmentPerSlider = adjustment / unlockedSliders.length;

    // Adjust the other unlocked sliders
    unlockedSliders.forEach(function (slider) {
        if (slider !== changedSlider) {
            let newValue = parseFloat(slider.value) + adjustmentPerSlider;
            slider.value = Math.max(newValue, 0); // Ensure slider does not go below 0
        }
    });
}

function updateHours(sliders, totalHours, shouldLock) {
    sliders.forEach(function (slider) {
        let sliderPercentage = parseFloat(slider.value);
        let sliderHours = (sliderPercentage / 100) * totalHours;
        let correspondingInput = document.querySelector(`input[name="${slider.id}_hours"]`);

        // Check if the correspondingInput exists and if the text input is empty or not
        if (correspondingInput) {
            // Only update the value if the input is empty or shouldLock is false
            if (correspondingInput.value.trim() === '' || !shouldLock) {
                correspondingInput.value = sliderHours.toFixed(1); // Set the value for form submission
            }

            // If shouldLock is true, lock the slider, otherwise ensure it's enabled
            slider.disabled = shouldLock;
        }
    });
}



function getAllocatedHours(lockedSliders) {
    return lockedSliders.reduce((total, input) => total + (parseFloat(input.value) || 0), 0);
}

function getRemainingHours(lockedSliders) {
    var totalHours = parseFloat(document.getElementById('hours').value);
    var allocatedHours = getAllocatedHours(lockedSliders);
    return totalHours - allocatedHours; // Remaining hours for unlocked sliders
}

function getTotalPercentage(sliders, lockedSliders) {
    var totalPercentage = 0;
    sliders.forEach(function (slider) {
        if (!lockedSliders.includes(slider.previousElementSibling.previousElementSibling)) {
            totalPercentage += parseFloat(slider.value);
        }
    });
    return totalPercentage;
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
