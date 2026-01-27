/** @odoo-module **/

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

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;
        this._lastValue = null;

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
                const currentValue = this.props.data;
                if (this._lastValue !== currentValue) {
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
        const canvas = this.canvasRef.el;
        if (!canvas) {
            console.warn('[OnTimeDelivery] Canvas not found');
            return;
        }
        
        const percentage = Number(this.chartValue) || 0;
        if (percentage === undefined || percentage === null) {
            console.warn('[OnTimeDelivery] No data available');
            return;
        }
        
        if (typeof Chart === 'undefined') {
            console.warn('[OnTimeDelivery] Chart.js not loaded yet');
            setTimeout(() => this.renderChart(), 100);
            return;
        }

        if (this._lastValue === percentage && this.chart) {
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

        this._lastValue = percentage;
        const remaining = 100 - percentage;

        try {
            this.chart = new Chart(canvas, {
                type: 'doughnut',
                data: {
                    labels: [_t('On Time'), _t('Late')],
                    datasets: [{
                        data: [percentage, remaining],
                        backgroundColor: ['#4CAF50', '#E0E0E0'],
                        borderWidth: 0,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
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

