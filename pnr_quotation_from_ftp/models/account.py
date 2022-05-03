# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import UserError
from  odoo.tools.misc import formatLang

class AccountMove(models.Model):
    _inherit = 'account.move'

    other_tax = fields.Float(string="Amount Tax", compute="_compute_other_tax")
    amount_without_any_tax = fields.Float(string="Amount Untaxed", compute="_compute_other_tax")
    amount_tva = fields.Float(string="Amount TVA", compute="_compute_other_tax")

    @api.model
    def _get_tax_totals(self, partner, tax_lines_data, amount_total, amount_untaxed, currency):
        res = super(AccountMove, self)._get_tax_totals(partner, tax_lines_data, amount_total, amount_untaxed, currency)

        lang_env = self.with_context(lang=partner.lang).env

        res.update({
            'amount_without_any_tax' : self.amount_without_any_tax,
            'other_tax' : self.other_tax,
            'formatted_amount_without_any_tax' : formatLang(lang_env, self.amount_without_any_tax, currency_obj=currency),
            'formatted_other_tax' : formatLang(lang_env, self.other_tax, currency_obj=currency),
        })

        return res

    @api.depends('invoice_line_ids.other_tax')
    def _compute_other_tax(self):
        for record in self:
            other_tax = 0.0
            amount_tva = record.amount_total - record.amount_untaxed
            for line in record.invoice_line_ids:
                other_tax += line.other_tax

            record.update({'other_tax' : other_tax, 'amount_without_any_tax' : record.amount_untaxed - other_tax, 'amount_tva' : amount_tva})

    def write(self, vals):
        if 'invoice_line_ids' in vals:
            for invoice_line in vals['invoice_line_ids']:
                if 'line_ids' in vals:
                    if invoice_line[2]:
                        corresponding_line_id = [line_id for line_id in vals['line_ids'] if line_id[1] == invoice_line[1]][0]

                        updates = {}
                        if 'other_tax' in invoice_line[2]:
                            updates['other_tax'] = invoice_line[2]['other_tax']
                        if 'supplier' in invoice_line[2]:
                            updates['supplier'] = invoice_line[2]['supplier']
                        if 'passenger' in invoice_line[2]:
                            updates['passenger'] = invoice_line[2]['passenger']
                        if 'ticket_number' in invoice_line[2]:
                            updates['ticket_number'] = invoice_line[2]['ticket_number']
                        if 'journey' in invoice_line[2]:
                            updates['journey'] = invoice_line[2]['journey']

                        if corresponding_line_id[2]:
                            corresponding_line_id[2].update(updates)
                        else:
                            corresponding_line_id[0] = 1
                            corresponding_line_id[2] = updates
        return super(AccountMove, self).write(vals)

    @api.model
    def create(self, vals):
        if 'invoice_line_ids' in vals:
            for invoice_line in vals['invoice_line_ids']:
                if 'line_ids' in vals:
                    if invoice_line[2]:
                        corresponding_line_id = [line_id for line_id in vals['line_ids'] if line_id[1] == invoice_line[1]][0]

                        updates = {}
                        if 'other_tax' in invoice_line[2]:
                            updates['other_tax'] = invoice_line[2]['other_tax']
                        if 'supplier' in invoice_line[2]:
                            updates['supplier'] = invoice_line[2]['supplier']
                        if 'passenger' in invoice_line[2]:
                            updates['passenger'] = invoice_line[2]['passenger']
                        if 'ticket_number' in invoice_line[2]:
                            updates['ticket_number'] = invoice_line[2]['ticket_number']
                        if 'journey' in invoice_line[2]:
                            updates['journey'] = invoice_line[2]['journey']

                        if corresponding_line_id[2]:
                            corresponding_line_id[2].update(updates)
                        else:
                            corresponding_line_id[2] = updates

        invoice = super(AccountMove, self).create(vals)

        for line in invoice.invoice_line_ids:
            line.price_unit -= line.other_tax

        # Set label of 401 or 411 in journal items
        for line in invoice.line_ids:
            if line.account_id.id == 288:
                line.name = invoice.global_label

        return invoice

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    other_tax = fields.Float(string="Other Taxes")

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'
        line_discount_price_unit = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * line_discount_price_unit

        # Compute 'price_total'
        if taxes:
            force_sign = -1 if move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1
            taxes_res = taxes._origin.with_context(force_sign=force_sign).compute_all(line_discount_price_unit,
                quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal

        res['price_subtotal'] += self.other_tax
        res['price_total'] += self.other_tax

        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k : currency.round(v) for k, v in res.items()}
        return res

    @api.onchange('other_tax')
    def _onchange_other_tax(self):
        for line in self:
            if not line.move_id.is_invoice(include_receipts=True):
                continue

            line.update(line._get_price_total_and_subtotal())
            line.update(line._get_fields_onchange_subtotal())
