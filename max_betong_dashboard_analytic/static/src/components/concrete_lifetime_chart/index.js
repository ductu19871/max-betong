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

export class ConcreteLifetimeChart extends Component {
    static template = "max_betong_dashboard_analytic.ConcreteLifetimeChart";
    static props = {
        data: { type: Object, optional: true },
        period: { type: String, optional: true },
        debugData: { type: Object, optional: true },
        onDebugClick: { type: Function, optional: true },
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
        }, 100);
    }

    renderChart() {
        const canvas = this.canvasRef.el;
        if (!canvas) {
            return;
        }

        // Ensure canvas has a usable size
        const parent = canvas.parentElement;
        if (parent) {
            const rect = parent.getBoundingClientRect();
            const width = rect.width || 0;
            const height = rect.height || 0;
            if (width === 0 || height === 0) {
                this.queueRender(); // Retry if layout not ready
                return;
            }

            canvas.style.width = `${width}px`;
            canvas.style.height = `${height}px`;
            const dpr = window.devicePixelRatio || 1;
            canvas.width = Math.floor(width * dpr);
            canvas.height = Math.floor(height * dpr);
            const ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            }
        }

        const chartData = this.chartData;
        if (!chartData || !Array.isArray(chartData.data)) {
            dwarn('[ConcreteLifetime] No data available', chartData);
            return;
        }

        dlog('[ConcreteLifetime] All checks passed, creating chart...');

        if (typeof Chart === 'undefined') {
            dwarn('[ConcreteLifetime] Chart.js not loaded yet');
            this.scheduleRender(100);
            return;
        }

        const currentData = JSON.stringify(chartData);
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

        // Defensive: if a Chart instance is still bound to this canvas, destroy it.
        try {
            if (typeof Chart !== 'undefined' && typeof Chart.getChart === 'function') {
                const existing = Chart.getChart(canvas);
                if (existing) {
                    existing.destroy();
                }
            }
        } catch (e) {
            // Ignore
        }

        const data = chartData;
        if (!data.data || data.data.length === 0) {
            return;
        }

        this._lastData = currentData;
        const labels = (data.labels && data.labels.length === data.data.length)
            ? data.labels
            : Array.from({ length: data.data.length }, (_, i) => `V${i + 201}`);

        const valueLabelPlugin = {
            id: 'valueLabelPlugin_lifetime',
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

        const maxVal = Math.max(...data.data.map(Number).filter(v => !isNaN(v)), 0);
        const yMax = Math.ceil((maxVal * 1.2) / 10) * 10 || 100;

        try {
            this.chart = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: _t('Minutes'),
                        data: data.data,
                        backgroundColor: '#829DF5',
                        borderColor: '#829DF5',
                        borderWidth: 0,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                        padding: { top: 20, bottom: 18, left: 24, right: 10 }
                    },
                    animation: {
                        duration: 0
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) => `${context.parsed.y} ${_t('minutes')}`
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: yMax,
                            title: {
                                display: true,
                                text: _t('Minutes'),
                                font: { size: 11, weight: '500' },
                                color: '#64748b'
                            },
                            ticks: {
                                stepSize: 10,
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

            // Add chart-loaded class to show the chart
            const chartBody = canvas.parentElement;
            if (chartBody && chartBody.classList) {
                chartBody.classList.add('chart-loaded');
            }
        } catch (e) {
            console.error('[ConcreteLifetime] Chart error:', e);
        }
    }

    destroyChart() {
        if (this._renderTimer) {
            clearTimeout(this._renderTimer);
            this._renderTimer = null;
        }
        if (this.chart) {
            try {
                this.chart.destroy();
            } catch (e) {
                // Ignore
            }
            this.chart = null;
        }

        const canvas = this.canvasRef?.el;
        if (canvas) {
            try {
                if (typeof Chart !== 'undefined' && typeof Chart.getChart === 'function') {
                    const existing = Chart.getChart(canvas);
                    if (existing) {
                        existing.destroy();
                    }
                }
            } catch (e) {
                // Ignore
            }
        }
    }

    formatAverage(avg) {
        if (avg === null || avg === undefined) return '0';
        const value = Number(avg);
        if (isNaN(value)) return '0';
        return Math.round(value);
    }

    t(key) {
        return _t(key);
    }
}

