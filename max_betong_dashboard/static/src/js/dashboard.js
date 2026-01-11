/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";


// Import reusable components
import { SearchInput } from "@max_betong_dashboard/components/search_input/index";
import { DashboardPagination } from "@max_betong_dashboard/components/pagination/index";
import { ConfirmModal } from "@max_betong_dashboard/components/confirm_modal/index";
import { ColumnMenu } from "@max_betong_dashboard/components/column_menu/index";
import { StationDropdown } from "@max_betong_dashboard/components/station_dropdown/index";
import { ContextMenu } from "@max_betong_dashboard/components/context_menu/index";
import { StatusBadge } from "@max_betong_dashboard/components/status_badge/index";
import { ProgressDots } from "@max_betong_dashboard/components/progress_dots/index";
import { LoadingOverlay } from "@max_betong_dashboard/components/loading_overlay/index";
import { DataTableHeader, EmptyState } from "@max_betong_dashboard/components/data_table/index";

// ===== Constants =====
const DEFAULT_LIMIT = 4;
const FULLSCREEN_LIMIT = 20;

const PROGRESS_COLUMNS = new Set(['assigned', 'loading', 'loaded', 'leave', 'arrived', 'unloading', 'return', 'completed']);

const SORTABLE_COLUMNS = {
    tickets: { name: true, delivery_address: true, sale_order: true, product: true, mix_note: true, station: true, volume: true, vehicle: true, eta: true, state: true },
    loads: { name: true, delivery_address: true, sale_order: true, product: true, mix_note: true, station: true, volume: true },
    orders: { name: true, delivery_address: true, product: true, mix_note: true, station: true, volume: true, volume_allocated: true, volume_unallocated: true, state: true, volume_delivered: true },
    vehicles: {},
};

const STATE_CLASSES = {
    'planned': 'status-planned',
    'dispatching': 'status-dispatching',
    'confirmed': 'status-assigned',
    'assigned': 'status-assigned',
    'loading': 'status-loading',
    'loaded': 'status-loaded',
    'leave': 'status-leave',
    'arrived': 'status-arrived',
    'unloading': 'status-unloading',
    'return': 'status-return',
    'completed': 'status-completed',
    'on_hold': 'status-on-hold',
    'dump': 'status-dump',
    'remix': 'status-remix',
    'cancel': 'status-cancelled',
    'cancelled': 'status-cancelled',
};

// ===== Default Column Configurations =====
const DEFAULT_COLUMNS = {
    tickets: [
        { key: 'stt', label: 'No.', visible: true, width: 60, order: 0 },
        { key: 'name', label: 'Ticket Code', visible: true, width: 120, order: 1 },
        { key: 'delivery_address', label: 'Construction Site Address', visible: true, width: 150, order: 2 },
        { key: 'sale_order', label: 'SO', visible: true, width: 100, order: 3 },
        { key: 'product', label: 'Product', visible: true, width: 150, order: 4 },
        { key: 'mix_note', label: 'Mix Note', visible: true, width: 150, order: 5 },
        { key: 'station', label: 'Station', visible: true, width: 80, order: 6 },
        { key: 'volume', label: 'Volume (m³)', visible: true, width: 100, order: 7 },
        { key: 'vehicle', label: 'Vehicle', visible: true, width: 120, order: 8 },
        { key: 'eta', label: 'ETA', visible: true, width: 120, order: 9 },
        { key: 'state', label: 'State', visible: true, width: 120, order: 10 },
        { key: 'assigned', label: 'Assigned', visible: true, width: 80, order: 11 },
        { key: 'loading', label: 'Loading', visible: true, width: 80, order: 12 },
        { key: 'loaded', label: 'Loaded', visible: true, width: 80, order: 13 },
        { key: 'leave', label: 'Leave', visible: true, width: 80, order: 14 },
        { key: 'arrived', label: 'Arrived', visible: true, width: 80, order: 15 },
        { key: 'unloading', label: 'Unloading', visible: true, width: 80, order: 16 },
        { key: 'return', label: 'Return', visible: true, width: 80, order: 17 },
        { key: 'completed', label: 'Completed', visible: true, width: 80, order: 18 },
    ],
    orders: [
        { key: 'stt', label: 'No.', visible: true, width: 60, order: 0 },
        { key: 'name', label: 'SO', visible: true, width: 100, order: 1 },
        { key: 'delivery_address', label: 'Construction Site Address', visible: true, width: 150, order: 2 },
        { key: 'product', label: 'Product', visible: true, width: 150, order: 3 },
        { key: 'mix_note', label: 'Mix Note', visible: true, width: 150, order: 4 },
        { key: 'station', label: 'Station', visible: true, width: 100, order: 5 },
        { key: 'volume', label: 'Volume (m³)', visible: true, width: 120, order: 6 },
        { key: 'volume_allocated', label: 'Allocated Volume (m³)', visible: true, width: 150, order: 7 },
        { key: 'volume_unallocated', label: 'Unallocated Volume (m³)', visible: true, width: 150, order: 8 },
        { key: 'state', label: 'State', visible: true, width: 120, order: 9 },
        { key: 'volume_delivered', label: 'Delivered Volume (m³)', visible: true, width: 120, order: 10 },
        { key: 'action', label: 'Action', visible: true, width: 120, order: 11 },
    ],
    loads: [
        { key: 'stt', label: 'No.', visible: true, width: 60, order: 0 },
        { key: 'name', label: 'Load Code', visible: true, width: 120, order: 1 },
        { key: 'delivery_address', label: 'Construction Site Address', visible: true, width: 150, order: 2 },
        { key: 'sale_order', label: 'SO', visible: true, width: 100, order: 3 },
        { key: 'product', label: 'Product', visible: true, width: 150, order: 4 },
        { key: 'mix_note', label: 'Mix Note', visible: true, width: 150, order: 5 },
        { key: 'station', label: 'Station', visible: true, width: 100, order: 6 },
        { key: 'volume', label: 'Volume (m³)', visible: true, width: 120, order: 7 },
    ],
    vehicles: [
        { key: 'stt', label: 'No.', visible: true, width: 60, order: 0 },
        { key: 'license_plate', label: 'Vehicle Code', visible: true, width: 120, order: 1 },
        { key: 'station', label: 'Station', visible: true, width: 100, order: 2 },
        { key: 'state_concrete', label: 'State', visible: true, width: 120, order: 3 },
    ],
};

// ===== Utility Functions =====
function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

function loadColumnConfig(tableName) {
    try {
        const saved = localStorage.getItem(`dashboard_columns_${tableName}`);
        if (saved) {
            const parsed = JSON.parse(saved);
            const defaults = DEFAULT_COLUMNS[tableName];
            return defaults.map(col => {
                const savedCol = parsed.find(c => c.key === col.key);
                return savedCol ? { ...col, ...savedCol, label: col.label } : col;
            });
        }
    } catch (e) {
        console.error('Error loading column config:', e);
    }
    return deepClone(DEFAULT_COLUMNS[tableName]);
}

function saveColumnConfig(tableName, columns) {
    try {
        localStorage.setItem(`dashboard_columns_${tableName}`, JSON.stringify(columns));
    } catch (e) {
        console.error('Error saving column config:', e);
    }
}

// ===== Main Dashboard Component =====
export class ConcreteDashboard extends Component {
    static template = "max_betong_dashboard.ConcreteDashboard";
    static props = {
        action: { type: Object, optional: true },
        actionId: { type: Number, optional: true },
        className: { type: String, optional: true },
        globalState: { type: Object, optional: true },
    };

    // Register child components
    static components = {
        SearchInput,
        DashboardPagination,
        ConfirmModal,
        ColumnMenu,
        StationDropdown,
        ContextMenu,
        StatusBadge,
        ProgressDots,
        LoadingOverlay,
        DataTableHeader,
        EmptyState,
    };

    setup() {
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.busService = this.env.services.bus_service || useService("bus_service");
        
        this._realtimeCallbacks = {};
        if (this.busService) {
            this.setupRealtimeSubscriptions();
        }
        
        // Bound event handlers
        this._boundHandleClickOutside = this.handleClickOutside.bind(this);
        this._boundCloseContextMenu = this.closeContextMenu.bind(this);
        this._boundCloseColumnMenu = this.closeColumnMenu.bind(this);

        // Initialize state
        this.state = useState({
            loading: true,
            
            // Station filter
            selectedStation: null, // For orders/loads (if needed in future)
            selectedVehicleStation: null, // For vehicles only
            stations: [],
            vehicleStationFilterDropdown: { show: false },
            
            // Column configurations
            ticketsColumns: loadColumnConfig('tickets'),
            ordersColumns: loadColumnConfig('orders'),
            loadsColumns: loadColumnConfig('loads'),
            vehiclesColumns: loadColumnConfig('vehicles'),
            
            // Column customization state
            columnMenu: { show: false, table: null, x: 0, y: 0 },
            draggingColumn: null,
            
            // Table states
            orders: { data: [], total: 0, page: 1, limit: DEFAULT_LIMIT, totalPages: 1 },
            loads: { data: [], total: 0, page: 1, limit: DEFAULT_LIMIT, totalPages: 1 },
            vehicles: { data: [], total: 0, page: 1, limit: DEFAULT_LIMIT, totalPages: 1 },
            tickets: { data: [], total: 0, page: 1, limit: DEFAULT_LIMIT, totalPages: 1 },
            
            // Selection states
            selectedOrderId: null,
            selectedLoads: [],
            selectedVehicle: null,
            
            // Fullscreen states
            ordersFullscreen: false,
            loadsFullscreen: false,
            vehiclesFullscreen: false,
            ticketsFullscreen: false,
            
            // Column backups
            ordersColumnsBackup: null,
            loadsColumnsBackup: null,
            vehiclesColumnsBackup: null,
            ticketsColumnsBackup: null,
            
            // Search states
            ordersSearch: "",
            loadsSearch: "",
            vehiclesSearch: "",
            ticketsSearch: "",
            
            // Sort states
            ordersSort: { field: 'name', order: 'asc' },
            loadsSort: { field: 'name', order: 'asc' },
            ticketsSort: { field: 'name', order: 'desc' },
            
            // Context menu
            contextMenu: { show: false, x: 0, y: 0, loadId: null },
            
            // Station dropdown for editing
            stationDropdown: { show: false, type: null, id: null, x: 0, y: 0 },
            
            // Vehicle station dropdown
            vehicleStationDropdown: { show: false, vehicleId: null, x: 0, y: 0 },
            
            // Vehicle state dropdown
            vehicleStateDropdown: { show: false, vehicleId: null, x: 0, y: 0 },
            
            // Confirmation modal
            confirmModal: { show: false, title: '', message: '', action: null },
            
            // User permissions
            permissions: {
                can_view: true,
                can_assign_ticket: false,
                can_split_load: false,
                can_edit: false,
                can_delete: false,
            },
        });

        onWillStart(async () => {
            await this.loadPermissions();
            await this.loadStations();
            await this.loadAllData();
        });
        
        onMounted(() => {
            document.addEventListener('click', this._boundCloseContextMenu);
            document.addEventListener('click', this._boundCloseColumnMenu);
            document.addEventListener('click', this._boundHandleClickOutside);
            this.fixOdooScrolling();
            
            if (this.busService) {
                this.setupRealtimeSubscriptions();
            }
        });


        onWillUnmount(() => {
            document.removeEventListener('click', this._boundCloseContextMenu);
            document.removeEventListener('click', this._boundCloseColumnMenu);
            document.removeEventListener('click', this._boundHandleClickOutside);
            this._subscriptionsSetup = false;
        });
    }

    // ===== Event Handlers for Click Outside =====
    
    handleClickOutside(event) {
        if (this.state.stationDropdown.show) {
            const dropdown = event.target.closest('.station-dropdown-menu');
            if (!dropdown) {
                this.state.stationDropdown.show = false;
            }
        }
        if (this.state.vehicleStationDropdown.show) {
            const dropdown = event.target.closest('.station-dropdown-menu');
            if (!dropdown) {
                this.state.vehicleStationDropdown.show = false;
            }
        }
        if (this.state.vehicleStateDropdown.show) {
            const dropdown = event.target.closest('.state-dropdown-menu');
            if (!dropdown) {
                this.state.vehicleStateDropdown.show = false;
            }
        }
        if (this.state.columnMenu.show) {
            this.state.columnMenu.show = false;
        }
    }

    closeContextMenu() {
        this.state.contextMenu.show = false;
        this.state.stationDropdown.show = false;
    }

    closeColumnMenu(event) {
        if (event?.target.closest('.column-menu-close')) {
            this.state.columnMenu.show = false;
            return;
        }
        if (event?.target.closest('.column-menu')) {
            return;
        }
        this.state.columnMenu.show = false;
    }

    // ===== Odoo Scrolling Fix =====
    
    fixOdooScrolling() {
        const fixScroll = () => {
            const actionManager = document.querySelector('.o_action_manager');
            if (!actionManager) return;
            
            const containers = [
                { el: actionManager, styles: { height: 'auto', maxHeight: 'none', overflowY: 'auto' } },
                { el: actionManager.querySelector('.o_action'), styles: { height: 'auto', maxHeight: 'none', overflowY: 'auto', overflowX: 'hidden' } },
                { el: actionManager.querySelector('.o_controller'), styles: { height: 'auto', maxHeight: 'none', overflowY: 'visible', overflowX: 'hidden' } },
                { el: actionManager.querySelector('.o_content'), styles: { height: 'auto', maxHeight: 'none', minHeight: 'auto', overflowY: 'visible', overflowX: 'hidden' } },
            ];
            
            containers.forEach(({ el, styles }) => {
                if (el) Object.assign(el.style, styles);
            });
            
            const dashboard = actionManager.querySelector('.concrete-dashboard');
            if (dashboard?.parentElement) {
                Object.assign(dashboard.parentElement.style, { height: 'auto', maxHeight: 'none', overflowY: 'visible' });
            }
        };
        
        fixScroll();
        setTimeout(fixScroll, 100);
        setTimeout(fixScroll, 500);
    }

    // ===== Realtime Subscriptions =====
    
    setupRealtimeSubscriptions() {
        if (!this.busService || this._subscriptionsSetup) {
            return;
        }
        
        try {
            this.busService.subscribe('dashboard/orders', (payload) => {
                if (payload) {
                    this.handleRealtimeUpdate('orders', payload);
                }
            });
            
            this.busService.subscribe('dashboard/loads', (payload) => {
                if (payload) {
                    this.handleRealtimeUpdate('loads', payload);
                }
            });
            
            this.busService.subscribe('dashboard/vehicles', (payload) => {
                if (payload) {
                    this.handleRealtimeUpdate('vehicles', payload);
                }
            });
            
            this.busService.subscribe('dashboard/tickets', (payload) => {
                if (payload) {
                    this.handleRealtimeUpdate('tickets', payload);
                }
            });
            
            this._subscriptionsSetup = true;
        } catch (error) {
            console.error('[Realtime] Error setting up subscriptions:', error);
        }
    }

    /**
     * Handle realtime update from bus notification
     * @param {string} tableName - Name of the table (orders, loads, vehicles, tickets)
     * @param {Object} payload - Notification payload containing action, data, etc.
     */
    handleRealtimeUpdate(tableName, payload) {
        if (!payload) return;
        
        const { action, record_id, data, affects_filter, changed_fields } = payload;
        const hasActiveSearch = this.hasActiveSearchOrFilter(tableName);
        
        if (action === 'create' || action === 'delete') {
            this.reloadTable(tableName);
            return;
        }
        
        if (action === 'update') {
            // For vehicles, if state_concrete changes, always reload to maintain sorting
            if (tableName === 'vehicles' && changed_fields && changed_fields.includes('state_concrete')) {
                this.reloadTable(tableName);
                return;
            }
            
            if (hasActiveSearch && affects_filter) {
                this.reloadTable(tableName);
            } else {
                this.updateRecordInline(tableName, record_id, data);
            }
        }
    }

    hasActiveSearchOrFilter(tableName) {
        const searchKey = `${tableName}Search`;
        const hasSearch = this.state[searchKey] && this.state[searchKey].trim() !== '';
        
        // Orders should not be affected by vehicle station filter
        if (tableName === 'orders') {
            return hasSearch;
        }
        
        // Loads and tickets can have station filter (if needed in future)
        if (tableName === 'loads') {
            const hasStationFilter = this.state.selectedStation !== null;
            return hasSearch || hasStationFilter || this.state.selectedOrderId !== null;
        }
        
        if (tableName === 'tickets') {
            const hasStationFilter = this.state.selectedStation !== null;
            return hasSearch || hasStationFilter;
        }
        
        // Vehicles use selectedVehicleStation
        if (tableName === 'vehicles') {
            const hasVehicleStationFilter = this.state.selectedVehicleStation !== null;
            return hasSearch || hasVehicleStationFilter;
        }
        
        return hasSearch;
    }

    async reloadTable(tableName) {
        await this.loadTableData(tableName);
    }

    updateRecordInline(tableName, recordId, newData) {
        if (!newData) return;
        
        const tableState = this.state[tableName];
        if (!tableState || !tableState.data) return;
        
        const recordIndex = tableState.data.findIndex(item => item.id === recordId);
        
        if (recordIndex !== -1) {
            const currentData = [...tableState.data];
            currentData[recordIndex] = { ...currentData[recordIndex], ...newData };
            this.state[tableName].data = currentData;
        } else {
            this.reloadTable(tableName);
        }
    }

    insertRecordRealtime(tableName, newData) {
        if (!newData) return;
        
        const tableState = this.state[tableName];
        if (!tableState || !tableState.data) return;
        
        const sortKey = `${tableName}Sort`;
        const sortConfig = this.state[sortKey];
        let currentData = [...tableState.data];
        
        const existingIndex = currentData.findIndex(item => item.id === newData.id);
        if (existingIndex !== -1) {
            currentData[existingIndex] = { ...currentData[existingIndex], ...newData };
            this.state[tableName].data = currentData;
            return;
        }
        
        if (sortConfig) {
            const { order } = sortConfig;
            if (order === 'desc') {
                currentData.unshift(newData);
            } else {
                currentData.push(newData);
            }
        } else {
            currentData.unshift(newData);
        }
        
        if (tableState.page === 1 && currentData.length > tableState.limit) {
            currentData = currentData.slice(0, tableState.limit);
        }
        
        this.state[tableName].total = tableState.total + 1;
        this.state[tableName].totalPages = Math.ceil((tableState.total + 1) / tableState.limit);
        this.state[tableName].data = currentData;
    }

    removeRecordRealtime(tableName, recordId) {
        const tableState = this.state[tableName];
        if (!tableState || !tableState.data) return;
        
        const recordIndex = tableState.data.findIndex(item => item.id === recordId);
        
        if (recordIndex !== -1) {
            const currentData = [...tableState.data];
            currentData.splice(recordIndex, 1);
            
            const newTotal = Math.max(0, tableState.total - 1);
            this.state[tableName].total = newTotal;
            this.state[tableName].totalPages = Math.ceil(newTotal / tableState.limit) || 1;
            this.state[tableName].data = currentData;
            
            if (currentData.length === 0 && tableState.page > 1) {
                this.state[tableName].page = tableState.page - 1;
                this.reloadTable(tableName);
            } else if (currentData.length < tableState.limit && newTotal > currentData.length) {
                this.reloadTable(tableName);
            }
        } else {
            this.reloadTable(tableName);
        }
    }

    // ===== Data Loading =====
    
    async loadPermissions() {
        try {
            const permissions = await this.rpc("/concrete/dashboard/permissions");
            this.state.permissions = permissions;
        } catch (error) {
            console.error("Error loading permissions:", error);
        }
    }
    
    async loadStations() {
        try {
            const stations = await this.rpc("/concrete/dashboard/stations", {});
            this.state.stations = stations || [];
        } catch (error) {
            console.error("Error loading stations:", error);
        }
    }

    async loadAllData() {
        this.state.loading = true;
        try {
            await Promise.all([
                this.loadOrders(),
                this.loadLoads(),
                this.loadVehicles(),
                this.loadTickets(),
            ]);
        } catch (error) {
            console.error("Error loading dashboard data:", error);
            this.notification.add(_t("Failed to load dashboard data"), { type: "danger" });
        }
        this.state.loading = false;
    }

    async loadOrders() {
        try {
            const result = await this.rpc("/concrete/dashboard/orders", {
                params: {
                    page: this.state.orders.page,
                    limit: this.state.orders.limit,
                    search: this.state.ordersSearch,
                    sort_field: this.state.ordersSort.field,
                    sort_order: this.state.ordersSort.order,
                    // Don't filter orders by vehicle station
                    // station_id: this.state.selectedStation,
                }
            });
            this.updateTableState('orders', result);
        } catch (error) {
            console.error("Error loading orders:", error);
        }
    }

    async loadLoads() {
        try {
            const result = await this.rpc("/concrete/dashboard/loads", {
                params: {
                    page: this.state.loads.page,
                    limit: this.state.loads.limit,
                    search: this.state.loadsSearch,
                    sort_field: this.state.loadsSort.field,
                    sort_order: this.state.loadsSort.order,
                    station_id: this.state.selectedStation,
                },
                selected_order_id: this.state.selectedOrderId,
            });
            this.updateTableState('loads', result);
        } catch (error) {
            console.error("Error loading loads:", error);
        }
    }

    async loadVehicles() {
        try {
            const params = {
                page: this.state.vehicles.page,
                limit: this.state.vehicles.limit,
                search: this.state.vehiclesSearch || '',
            };
            if (this.state.selectedVehicleStation != null) {
                params.station_id = this.state.selectedVehicleStation;
            }
            const result = await this.rpc("/concrete/dashboard/vehicles", { params });
            this.updateTableState('vehicles', result);
        } catch (error) {
            console.error("Error loading vehicles:", error);
        }
    }

    async loadTickets() {
        try {
            const result = await this.rpc("/concrete/dashboard/tickets", {
                params: {
                    page: this.state.tickets.page,
                    limit: this.state.tickets.limit,
                    search: this.state.ticketsSearch,
                    sort_field: this.state.ticketsSort.field,
                    sort_order: this.state.ticketsSort.order,
                    station_id: this.state.selectedStation,
                }
            });
            this.updateTableState('tickets', result);
        } catch (error) {
            console.error("Error loading tickets:", error);
        }
    }

    updateTableState(tableName, result) {
        this.state[tableName] = {
            data: result.data || [],
            total: result.total || 0,
            page: result.page || 1,
            limit: result.limit || DEFAULT_LIMIT,
            totalPages: result.total_pages || 1,
        };
    }

    loadTableData(tableName) {
        const loaders = {
            orders: () => this.loadOrders(),
            loads: () => this.loadLoads(),
            vehicles: () => this.loadVehicles(),
            tickets: () => this.loadTickets(),
        };
        return loaders[tableName]?.();
    }

    // ===== Search Handlers =====
    
    onOrdersSearchChange(event) {
        this.state.ordersSearch = event.target.value;
        this.state.orders.page = 1;
        this.loadOrders();
    }

    onLoadsSearchChange(event) {
        this.state.loadsSearch = event.target.value;
        this.state.loads.page = 1;
        this.loadLoads();
    }

    onVehiclesSearchChange(event) {
        this.state.vehiclesSearch = event.target.value;
        this.state.vehicles.page = 1;
        this.loadVehicles();
    }

    onTicketsSearchChange(event) {
        this.state.ticketsSearch = event.target.value;
        this.state.tickets.page = 1;
        this.loadTickets();
    }

    // ===== Sort Handlers =====
    
    onOrdersSort(field) {
        this.toggleSort('ordersSort', field);
        this.loadOrders();
    }

    onLoadsSort(field) {
        this.toggleSort('loadsSort', field);
        this.loadLoads();
    }

    onTicketsSort(field) {
        this.toggleSort('ticketsSort', field);
        this.loadTickets();
    }

    toggleSort(sortKey, field) {
        const currentSort = this.state[sortKey];
        if (currentSort.field === field) {
            currentSort.order = currentSort.order === 'asc' ? 'desc' : 'asc';
        } else {
            currentSort.field = field;
            currentSort.order = 'asc';
        }
    }

    // ===== Page Change Handlers =====
    
    onOrdersPageChange(page) {
        this.state.orders.page = page;
        this.loadOrders();
    }

    onLoadsPageChange(page) {
        this.state.loads.page = page;
        this.loadLoads();
    }

    onVehiclesPageChange(page) {
        this.state.vehicles.page = page;
        this.loadVehicles();
    }

    onTicketsPageChange(page) {
        this.state.tickets.page = page;
        this.loadTickets();
    }

    // ===== Station Filter =====
    
    onGlobalStationChange(event) {
        const value = event.target.value;
        this.state.selectedStation = value ? parseInt(value) : null;
        this.loadAllData();
    }

    // ===== Vehicle Station Dropdown =====
    
    toggleVehicleStationDropdown() {
        this.state.vehicleStationFilterDropdown.show = !this.state.vehicleStationFilterDropdown.show;
    }

    closeVehicleStationDropdown() {
        this.state.vehicleStationFilterDropdown.show = false;
    }

    async onVehicleStationChange(stationId) {
        this.state.selectedVehicleStation = stationId ?? null;
        this.state.vehicles.page = 1;
        this.closeVehicleStationDropdown();
        await this.loadVehicles();
    }

    getVehicleStationDisplayName() {
        if (!this.state.selectedVehicleStation) return _t('All Vehicles');
        const station = this.state.stations.find(s => s.id === this.state.selectedVehicleStation);
        return station?.name || _t('All Vehicles');
    }

    // ===== Selection Handlers =====
    
    selectOrder(orderId) {
        this.state.selectedOrderId = orderId === this.state.selectedOrderId ? null : orderId;
        this.state.loads.page = 1;
        this.loadLoads();
    }

    isOrderSelected(orderId) {
        return this.state.selectedOrderId === orderId;
    }

    toggleLoadSelection(loadId) {
        const index = this.state.selectedLoads.indexOf(loadId);
        if (index === -1) {
            this.state.selectedLoads.push(loadId);
        } else {
            this.state.selectedLoads.splice(index, 1);
        }
    }

    isLoadSelected(loadId) {
        return this.state.selectedLoads.includes(loadId);
    }

    selectVehicle(vehicleId) {
        this.state.selectedVehicle = vehicleId === this.state.selectedVehicle ? null : vehicleId;
    }

    isVehicleSelected(vehicleId) {
        return this.state.selectedVehicle === vehicleId;
    }

    // ===== Fullscreen Toggle =====
    
    async toggleFullscreen(tableName) {
        const fullscreenKey = `${tableName}Fullscreen`;
        const columnsKey = `${tableName}Columns`;
        const backupKey = `${tableName}ColumnsBackup`;
        
        const isEnteringFullscreen = !this.state[fullscreenKey];
        this.state[fullscreenKey] = isEnteringFullscreen;
        
        if (this.state.columnMenu.show && this.state.columnMenu.table === tableName) {
            this.state.columnMenu.show = false;
        }
        
        if (isEnteringFullscreen) {
            this.state[backupKey] = deepClone(this.state[columnsKey]);
            this.state[columnsKey].forEach(col => col.visible = true);
            this.state[tableName].limit = FULLSCREEN_LIMIT;
        } else {
            if (this.state[backupKey]) {
                this.state[columnsKey] = this.state[backupKey];
                this.state[backupKey] = null;
            }
            this.state[tableName].limit = DEFAULT_LIMIT;
        }
        
        this.state[tableName].page = 1;
        await this.loadTableData(tableName);
    }

    async toggleOrdersFullscreen() { await this.toggleFullscreen('orders'); }
    async toggleLoadsFullscreen() { await this.toggleFullscreen('loads'); }
    async toggleVehiclesFullscreen() { await this.toggleFullscreen('vehicles'); }
    async toggleTicketsFullscreen() { await this.toggleFullscreen('tickets'); }

    // ===== Context Menu =====
    
    onLoadContextMenu(event, loadId) {
        if (!this.state.permissions.can_delete) {
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        this.state.contextMenu = {
            show: true,
            x: event.clientX,
            y: event.clientY,
            loadId: loadId,
        };
    }

    getContextMenuItems() {
        const items = [];
        
        if (this.state.permissions.can_delete) {
            items.push({
                label: _t('Delete Load'),
                icon: 'fa fa-trash',
                danger: true,
                action: () => this.confirmDeleteLoad(),
            });
        }
        
        return items;
    }
    
    canAssignTicket() {
        return this.state.permissions.can_assign_ticket && 
               this.state.selectedLoads.length > 0 && 
               this.state.selectedVehicle;
    }

    async confirmDeleteLoad() {
        const loadId = this.state.contextMenu.loadId;
        this.state.confirmModal = {
            show: true,
            title: _t('Confirm Delete Load'),
            message: _t('Are you sure you want to delete this Load? The volume will be returned to the unallocated volume of the SO.'),
            action: async () => await this.deleteLoad(loadId)
        };
        this.state.contextMenu.show = false;
    }

    async deleteLoad(loadId) {
        try {
            const result = await this.rpc("/concrete/dashboard/delete_load", { load_id: loadId });
            if (result.success) {
                this.notification.add(_t("Load deleted successfully"), { type: "success" });
                await Promise.all([this.loadOrders(), this.loadLoads()]);
            } else {
                this.notification.add(result.error || _t("Failed to delete load"), { type: "danger" });
            }
        } catch (error) {
            console.error("Error deleting load:", error);
            this.notification.add(_t("Failed to delete load"), { type: "danger" });
        }
        this.closeConfirmModal();
    }

    // ===== Station Dropdown for Editing =====
    
    showStationDropdown(event, type, id) {
        if (!this.state.permissions.can_edit) {
            return;
        }
        event.preventDefault();
        event.stopPropagation();
        this.state.stationDropdown = {
            show: true,
            type,
            id,
            x: event.clientX,
            y: event.clientY,
        };
    }

    async selectStation(stationId) {
        const { type, id } = this.state.stationDropdown;
        this.state.confirmModal = {
            show: true,
            title: _t('Confirm Change Station'),
            message: _t(`Are you sure you want to change the Station for this ${type === 'order' ? 'order' : 'Load'}?`),
            action: async () => await this.updateStation(type, id, stationId)
        };
        this.state.stationDropdown.show = false;
    }

    async updateStation(type, id, stationId) {
        try {
            const endpoint = type === 'order' 
                ? '/concrete/dashboard/update_order_station'
                : '/concrete/dashboard/update_load_station';
            const params = type === 'order'
                ? { order_id: id, station_id: stationId }
                : { load_id: id, station_id: stationId };
            
            const result = await this.rpc(endpoint, params);
            if (result.success) {
                this.notification.add(_t("Station updated successfully"), { type: "success" });
                await this.loadAllData();
            } else {
                this.notification.add(result.error || _t("Failed to update station"), { type: "danger" });
            }
        } catch (error) {
            console.error("Error updating station:", error);
            this.notification.add(_t("Failed to update station"), { type: "danger" });
        }
        this.closeConfirmModal();
    }

    // ===== Vehicle Station Dropdown =====
    
    showVehicleStationDropdown(event, vehicleId) {
        event.preventDefault();
        event.stopPropagation();
        const rect = event.currentTarget.getBoundingClientRect();
        this.state.vehicleStationDropdown = {
            show: true,
            vehicleId,
            x: rect.left,
            y: rect.bottom + 4,
        };
    }

    async selectVehicleStation(vehicleId, stationId) {
        this.state.confirmModal = {
            show: true,
            title: _t('Confirm Change Station'),
            message: _t('Are you sure you want to change the Station for this Vehicle?'),
            action: async () => await this.updateVehicleStation(vehicleId, stationId)
        };
        this.state.vehicleStationDropdown.show = false;
    }

    async updateVehicleStation(vehicleId, stationId) {
        try {
            const result = await this.rpc('/concrete/dashboard/update_vehicle_station', {
                vehicle_id: vehicleId,
                station_id: stationId
            });
            if (result.success) {
                this.notification.add(_t("Station updated successfully"), { type: "success" });
                await this.loadVehicles();
            } else {
                this.notification.add(result.error || _t("Failed to update station"), { type: "danger" });
            }
        } catch (error) {
            console.error("Error updating vehicle station:", error);
            this.notification.add(_t("Failed to update station"), { type: "danger" });
        }
        this.closeConfirmModal();
    }

    // ===== Vehicle State Dropdown =====
    
    showVehicleStateDropdown(event, vehicleId) {
        event.preventDefault();
        event.stopPropagation();
        const rect = event.currentTarget.getBoundingClientRect();
        this.state.vehicleStateDropdown = {
            show: true,
            vehicleId,
            x: rect.left,
            y: rect.bottom + 4,
        };
    }

    canSelectAvailable(currentState) {
        return ['completed', 'not_available', 'broken'].includes(currentState);
    }

    canSelectBroken(currentState) {
        return !['completed', 'not_available', 'broken'].includes(currentState);
    }

    getAvailableText() {
        return _t('Available');
    }

    getBrokenText() {
        return _t('Broken');
    }

    async selectVehicleState(vehicleId, stateConcrete) {
        const vehicle = this.state.vehicles.data.find(v => v.id === vehicleId);
        if (!vehicle) return;
        
        if (stateConcrete === 'available' && !this.canSelectAvailable(vehicle.state_concrete)) {
            return;
        }
        if (stateConcrete === 'broken' && !this.canSelectBroken(vehicle.state_concrete)) {
            return;
        }
        
        this.state.confirmModal = {
            show: true,
            title: _t('Confirm Change State'),
            message: _t(`Are you sure you want to change the State to ${stateConcrete === 'available' ? _t('Available') : _t('Broken')}?`),
            action: async () => await this.updateVehicleState(vehicleId, stateConcrete)
        };
        this.state.vehicleStateDropdown.show = false;
    }

    async updateVehicleState(vehicleId, stateConcrete) {
        try {
            const result = await this.rpc('/concrete/dashboard/update_vehicle_state', {
                vehicle_id: vehicleId,
                state_concrete: stateConcrete
            });
            if (result.success) {
                this.notification.add(_t("State updated successfully"), { type: "success" });
                await this.loadVehicles();
            } else {
                this.notification.add(result.error || _t("Failed to update state"), { type: "danger" });
            }
        } catch (error) {
            console.error("Error updating vehicle state:", error);
            this.notification.add(_t("Failed to update state"), { type: "danger" });
        }
        this.closeConfirmModal();
    }

    // ===== Confirmation Modal =====
    
    confirmAction() {
        this.state.confirmModal.action?.();
    }

    closeConfirmModal() {
        this.state.confirmModal = { show: false, title: '', message: '', action: null };
    }

    // ===== Actions =====
    
    canAssignTicket() {
        return this.state.selectedLoads.length > 0 && this.state.selectedVehicle !== null;
    }

    async assignTicket() {
        if (this.state.selectedLoads.length === 0) {
            this.notification.add(_t("Please select at least one Load"), { type: "warning" });
            return;
        }

        if (!this.state.selectedVehicle) {
            this.notification.add(_t("Please select a Vehicle"), { type: "warning" });
            return;
        }

        const selectedVehicleData = this.state.vehicles.data.find(v => v.id === this.state.selectedVehicle);
        if (!selectedVehicleData) {
            this.notification.add(_t("Vehicle information not found"), { type: "danger" });
            return;
        }

        if (selectedVehicleData.state_concrete !== 'available') {
            this.notification.add(_t("Cannot Assign Ticket: Vehicle is not Available."), { type: "danger" });
            return;
        }

        for (const loadId of this.state.selectedLoads) {
            const selectedLoadData = this.state.loads.data.find(l => l.id === loadId);
            if (!selectedLoadData) {
                this.notification.add(_t("Load information not found"), { type: "danger" });
                return;
            }
            if ((selectedLoadData.station_id || false) !== (selectedVehicleData.station_id || false)) {
                this.notification.add(_t("Cannot Assign Ticket: Load station and Vehicle station do not match."), { type: "danger" });
                return;
            }
        }

        try {
            for (const loadId of this.state.selectedLoads) {
                const result = await this.rpc("/concrete/dashboard/assign_ticket", {
                    load_id: loadId,
                    vehicle_id: this.state.selectedVehicle,
                });
                if (!result.success) {
                    this.notification.add(result.error || _t("Failed to assign ticket"), { type: "danger" });
                    return;
                }
            }
            this.notification.add(_t("Ticket assigned successfully"), { type: "success" });
            this.state.selectedLoads = [];
            this.state.selectedVehicle = null;
            await this.loadAllData();
        } catch (error) {
            console.error("Error assigning ticket:", error);
            this.notification.add(_t("Failed to assign ticket"), { type: "danger" });
        }
    }

    async splitLoad(orderId) {
        try {
            const result = await this.rpc("/concrete/dashboard/split_load", { order_id: orderId });
            if (result.success) {
                this.notification.add(_t("Load split successfully"), { type: "success" });
                await Promise.all([this.loadOrders(), this.loadLoads()]);
            } else {
                this.notification.add(result.error || _t("Failed to split load"), { type: "danger" });
            }
        } catch (error) {
            console.error("Error splitting load:", error);
            this.notification.add(_t("Failed to split load"), { type: "danger" });
        }
    }

    // ===== Format Helpers =====
    
    formatDateTime(dateStr) {
        if (!dateStr) return '';
        return new Date(dateStr).toLocaleString('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // ===== Translation Helpers =====
    
    t(key) {
        const translations = {
            'search_tickets': _t('Search by ticket code, product,...'),
            'no_tickets': _t('No tickets'),
            'loads_and_vehicles': _t('Load List and Vehicle List'),
            'load_list': _t('Load List'),
            'search_loads': _t('Search by Load code...'),
            'select_station': _t('Select station'),
            'no_loads': _t('No loads'),
            'vehicle_list': _t('Vehicle List'),
            'search_vehicles': _t('Search by vehicle code...'),
            'no_vehicles': _t('No vehicles'),
            'orders_list': _t('Orders being delivered and pending delivery'),
            'search_orders': _t('Search: SO, Address, Product, Note...'),
            'split_load': _t('Split Load'),
            'no_orders': _t('No orders'),
            'customize_columns': _t('Customize Columns'),
            'expand_collapse': _t('Expand/Collapse'),
            'expand': _t('Expand'),
            'collapse': _t('Collapse'),
            'drag_to_resize': _t('Drag to resize width'),
        };
        return translations[key] || key;
    }

    formatNumber(num) {
        if (num == null) return '0';
        return parseFloat(num).toFixed(2);
    }

    // ===== Open Form View =====
    
    async openRecord(model, resId) {
        if (!resId) return;
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    // ===== Column Customization =====
    
    translateColumns(columns) {
        const labelMap = {
            'No.': _t('No.'),
            'Ticket Code': _t('Ticket Code'),
            'Mã Ticket': _t('Ticket Code'),
            'Construction Site Address': _t('Construction Site Address'),
            'Địa chỉ công trường': _t('Construction Site Address'),
            'SO': _t('SO'),
            'Product': _t('Product'),
            'Sản phẩm': _t('Product'),
            'Mix Note': _t('Mix Note'),
            'Ghi chú cấp phối': _t('Mix Note'),
            'Station': _t('Station'),
            'Trạm': _t('Station'),
            'Volume (m³)': _t('Volume (m³)'),
            'K.Lượng (m³)': _t('Volume (m³)'),
            'Vehicle': _t('Vehicle'),
            'Xe': _t('Vehicle'),
            'ETA': _t('ETA'),
            'State': _t('State'),
            'Trạng thái': _t('State'),
            'Assigned': _t('Assigned'),
            'Loading': _t('Loading'),
            'Loaded': _t('Loaded'),
            'Leave': _t('Leave'),
            'Arrived': _t('Arrived'),
            'Unloading': _t('Unloading'),
            'Return': _t('Return'),
            'Completed': _t('Completed'),
            'Allocated Volume (m³)': _t('Allocated Volume (m³)'),
            'KL đã chia Load (m³)': _t('Allocated Volume (m³)'),
            'Unallocated Volume (m³)': _t('Unallocated Volume (m³)'),
            'KL chưa chia Load (m³)': _t('Unallocated Volume (m³)'),
            'Delivered Volume (m³)': _t('Delivered Volume (m³)'),
            'KL đã giao (m³)': _t('Delivered Volume (m³)'),
            'Action': _t('Action'),
            'Hành động': _t('Action'),
            'Load Code': _t('Load Code'),
            'Mã Load': _t('Load Code'),
            'Vehicle Code': _t('Vehicle Code'),
            'Mã xe': _t('Vehicle Code'),
            'Status': _t('Status'),
        };
        return columns.map(col => ({
            ...col,
            label: labelMap[col.label] || col.label
        }));
    }

    getColumns(tableName) {
        const columnsMap = {
            tickets: this.state.ticketsColumns,
            orders: this.state.ordersColumns,
            loads: this.state.loadsColumns,
            vehicles: this.state.vehiclesColumns,
        };
        const columns = columnsMap[tableName] || [];
        return this.translateColumns(columns);
    }

    setColumns(tableName, columns) {
        this.state[`${tableName}Columns`] = columns;
        saveColumnConfig(tableName, columns);
    }

    getVisibleColumns(tableName) {
        const columns = this.getColumns(tableName);
        const isFullscreen = this.state[`${tableName}Fullscreen`];
        if (isFullscreen) {
            return columns.slice().sort((a, b) => a.order - b.order);
        }
        return columns.filter(col => col.visible).sort((a, b) => a.order - b.order);
    }

    getSortableColumns(tableName) {
        return SORTABLE_COLUMNS[tableName] || {};
    }

    isProgressColumn(columnKey) {
        return PROGRESS_COLUMNS.has(columnKey);
    }

    isSortableColumn(tableName, columnKey) {
        return SORTABLE_COLUMNS[tableName]?.[columnKey] || false;
    }

    handleColumnClick(tableName, columnKey) {
        if (this.isSortableColumn(tableName, columnKey)) {
            const sortHandlers = {
                tickets: () => this.onTicketsSort(columnKey),
                loads: () => this.onLoadsSort(columnKey),
                orders: () => this.onOrdersSort(columnKey),
            };
            sortHandlers[tableName]?.();
        }
    }

    showColumnMenu(event, tableName) {
        event.stopPropagation();
        const menuWidth = 280;
        const buttonRect = event.currentTarget.getBoundingClientRect();
        const menuX = Math.max(10, buttonRect.left - menuWidth - 2);
        
        this.state.columnMenu = {
            show: true,
            table: tableName,
            x: menuX,
            y: buttonRect.top,
        };
    }

    toggleColumnVisibility(tableName, columnKey) {
        const columns = this.getColumns(tableName);
        const column = columns.find(col => col.key === columnKey);
        if (column) {
            column.visible = !column.visible;
            saveColumnConfig(tableName, columns);
            this.setColumns(tableName, [...columns]);
        }
    }

    resetColumns(tableName) {
        const defaults = deepClone(DEFAULT_COLUMNS[tableName]);
        if (defaults) {
            this.setColumns(tableName, defaults);
            saveColumnConfig(tableName, defaults);
        }
    }

    // ===== Column Resize =====
    
    startResize(event, tableName, columnKey) {
        event.preventDefault();
        event.stopPropagation();
        
        const columns = this.getColumns(tableName);
        const column = columns.find(col => col.key === columnKey);
        if (!column) return;
        
        const startWidth = column.width;
        const startX = event.clientX;
        const dashboard = event.target.closest('.concrete-dashboard');
        
        if (dashboard) dashboard.classList.add('resizing');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        
        const handleMouseMove = (e) => {
            e.preventDefault();
            column.width = Math.max(50, startWidth + (e.clientX - startX));
            this.setColumns(tableName, [...columns]);
        };
        
        const handleMouseUp = (e) => {
            e.preventDefault();
            saveColumnConfig(tableName, columns);
            if (dashboard) dashboard.classList.remove('resizing');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
        
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }

    // ===== Column Reorder =====
    
    startDrag(event, tableName, columnKey) {
        event.preventDefault();
        this.state.draggingColumn = { table: tableName, key: columnKey };
        
        const handleMouseUp = (e) => {
            if (this.state.draggingColumn) {
                const target = e.target.closest('th');
                if (target?.dataset.columnKey && target.dataset.columnKey !== columnKey) {
                    this.reorderColumn(tableName, columnKey, target.dataset.columnKey);
                }
                this.state.draggingColumn = null;
            }
            document.removeEventListener('mouseup', handleMouseUp);
        };
        
        document.addEventListener('mouseup', handleMouseUp);
    }

    handleColumnDrop(event, tableName, targetKey) {
        event.preventDefault();
        if (this.state.draggingColumn?.table === tableName) {
            const sourceKey = this.state.draggingColumn.key;
            if (sourceKey !== targetKey) {
                this.reorderColumn(tableName, sourceKey, targetKey);
            }
        }
    }

    reorderColumn(tableName, sourceKey, targetKey) {
        const columns = this.getColumns(tableName);
        const sourceIndex = columns.findIndex(col => col.key === sourceKey);
        const targetIndex = columns.findIndex(col => col.key === targetKey);
        
        if (sourceIndex !== -1 && targetIndex !== -1) {
            const [removed] = columns.splice(sourceIndex, 1);
            columns.splice(targetIndex, 0, removed);
            columns.forEach((col, idx) => col.order = idx);
            saveColumnConfig(tableName, columns);
            this.setColumns(tableName, [...columns]);
        }
    }

    // ===== State Class Helper =====
    
    getStateClass(state) {
        return STATE_CLASSES[state] || '';
    }

    // ===== Progress States Helper =====
    
    getProgressStates(ticket) {
        const states = ['assigned', 'loading', 'loaded', 'leave', 'arrived', 'unloading', 'return', 'completed'];
        const currentState = ticket.state;
        
        const isCancelled = currentState === 'cancel';
        const isOnHold = currentState === 'on_hold';
        
        const stateMap = { 'confirmed': 'assigned', 'assigned': 'assigned' };
        const normalizedState = stateMap[currentState] || currentState;
        const currentIndex = states.indexOf(normalizedState);
        
        return states.map((state, index) => ({
            name: state,
            active: index === currentIndex && !isCancelled && !isOnHold,
            completed: index < currentIndex && !isCancelled && !isOnHold,
            completedBeforeIssue: (isCancelled || isOnHold) && index < currentIndex,
        }));
    }
}

// Register the client action
registry.category("actions").add("concrete_dashboard", ConcreteDashboard);
