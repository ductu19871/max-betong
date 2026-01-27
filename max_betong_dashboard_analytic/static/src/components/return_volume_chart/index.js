/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { loadBundle } from "@web/core/assets";
import { Component, onWillStart, onMounted, onWillUnmount, onPatched, useRef } from "@odoo/owl";

export class ReturnVolumeChart extends Component {
    static template = "max_betong_dashboard_analytic.ReturnVolumeChart";
    static props = {
        data: { type: Object, optional: true },
        period: { type: String, optional: true },
    };

    get chartData() {
        return this.props.data || {};
    }

    get hasData() {
        const data = this.chartData;
        if (!data) return false;
        const remixValue = Number(data.remix?.value) || 0;
        const dumpValue = Number(data.dump?.value) || 0;
        const swapValue = Number(data.swap?.value) || 0;
        return (remixValue + dumpValue + swapValue) > 0;
    }

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;
        this._lastData = null;
        this._isRendering = false;

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
        if (this._isRendering) {
            return;
        }

        const canvas = this.canvasRef.el;
        if (!canvas || !canvas.parentElement) {
            console.warn('[ReturnVolume] Canvas not found');
            return;
        }

        const chartData = this.chartData;
        if (!chartData || !chartData.remix || !chartData.dump || !chartData.swap) {
            console.warn('[ReturnVolume] No data available', chartData);
            return;
        }

        if (typeof Chart === 'undefined') {
            console.warn('[ReturnVolume] Chart.js not loaded yet');
            setTimeout(() => this.renderChart(), 100);
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

        const data = chartData;

        const remixValue = Number(data.remix.value) || 0;
        const dumpValue = Number(data.dump.value) || 0;
        const swapValue = Number(data.swap.value) || 0;

        if (remixValue === 0 && dumpValue === 0 && swapValue === 0) {
            return;
        }

        const total = remixValue + dumpValue + swapValue;
        if (total <= 0) {
            return;
        }

        const rect = canvas.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) {
            return;
        }

        this._isRendering = true;
        this._lastData = currentData;

        try {
            this.chart = new Chart(canvas, {
                type: 'pie',
                data: {
                    labels: [_t('Remix'), _t('Dump'), _t('Swap')],
                    datasets: [{
                        data: [remixValue, dumpValue, swapValue],
                        backgroundColor: [
                            data.remix.color || '#1976D2',
                            data.dump.color || '#FB8C00',
                            data.swap.color || '#43A047'
                        ],
                        borderWidth: 0,
                    }]
                },
                options: {
                    responsive: false,
                    maintainAspectRatio: false,
                    animation: false,
                    interaction: {
                        intersect: false,
                        mode: 'nearest'
                    },
                    resizeDelay: 0,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            enabled: true,
                            callbacks: {
                                label: (context) => {
                                    const value = context.parsed || 0;
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${context.label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    },
                    transitions: {
                        active: {
                            animation: {
                                duration: 0
                            }
                        }
                    }
                }
            });

            if (this.chart && this.chart.stop) {
                this.chart.stop();
            }
            
            // Add chart-loaded class to show the chart
            const chartBody = canvas.parentElement;
            if (chartBody && chartBody.classList) {
                chartBody.classList.add('chart-loaded');
            }
        } catch (e) {
            console.error('[ReturnVolume] Chart error:', e);
        } finally {
            this._isRendering = false;
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

