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
                this.queueRender();
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
        if (!chartData || !Array.isArray(chartData.wait_time) || !Array.isArray(chartData.delivery_time)) {
            dwarn('[VehicleCycleTime] Invalid data format', chartData);
            return;
        }

        dlog('[VehicleCycleTime] Data validation passed:', {
            wait_time: chartData.wait_time,
            delivery_time: chartData.delivery_time,
            labels: chartData.labels
        });

        if (typeof Chart === 'undefined') {
            dwarn('[VehicleCycleTime] Chart.js not loaded yet');
            this.scheduleRender(100);
            return;
        }

        const data = chartData;
        if (!Array.isArray(data.wait_time) || !Array.isArray(data.delivery_time)) {
            dwarn('[VehicleCycleTime] Data arrays missing');
            return;
        }

        if (data.wait_time.length === 0 || data.delivery_time.length === 0) {
            dwarn('[VehicleCycleTime] Empty data arrays');
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
                dwarn('[VehicleCycleTime] Chart destroy error:', e);
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

        this._lastData = currentData;

        const n = Math.min(data.wait_time.length, data.delivery_time.length);
        const labels = Array.isArray(data.labels) && data.labels.length === n
            ? data.labels
            : Array.from({ length: n }, (_, i) => `#${i + 1}`);

        const totals = Array.from({ length: n }, (_, i) => (Number(data.wait_time[i]) || 0) + (Number(data.delivery_time[i]) || 0));
        const maxVal = Math.max(...totals, 0);
        const suggestedMax = maxVal > 0 ? Math.ceil(maxVal / 10) * 10 : undefined;

        const numBars = n;
        const showSegmentLabels = numBars <= 10;

        const segmentAndTotalLabelPlugin = {
            id: 'segmentAndTotalLabelPlugin_vehicleCycleTime',
            afterDatasetsDraw: (chart) => {
                const { ctx } = chart;
                ctx.save();
                // Use system font stack for consistency with Odoo backend
                ctx.font = '500 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif';
                ctx.fillStyle = '#334155';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'bottom';

                if (showSegmentLabels) {
                    chart.data.datasets.forEach((dataset, datasetIndex) => {
                        const meta = chart.getDatasetMeta(datasetIndex);
                        if (!meta || !meta.data) return;
                        meta.data.forEach((bar, index) => {
                            if (!bar) return;
                            const v = Number(dataset.data[index]) || 0;
                            if (v <= 0) return;
                            const h = Math.abs((bar.base ?? 0) - (bar.y ?? 0));
                            if (h < 14) return;

                            const midY = (bar.base + bar.y) / 2;
                            ctx.textBaseline = 'middle';
                            ctx.fillText(String(Math.round(v * 10) / 10), bar.x, midY);
                            ctx.textBaseline = 'bottom';
                        });
                    });
                }

                const lastMeta = chart.getDatasetMeta(chart.data.datasets.length - 1);
                if (lastMeta && lastMeta.data) {
                    lastMeta.data.forEach((bar, index) => {
                        if (!bar) return;
                        const v = Number(totals[index]) || 0;
                        if (v <= 0) return;
                        const fontSize = numBars > 15 ? 8 : 10;
                        ctx.font = `${fontSize}px sans-serif`;
                        ctx.fillText(String(Math.round(v * 10) / 10), bar.x, bar.y - 3);
                    });
                }

                ctx.restore();
            },
        };

        try {
            dlog('[VehicleCycleTime] Creating chart...');
            this.chart = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: _t('Waiting at Station'),
                            data: data.wait_time,
                            backgroundColor: '#7086FD',
                            borderColor: '#7086FD',
                            borderWidth: 0,
                        },
                        {
                            label: _t('Delivery Time'),
                            data: data.delivery_time,
                            backgroundColor: '#6FD195',
                            borderColor: '#6FD195',
                            borderWidth: 0,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                        padding: {
                            top: 18,
                            bottom: 18,
                            left: 24,
                            right: 10,
                        },
                    },
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
                                label: (context) => `${context.dataset.label}: ${context.parsed.y} ${_t('min')}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            stacked: true,
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
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            suggestedMax: suggestedMax,
                            title: {
                                display: true,
                                text: _t('Minutes'),
                                font: { size: 11, weight: '500' },
                                color: '#64748b'
                            },
                            ticks: {
                                font: { size: 10 }
                            },
                            grid: {
                                display: true,
                                color: 'rgba(0,0,0,0.05)',
                                borderDash: [4, 4],
                            }
                        }
                    }
                },
                plugins: [segmentAndTotalLabelPlugin],
            });

            dlog('[VehicleCycleTime] Chart created successfully');

            const chartBody = canvas.parentElement;
            if (chartBody && chartBody.classList) {
                chartBody.classList.add('chart-loaded');
            }
        } catch (e) {
            console.error('[VehicleCycleTime] Chart error:', e);
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
