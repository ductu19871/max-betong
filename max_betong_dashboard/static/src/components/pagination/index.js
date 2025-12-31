/** @odoo-module **/

import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class DashboardPagination extends Component {
    static template = "max_betong_dashboard.DashboardPagination";
    
    static props = {
        data: { type: Object, required: true }, // { page, limit, total, totalPages }
        onPageChange: { type: Function, required: true },
    };

    get showPagination() {
        return this.props.data.totalPages > 1;
    }

    get pageInfo() {
        const { page, limit, total } = this.props.data;
        const start = ((page - 1) * limit) + 1;
        const end = Math.min(page * limit, total);
        return { start, end, total };
    }

    get visiblePages() {
        const { page, totalPages } = this.props.data;
        return [...Array(totalPages).keys()]
            .map(i => i + 1)
            .filter(p => Math.abs(p - page) <= 2 || p === 1 || p === totalPages);
    }

    goToFirst() {
        this.props.onPageChange(1);
    }

    goToPrevious() {
        if (this.props.data.page > 1) {
            this.props.onPageChange(this.props.data.page - 1);
        }
    }

    goToNext() {
        if (this.props.data.page < this.props.data.totalPages) {
            this.props.onPageChange(this.props.data.page + 1);
        }
    }

    goToLast() {
        this.props.onPageChange(this.props.data.totalPages);
    }

    goToPage(pageNum) {
        this.props.onPageChange(pageNum);
    }

    onPageInputKeydown(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            this.handlePageInput(event.target);
        }
    }

    onPageInputBlur(event) {
        this.handlePageInput(event.target);
    }

    handlePageInput(inputElement) {
        const page = parseInt(inputElement.value);
        const { totalPages, page: currentPage } = this.props.data;
        
        if (isNaN(page) || page < 1) {
            inputElement.value = currentPage;
            return;
        }
        
        if (page > totalPages) {
            inputElement.value = totalPages;
            this.props.onPageChange(totalPages);
            return;
        }
        
        if (page !== currentPage) {
            this.props.onPageChange(page);
        } else {
            inputElement.value = currentPage;
        }
    }

    getPaginationInfoText() {
        const { start, end, total } = this.pageInfo;
        return `${_t('Showing')} ${start} - ${end} ${_t('of')} ${total} ${_t('records')}`;
    }

    getPageLabelText() {
        return _t('Page:');
    }
}

