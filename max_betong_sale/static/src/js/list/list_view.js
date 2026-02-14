/** @odoo-module **/

import { registry } from "@web/core/registry";
import { OnTimeListRenderer } from "./list_renderer";
import { ClickableListRenderer } from "./list_renderer";
import { listView } from "@web/views/list/list_view";

export const onTimeListView = {
    ...listView,
    Renderer: OnTimeListRenderer,
};

export const clickableListView = {
    ...listView,
    Renderer: ClickableListRenderer,
};

registry.category("views").add("on_time_list_view", onTimeListView);
registry.category("views").add("clickable_list_renderer", clickableListView);
