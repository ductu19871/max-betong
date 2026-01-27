/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { loadBundle } from "@web/core/assets";
import { Component, onWillStart, onMounted, onWillUnmount, onPatched, useRef } from "@odoo/owl";

export class TripsPerVehicleChart extends Component {
    static template = "max_betong_dashboard_analytic.TripsPerVehicleChart";
    static props = {
        data: { type: Object, optional: true },
        period: { type: String, optional: true },
    };

    get chartData() {
        return this.props.data || {};
    }

    get hasData() {
        const data = this.chartData;
        return data && data.data && Array.isArray(data.data) && data.data.length > 0;
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

        onPatched(() => {
            if (this.hasData) {
                const currentData = JSON.stringify(this.chartData);
                if (this._lastData !== currentData) {
                    setTimeout(() => this.renderChart(), 50);
                }
            } else if (this.chart) {
                this.destroyChart();
            }
        });

        onWillUnmount(() => {
            this.destroyChart();
        });
    }

    renderChart() {
        console.log('[TripsPerVehicle] renderChart called', {
            hasData: !!this.props.data,
            hasTripsData: !!this.props.data?.trips_per_vehicle,
            data: this.props.data?.trips_per_vehicle
        });

        if (!this.props.data || !this.props.data.data) {
            console.warn('[TripsPerVehicle] No data available', this.props.data);
            return;
        }

        const canvas = this.canvasRef.el;
        if (!canvas) {
            console.warn('[TripsPerVehicle] Canvas not found');
            return;
        }

        if (typeof Chart === 'undefined') {
            console.warn('[TripsPerVehicle] Chart.js not loaded yet');
            setTimeout(() => this.renderChart(), 100);
            return;
        }

        // Ensure canvas has size
        const rect = canvas.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) {
            console.warn('[TripsPerVehicle] Canvas has no size, waiting...', rect);
            setTimeout(() => this.renderChart(), 200);
            return;
        }

        const currentData = JSON.stringify(this.props.data.trips_per_vehicle);
        if (this._lastData === currentData && this.chart) {
            return;
        }

        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }

        const data = this.props.data;
        this._lastData = currentData;
        const maxValue = Math.max(...data.data, 10);

        try {
            console.log('[TripsPerVehicle] Creating chart with data:', data);
            const rect = canvas.getBoundingClientRect();
            console.log('[TripsPerVehicle] Canvas rect:', rect);
            
            // Force canvas to have size
            const parent = canvas.parentElement;
            if (parent) {
                const parentRect = parent.getBoundingClientRect();
                const width = parentRect.width || 400;
                const height = parentRect.height || 150;
                
                // Set canvas display size (CSS)
                canvas.style.width = width + 'px';
                canvas.style.height = height + 'px';
                
                // Set canvas internal size (for Chart.js)
                const dpr = window.devicePixelRatio || 1;
                canvas.width = width * dpr;
                canvas.height = height * dpr;
                
                const ctx = canvas.getContext('2d');
                if (ctx) {
                    ctx.scale(dpr, dpr);
                }
                
                console.log('[TripsPerVehicle] Canvas size set:', canvas.width, canvas.height, canvas.style.width, canvas.style.height);
            }
            
            this.chart = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: _t('Trips'),
                        data: data.data,
                        backgroundColor: '#829DF5',
                        borderColor: '#829DF5',
                        borderWidth: 0,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 0
                    },
                    layout: {
                        padding: {
                            top: 10,
                            bottom: 10,
                            left: 10,
                            right: 10
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            enabled: true,
                            callbacks: {
                                label: (context) => `${context.parsed.y} ${_t('trips')}`
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: maxValue + 2,
                            ticks: {
                                stepSize: 1,
                                font: { size: 10 }
                            },
                            grid: {
                                display: true,
                                color: 'rgba(0,0,0,0.05)'
                            }
                        },
                        x: {
                            ticks: {
                                font: { size: 8 },
                                maxRotation: 45,
                                minRotation: 45
                            },
                            grid: { display: false }
                        }
                    }
                }
            });
            console.log('[TripsPerVehicle] Chart created successfully');
            
            // Add chart-loaded class to show the chart
            const chartBody = canvas.parentElement;
            if (chartBody && chartBody.classList) {
                chartBody.classList.add('chart-loaded');
            }
        } catch (e) {
            console.error('[TripsPerVehicle] Chart error:', e);
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

