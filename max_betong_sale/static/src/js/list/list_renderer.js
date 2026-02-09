/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useState, onWillUnmount } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
const formatters = registry.category("formatters");

export class OnTimeListRenderer extends ListRenderer {
    setup() {
        super.setup();
    }

    get aggregates() {
        debugger;
        var aggregates = super.aggregates;
        var list = this.props.list;

        var is_late_data = list.records.filter((record) => record.data.is_late);
        var is_on_time_data = list.records.filter((record) => record.data.is_on_time);

        aggregates.is_late = {
            help: _t("Is Late (%)"),
            value: list.records.length > 0 ? `${is_late_data / list.records.length}%` : '0%',
        };
        aggregates.is_on_time = {
            help: _t("Is On Time (%)"),
            value: list.records.length > 0 ? `${is_on_time_data / list.records.length}%` : '0%',
        };
        return aggregates;
    }
}