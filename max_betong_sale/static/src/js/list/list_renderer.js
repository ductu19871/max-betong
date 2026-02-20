/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useState, onWillUnmount } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
const formatters = registry.category("formatters");

export class ClickableListRenderer extends ListRenderer {
    setup() {
        super.setup();
    }

    async onCellClicked(record, column, ev) {
        if (column.name === "name") {
            this.env.services.action.doAction({
                type: "ir.actions.act_window",
                res_model: "mrp.production",
                res_id: record.resId,
                views: [[false, "form"]],
            });
            return;
        }
        super.onCellClicked(record, column, ev);
    }

    getCellClass(column, record) {
        var cellClass = super.getCellClass(column, record);

        if (column.name === "name") {
            cellClass += " custom_clickable_cell";
        }
        return cellClass;
    }
}

export class OnTimeListRenderer extends ClickableListRenderer {
    setup() {
        super.setup();
    }

    get aggregates() {
        var aggregates = super.aggregates;
        var list = this.props.list;
        var is_late_data = list.records.filter((record) => record.data.is_late);
        var is_on_time_data = list.records.filter((record) => record.data.is_on_time);
        aggregates.is_late = {
            help: _t("Late (%)"),
            value: list.records.length > 0 ? `${(is_late_data.length / list.records.length * 100).toFixed(2)}%` : '0%',
        };
        aggregates.is_on_time = {
            help: _t("On time (%)"),
            value: list.records.length > 0 ? `${(is_on_time_data.length / list.records.length * 100).toFixed(2)}%` : '0%',
        };
        return aggregates;
    }
}