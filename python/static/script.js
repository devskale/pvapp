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
  dateInput.value = `2024-05-03`;
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
    // Add more specific date format validation based on selected function if needed

    const apiUrl = `/api/${selectedFunction}?date=${encodeURIComponent(
      date
    )}&kategorie=${encodeURIComponent(
      kategorie
    )}&yearly_sum=${encodeURIComponent(yearlySum)}`;

    resultsArea.textContent = "Fetching data...";
    chartArea.innerHTML = ""; // Clear previous chart area

    try {
      const response = await fetch(apiUrl);
      const data = await response.json();

      if (!response.ok) {
        // Display detail message from FastAPI HTTPException if available
        const errorDetail =
          data.detail || `HTTP error! status: ${response.status}`;
        throw new Error(errorDetail);
      }

      // Display JSON data in hidden element for copying
      const jsonData = JSON.stringify(data, null, 2);
      resultsArea.textContent = jsonData;

      // Add copy button functionality
      document.getElementById("copy-button").addEventListener("click", () => {
        navigator.clipboard
          .writeText(jsonData)
          .then(() => {
            const copyBtn = document.getElementById("copy-button");
            copyBtn.innerHTML =
              '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"/></svg>';
            setTimeout(() => {
              copyBtn.innerHTML =
                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/><path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/></svg>';
            }, 2000);
          })
          .catch((err) => {
            console.error("Failed to copy: ", err);
          });
      });

      // Create chart if we have monthly or daily data
      if (
        (selectedFunction === "pym" && data.monthly_values) ||
        (selectedFunction === "pm" && data.daily_values)
      ) {
        const ctx = document.createElement("canvas");
        chartArea.appendChild(ctx);

        const isMonthly = selectedFunction === "pym";
        const labels = isMonthly
          ? data.monthly_values.map((m) => m.month_name)
          : data.daily_values.map((d) => d.date.split("-")[2]); // Just show day number
        const values = isMonthly
          ? data.monthly_values.map((m) => m.kwh)
          : data.daily_values.map((d) => d.kwh);
        const percentages = isMonthly
          ? data.monthly_values.map((m) => m.percent_of_year)
          : data.daily_values.map(
              (d) => d.percentage_of_month || d.percentage_of_year
            );

        // Extract short and long form name from selected category
        const selectedOption =
          kategorieSelect.options[kategorieSelect.selectedIndex];
        const shortName = selectedOption.value;
        const longName =
          selectedOption.textContent.split(" (")[1]?.replace(")", "") ||
          data.category_name ||
          "";

        // Format date to yyyy-mm format
        const dateComponents = date.split("-");
        const formattedDate =
          dateComponents.length >= 2
            ? `${dateComponents[0]}-${dateComponents[1]}`
            : dateComponents[0];

        new Chart(ctx, {
          type: "bar",
          data: {
            labels: labels,
            datasets: [
              {
                label: `${data.category_name || kategorie} (kWh)`,
                data: values,
                backgroundColor: "rgba(54, 162, 235, 0.5)",
                borderColor: "rgba(54, 162, 235, 1)",
                borderWidth: 1,
              },
            ],
          },
          options: {
            responsive: true,
            plugins: {
              title: {
                display: true,
                text: `${shortName} - ${longName} ${formattedDate}`,
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
                    const value = isMonthly
                      ? data.monthly_values[index]
                      : data.daily_values[index];
                    const percentField = isMonthly
                      ? "percent_of_year"
                      : value.percentage_of_month || value.percentage_of_year;
                    return `${value.kwh} kWh (${percentField}% of ${
                      isMonthly ? "year" : "month"
                    })`;
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
                    const values = isMonthly
                      ? data.monthly_values
                      : data.daily_values;
                    const maxValue = values.reduce(
                      (max, v) => (v.kwh > max.kwh ? v : max),
                      values[0]
                    );
                    const minValue = values.reduce(
                      (min, v) => (v.kwh < min.kwh ? v : min),
                      values[0]
                    );
                    const totalKwh = values.reduce((sum, v) => sum + v.kwh, 0);
                    const dateInfo = isMonthly
                      ? dateInput.value.split("-")[0]
                      : date;

                    return [
                      {
                        text: `${isMonthly ? "Year" : "Month"}: ${dateInfo}`,
                        fillStyle: "transparent",
                        hidden: false,
                      },
                      {
                        text: `Total: ${totalKwh.toFixed(1)} kWh`,
                        fillStyle: "transparent",
                        hidden: false,
                      },
                      {
                        text: `Max: ${
                          isMonthly
                            ? maxValue.month_name
                            : maxValue.date.split("-")[2]
                        } (${maxValue.kwh.toFixed(1)} kWh, 100%)`,
                        fillStyle: "rgba(54, 162, 235, 0.5)",
                        hidden: false,
                      },
                      {
                        text: `Min: ${
                          isMonthly
                            ? minValue.month_name
                            : minValue.date.split("-")[2]
                        } (${minValue.kwh.toFixed(1)} kWh, ${Math.round(
                          (minValue.kwh / maxValue.kwh) * 100
                        )}%)`,
                        fillStyle: "rgba(54, 162, 235, 0.2)",
                        hidden: false,
                      },
                    ];
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
            },
          },
        });
      }
    } catch (error) {
      console.error("Error fetching data:", error);
      resultsArea.textContent = `Error: ${error.message}`;
    }
  }

  // --- Event Listeners ---
  fetchButton.addEventListener("click", fetchData);

  // --- Initial Load ---
  loadCategories();
});
