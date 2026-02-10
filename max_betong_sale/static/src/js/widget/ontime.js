/** @odoo-module **/

import { Component } from '@odoo/owl';
import { BooleanField } from "@web/views/fields/boolean/boolean_field";
import { registry } from '@web/core/registry';
import { _t } from "@web/core/l10n/translation";

export class OntimeComponent extends Component {
    static template = 'max_betong_sale.ontime';

    get getTitle() {
        let fieldName = this.props.name;
        let record = this.props.record;

        if (fieldName === 'is_late' && record.data.is_late) {
            return _t('Late');
        }
        if (fieldName === 'is_on_time' && record.data.is_on_time) {
            return _t('On Time');
        }
        return '';
    }

    get getBadgeClass() {
        let fieldName = this.props.name;
        let record = this.props.record;

        if (fieldName === 'is_late' && record.data.is_late) {
            return 'danger';
        }
        if (fieldName === 'is_on_time' && record.data.is_on_time) {
            return 'success';
        }
        return '';
    }
}

export const ontimeWidget = {
    ...BooleanField,
    component: OntimeComponent,
};

registry.category('fields').add('ontime', ontimeWidget);
