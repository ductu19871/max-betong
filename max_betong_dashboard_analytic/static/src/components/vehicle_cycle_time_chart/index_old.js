/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { loadBundle } from "@web/core/assets";
import { Component, onWillStart, onMounted, onWillUnmount, onPatched, useRef } from "@odoo/owl";

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
            console.log('[VehicleCycleTime] onMounted - hasData:', this.hasData, 'data:', this.chartData);
            setTimeout(() => {
                console.log('[VehicleCycleTime] onMounted timeout - hasData:', this.hasData);
                if (this.hasData) {
                    this.renderChart();
                }
            }, 200);
        });

        onPatched(() => {
            console.log('[VehicleCycleTime] onPatched - hasData:', this.hasData);
            if (this.hasData) {
                const currentData = JSON.stringify(this.chartData);
                if (this._lastData !== currentData) {
                    console.log('[VehicleCycleTime] onPatched - data changed, re-rendering');
                    setTimeout(() => this.renderChart(), 50);
                }
            } else if (this.chart) {
                console.log('[VehicleCycleTime] onPatched - no data, destroying chart');
                this.destroyChart();
            }
        });

        onWillUnmount(() => {
            this.destroyChart();
        });
    }

    renderChart() {
        console.log('[VehicleCycleTime] renderChart called, chartData:', this.chartData);
        const canvas = this.canvasRef.el;
        if (!canvas) {
            console.warn('[VehicleCycleTime] Canvas not found');
            return;
        }
        
        const chartData = this.chartData;
        if (!chartData || !Array.isArray(chartData.wait_time) || !Array.isArray(chartData.delivery_time)) {
            console.warn('[VehicleCycleTime] Invalid data format', chartData);
            return;
        }
        
        console.log('[VehicleCycleTime] Data validation passed:', {
            wait_time: chartData.wait_time,
            delivery_time: chartData.delivery_time,
            labels: chartData.labels
        });
        
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

