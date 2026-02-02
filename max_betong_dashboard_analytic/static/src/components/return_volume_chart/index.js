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

    get chartPercentage() {
        const raw = Number(this.props.data?.percentage);
        const value = Number.isFinite(raw) ? raw : 0;
        return value.toFixed(1);
    }

    get incidentVolume() {
        const data = this.chartData;
        if (!data) return 0;
        const remix = Number(data.remix?.value) || 0;
        const dump = Number(data.dump?.value) || 0;
        const swap = Number(data.swap?.value) || 0;
        return (remix + dump + swap).toFixed(1);
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

        const chartData = this.chartData;
        if (!chartData || !chartData.remix || !chartData.dump || !chartData.swap) {
            // Keep existing chart if we just lose data momentarily, or destroy if you prefer strict emptiness
            return;
        }

        if (typeof Chart === 'undefined') {
            this.queueRender();
            return;
        }

        if (!canvas.isConnected) {
            return;
        }

        const currentData = JSON.stringify(chartData);
        if (this._lastData === currentData && this.chart) {
            return;
        }

        // DESTROY before re-creating
        this.destroyChart();

        const data = chartData;

        // ============================================================================
        // KHỐI LƯỢNG BÊ TÔNG SỰ CỐ (RETURN VOLUME / INCIDENT VOLUME)
        // ============================================================================
        // Data nhận từ backend chỉ có: remix, dump, swap (KHÔNG có completed)
        // Percentage đã được tính sẵn ở backend = (remix+dump+swap) / (completed+remix+dump+swap)
        // Chart chỉ hiển thị: Remix, Dump, Swap
        // ============================================================================

        const remixValue = Number(data.remix.value) || 0;
        const dumpValue = Number(data.dump.value) || 0;
        const swapValue = Number(data.swap.value) || 0;

        if (remixValue === 0 && dumpValue === 0 && swapValue === 0) {
            return;
        }

        // Total for chart display (not for percentage calculation)
        // Percentage is already calculated in backend
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
            // Note: Center text is rendered via HTML overlay, not canvas plugin
            this.chart = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: [_t('Remix'), _t('Dump'), _t('Swap')],
                    datasets: [{
                        data: [remixValue, dumpValue, swapValue],
                        backgroundColor: [
                            '#1C75BC',  // Blue - Remix
                            '#F87B38',  // Orange - Dump
                            '#5DC08B'   // Green - Swap
                        ],
                        borderWidth: 0,
                    }]
                },
                options: {
                    responsive: false,
                    maintainAspectRatio: false,
                    cutout: '70%',
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
                                    const pct = ((value / total) * 100).toFixed(1);
                                    return `${context.label}: ${value} m³ (${pct}% of incidents)`;
                                },
                                footer: (tooltipItems) => {
                                    return [
                                        '─────────────────',
                                        `Total incidents: ${total} m³`,
                                        `Incident Ratio / Total Completed: ${chartData.percentage}%`
                                    ];
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
                },
            });

            if (this.chart && this.chart.stop) {
                this.chart.stop();
            }

            // Hide center text when hovering canvas (tooltip will show)
            const centerValue = canvas.parentElement.querySelector('.chart-center-value');
            if (centerValue) {
                const wrapper = canvas.parentElement;
                wrapper.addEventListener('mouseenter', () => {
                    centerValue.style.opacity = '0';
                });
                wrapper.addEventListener('mouseleave', () => {
                    centerValue.style.opacity = '1';
                });
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

