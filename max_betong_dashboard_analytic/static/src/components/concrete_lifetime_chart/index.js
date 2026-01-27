/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { loadBundle } from "@web/core/assets";
import { Component, onWillStart, onMounted, onWillUnmount, onPatched, useRef } from "@odoo/owl";

export class ConcreteLifetimeChart extends Component {
    static template = "max_betong_dashboard_analytic.ConcreteLifetimeChart";
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
            console.log('[ConcreteLifetime] onMounted - hasData:', this.hasData, 'data:', this.chartData);
            setTimeout(() => {
                console.log('[ConcreteLifetime] onMounted timeout - hasData:', this.hasData);
                if (this.hasData) {
                    this.renderChart();
                }
            }, 200);
        });

        onPatched(() => {
            console.log('[ConcreteLifetime] onPatched - hasData:', this.hasData, 'data:', this.chartData);
            if (this.hasData) {
                const currentData = JSON.stringify(this.chartData);
                if (this._lastData !== currentData) {
                    console.log('[ConcreteLifetime] onPatched - data changed, re-rendering');
                    setTimeout(() => this.renderChart(), 50);
                }
            } else if (this.chart) {
                console.log('[ConcreteLifetime] onPatched - no data, destroying chart');
                this.destroyChart();
            }
        });

        onWillUnmount(() => {
            this.destroyChart();
        });
    }

    renderChart() {
        console.log('[ConcreteLifetime] renderChart called, chartData:', this.chartData);
        const canvas = this.canvasRef.el;
        if (!canvas) {
            console.warn('[ConcreteLifetime] Canvas not found');
            return;
        }
        
        const chartData = this.chartData;
        if (!chartData || !Array.isArray(chartData.data)) {
            console.warn('[ConcreteLifetime] No data available', chartData);
            return;
        }
        
        console.log('[ConcreteLifetime] All checks passed, creating chart...');
        
        if (typeof Chart === 'undefined') {
            console.warn('[ConcreteLifetime] Chart.js not loaded yet');
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
        if (!data.data || data.data.length === 0) {
            return;
        }

        this._lastData = currentData;
        const labels = Array.from({ length: data.data.length }, (_, i) => `V${i + 201}`);

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
                            max: 100,
                            ticks: {
                                stepSize: 10,
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

