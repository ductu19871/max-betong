/** @odoo-module **/

const DEBUG_DASHBOARD = false;
const dlog = (...args) => {
    if (DEBUG_DASHBOARD) {
        console.log(...args);
    }
};
const dwarn = (...args) => {
    if (DEBUG_DASHBOARD) {
        console.warn(...args);
    }
};

const isChartDebugEnabled = () => {
    try {
        if (window?.localStorage?.getItem('max_betong_chart_debug') === '1') {
            return true;
        }
        const hash = (window.location && window.location.hash) ? window.location.hash.replace(/^#/, '') : '';
        if (!hash) {
            return false;
        }
        const params = new URLSearchParams(hash);
        return params.get('chart_debug') === '1';
    } catch (e) {
        return false;
    }
};

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

    get debugEnabled() {
        return isChartDebugEnabled();
    }

    get debugText() {
        try {
            return JSON.stringify(this.props.data ?? null, null, 2);
        } catch (e) {
            return String(this.props.data);
        }
    }

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;
        this._lastData = null;
        this._renderTimeout = null;

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
        });

        onMounted(() => {
            if (this.hasData) {
                this.queueRender();
            }
        });

        onPatched(() => {
            if (this.hasData) {
                const currentData = JSON.stringify(this.chartData);
                if (this._lastData !== currentData) {
                    this.queueRender();
                }
            } else {
                // If no data, we don't necessarily need to destroy immediately.
                // We can just clear the canvas or leave it as is until data comes back.
                // But for now, let's just queue a render which will handle empty state.
                this.queueRender();
            }
        });

        onWillUnmount(() => {
            this.clearRenderTimeout();
            this.destroyChart();
        });
    }

    clearRenderTimeout() {
        if (this._renderTimeout) {
            clearTimeout(this._renderTimeout);
            this._renderTimeout = null;
        }
    }

    queueRender() {
        this.clearRenderTimeout();
        this._renderTimeout = setTimeout(() => {
            this.renderChart();
        }, 100); // 100ms debounce
    }

    renderChart() {
        const canvas = this.canvasRef.el;
        if (!canvas) {
            return;
        }

        if (typeof Chart === 'undefined') {
            this.queueRender();
            return;
        }

        // Check if canvas is attached to DOM
        if (!canvas.isConnected) {
            return;
        }

        const data = this.props.data;
        // If NO data, then we can destroy chart if it exists
        if (!this.hasData) {
            this.destroyChart();
            return;
        }

        // If we have data, proceed to render
        const currentData = JSON.stringify(data.trips_per_vehicle);
        // Optimization: if exact same data string and chart exists, skip
        if (this._lastData === currentData && this.chart) {
            return;
        }

        // DESTROY existing chart before creating new one
        this.destroyChart();

        this._lastData = currentData;
        const maxValue = Math.max(...data.data, 10);


        const valueLabelPlugin = {
            id: 'valueLabelPlugin_trips',
            afterDatasetsDraw: (chart) => {
                const { ctx } = chart;
                const meta = chart.getDatasetMeta(0);
                if (!meta || !meta.data) return;
                ctx.save();
                // Use system font stack for consistency with Odoo backend
                ctx.font = '500 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
                ctx.fillStyle = '#334155';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';
                meta.data.forEach((bar, index) => {
                    const v = Number(chart.data.datasets[0].data[index]) || 0;
                    if (v <= 0) return;
                    ctx.fillText(String(v), bar.x, bar.y - 3);
                });
                ctx.restore();
            }
        };

        try {
            dlog('[TripsPerVehicle] Creating chart with data:', data);
            const rect = canvas.getBoundingClientRect();
            dlog('[TripsPerVehicle] Canvas rect:', rect);

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

                dlog('[TripsPerVehicle] Canvas size set:', canvas.width, canvas.height, canvas.style.width, canvas.style.height);
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
                            top: 20,
                            bottom: 18,
                            left: 24,
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
                            title: {
                                display: true,
                                text: _t('Trips'),
                                font: { size: 11, weight: '500' },
                                color: '#64748b'
                            },
                            ticks: {
                                stepSize: 1,
                                font: { size: 10 }
                            },
                            grid: {
                                display: true,
                                color: 'rgba(0,0,0,0.05)',
                                borderDash: [4, 4],
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: _t('Vehicle'),
                                font: { size: 11, weight: '500' },
                                color: '#64748b'
                            },
                            ticks: {
                                font: { size: 8 },
                                maxRotation: 45,
                                minRotation: 45
                            },
                            grid: { display: false }
                        }
                    }
                },
                plugins: [valueLabelPlugin],
            });
            dlog('[TripsPerVehicle] Chart created successfully');

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

    formatAverage(avg) {
        if (avg === null || avg === undefined) return '0';
        const value = Number(avg);
        if (isNaN(value)) return '0';
        return value.toFixed(0).padStart(2, '0');
    }

    t(key) {
        return _t(key);
    }
}

