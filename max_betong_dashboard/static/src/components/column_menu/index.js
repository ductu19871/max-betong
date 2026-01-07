/** @odoo-module **/

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class ColumnMenu extends Component {
    static template = "max_betong_dashboard.ColumnMenu";
    
    static props = {
        show: { type: Boolean, required: true },
        columns: { type: Array, required: true },
        position: { type: Object, optional: true }, // { x, y }
        onToggleVisibility: { type: Function, required: true },
        onReset: { type: Function, required: true },
        onClose: { type: Function, required: true },
    };

    static defaultProps = {
        position: { x: 0, y: 0 },
    };

    get style() {
        return `left: ${this.props.position.x}px; top: ${this.props.position.y}px;`;
    }

    toggleColumn(columnKey) {
        this.props.onToggleVisibility(columnKey);
    }

    reset() {
        this.props.onReset();
    }

    close(event) {
        // Close when clicking the close button
        if (event?.target.closest('.column-menu-close')) {
            this.props.onClose();
            return;
        }
        // Don't close when clicking inside the menu
        if (event?.target.closest('.column-menu')) {
            return;
        }
        this.props.onClose();
    }

    getCustomizeColumnsText() {
        return _t('Customize Columns');
    }

    getResetToDefaultText() {
        return _t('Reset to Default');
    }
}

