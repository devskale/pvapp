import Config from './config.js';


document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("solarForm");

    form.addEventListener("submit", function (e) {
        e.preventDefault();

        const kWp = parseFloat(form.elements.kW.value);

        const m2 = Config.m2_per_kW * kWp;
        const cost = Config.cost_per_kW * kWp;
        let no_of_panels = Config.no_of_panels_per_kW * kWp;
        no_of_panels = Math.ceil(no_of_panels);
        const kWh_per_year = Math.ceil(Config.kWh_per_year_per_kW * kWp);


        const resultHTML = `
      <h2>Results:</h2>
      <p>Required m2: ${m2}</p>
      <p>Cost of Installation: €${cost}</p>
      <p>Number of Panels: ${no_of_panels}</p>
      <p>Production Per Year kWh: ${kWh_per_year}</p>
      `;

        document.getElementById("results").innerHTML = resultHTML;

        // Monthly distribution (kWh Energy per Day per kWp installed)
        const monthlyDist = [0.9, 1.5, 3.1, 4.8, 4.5, 4.0, 4.3, 3.9, 3.4, 1.5, 1.2, 0.5];

        // Daily average kWh production per month
        const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
        const actualDailyAvg = monthlyDist.map(kWh_per_day_per_kWp => kWh_per_day_per_kWp * kWp);

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
                        data: actualDailyAvg,
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
