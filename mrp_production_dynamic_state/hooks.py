# -*- coding: utf-8 -*-

def post_init_hook(env):
    """
    Post-init hook to migrate existing mrp.production records
    Assign stage_id based on their current state
    """
    # Get state mapping
    env.cr.execute("""
        SELECT id, original_state 
        FROM mrp_production_state 
        WHERE active = true
        ORDER BY sequence, id
    """)
    
    state_mapping = {}
    for state_id, original_state in env.cr.fetchall():
        # Use the first state found for each original_state (if multiple exist)
        if original_state not in state_mapping:
            state_mapping[original_state] = state_id
    
    # Update existing mrp.production records
    for original_state, stage_id in state_mapping.items():
        env.cr.execute("""
            UPDATE mrp_production 
            SET stage_id = %s 
            WHERE state = %s 
            AND (stage_id IS NULL OR stage_id = 0)
        """, (stage_id, original_state))

