from odoo import models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'autopost_bills' in fields_list and not res.get('autopost_bills'):
            default_val = self._fields['autopost_bills'].default(self.env) or 'ask'
            res['autopost_bills'] = default_val
        return res

    @api.model_create_multi
    def create(self, vals_list):
        default_val = self._fields['autopost_bills'].default(self.env) or 'ask'
        for vals in vals_list:
            if not vals.get('autopost_bills'):
                vals['autopost_bills'] = default_val
        return super().create(vals_list)
