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

export class OnTimeDeliveryChart extends Component {
    static template = "max_betong_dashboard_analytic.OnTimeDeliveryChart";
    static props = {
        data: { type: Number, optional: true },
        period: { type: String, optional: true },
    };

    get chartValue() {
        // props.data is already the on_time_delivery number from XML
        return typeof this.props.data === 'number' ? this.props.data : 0;
    }

    get hasData() {
        // Consider it has data if value is defined (even if 0)
        return this.props.data !== undefined && this.props.data !== null;
    }

    get debugEnabled() {
        return isChartDebugEnabled();
    }

    get debugText() {
        try {
            return JSON.stringify({ value: this.props.data ?? null }, null, 2);
        } catch (e) {
            return String(this.props.data);
        }
    }

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;
        this._lastValue = null;
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
                const currentValue = this.props.data;
                if (this._lastValue !== currentValue) {
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

        const percentage = Number(this.chartValue) || 0;

        if (typeof Chart === 'undefined') {
            this.queueRender();
            return;
        }

        if (!canvas.isConnected) {
            return;
        }

        if (this._lastValue === percentage && this.chart) {
            return;
        }

        this.destroyChart();
        this._lastValue = percentage;
        const remaining = 100 - percentage;

        try {
            this.chart = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: [_t('On Time'), _t('Late')],
                    datasets: [{
                        data: [percentage, remaining],
                        backgroundColor: ['#5DC08B', '#F5F5F5'],  // Green for on-time, light gray for late
                        borderWidth: 0,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    cutout: '70%',
                    animation: {
                        duration: 0
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) => `${context.label}: ${context.parsed}%`
                            }
                        }
                    }
                }
            });

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
            console.error('[OnTimeDelivery] Chart error:', e);
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

