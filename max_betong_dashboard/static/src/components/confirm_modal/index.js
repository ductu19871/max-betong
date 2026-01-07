/** @odoo-module **/

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class ConfirmModal extends Component {
    static template = "max_betong_dashboard.ConfirmModal";
    
    static props = {
        show: { type: Boolean, required: true },
        title: { type: String, optional: true },
        message: { type: String, optional: true },
        onConfirm: { type: Function, required: true },
        onCancel: { type: Function, required: true },
    };

    static defaultProps = {
        title: _t("Confirm"),
        message: _t("Are you sure you want to perform this action?"),
    };

    confirm() {
        this.props.onConfirm();
    }

    cancel() {
        this.props.onCancel();
    }

    getCancelText() {
        return _t('Cancel');
    }

    getConfirmText() {
        return _t('Confirm');
    }
}

