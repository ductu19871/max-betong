/** @odoo-module **/

import { Component } from "@odoo/owl";

const PROGRESS_STATES = ['assigned', 'loading', 'loaded', 'leave', 'arrived', 'unloading', 'return', 'completed'];

const STATE_TO_DATETIME_FIELD = {
    'assigned': 'assigned_datetime',
    'loading': 'loading_datetime',
    'loaded': 'loaded_datetime',
    'leave': 'leave_datetime',
    'arrived': 'arrived_datetime',
    'unloading': 'unloading_datetime',
    'return': 'return_datetime',
    'completed': 'completed_datetime',
};

export class ProgressDots extends Component {
    static template = "max_betong_dashboard.ProgressDots";
    
    static props = {
        ticket: { type: Object, required: true },
        displayState: { type: String, required: true },
    };

    get dotClass() {
        const ticket = this.props.ticket;
        const currentState = ticket.state;
        const displayState = this.props.displayState;
        
        const isCancelled = currentState === 'cancel';
        const isOnHold = currentState === 'on_hold';
        
        // Map 'confirmed' to 'assigned'
        const stateMap = { 'confirmed': 'assigned', 'assigned': 'assigned' };
        const normalizedState = stateMap[currentState] || currentState;
        const currentIndex = PROGRESS_STATES.indexOf(normalizedState);
        const displayIndex = PROGRESS_STATES.indexOf(displayState);
        
        // For cancelled or on_hold, check datetime fields to see which states were passed
        if (isCancelled || isOnHold) {
            const datetimeField = STATE_TO_DATETIME_FIELD[displayState];
            const hasPassedState = datetimeField && ticket[datetimeField];
            
            if (hasPassedState) {
                return {
                    'status-dot': true,
                    'status-dot-gray': true,
                };
            }
            return {
                'status-dot': true,
                'status-dot-inactive': true,
            };
        }
        
        // Normal flow
        const isCompleted = displayIndex < currentIndex;
        const isActive = displayIndex === currentIndex;
        
        return {
            'status-dot': true,
            'status-dot-active': isActive || isCompleted,
            'status-dot-completed': !isActive && !isCompleted,
            'status-dot-inactive': !isActive && !isCompleted,
        };
    }
}
