class AttendanceChart {
  constructor() {
    this.chart = null;
  }

  load() {
    fetch("/api/attendance")
      .then(res => res.json())
      .then(data => this.render(data));
  }

  render(data) {
    const canvas = document.getElementById("attendanceChart");
    if (!canvas) return;

    if (this.chart) this.chart.destroy();

    const labels = data.subjects.map(s => s.code);
    const values = data.subjects.map(s =>
      s.total ? Math.round((s.present / s.total) * 100) : 0
    );

    Chart.register(ChartDataLabels);

    this.chart = new Chart(canvas, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Attendance %",
          data: values,
          backgroundColor: "#2563eb"
        }]
      },
      options: {
        plugins: {
          datalabels: {
            formatter: v => v + "%",
            anchor: "end",
            align: "top"
          }
        },
        scales: {
          y: { beginAtZero: true, max: 100 }
        }
      }
    });
  }
}

function initAttendanceChart() {
  new AttendanceChart().load();
}
