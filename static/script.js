window.onload = function () {
    var sliders = document.querySelectorAll('input[type="range"]');
    sliders.forEach(function (slider) {
        slider.addEventListener('input', updateSliders);
    });
};

function updateSliders(changedSlider) {
    var sliders = document.querySelectorAll('input[type="range"]');
    var totalPercentage = 0;
    var changedSliderValue = parseFloat(changedSlider.value);

    // Calculate total percentage
    sliders.forEach(function (slider) {
        totalPercentage += parseFloat(slider.value);
    });

    // Determine the amount to add or subtract from the other sliders
    var adjustmentValue = (100 - totalPercentage) / (sliders.length - 1);

    // Adjust the other sliders
    sliders.forEach(function (slider) {
        if (slider !== changedSlider) {
            // Increase or decrease the slider value
            let newValue = parseFloat(slider.value) + adjustmentValue;

            // Ensure the new value is within the bounds [0, 100]
            newValue = Math.max(Math.min(newValue, 100), 0);

            // Update the value and the display
            slider.value = newValue;
            document.getElementById(slider.name + '_value').textContent = newValue + '%';
        }
    });

    // Update the displayed value for the changed slider
    document.getElementById(changedSlider.name + '_value').textContent = changedSliderValue + '%';
}
