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
        
        // For cancelled or on_hold, find the highest index state that was passed
        if (isCancelled || isOnHold) {
            // Use highest_passed_state_index from backend if available
            let highestPassedIndex = -1;
            if (ticket.highest_passed_state_index !== undefined && ticket.highest_passed_state_index !== null) {
                highestPassedIndex = ticket.highest_passed_state_index;
            } else {
                // Fallback: Find the highest index state that has a datetime
                for (let i = PROGRESS_STATES.length - 1; i >= 0; i--) {
                    const state = PROGRESS_STATES[i];
                    const datetimeField = STATE_TO_DATETIME_FIELD[state];
                    if (datetimeField) {
                        const datetimeValue = ticket[datetimeField];
                        if (datetimeValue && datetimeValue !== false && datetimeValue !== '') {
                            highestPassedIndex = i;
                            break;
                        }
                    }
                }
            }
            
            // If displayState is at or before the highest passed state, it should be gray
            // (tô xám tất cả các state từ state cao nhất trở về trước)
            if (highestPassedIndex >= 0 && displayIndex <= highestPassedIndex) {
                return {
                    'status-dot': true,
                    'status-dot-gray': true,
                };
            }
            
            // State was not passed, show as inactive (no blue border for on_hold/cancel)
            return {
                'status-dot': true,
                'status-dot-inactive-no-border': true,
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
