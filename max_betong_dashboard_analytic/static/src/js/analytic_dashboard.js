/** @odoo-module **/

const DEBUG_DASHBOARD = false;
const dlog = (...args) => {
    if (DEBUG_DASHBOARD) {
        console.log(...args);
    }
};
const dwarn = (...args) => {
    if (DEBUG_DASHBOARD) {
        console.warn(...args);
    }
};

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { TripsPerVehicleChart } from "../components/trips_per_vehicle_chart/index";
import { ReturnVolumeChart } from "../components/return_volume_chart/index";
import { OnTimeDeliveryChart } from "../components/on_time_delivery_chart/index";
import { ConcreteLifetimeChart } from "../components/concrete_lifetime_chart/index";
import { VehicleCycleTimeChart } from "../components/vehicle_cycle_time_chart/index";

const isChartDebugEnabled = () => {
    try {
        if (window?.localStorage?.getItem('max_betong_chart_debug') === '1') {
            return true;
        }
        const hash = (window.location && window.location.hash) ? window.location.hash.replace(/^#/, '') : '';
        if (!hash) {
            return false;
        }
        const params = new URLSearchParams(hash);
        return params.get('chart_debug') === '1';
    } catch (e) {
        return false;
    }
};

export class AnalyticDashboard extends Component {
    static template = "max_betong_dashboard_analytic.AnalyticDashboard";
    static components = {
        TripsPerVehicleChart,
        ReturnVolumeChart,
        OnTimeDeliveryChart,
        ConcreteLifetimeChart,
        VehicleCycleTimeChart,
    };
    static props = {
        action: { type: Object, optional: true },
        actionId: { type: Number, optional: true },
        className: { type: String, optional: true },
        globalState: { type: Object, optional: true },
    };

    setup() {
        this.rpc = useService("rpc");
        this.router = useService("router");
        this.companyService = useService("company");
        this.busService = this.env.services.bus_service || useService("bus_service");

        // Get user timezone from Odoo session
        this.userTimezone = this.env.services?.user?.context?.tz || Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
        dlog('[AnalyticDashboard] User timezone:', this.userTimezone);

        this.state = useState({
            loading: true,
            data: null,
            stations: [],
            selectedStationId: null,
            selectedStationName: null,
            periodFilter: 'today',
            timeFilter: 'today',
            dateFrom: null,
            dateTo: null,
            stationDropdownOpen: false,
            periodDropdownOpen: false,
            timeFilterDropdownOpen: false,
            showCustomDatePicker: false,
            chartUpdateToken: 0,
        });
        this._subscriptionsSetup = false;
        this._loadInFlight = false;
        this._loadQueued = false;
        this._loadQueuedSource = null;
        this._loadRequestSeq = 0;
        this._routeChangeHandler = null;
        this._realtimeDebounceTimer = null;

        onWillStart(async () => {
            await this.loadData('init');
        });

        onMounted(() => {
            // Setup realtime subscriptions in onMounted to ensure bus service is ready
            if (this.busService) {
                this.setupRealtimeSubscriptions();
            }
            this.setupClickOutside();
            this.setupRouteChangeReload();
        });

        onWillUnmount(() => {
            this.cleanupSubscriptions();
            this.cleanupRouteChangeReload();
        });
    }


    setupRouteChangeReload() {
        // Company switch updates the router hash/cids; reload dashboard data when that happens.
        if (this._routeChangeHandler || !this.env?.bus) {
            return;
        }
        this._routeChangeHandler = () => {
            this.loadData('route-change');
        };
        this.env.bus.addEventListener('ROUTE_CHANGE', this._routeChangeHandler);
    }

    cleanupRouteChangeReload() {
        if (this._routeChangeHandler && this.env?.bus) {
            this.env.bus.removeEventListener('ROUTE_CHANGE', this._routeChangeHandler);
        }
        this._routeChangeHandler = null;
    }

    async loadData(source = 'unknown') {
        // Increment sequence for EVERY call. This makes this the "latest" request.
        const requestSeq = ++this._loadRequestSeq;

        // Don't load if user is in the middle of selecting custom date range
        if (this.state.periodFilter === 'custom' && this.state.showCustomDatePicker && (!this.state.dateFrom || !this.state.dateTo)) {
            return;
        }

        // Capture current filter state at request time
        const requestFilters = {
            station_id: this.state.selectedStationId || null,
            time_filter: this.state.periodFilter || 'today',
            date_from: this.state.dateFrom || null,
            date_to: this.state.dateTo || null,
        };

        try {
            // Always set loading true for the new request
            this.state.loading = true;

            // IMPORTANT: Clear data AFTER validation checks, not before
            // This prevents clearing existing data when user is still in the date picker
            // Use empty objects instead of null to avoid Owl validation errors
            this.state.data = {
                kpis: {},
                stations: this.state.stations,
                trips_per_vehicle: { data: [], labels: [], average: 0 },
                return_volume: { percentage: 0, remix: { value: 0, color: '#1976D2' }, dump: { value: 0, color: '#FB8C00' }, swap: { value: 0, color: '#43A047' } },
                on_time_delivery: 0,
                concrete_lifetime: { data: [], labels: [], average: 0 },
                vehicle_cycle_time: { average: 0, wait_time: [], delivery_time: [], labels: [] },
                debug: null,
            };

            const params = {
                ...requestFilters,
                include_debug: this.debugEnabled,
            };

            const data = await this.rpc("/concrete/analytic/get_data", params);

            // CRITICAL: Check if this is still the latest request. 
            if (requestSeq !== this._loadRequestSeq) {
                console.warn(`⚠️ [Dashboard] IGNORING STALE RESPONSE - Seq: ${requestSeq}, Latest: ${this._loadRequestSeq}`);
                return;
            }

            // CRITICAL: Verify that current filter state still matches the request we made
            // This prevents applying data from an old filter selection
            const currentFilters = {
                station_id: this.state.selectedStationId || null,
                time_filter: this.state.periodFilter || 'today',
                date_from: this.state.dateFrom || null,
                date_to: this.state.dateTo || null,
            };

            const filtersMatch =
                currentFilters.station_id === requestFilters.station_id &&
                currentFilters.time_filter === requestFilters.time_filter &&
                currentFilters.date_from === requestFilters.date_from &&
                currentFilters.date_to === requestFilters.date_to;

            if (!filtersMatch) {
                console.warn(`⚠️ [Dashboard] FILTERS CHANGED DURING REQUEST - Ignoring response`, {
                    requestedFilters: requestFilters,
                    currentFilters: currentFilters,
                });
                return;
            }

            // Normalization - use empty objects instead of null to avoid Owl validation errors
            const normalizedData = {
                kpis: data.kpis || {},
                stations: data.stations || [],
                trips_per_vehicle: data.trips_per_vehicle || { data: [], labels: [], average: 0 },
                return_volume: data.return_volume || { percentage: 0, remix: { value: 0, color: '#1976D2' }, dump: { value: 0, color: '#FB8C00' }, swap: { value: 0, color: '#43A047' } },
                on_time_delivery: data.on_time_delivery !== undefined ? data.on_time_delivery : 0,
                concrete_lifetime: data.concrete_lifetime || { data: [], labels: [], average: 0 },
                vehicle_cycle_time: data.vehicle_cycle_time || { average: 0, wait_time: [], delivery_time: [], labels: [] },
                debug: data.debug || null,
            };

            this.state.data = normalizedData;
            this.state.chartUpdateToken = (this.state.chartUpdateToken || 0) + 1; // Force remount charts
            if (data.stations) {
                this.state.stations = data.stations;
            }

        } catch (error) {
            // Only log errors for the latest request
            if (requestSeq === this._loadRequestSeq) {
                console.error(`❌ [Dashboard] ERROR - Seq: ${requestSeq}:`, error);
            }
        } finally {
            // Only turn off loading if we are still the latest request
            if (requestSeq === this._loadRequestSeq) {
                this.state.loading = false;
            }
        }
    }

    setupRealtimeSubscriptions() {
        if (!this.busService || this._subscriptionsSetup) {
            return;
        }

        try {
            // Subscribe to stations updates
            this.busService.subscribe('dashboard/stations', (payload) => {
                if (payload && payload.action === 'create') {
                    // Reload to get new stations (with current filters)
                    this.debouncedLoadData('bus-stations');
                }
            });

            // Subscribe to orders updates - reload analytics when orders change
            // loadData() will automatically use current filters (station, time filter)
            this.busService.subscribe('dashboard/orders', (payload) => {
                if (payload) {
                    // Only reload if not in custom date picker mode
                    if (!this.state.showCustomDatePicker) {
                        this.debouncedLoadData('bus-orders');
                    }
                }
            });

            // Subscribe to loads updates - reload analytics when loads change
            this.busService.subscribe('dashboard/loads', (payload) => {
                if (payload) {
                    // Only reload if not in custom date picker mode
                    if (!this.state.showCustomDatePicker) {
                        this.debouncedLoadData('bus-loads');
                    }
                }
            });

            // Subscribe to tickets updates - reload analytics when tickets change
            this.busService.subscribe('dashboard/tickets', (payload) => {
                if (payload) {
                    // Only reload if not in custom date picker mode
                    if (!this.state.showCustomDatePicker) {
                        this.debouncedLoadData('bus-tickets');
                    }
                }
            });

            // Subscribe to vehicles updates - reload analytics when vehicles change
            this.busService.subscribe('dashboard/vehicles', (payload) => {
                if (payload) {
                    // Only reload if not in custom date picker mode
                    if (!this.state.showCustomDatePicker) {
                        this.debouncedLoadData('bus-vehicles');
                    }
                }
            });

            this._subscriptionsSetup = true;
        } catch (error) {
            console.error('[AnalyticDashboard] Error setting up subscriptions:', error);
        }
    }

    /**
     * Debounced version of loadData to prevent too many rapid reloads
     * When multiple realtime updates come in quick succession, only reload once
     */
    debouncedLoadData(source = 'unknown', delay = 500) {
        // Clear existing timer
        if (this._realtimeDebounceTimer) {
            clearTimeout(this._realtimeDebounceTimer);
        }
        
        // Set new timer
        this._realtimeDebounceTimer = setTimeout(() => {
            this.loadData(source);
            this._realtimeDebounceTimer = null;
        }, delay);
    }

    cleanupSubscriptions() {
        if (this.busService && this._subscriptionsSetup) {
            try {
                this.busService.unsubscribe('dashboard/stations');
                this.busService.unsubscribe('dashboard/orders');
                this.busService.unsubscribe('dashboard/loads');
                this.busService.unsubscribe('dashboard/tickets');
                this.busService.unsubscribe('dashboard/vehicles');
                this._subscriptionsSetup = false;
            } catch (error) {
                console.error('[AnalyticDashboard] Error cleaning up subscriptions:', error);
            }
        }
        
        // Clear debounce timer
        if (this._realtimeDebounceTimer) {
            clearTimeout(this._realtimeDebounceTimer);
            this._realtimeDebounceTimer = null;
        }
    }

    setupClickOutside() {
        this._clickOutsideHandler = (event) => {
            if (!this.el) return;

            // Check if click is inside dropdown menu or button
            const filterGroup = event.target.closest('.filter-group');
            const filterBtn = event.target.closest('.filter-btn');

            // Only close if click is outside filter group (not on button)
            if (!filterGroup && !filterBtn) {
                dlog('[AnalyticDashboard] Click outside - closing dropdowns');
                if (this.state.stationDropdownOpen) {
                    this.state.stationDropdownOpen = false;
                }
                if (this.state.periodDropdownOpen) {
                    this.state.periodDropdownOpen = false;
                    this.state.showCustomDatePicker = false;
                }
                if (this.state.timeFilterDropdownOpen) {
                    this.state.timeFilterDropdownOpen = false;
                }
            }
        };
        document.addEventListener('click', this._clickOutsideHandler);
    }

    onWillUnmount() {
        if (this._clickOutsideHandler) {
            document.removeEventListener('click', this._clickOutsideHandler);
        }
        this.cleanupSubscriptions();
    }

    toggleStationDropdown(event) {
        if (event) {
            event.stopPropagation();
            event.preventDefault();
        }
        dlog('[AnalyticDashboard] toggleStationDropdown - before:', this.state.stationDropdownOpen);
        this.state.stationDropdownOpen = !this.state.stationDropdownOpen;
        dlog('[AnalyticDashboard] toggleStationDropdown - after:', this.state.stationDropdownOpen);
        this.state.periodDropdownOpen = false;
        this.state.timeFilterDropdownOpen = false;
        this.state.showCustomDatePicker = false;
    }

    selectStation(stationId, stationName) {
        dlog('[AnalyticDashboard] selectStation called:', stationId, stationName);
        if (stationId === null || stationId === undefined) {
            this.state.selectedStationId = null;
            this.state.selectedStationName = null;
        } else {
            this.state.selectedStationId = stationId;
            this.state.selectedStationName = stationName;
        }
        this.state.stationDropdownOpen = false;
        this.state.showCustomDatePicker = false;
        this.loadData('selectStation');
    }

    togglePeriodDropdown(event) {
        if (event) {
            event.stopPropagation();
            event.preventDefault();
        }
        this.state.periodDropdownOpen = !this.state.periodDropdownOpen;
        this.state.stationDropdownOpen = false;
        this.state.timeFilterDropdownOpen = false;

        // Always show the options list when opening the dropdown.
        // Only show the custom picker after user explicitly selects the custom option.
        if (this.state.periodDropdownOpen) {
            this.state.showCustomDatePicker = false;
        } else {
            this.state.showCustomDatePicker = false;
        }
    }

    selectPeriodFilter(filter) {
        dlog('[AnalyticDashboard] selectPeriodFilter called:', filter);
        this.state.periodFilter = filter;
        if (filter === 'custom') {
            if (!this.state.dateFrom && !this.state.dateTo) {
                this.state.dateFrom = null;
                this.state.dateTo = null;
            }
            this.state.showCustomDatePicker = true;
            this.state.periodDropdownOpen = true;
            dlog('[AnalyticDashboard] Custom date picker opened - NOT loading data', {
                dateFrom: this.state.dateFrom,
                dateTo: this.state.dateTo,
                showCustomDatePicker: this.state.showCustomDatePicker
            });
        } else {
            this.state.dateFrom = null;
            this.state.dateTo = null;
            this.state.showCustomDatePicker = false;
            this.state.periodDropdownOpen = false;
            dlog('[AnalyticDashboard] Period filter selected - loading data');
            this.loadData('selectPeriodFilter');
        }
    }

    toggleTimeFilterDropdown(event) {
        if (event) {
            event.stopPropagation();
            event.preventDefault();
        }
        const wasOpen = this.state.timeFilterDropdownOpen;
        this.state.timeFilterDropdownOpen = !this.state.timeFilterDropdownOpen;
        this.state.stationDropdownOpen = false;
        this.state.periodDropdownOpen = false;
    }

    selectTimeFilter(filter, dateFrom = null, dateTo = null) {
        dlog('[AnalyticDashboard] selectTimeFilter called:', filter, dateFrom, dateTo);
        this.state.timeFilter = filter;
        if (filter === 'custom') {
            // Show custom date picker instead of closing dropdown
            // Don't change dateFrom/dateTo if already set (user might be editing)
            if (!this.state.dateFrom && !this.state.dateTo) {
                this.state.dateFrom = null;
                this.state.dateTo = null;
            }
            // Set showCustomDatePicker BEFORE setting timeFilter to prevent any reactivity issues
            this.state.showCustomDatePicker = true;
            this.state.timeFilterDropdownOpen = true; // Keep dropdown open
            dlog('[AnalyticDashboard] Custom date picker opened - NOT loading data', {
                dateFrom: this.state.dateFrom,
                dateTo: this.state.dateTo,
                showCustomDatePicker: this.state.showCustomDatePicker
            });
            // Don't load data - wait for user to select dates and click Apply
        } else {
            this.state.dateFrom = dateFrom;
            this.state.dateTo = dateTo;
            this.state.showCustomDatePicker = false;
            this.state.timeFilterDropdownOpen = false;
            dlog('[AnalyticDashboard] Non-custom filter selected - loading data');
            this.loadData('selectTimeFilter');
        }
    }

    closeCustomDatePicker() {
        // Just close the picker, don't reset dates
        this.state.showCustomDatePicker = false;
        this.state.periodDropdownOpen = false;
    }

    cancelCustomDatePicker() {
        // Reset to today when user explicitly cancels
        this.state.showCustomDatePicker = false;
        this.state.periodFilter = 'today';
        this.state.dateFrom = null;
        this.state.dateTo = null;
        this.state.periodDropdownOpen = false;
        this.loadData('cancelCustomDatePicker');
    }

    applyCustomDateRange() {
        if (this.state.dateFrom && this.state.dateTo) {
            // Ensure custom mode is active
            this.state.periodFilter = 'custom';

            // If user accidentally picks an inverted range, normalize it.
            const from = new Date(this.state.dateFrom);
            const to = new Date(this.state.dateTo);
            if (!isNaN(from) && !isNaN(to) && from > to) {
                const tmp = this.state.dateFrom;
                this.state.dateFrom = this.state.dateTo;
                this.state.dateTo = tmp;
            }

            this.state.showCustomDatePicker = false;
            this.state.periodDropdownOpen = false;
            this.loadData('applyCustomDateRange');
        }
    }

    onDateFromChange(event) {
        this.state.dateFrom = event.target.value || null;
    }

    onDateToChange(event) {
        this.state.dateTo = event.target.value || null;
    }

    getStationDisplayName() {
        if (this.state.selectedStationName) {
            return this.state.selectedStationName;
        }
        return 'All';
    }

    getPeriodFilterDisplayName() {
        if (this.state.periodFilter === 'custom' && this.state.dateFrom && this.state.dateTo) {
            return this._formatCustomDateRange(this.state.dateFrom, this.state.dateTo);
        }
        const filters = {
            'today': 'Today',
            'week': 'This Week',
            'month': 'This Month',
            'quarter': 'This Quarter',
            'year': 'This Year',
            'custom': 'Custom Range',
        };
        return filters[this.state.periodFilter] || 'Select Date Range';
    }

    _formatCustomDateRange(dateFrom, dateTo) {
        // Parse datetime-local string (YYYY-MM-DDTHH:MM) as local time
        const fromDate = new Date(dateFrom);
        const toDate = new Date(dateTo);

        const formatDateTime = (date) => {
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const year = date.getFullYear();
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            return `${day}/${month}/${year} ${hours}:${minutes}`;
        };

        return `${formatDateTime(fromDate)} - ${formatDateTime(toDate)}`;
    }

    getTimeFilterDisplayName() {
        if (this.state.timeFilter === 'custom' && this.state.dateFrom && this.state.dateTo) {
            return this._formatCustomDateRange(this.state.dateFrom, this.state.dateTo);
        }
        const filters = {
            'today': 'Today',
            'week': 'This Week',
            'month': 'This Month',
            'quarter': 'This Quarter',
            'year': 'This Year',
            'custom': 'Custom Range',
        };
        return filters[this.state.timeFilter] || 'Select Date';
    }

    get data() {
        return this.state.data || {};
    }

    get kpis() {
        return this.data.kpis || {};
    }

    formatNumber(num) {
        if (num === null || num === undefined) return '0';
        const value = Number(num);
        if (isNaN(value)) return '0';
        // Format with comma as thousands separator
        return value.toLocaleString('en-US');
    }

    t(key) {
        return _t(key);
    }

    get debugEnabled() {
        const enabled = isChartDebugEnabled();
        if (enabled) {
            console.log('[AnalyticDashboard] Debug mode enabled!', {
                hasDebugData: !!this.data.debug,
                debugKeys: this.data.debug ? Object.keys(this.data.debug) : []
            });
        }
        return enabled;
    }

    get debugText() {
        try {
            const payload = {
                filters: {
                    station_id: this.state.selectedStationId || null,
                    periodFilter: this.state.periodFilter,
                    date_from: this.state.dateFrom,
                    date_to: this.state.dateTo,
                },
                data: this.state.data || null,
            };
            return JSON.stringify(payload, null, 2);
        } catch (e) {
            return String(this.state.data);
        }
    }

    openDebugView(chartKey) {
        const debugData = this.state.data?.debug?.[chartKey];
        if (!debugData) {
            console.warn(`No debug data for ${chartKey}`);
            return;
        }

        const { model, domain, record_ids, count } = debugData;

        // Open list view with domain filter
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: `Debug: ${chartKey} (${count} records)`,
            res_model: model,
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            target: 'current',
            context: {},
        });
    }
}

registry.category("actions").add("analytic_dashboard", AnalyticDashboard);

