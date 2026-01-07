/** @odoo-module **/

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class SearchInput extends Component {
    static template = "max_betong_dashboard.SearchInput";
    
    static props = {
        placeholder: { type: String, optional: true },
        value: { type: String, optional: true },
        onInput: { type: Function, required: true },
        size: { type: String, optional: true }, // 'normal' | 'small'
    };

    static defaultProps = {
        placeholder: _t("Search..."),
        value: "",
        size: "normal",
    };

    onInputChange(event) {
        this.props.onInput(event);
    }
}

