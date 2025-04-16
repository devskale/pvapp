document.addEventListener("DOMContentLoaded", () => {
  const functionSelect = document.getElementById("function-select");
  const dateInput = document.getElementById("date-input");
  const kategorieSelect = document.getElementById("kategorie-select");
  const yearlySumInput = document.getElementById("yearly-sum-input");
  const fetchButton = document.getElementById("fetch-button");
  const resultsArea = document.getElementById("results");
  const chartArea = document.getElementById("chart-area"); // Keep for potential future chart integration

  // Set default values
  const today = new Date();
  dateInput.value = `2025-06-29`;
  yearlySumInput.value = "5500";

  // --- Load Categories ---
  async function loadCategories() {
    try {
      const response = await fetch("/api/categories");
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const categories = await response.json();

      kategorieSelect.innerHTML = ""; // Clear loading message
      categories.forEach((cat) => {
        const option = document.createElement("option");
        option.value = cat.Typname;
        // Display both name and text for clarity
        option.textContent = `${cat.Typname} (${cat.Typtext})`;
        kategorieSelect.appendChild(option);
      });
      // Set default or previously selected category if needed
      kategorieSelect.value = "H0";
    } catch (error) {
      console.error("Error loading categories:", error);
      kategorieSelect.innerHTML = '<option value="">Error loading</option>';
      resultsArea.textContent = `Error loading categories: ${error.message}`;
    }
  }

  // --- Fetch Data ---
  async function fetchData() {
    const selectedFunction = functionSelect.value;
    const date = dateInput.value.trim();
    const kategorie = kategorieSelect.value;
    const yearlySum = yearlySumInput.value;

    // Basic input validation
    if (!date) {
      resultsArea.textContent = "Please enter a date.";
      return;
    }

    // Format date based on function
    let formattedDate = date;
    if (selectedFunction === "pyd" || selectedFunction === "pym") {
      // For year-based functions, just extract the year part
      const yearMatch = date.match(/^\d{4}/);
      if (yearMatch) {
        formattedDate = yearMatch[0];
      }
    }

    const apiUrl = `/api/${selectedFunction}?date=${encodeURIComponent(
      formattedDate
    )}&kategorie=${encodeURIComponent(
      kategorie
    )}&yearly_sum=${encodeURIComponent(yearlySum)}`;

    // Show loading state
    resultsArea.textContent = "Fetching data...";
    chartArea.innerHTML = `
      <div class="loading-container">
        <div style="display: flex; flex-direction: column; align-items: center; gap: 10px;">
          <div class="loading"></div>
          <span>Loading chart data...</span>
        </div>
      </div>
    `;

    try {
      const response = await fetch(apiUrl);
      const data = await response.json();

      if (!response.ok) {
        // Display detail message from FastAPI HTTPException if available
        const errorDetail =
          data.detail || `HTTP error! status: ${response.status}`;
        throw new Error(errorDetail);
      }

      // Store JSON data but don't display it in the results area
      const jsonData = JSON.stringify(data, null, 2);

      // Update results area with a minimal message instead of full JSON
      resultsArea.textContent =
        "Data retrieved successfully. Click 'Copy JSON' to copy the raw data.";

      // Update copy button functionality
      document.getElementById("copy-button").addEventListener("click", () => {
        navigator.clipboard
          .writeText(jsonData)
          .then(() => {
            const copyBtn = document.getElementById("copy-button");
            copyBtn.textContent = "Copied!";
            setTimeout(() => {
              copyBtn.textContent = "Copy JSON";
            }, 2000);
          })
          .catch((err) => {
            console.error("Failed to copy: ", err);
          });
      });

      // Update the fetch button to show success briefly
      fetchButton.classList.add("success");
      fetchButton.innerHTML = `<i class="fas fa-check button-icon"></i> Success!`;
      setTimeout(() => {
        fetchButton.classList.remove("success");
        fetchButton.innerHTML = `<i class="fas fa-chart-line button-icon"></i> Generate Chart`;
      }, 2000);

      // Clear the entire chart area before creating new chart
      chartArea.innerHTML = "";

      // Create chart if we have monthly, daily or hourly data
      if (
        (selectedFunction === "pym" && data.monthly_values) ||
        (selectedFunction === "pm" && data.daily_values) ||
        (selectedFunction === "pd" && data.hourly_values) ||
        (selectedFunction === "pyd" && data.daily_values)
      ) {
        const ctx = document.createElement("canvas");
        chartArea.appendChild(ctx);

        const isMonthly = selectedFunction === "pym";
        const isDaily = selectedFunction === "pm";
        const isHourly = selectedFunction === "pd";
        const isYearDays = selectedFunction === "pyd";

        let labels, values, percentages;

        if (isMonthly) {
          labels = data.monthly_values.map((m) => m.month_name);
          values = data.monthly_values.map((m) => m.kwh);
          percentages = data.monthly_values.map((m) => m.percent_of_year);
        } else if (isDaily) {
          labels = data.daily_values.map((d) => d.date.split("-")[2]); // Just show day number
          values = data.daily_values.map((d) => d.kwh);
          percentages = data.daily_values.map(
            (d) => d.percentage_of_month || d.percentage_of_year
          );
        } else if (isHourly) {
          labels = data.hourly_values.map((h) => h.hour); // Hour of day
          values = data.hourly_values.map((h) => h.kwh);
          percentages = data.hourly_values.map((h) => h.percentage_of_day);
        } else if (isYearDays) {
          // Format as MM-DD for better readability
          labels = data.daily_values.map((d) => {
            const dateParts = d.date.split("-");
            return `${dateParts[1]}-${dateParts[2]}`;
          });
          values = data.daily_values.map((d) => d.kwh);
          percentages = data.daily_values.map((d) => d.percentage_of_year);
        }

        // Extract short and long form name from selected category
        const selectedOption =
          kategorieSelect.options[kategorieSelect.selectedIndex];
        const shortName = selectedOption.value;
        const longName =
          selectedOption.textContent.split(" (")[1]?.replace(")", "") ||
          data.category_name ||
          "";

        // Format date based on the function for display
        let displayDate;
        if (isMonthly || isYearDays) {
          // Extract just the year for year-based functions
          displayDate = formattedDate;
        } else if (isDaily) {
          const dateComponents = date.split("-");
          displayDate =
            dateComponents.length >= 2
              ? `${dateComponents[0]}-${dateComponents[1]}`
              : dateComponents[0];
        } else if (isHourly) {
          displayDate = date; // Full date for hourly view
        }

        // For Year Days, set a specific chart type to handle the large number of data points
        const chartType = isYearDays ? "line" : "bar";
        const chartConfig = {
          type: chartType,
          data: {
            labels: labels,
            datasets: [
              {
                label: `${data.category_name || kategorie} (kWh)`,
                data: values,
                backgroundColor: "rgba(54, 162, 235, 0.5)",
                borderColor: "rgba(54, 162, 235, 1)",
                borderWidth: 1,
                // For line chart (year days), make it smooth
                tension: isYearDays ? 0.2 : 0,
                // For line chart, ensure points are shown
                pointRadius: isYearDays ? 1 : 0,
                // For year days, fill under the line
                fill: isYearDays ? true : false,
              },
            ],
          },
          options: {
            responsive: true,
            plugins: {
              title: {
                display: true,
                text: `${shortName} - ${longName} ${displayDate}`,
                font: {
                  size: 16,
                  weight: "bold",
                },
                padding: {
                  top: 10,
                  bottom: 20,
                },
              },
              tooltip: {
                callbacks: {
                  label: (context) => {
                    const index = context.dataIndex;
                    let value, percentField, periodName;

                    if (isMonthly) {
                      value = data.monthly_values[index];
                      percentField = value.percent_of_year;
                      periodName = "year";
                    } else if (isDaily) {
                      value = data.daily_values[index];
                      percentField =
                        value.percentage_of_month || value.percentage_of_year;
                      periodName = "month";
                    } else if (isHourly) {
                      value = data.hourly_values[index];
                      percentField = value.percentage_of_day;
                      periodName = "day";
                    } else if (isYearDays) {
                      value = data.daily_values[index];
                      percentField = value.percentage_of_year;
                      periodName = "year";
                    }

                    return `${value.kwh.toFixed(
                      2
                    )} kWh (${percentField}% of ${periodName})`;
                  },
                  // For year days, show the full date in tooltip title
                  title: (context) => {
                    if (isYearDays) {
                      const index = context[0].dataIndex;
                      return data.daily_values[index].date;
                    }
                    return context[0].label;
                  },
                },
              },
              legend: {
                position: "right",
                labels: {
                  padding: 30,
                  font: {
                    size: 12,
                  },
                  generateLabels: (chart) => {
                    let values, dateInfo;

                    if (isMonthly) {
                      values = data.monthly_values;
                      dateInfo = formattedDate;
                    } else if (isDaily) {
                      values = data.daily_values;
                      dateInfo = date;
                    } else if (isHourly) {
                      values = data.hourly_values;
                      dateInfo = date;
                    } else if (isYearDays) {
                      values = data.daily_values;
                      dateInfo = formattedDate;
                    }

                    const maxValue = values.reduce(
                      (max, v) => (v.kwh > max.kwh ? v : max),
                      values[0]
                    );
                    const minValue = values.reduce(
                      (min, v) => (v.kwh < min.kwh ? v : min),
                      values[0]
                    );
                    const totalKwh = values.reduce((sum, v) => sum + v.kwh, 0);
                    const avgKwh = totalKwh / values.length;

                    let periodName, maxLabel, minLabel;

                    if (isMonthly) {
                      periodName = "Year";
                      maxLabel = maxValue.month_name;
                      minLabel = minValue.month_name;
                    } else if (isDaily) {
                      periodName = "Month";
                      maxLabel = maxValue.date.split("-")[2];
                      minLabel = minValue.date.split("-")[2];
                    } else if (isHourly) {
                      periodName = "Day";
                      maxLabel = `${maxValue.hour}:00`;
                      minLabel = `${minValue.hour}:00`;
                    } else if (isYearDays) {
                      periodName = "Year";
                      // Format date as MM-DD for readability
                      const maxDateParts = maxValue.date.split("-");
                      const minDateParts = minValue.date.split("-");
                      maxLabel = `${maxDateParts[1]}-${maxDateParts[2]}`;
                      minLabel = `${minDateParts[1]}-${minDateParts[2]}`;
                    }

                    const legendItems = [
                      {
                        text: `${periodName}: ${dateInfo}`,
                        fillStyle: "transparent",
                        hidden: false,
                      },
                      {
                        text: `Total: ${totalKwh.toFixed(1)} kWh`,
                        fillStyle: "transparent",
                        hidden: false,
                      },
                    ];

                    // For year days, also show average
                    if (isYearDays) {
                      legendItems.push({
                        text: `Avg: ${avgKwh.toFixed(1)} kWh/day`,
                        fillStyle: "transparent",
                        hidden: false,
                      });
                    }

                    legendItems.push(
                      {
                        text: `Max: ${maxLabel} (${maxValue.kwh.toFixed(
                          1
                        )} kWh, 100%)`,
                        fillStyle: "rgba(54, 162, 235, 0.5)",
                        hidden: false,
                      },
                      {
                        text: `Min: ${minLabel} (${minValue.kwh.toFixed(
                          1
                        )} kWh, ${Math.round(
                          (minValue.kwh / maxValue.kwh) * 100
                        )}%)`,
                        fillStyle: "rgba(54, 162, 235, 0.2)",
                        hidden: false,
                      }
                    );

                    return legendItems;
                  },
                },
              },
            },
            scales: {
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: "kWh",
                },
              },
              x: {
                // For year days, don't show all labels as it would be too crowded
                ticks: {
                  autoSkip: isYearDays,
                  maxTicksLimit: isYearDays ? 12 : undefined, // Show roughly one label per month for year days
                  maxRotation: isYearDays ? 0 : 0, // Don't rotate labels for year days
                  callback: function (value, index, values) {
                    // For year days, only show the 1st of each month
                    if (isYearDays) {
                      const label = this.getLabelForValue(value);
                      // If the label ends with "-01", it's the first of a month
                      if (label.endsWith("-01")) {
                        return label;
                      }
                      return ""; // Hide other labels
                    }
                    return this.getLabelForValue(value);
                  },
                },
              },
            },
          },
        };

        new Chart(ctx, chartConfig);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      chartArea.innerHTML = `
        <div class="error-message">
          <i class="fas fa-exclamation-triangle" style="margin-right: 8px;"></i>
          ${error.message}
        </div>
      `;
      resultsArea.textContent = `Error: ${error.message}`;
    }
  }

  // --- Event Listeners ---
  fetchButton.addEventListener("click", fetchData);

  // Add transition animation when changing function
  functionSelect.addEventListener("change", () => {
    document.getElementById("output-area").classList.remove("fade-in");
    void document.getElementById("output-area").offsetWidth; // Trigger reflow
    document.getElementById("output-area").classList.add("fade-in");
  });

  // --- Initial Load ---
  loadCategories();

  // Update function display when page loads
  updateFunctionDisplay();

  // Update function display when function changes
  functionSelect.addEventListener("change", () => {
    updateFunctionDisplay();
  });
});

// Helper function to update function field text display
function updateFunctionDisplay() {
  const select = document.getElementById("function-select");
  const selectedOption = select.options[select.selectedIndex];

  // Set title attribute to show full text on hover
  select.title = selectedOption.textContent;
}
