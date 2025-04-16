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

      // Display JSON data
      resultsArea.textContent = JSON.stringify(data, null, 2);

      // Create chart if we have monthly data
      if (selectedFunction === "pym" && data.monthly_values) {
        const ctx = document.createElement("canvas");
        chartArea.appendChild(ctx);

        new Chart(ctx, {
          type: "bar",
          data: {
            labels: data.monthly_values.map((m) => m.month_name),
            datasets: [
              {
                label: `${data.category_name} (kWh)`,
                data: data.monthly_values.map((m) => m.kwh),
                backgroundColor: "rgba(54, 162, 235, 0.5)",
                borderColor: "rgba(54, 162, 235, 1)",
                borderWidth: 1,
              },
            ],
          },
          options: {
            responsive: true,
            plugins: {
              tooltip: {
                callbacks: {
                  label: (context) => {
                    const month = data.monthly_values[context.dataIndex];
                    return `${month.kwh} kWh (${month.percent_of_year}% of year)`;
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

      // --- Optional: Basic Charting (Example using Chart.js) ---
      // Uncomment and adapt if you want to add charting
      /*
            if (data && data.timestamps && data.values) { // Check if data suitable for charting exists
                renderChart(data.timestamps, data.values, selectedFunction, kategorie, date);
            }
            */
    } catch (error) {
      console.error("Error fetching data:", error);
      resultsArea.textContent = `Error: ${error.message}`;
    }
  }

  // --- Optional: Chart Rendering Function (Example) ---
  /*
    function renderChart(timestamps, values, func, kat, dateStr) {
        // Assumes you have included Chart.js library in index.html
        // <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        const ctx = document.createElement('canvas');
        chartArea.appendChild(ctx);

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: timestamps, // Assuming timestamps are suitable labels
                datasets: [{
                    label: `Energy Profile (${func} - ${kat} - ${dateStr})`,
                    data: values,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                scales: {
                    x: {
                        // Add time scale configuration if needed
                        // type: 'time', 
                        // time: { unit: 'hour' } 
                    },
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'kWh' }
                    }
                },
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
    */

  // --- Event Listeners ---
  fetchButton.addEventListener("click", fetchData);

  // --- Initial Load ---
  loadCategories();
});
