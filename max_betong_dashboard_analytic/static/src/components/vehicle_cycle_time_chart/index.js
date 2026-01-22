/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { loadBundle } from "@web/core/assets";
import { Component, onWillStart, onMounted, onWillUnmount, onWillUpdateProps, useRef } from "@odoo/owl";

export class VehicleCycleTimeChart extends Component {
    static template = "max_betong_dashboard_analytic.VehicleCycleTimeChart";
    static props = {
        data: { type: Object, optional: true },
        period: { type: String, optional: true },
    };

    get chartData() {
        return this.props.data || {};
    }

    get hasData() {
        const data = this.chartData;
        return data && data.labels && Array.isArray(data.labels) && data.labels.length > 0;
    }

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;
        this._lastData = null;

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
        });

        onMounted(() => {
            setTimeout(() => {
                if (this.hasData) {
                    this.renderChart();
                }
            }, 200);
        });

        onWillUnmount(() => {
            this.destroyChart();
        });
    }

    onWillUpdateProps(nextProps) {
        const nextChartData = nextProps.data || {};
        const nextHasData = nextChartData && nextChartData.labels && Array.isArray(nextChartData.labels) && nextChartData.labels.length > 0;
        if (nextHasData) {
            const currentData = JSON.stringify(nextChartData);
            if (this._lastData !== currentData) {
                setTimeout(() => {
                    if (this.hasData) {
                        this.renderChart();
                    }
                }, 50);
            }
        } else if (this.chart) {
            // Destroy chart if data becomes empty
            this.destroyChart();
        }
    }

    renderChart() {
        const canvas = this.canvasRef.el;
        if (!canvas) {
            console.warn('[VehicleCycleTime] Canvas not found');
            return;
        }
        
        const chartData = this.chartData;
        if (!chartData || !Array.isArray(chartData.wait_time) || !Array.isArray(chartData.delivery_time)) {
            console.warn('[VehicleCycleTime] No data available', chartData);
            return;
        }
        
        if (typeof Chart === 'undefined') {
            console.warn('[VehicleCycleTime] Chart.js not loaded yet');
            setTimeout(() => this.renderChart(), 100);
            return;
        }

        const data = chartData;
        if (!Array.isArray(data.wait_time) || !Array.isArray(data.delivery_time)) {
            return;
        }

        if (data.wait_time.length === 0 || data.delivery_time.length === 0) {
            return;
        }

        const currentData = JSON.stringify(data);
        if (this._lastData === currentData && this.chart) {
            return;
        }

        if (this.chart) {
            try {
                this.chart.destroy();
            } catch (e) {
                // Ignore
            }
            this.chart = null;
        }

        this._lastData = currentData;
        const labels = Array.from({ length: Math.min(data.wait_time.length, data.delivery_time.length) }, (_, i) => `V${i + 201}`);

        try {
            this.chart = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: _t('Wait Time'),
                            data: data.wait_time,
                            backgroundColor: '#5CD694',
                            borderColor: '#5CD694',
                            borderWidth: 0,
                        },
                        {
                            label: _t('Delivery Time'),
                            data: data.delivery_time,
                            backgroundColor: '#7B80FF',
                            borderColor: '#7B80FF',
                            borderWidth: 0,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 0
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom',
                            labels: {
                                font: { size: 10 },
                                usePointStyle: true,
                                padding: 15
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => `${context.dataset.label}: ${context.parsed.y} ${_t('minutes')}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            stacked: true,
                            ticks: {
                                font: { size: 8 },
                                maxRotation: 45,
                                minRotation: 45
                            },
                            grid: { display: false }
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                stepSize: 10,
                                font: { size: 10 }
                            },
                            grid: {
                                display: true,
                                color: 'rgba(0,0,0,0.05)'
                            }
                        }
                    }
                }
            });
            
            // Add chart-loaded class to show the chart
            const chartBody = canvas.parentElement;
            if (chartBody && chartBody.classList) {
                chartBody.classList.add('chart-loaded');
            }
        } catch (e) {
            console.error('[VehicleCycleTime] Chart error:', e);
        }
    }

    destroyChart() {
        if (this.chart) {
            try {
                this.chart.destroy();
            } catch (e) {
                // Ignore
            }
            this.chart = null;
        }
    }

    t(key) {
        return _t(key);
    }
}

