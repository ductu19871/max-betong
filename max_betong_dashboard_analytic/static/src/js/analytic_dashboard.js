/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { TripsPerVehicleChart } from "../components/trips_per_vehicle_chart/index";
import { ReturnVolumeChart } from "../components/return_volume_chart/index";
import { OnTimeDeliveryChart } from "../components/on_time_delivery_chart/index";
import { ConcreteLifetimeChart } from "../components/concrete_lifetime_chart/index";
import { VehicleCycleTimeChart } from "../components/vehicle_cycle_time_chart/index";

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
        this.busService = this.env.services.bus_service || useService("bus_service");
        this.state = useState({
            loading: true,
            data: null,
            stations: [],
            selectedStationId: null,
            selectedStationName: null,
            timeFilter: 'today',
            dateFrom: null,
            dateTo: null,
            stationDropdownOpen: false,
            timeFilterDropdownOpen: false,
            showCustomDatePicker: false,
        });
        this._subscriptionsSetup = false;

        onWillStart(async () => {
            await this.loadData();
        });

        onMounted(() => {
            this.setupRealtimeSubscriptions();
            this.setupClickOutside();
        });

        onWillUnmount(() => {
            this.cleanupSubscriptions();
        });
    }

    async loadData() {
        // Don't load if user is in the middle of selecting custom date range (no dates selected yet)
        if (this.state.timeFilter === 'custom' && this.state.showCustomDatePicker && (!this.state.dateFrom || !this.state.dateTo)) {
            console.log('[AnalyticDashboard] Skipping loadData - user selecting custom date range', {
                timeFilter: this.state.timeFilter,
                showCustomDatePicker: this.state.showCustomDatePicker,
                dateFrom: this.state.dateFrom,
                dateTo: this.state.dateTo
            });
            return;
        }
        
        try {
            this.state.loading = true;
            const params = {
                station_id: this.state.selectedStationId || null,
                time_filter: this.state.timeFilter || 'today',
                date_from: this.state.dateFrom || null,
                date_to: this.state.dateTo || null,
            };
            console.log('[AnalyticDashboard] loadData called with params:', params);
            const data = await this.rpc("/concrete/analytic/get_data", params);
            console.log('[AnalyticDashboard] Data loaded:', data);
            this.state.data = data;
            if (data.stations) {
                this.state.stations = data.stations;
            }
        } catch (error) {
            console.error("Error loading analytics data:", error);
        } finally {
            this.state.loading = false;
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
                    // Only reload stations list, don't reload all data
                    this.loadData(); // Reload to get new stations
                }
            });
            
            // Subscribe to relevant model updates - only reload if not in custom date picker mode
            this.busService.subscribe('dashboard/orders', () => {
                if (!this.state.showCustomDatePicker) {
                    this.loadData();
                }
            });
            
            this.busService.subscribe('dashboard/tickets', () => {
                if (!this.state.showCustomDatePicker) {
                    this.loadData();
                }
            });
            
            this.busService.subscribe('dashboard/vehicles', () => {
                if (!this.state.showCustomDatePicker) {
                    this.loadData();
                }
            });
            
            this._subscriptionsSetup = true;
        } catch (error) {
            console.error('[AnalyticDashboard] Error setting up subscriptions:', error);
        }
    }

    cleanupSubscriptions() {
        if (this.busService && this._subscriptionsSetup) {
            try {
                this.busService.unsubscribe('dashboard/stations');
                this.busService.unsubscribe('dashboard/orders');
                this.busService.unsubscribe('dashboard/tickets');
                this.busService.unsubscribe('dashboard/vehicles');
            } catch (error) {
                // Ignore
            }
            this._subscriptionsSetup = false;
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
                console.log('[AnalyticDashboard] Click outside - closing dropdowns');
                if (this.state.stationDropdownOpen) {
                    this.state.stationDropdownOpen = false;
                }
                if (this.state.timeFilterDropdownOpen) {
                    this.state.timeFilterDropdownOpen = false;
                    this.state.showCustomDatePicker = false;
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
        console.log('[AnalyticDashboard] toggleStationDropdown - before:', this.state.stationDropdownOpen);
        this.state.stationDropdownOpen = !this.state.stationDropdownOpen;
        console.log('[AnalyticDashboard] toggleStationDropdown - after:', this.state.stationDropdownOpen);
        this.state.timeFilterDropdownOpen = false;
        this.state.showCustomDatePicker = false;
    }

    selectStation(stationId, stationName) {
        console.log('[AnalyticDashboard] selectStation called:', stationId, stationName);
        if (stationId === null || stationId === undefined) {
            this.state.selectedStationId = null;
            this.state.selectedStationName = null;
        } else {
            this.state.selectedStationId = stationId;
            this.state.selectedStationName = stationName;
        }
        this.state.stationDropdownOpen = false;
        this.state.showCustomDatePicker = false;
        this.loadData();
    }

    toggleTimeFilterDropdown(event) {
        if (event) {
            event.stopPropagation();
        }
        const wasOpen = this.state.timeFilterDropdownOpen;
        this.state.timeFilterDropdownOpen = !this.state.timeFilterDropdownOpen;
        this.state.stationDropdownOpen = false;
        
        // If opening dropdown and already have custom date selected, show date picker
        if (this.state.timeFilterDropdownOpen && this.state.timeFilter === 'custom' && this.state.dateFrom && this.state.dateTo) {
            this.state.showCustomDatePicker = true;
        } else if (!this.state.timeFilterDropdownOpen) {
            // Only reset if closing dropdown and user didn't apply
            // Don't reset if we're just toggling
            this.state.showCustomDatePicker = false;
        }
    }

    selectTimeFilter(filter, dateFrom = null, dateTo = null) {
        console.log('[AnalyticDashboard] selectTimeFilter called:', filter, dateFrom, dateTo);
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
            console.log('[AnalyticDashboard] Custom date picker opened - NOT loading data', {
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
            console.log('[AnalyticDashboard] Non-custom filter selected - loading data');
            this.loadData();
        }
    }

    closeCustomDatePicker() {
        // Just close the picker, don't reset dates
        this.state.showCustomDatePicker = false;
        this.state.timeFilterDropdownOpen = false;
    }
    
    cancelCustomDatePicker() {
        // Reset to today when user explicitly cancels
        this.state.showCustomDatePicker = false;
        this.state.timeFilter = 'today';
        this.state.dateFrom = null;
        this.state.dateTo = null;
        this.state.timeFilterDropdownOpen = false;
        this.loadData();
    }

    applyCustomDateRange() {
        if (this.state.dateFrom && this.state.dateTo) {
            this.state.showCustomDatePicker = false;
            this.state.timeFilterDropdownOpen = false;
            this.loadData();
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
        return _t('All Stations');
    }

    getTimeFilterDisplayName() {
        if (this.state.timeFilter === 'custom' && this.state.dateFrom && this.state.dateTo) {
            // Format dates for display
            const fromDate = new Date(this.state.dateFrom);
            const toDate = new Date(this.state.dateTo);
            const formatDate = (date) => {
                const day = String(date.getDate()).padStart(2, '0');
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const year = date.getFullYear();
                return `${day}/${month}/${year}`;
            };
            return `${formatDate(fromDate)} - ${formatDate(toDate)}`;
        }
        const filters = {
            'today': _t('Today'),
            'week': _t('This Week'),
            'month': _t('This Month'),
            'quarter': _t('This Quarter'),
            'year': _t('This Year'),
            'custom': _t('Custom Date Range'),
        };
        return filters[this.state.timeFilter] || _t('Select Date');
    }

    get data() {
        return this.state.data || {};
    }

    get kpis() {
        return this.data.kpis || {};
    }

    t(key) {
        return _t(key);
    }
}

registry.category("actions").add("analytic_dashboard", AnalyticDashboard);

