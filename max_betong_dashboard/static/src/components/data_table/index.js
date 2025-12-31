/** @odoo-module **/

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class DataTableHeader extends Component {
    static template = "max_betong_dashboard.DataTableHeader";
    
    static props = {
        columns: { type: Array, required: true },
        sortField: { type: String, optional: true },
        sortOrder: { type: String, optional: true }, // 'asc' | 'desc'
        sortableColumns: { type: Object, optional: true }, // Set-like object
        onSort: { type: Function, optional: true },
        onResize: { type: Function, optional: true },
        onDragStart: { type: Function, optional: true },
        onDrop: { type: Function, optional: true },
    };

    static defaultProps = {
        sortOrder: 'asc',
        sortableColumns: {},
    };

    isSortable(columnKey) {
        return this.props.sortableColumns[columnKey] === true;
    }

    getSortIcon(columnKey) {
        if (this.props.sortField === columnKey) {
            return this.props.sortOrder === 'asc' ? 'fa fa-sort-up' : 'fa fa-sort-down';
        }
        return 'fa fa-sort';
    }

    onColumnClick(columnKey) {
        if (this.isSortable(columnKey) && this.props.onSort) {
            this.props.onSort(columnKey);
        }
    }

    onResizeStart(event, columnKey) {
        if (this.props.onResize) {
            this.props.onResize(event, columnKey);
        }
    }

    onDragStart(event, columnKey) {
        if (this.props.onDragStart) {
            this.props.onDragStart(event, columnKey);
        }
    }

    onDrop(event, columnKey) {
        if (this.props.onDrop) {
            this.props.onDrop(event, columnKey);
        }
    }

    getResizeTitle() {
        return _t('Drag to resize width');
    }
}

// Empty State Component
export class EmptyState extends Component {
    static template = "max_betong_dashboard.EmptyState";
    
    static props = {
        icon: { type: String, optional: true },
        message: { type: String, optional: true },
        colspan: { type: Number, optional: true },
    };

    static defaultProps = {
        icon: "fa fa-inbox",
        message: _t("No data"),
        colspan: 1,
    };
}

