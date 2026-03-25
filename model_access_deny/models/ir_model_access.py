from odoo import models, tools

class IrModelAccess(models.Model):
    _inherit = 'ir.model.access'

    @tools.ormcache('self.env.uid', 'mode')
    def _get_allowed_models(self, mode='read'):
        assert mode in ('read', 'write', 'create', 'unlink')

        self.flush_model()

        self.env.cr.execute(f'''
            SELECT m.model
            FROM ir_model_access a
            JOIN ir_model m ON m.id = a.model_id
            WHERE a.perm_{mode}
              AND a.active
              AND (
                    a.group_id IS NULL OR
                    a.group_id IN (
                        SELECT gu.gid
                        FROM res_groups_users_rel gu
                        WHERE gu.uid = %s
                    )
              )
        ''', (self.env.uid,))
        allowed = set(v[0] for v in self.env.cr.fetchall())

        self.env.cr.execute(f'''
            SELECT m.model
            FROM ir_model_denied d
            JOIN ir_model m ON m.id = d.model_id
            WHERE d.perm_{mode}
              AND d.active
              AND (
                    d.group_id IS NULL OR
                    d.group_id IN (
                        SELECT gu.gid
                        FROM res_groups_users_rel gu
                        WHERE gu.uid = %s
                    )
              )
        ''', (self.env.uid,))
        denied = set(v[0] for v in self.env.cr.fetchall())
        res = frozenset(allowed - denied)
        return res
