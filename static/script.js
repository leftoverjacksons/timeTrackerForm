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
        // Set this slider to the remaining percentage but not above it
        changedSlider.value = Math.min(parseFloat(changedSlider.value), remainingPercentage).toString();
    } else if (activeSliders.length === 1) {
        // If there's only one active slider and it's not the one being changed, set it to the remaining hours
        activeSliders[0].value = remainingPercentage.toString();
    } else {
        // If there are other sliders, distribute the remaining percentage among them
        distributeRemainingPercentage(sliders, changedSlider, remainingPercentage, lockedSliders);
    }

    // Update the hours display for all sliders
    updateHours(sliders, totalHours);
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

function updateHours(sliders, totalHours) {
    sliders.forEach(function (slider) {
        let sliderPercentage = parseFloat(slider.value);
        let sliderHours = (sliderPercentage / 100) * totalHours;
        document.getElementById(slider.id + '_value').textContent = sliderPercentage.toFixed(0) + '%';
        let correspondingInput = slider.previousElementSibling.previousElementSibling;
        if (correspondingInput && correspondingInput.value.trim() === '') {
            correspondingInput.placeholder = sliderHours.toFixed(1) + 'h';
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
