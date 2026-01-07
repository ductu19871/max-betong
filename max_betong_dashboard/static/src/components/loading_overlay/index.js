/** @odoo-module **/

import { Component } from "@odoo/owl";

export class LoadingOverlay extends Component {
    static template = "max_betong_dashboard.LoadingOverlay";
    
    static props = {
        show: { type: Boolean, required: true },
    };
}

