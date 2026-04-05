/** @odoo-module **/

import { Component, useState, onWillStart, useRef, useEffect } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { Many2ManyTags } from  "@web/views/fields/relational_utils";;
export class OutputDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        
        this.state = useState({
            filters: {
                customer_partner_id: "", // Đổi từ [] thành ""
                project_id: [],          // Đổi từ [] thành ""
                subcontractor_partner_id: "",
                customer_contract_ids: ""
            },
            // Tạo thêm một biến để lưu ID thực tế phục vụ query server
            selected_ids: {
                customer_partner_id: false,
                project_id: false,
                subcontractor_partner_id: false,
                customer_contract_ids: false,
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
                customer_partner_id: this.state.selected_ids.customer_partner_id,
                project_id: this.state.filters.project_id.map(r => r.id),
                subcontractor_partner_id: this.state.selected_ids.subcontractor_partner_id,
                customer_contract_ids: this.state.selected_ids.customer_contract_ids,
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
        this.state.filters[field] = records.map(r => ({
            id: r.id,
            display_name: r.display_name || r.name,
        }));
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
// OutputDashboard.components = { Many2XAutocomplete };
OutputDashboard.components = { Many2XAutocomplete, Many2ManyTags };
registry.category("actions").add("max_betong_output_dashboard_action", OutputDashboard);
