/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";

const STATE_CONFIG = {
    'assigned': {
        label: _t('Assigned'),
        color: '#B2BABB',
        icon: 'fa-circle',
        group: 'process'
    },
    'loading': {
        label: _t('Loading'),
        color: '#B2BABB',
        icon: 'fa-circle',
        group: 'process'
    },
    'loaded': {
        label: _t('Loaded'),
        color: '#B2BABB',
        icon: 'fa-circle',
        group: 'process'
    },
    'leave': {
        label: _t('Leave'),
        color: '#58D68D',
        icon: 'fa-circle',
        group: 'process'
    },
    'arrived': {
        label: _t('Arrived'),
        color: '#58D68D',
        icon: 'fa-circle',
        group: 'process'
    },
    'unloading': {
        label: _t('Unloading'),
        color: '#58D68D',
        icon: 'fa-circle',
        group: 'process'
    },
    'return': {
        label: _t('Return'),
        color: '#58D68D',
        icon: 'fa-circle',
        group: 'process'
    },
    'completed': {
        label: _t('Completed'),
        color: '#58D68D',
        icon: 'fa-circle',
        group: 'process'
    },
    'on_hold': {
        label: _t('On Hold'),
        color: '#F5B041',
        icon: 'fa-exclamation-circle',
        group: 'process'
    },
    'broken': {
        label: _t('Broken'),
        color: '#C0392B',
        icon: 'fa-times-circle',
        group: 'availability'
    },
    'not_available': {
        label: _t('Not Available'),
        color: '#C0392B',
        icon: 'fa-ban',
        group: 'availability'
    },
    'available': {
        label: _t('Available'),
        color: '#58D68D',
        icon: 'fa-check-circle',
        group: 'availability'
    },
};

const GROUP_ORDER = ['process', 'availability'];

export class SelectionStateBadgeField extends Component {
    static template = "max_betong_fleet.SelectionStateBadgeField";
    static props = {
        ...standardFieldProps,
    };
    
    setup() {
        this.state = useState({
            isOpen: false,
        });
        
        this._boundClickOutside = this.handleClickOutside.bind(this);
        this.elRef = useRef("el");
        
        onMounted(() => {
            if (this.state.isOpen) {
                document.addEventListener('click', this._boundClickOutside);
            }
        });
        
        onWillUnmount(() => {
            document.removeEventListener('click', this._boundClickOutside);
        });
    }

    get readonly() {
        return this.props?.readonly || false;
    }

    get record() {
        return this.props?.record;
    }

    get fieldName() {
        return this.props?.name;
    }

    get options() {
        if (!this.record || !this.fieldName) {
            return [];
        }
        
        const field = this.record.fields?.[this.fieldName];
        if (!field || !field.selection) {
            return [];
        }
        
        const selection = Array.isArray(field.selection) ? field.selection : [];
        
        const grouped = {};
        selection.forEach(([value, label]) => {
            if (!value) return;
            const config = STATE_CONFIG[value] || { label, color: '#999', icon: 'fa-circle', group: 'process' };
            const group = config.group || 'process';
            if (!grouped[group]) {
                grouped[group] = [];
            }
            grouped[group].push({ value, label: config.label || label, config });
        });
        
        const result = [];
        GROUP_ORDER.forEach(group => {
            if (grouped[group]) {
                result.push({ group, options: grouped[group] });
            }
        });
        
        return result;
    }

    get currentValue() {
        if (!this.record || !this.fieldName) {
            return false;
        }
        return this.record.data?.[this.fieldName] || false;
    }

    get currentConfig() {
        if (!this.currentValue) {
            return { label: '', color: '#999', icon: 'fa-circle' };
        }
        return STATE_CONFIG[this.currentValue] || { label: this.currentValue, color: '#999', icon: 'fa-circle' };
    }

    get currentLabel() {
        if (!this.currentValue) return '';
        if (!this.record || !this.fieldName) {
            return this.currentValue || '';
        }
        const field = this.record.fields?.[this.fieldName];
        if (!field || !field.selection) {
            return this.currentConfig.label || this.currentValue || '';
        }
        const selection = Array.isArray(field.selection) ? field.selection : [];
        const option = selection.find(([value]) => value === this.currentValue);
        return this.currentConfig.label || (option ? option[1] : this.currentValue);
    }

    toggleDropdown() {
        this.state.isOpen = !this.state.isOpen;
        if (this.state.isOpen) {
            setTimeout(() => {
                document.addEventListener('click', this._boundClickOutside);
            }, 0);
        } else {
            document.removeEventListener('click', this._boundClickOutside);
        }
    }

    handleClickOutside(event) {
        const el = this.elRef.el;
        if (el && !el.contains(event.target)) {
            this.state.isOpen = false;
            document.removeEventListener('click', this._boundClickOutside);
        }
    }

    selectOption(value) {
        if (this.readonly || !this.record || !this.fieldName) return;
        this.record.update({ [this.fieldName]: value });
        this.state.isOpen = false;
        document.removeEventListener('click', this._boundClickOutside);
    }

    isSelected(value) {
        return this.currentValue === value;
    }
}

registry.category("fields").add("selection_state_badge", {
    component: SelectionStateBadgeField,
});

