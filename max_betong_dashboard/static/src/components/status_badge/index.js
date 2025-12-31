/** @odoo-module **/

import { Component } from "@odoo/owl";

const STATE_CLASSES = {
    'planned': 'status-planned',
    'dispatching': 'status-dispatching',
    'confirmed': 'status-assigned',
    'assigned': 'status-assigned',
    'loading': 'status-loading',
    'loaded': 'status-loaded',
    'leave': 'status-leave',
    'arrived': 'status-arrived',
    'unloading': 'status-unloading',
    'return': 'status-return',
    'completed': 'status-completed',
    'on_hold': 'status-on-hold',
    'dump': 'status-dump',
    'remix': 'status-remix',
    'cancel': 'status-cancelled',
    'cancelled': 'status-cancelled',
};

export class StatusBadge extends Component {
    static template = "max_betong_dashboard.StatusBadge";
    
    static props = {
        state: { type: String, required: true },
        label: { type: String, optional: true },
    };

    get stateClass() {
        return STATE_CLASSES[this.props.state] || '';
    }

    get displayLabel() {
        return this.props.label || this.props.state;
    }
}

