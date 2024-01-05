window.onload = function () {
    document.querySelectorAll('input[type="range"]').forEach(function (slider) {
        slider.addEventListener('input', function () {
            updateSliderValues(slider);
        });
    });
    // Trigger an update immediately to set the initial hours values
    updateSliderValues(document.querySelector('input[type="range"]'));
};

function updateSliderValues(changedSlider) {
    var sliders = document.querySelectorAll('input[type="range"]');
    var totalPercentage = getTotalPercentage(sliders);
    var totalHours = parseFloat(document.getElementById('hours').value);

    // If total is exactly 100, just update the hours
    if (totalPercentage === 100) {
        updateHours(sliders, totalHours);
        return;
    }

    // Distribute the remaining percentage to other sliders
    distributeRemainingPercentage(sliders, changedSlider, totalPercentage);

    // Update hours after adjusting the sliders
    updateHours(sliders, totalHours);
}

function getTotalPercentage(sliders) {
    var totalPercentage = 0;
    sliders.forEach(function (slider) {
        totalPercentage += parseFloat(slider.value);
    });
    return totalPercentage;
}

function distributeRemainingPercentage(sliders, changedSlider, totalPercentage) {
    var adjustment = 100 - totalPercentage;
    var slidersToAdjust = Array.from(sliders).filter(function (s) { return s !== changedSlider && parseFloat(s.value) !== 0; });

    // Calculate the adjustment per slider
    var adjustmentPerSlider = adjustment / slidersToAdjust.length;

    // Adjust the other sliders, ensuring no slider value becomes negative
    slidersToAdjust.forEach(function (slider) {
        let newValue = parseFloat(slider.value) + adjustmentPerSlider;
        slider.value = Math.max(Math.min(newValue, 100), 0);
    });
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
    updateSliderValues(document.querySelector('input[type="range"]'));
});
