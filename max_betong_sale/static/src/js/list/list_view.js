/** @odoo-module **/

import { registry } from "@web/core/registry";
import { OnTimeListRenderer } from "./list_renderer";
import { listView } from "@web/views/list/list_view";

export const onTimeListView = {
    ...listView,
    Renderer: OnTimeListRenderer,
};

registry.category("views").add("on_time_list_view", onTimeListView);
