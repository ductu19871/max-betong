/** @odoo-module **/

import { Component, useState, onWillStart, useRef, useEffect } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";

export class OutputDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        
        this.state = useState({
            filters: {
                investor_id: [],
                project_id: [],
                contractor_id: [],
                contract_id: []
            },
            data: null,
            loading: true,
        });

        this.chartRef = useRef("chartCanvas");
        this.chartInstance = null;

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadData();
        });

        useEffect(() => {
            if (this.state.data && this.chartRef.el) {
                this.renderChart();
            }
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const queryFilters = {
                investor_id: this.state.filters.investor_id.length ? this.state.filters.investor_id[0].id : false,
                project_id: this.state.filters.project_id.length ? this.state.filters.project_id[0].id : false,
                contractor_id: this.state.filters.contractor_id.length ? this.state.filters.contractor_id[0].id : false,
                contract_id: this.state.filters.contract_id.length ? this.state.filters.contract_id[0].id : false,
            };
            this.state.data = await this.orm.call("max_betong.output.dashboard", "get_dashboard_data", [], {
                filters: queryFilters
            });
        } catch (error) {
            console.error("Dashboard error:", error);
        }
        this.state.loading = false;
    }

    onFilterUpdate(field, records) {
        this.state.filters[field] = records;
        this.loadData();
    }

    renderChart() {
        if (!this.chartRef.el) return;
        
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }

        const ctx = this.chartRef.el.getContext("2d");
        // Odoo 17 normally uses ChartJS 3/4
        this.chartInstance = new Chart(ctx, {
            type: 'line',
            data: Object.assign({}, this.state.data.chart),
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        
        // Handle fallback for Chartjs 2 if applicable in environment
        if (!this.chartInstance.options.plugins) {
             this.chartInstance.options.legend = {position: 'bottom'};
             this.chartInstance.options.scales.yAxes = [{ticks: {beginAtZero: true}}];
             this.chartInstance.update();
        }
    }

    getDomain() {
        return []
    }
}

OutputDashboard.template = "max_betong_output_dashboard.Dashboard";
OutputDashboard.components = { Many2XAutocomplete };

registry.category("actions").add("max_betong_output_dashboard_action", OutputDashboard);
