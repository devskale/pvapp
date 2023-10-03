document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("solarForm");

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        const kW = parseFloat(document.getElementById("kW").value);

        // Updated parameters
        const kW_per_panel = 0.4;
        const m2_per_kW = 2 / kW_per_panel;
        const cost_per_kW = 2500;
        const no_of_panels_per_kW = 1 / kW_per_panel;
        const kWh_per_year_per_kW = 1000;

        const m2 = m2_per_kW * kW;
        const cost = cost_per_kW * kW;
        let no_of_panels = no_of_panels_per_kW * kW;
        no_of_panels = Math.ceil(no_of_panels);
        const kWh_per_year = Math.ceil(kWh_per_year_per_kW * kW);

        const resultHTML = `
      <h2>Results:</h2>
      <p>Required m2: ${m2}</p>
      <p>Cost of Installation: €${cost}</p>
      <p>Number of Panels: ${no_of_panels}</p>
      <p>Production Per Year kWh: ${kWh_per_year}</p>
      `;

        document.getElementById("results").innerHTML = resultHTML;

        // Monthly distribution (sample for 10,000 kWh)
        const monthlyDist = [205, 316, 803, 1385, 1460, 1393, 1460, 1240, 926, 410, 265, 137];

        // Daily average kWh production per month
        const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
        const dailyAvg = monthlyDist.map((kWh, index) => (kWh / daysInMonth[index]).toFixed(2));

        // Central Europe consumption
        const singlePersonMonthly = [150, 130, 120, 110, 100, 90, 90, 100, 110, 120, 140, 150];
        const familyMonthly = [410, 370, 350, 320, 290, 250, 250, 290, 320, 350, 390, 410];
        const singlePersonDailyAvg = singlePersonMonthly.map((kWh, index) => (kWh / daysInMonth[index]).toFixed(2));
        const familyDailyAvg = familyMonthly.map((kWh, index) => (kWh / daysInMonth[index]).toFixed(2));

        const ctx = document.getElementById('myChart').getContext('2d');
        const myChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [
                    {
                        label: 'Daily Avg Production kWh',
                        data: dailyAvg,
                        backgroundColor: 'rgba(75, 192, 192, 0.5)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Single Person Consumption (Central Europe)',
                        type: 'line',
                        data: singlePersonDailyAvg,
                        borderColor: 'rgba(255, 159, 64, 1)',
                        fill: false
                    },
                    {
                        label: 'Family Consumption (Central Europe)',
                        type: 'line',
                        data: familyDailyAvg,
                        borderColor: 'rgba(54, 162, 235, 1)',
                        fill: false
                    }
                ]
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                        suggestedMax: 50,
                        suggestedMin: 0
                    }
                }
            }
        });
    });
});
