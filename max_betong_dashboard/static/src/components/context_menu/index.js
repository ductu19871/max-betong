/** @odoo-module **/

import { Component } from "@odoo/owl";

export class ContextMenu extends Component {
    static template = "max_betong_dashboard.ContextMenu";
    
    static props = {
        show: { type: Boolean, required: true },
        position: { type: Object, optional: true }, // { x, y }
        items: { type: Array, required: true }, // [{ label, icon, action, danger }]
    };

    static defaultProps = {
        position: { x: 0, y: 0 },
    };

    get style() {
        return `left: ${this.props.position.x}px; top: ${this.props.position.y}px;`;
    }

    onItemClick(item) {
        if (item.action) {
            item.action();
        }
    }
}

