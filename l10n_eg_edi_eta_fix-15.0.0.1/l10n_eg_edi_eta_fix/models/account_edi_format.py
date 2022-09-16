# -*- coding: utf-8 -*-
from odoo import api, models, _


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    @api.model
    def _l10n_eg_eta_prepare_address_data(self, partner, invoice, issuer=False):
        address = super(AccountEdiFormat, self)._l10n_eg_eta_prepare_address_data(partner, invoice, issuer)
        individual_type = self._l10n_eg_get_partner_tax_type(partner, issuer)
        address['type'] = individual_type or ''
        return address
