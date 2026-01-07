/** @odoo-module **/

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class StationDropdown extends Component {
    static template = "max_betong_dashboard.StationDropdown";
    
    static props = {
        show: { type: Boolean, required: true },
        stations: { type: Array, required: true },
        selectedId: { type: [Number, { value: null }], optional: true },
        displayName: { type: String, optional: true },
        onToggle: { type: Function, required: true },
        onChange: { type: Function, required: true },
    };

    static defaultProps = {
        displayName: _t("All Vehicles"),
    };

    toggle(event) {
        event.stopPropagation();
        this.props.onToggle();
    }

    selectStation(stationId) {
        this.props.onChange(stationId);
    }

    isActive(stationId) {
        if (stationId === null) {
            return !this.props.selectedId;
        }
        return this.props.selectedId === stationId;
    }

    getAllVehiclesText() {
        return _t('All Vehicles');
    }
}

