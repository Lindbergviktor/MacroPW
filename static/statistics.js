const calorieBarChart = document.getElementById("calorieBarChart");

if (calorieBarChart && typeof Chart !== "undefined") {
  const chartStyles = getComputedStyle(calorieBarChart);
  const chartLabels = JSON.parse(calorieBarChart.dataset.labels || "[]");
  const chartValues = JSON.parse(calorieBarChart.dataset.values || "[]");
  const chartMax = Number.parseFloat(calorieBarChart.dataset.max || "0") || 0;
  const chartBarBorderWidth =
    Number.parseFloat(chartStyles.getPropertyValue("--stats-bar-border-width")) || 1.5;
  const chartBarRadius =
    Number.parseFloat(chartStyles.getPropertyValue("--stats-bar-radius")) || 10;
  const chartAnimationDuration =
    Number.parseInt(chartStyles.getPropertyValue("--stats-animation-duration"), 10) || 700;
  const chartAxisFontFamily =
    chartStyles.getPropertyValue("--stats-axis-font-family").trim() || "DM Sans";
  const chartAxisFontSizeX =
    Number.parseInt(chartStyles.getPropertyValue("--stats-axis-font-size-x"), 10) || 12;
  const chartAxisFontSizeY =
    Number.parseInt(chartStyles.getPropertyValue("--stats-axis-font-size-y"), 10) || 11;
  const chartAxisFontWeightX =
    chartStyles.getPropertyValue("--stats-axis-font-weight-x").trim() || "600";

  new Chart(calorieBarChart, {
    type: "bar",
    data: {
      labels: chartLabels,
      datasets: [
        {
          label: "Calories",
          data: chartValues,
          backgroundColor: chartStyles.getPropertyValue("--stats-bar-fill").trim(),
          borderColor: chartStyles.getPropertyValue("--stats-bar-border").trim(),
          borderWidth: chartBarBorderWidth,
          borderRadius: chartBarRadius,
          borderSkipped: false,
          hoverBackgroundColor: chartStyles.getPropertyValue("--stats-bar-hover").trim(),
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: {
        duration: chartAnimationDuration,
      },
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          displayColors: false,
          callbacks: {
            label(context) {
              return `${context.parsed.y} kcal`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: {
            display: false,
          },
          ticks: {
            color: chartStyles.getPropertyValue("--stats-axis-text").trim(),
            font: {
              family: chartAxisFontFamily,
              size: chartAxisFontSizeX,
              weight: chartAxisFontWeightX,
            },
          },
          border: {
            color: chartStyles.getPropertyValue("--stats-axis-line").trim(),
          },
        },
        y: {
          beginAtZero: true,
          suggestedMax: chartMax,
          ticks: {
            color: chartStyles.getPropertyValue("--stats-axis-text").trim(),
            stepSize: Math.max(Math.ceil(chartMax / 4), 1),
            callback(value) {
              return `${value} kcal`;
            },
            font: {
              family: chartAxisFontFamily,
              size: chartAxisFontSizeY,
            },
          },
          grid: {
            color: chartStyles.getPropertyValue("--stats-grid-line").trim(),
            drawBorder: false,
          },
          border: {
            color: chartStyles.getPropertyValue("--stats-axis-line").trim(),
          },
        },
      },
    },
  });
}
