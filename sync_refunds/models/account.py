# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import UserError

import re

class AccountMove(models.Model):
    _inherit = 'account.move'
    related_out_refund = fields.Many2one('account.move', string="Related Out Refund")

    def action_post(self):
        # if not self.order_ref:
        #     raise UserError(_("You should first define the Order Reference"))
        # else:
        #     order = self.env['travel.order'].search([('ref', '=', self.order_ref)])
        #     if not order:
        #         raise UserError(_("Order Reference %s not found!") % self.order_ref)
        # ------------------------------------ #
        # If current record is an out invoice  #
        # ------------------------------------ #
        if self.move_type == 'out_refund':
            # ----------------------------------------
            # If current invoice doesn't have origin
            # ----------------------------------------
            # if not self.invoice_origin:
                in_refunds = {}

                # ###################################################################################### #
                # Description of the in_refunds variable                                                 #
                # -------------------------------------------------------------------------------------- #
                # in_refunds = {                                                                         #
                #   < instancce of res.partner > : [< dict to create the bill refund >]                  #
                # }                                                                                      #
                # ###################################################################################### #


                for invoice_line in self.invoice_line_ids:
                    # -------------------------------------
                    # If line has not been refunded yet
                    # -------------------------------------
                    if not invoice_line.related_in_refund:
                        # ------------------------
                        # If line has supplier
                        # ------------------------
                        if invoice_line.supplier:
                            # Ne créer de RBILL si déjà existant
                            # rbill = self.env['account.move'].search([('invoice_origin', '!=', False), ('invoice_origin', '=', self.invoice_origin), ('move_type', '=', 'in_refund'), ('partner_id', '=', invoice_line.supplier.id)])

                            if invoice_line.supplier not in in_refunds:
                                # ---------------------- #
                                # Create Refunds header  #
                                # ---------------------- #
                                in_invoice = self.env['account.move'].search(['&', ('partner_id', '=', invoice_line.supplier.id), ('invoice_origin', '=', self.invoice_origin), ('order_ref', '=', self.order_ref)])

                                if len(in_invoice) == 1:
                                    in_invoice_num = in_invoice.name
                                elif len(in_invoice) > 1:
                                    in_invoice_num = " - ".join([invoice.name for invoice in in_invoice])
                                else:
                                    in_invoice_num = ""

                                if 'Extourne de' in self.ref:
                                    out_invoices_num = [item for item in self.ref.replace(',', ' ').split() if len(item) == len(re.findall('\d', item)) and re.search('^008', item)]
                                    out_invoice_num = out_invoices_num[0]
                                    ref = self.ref.replace(out_invoice_num, in_invoice_num)
                                else:
                                    ref = "[ %s ] %s" % (in_invoice_num, self.ref if self.ref else "")

                                in_refunds[invoice_line.supplier] = {
                                    'partner_id' : invoice_line.supplier.id,
                                    'origin_type' : self.origin_type,
                                    'ref' : ref,
                                    'invoice_date' : self.invoice_date,
                                    'global_label' : self.global_label,
                                    'invoice_payment_term_id' : self.invoice_payment_term_id.id,
                                    'move_type' : 'in_refund',
                                    # 'journal_id' : 
                                    'order_ref' : self.order_ref,
                                    'invoice_origin' : self.invoice_origin,
                                    'invoice_origin_id' : self.invoice_origin_id.id,
                                    'related_out_refund' : self.id,
                                    'invoice_line_ids' : []
                                }

                            # ---------------------- #
                            # Create Refunds lines   #
                            # ---------------------- #
                            in_refunds[invoice_line.supplier]['invoice_line_ids'].append((0,0,{
                                'product_id' : invoice_line.product_id.id,
                                'name' : invoice_line.name,
                                'passenger' : invoice_line.passenger,
                                'ticket_number' : invoice_line.ticket_number,
                                'journey' : invoice_line.journey,
                                'quantity' : invoice_line.quantity,
                                'price_unit' : invoice_line.price_unit,
                                # 'tax_ids' : invoice_line.tax_ids,
                                'other_tax' : invoice_line.other_tax
                            }))
                    # ----------------------------------
                    # If line has been refunded before
                    # ----------------------------------
                    else:
                        if invoice_line.related_in_refund.state == 'draft':
                            invoice_line.related_in_refund.action_post()

                for supplier in in_refunds:
                    # raise UserError(str(in_refunds[supplier]))
                    in_refund = self.env['account.move'].create(in_refunds[supplier])
                    for invoice_line in self.invoice_line_ids:
                        if invoice_line.supplier == supplier:
                            invoice_line.update({'related_in_refund' : in_refund.id})

                    in_refund.action_post()
            # ------------------------------
            # If current invoice has origin
            # ------------------------------
            # else:
            #     # in_invoices = self.env['account.move'].search([
            #     #     ('move_type', '=', 'in_refund'), 
            #     #     ('invoice_origin', '=', self.invoice_origin), ('partner_id', 'in', [line.supplier.id for line in self.invoice_line_ids])])

            #     # am_reversal = {
            #     #     'refund_method' : 'refund',
            #     #     'date_mode' : 'custome',
            #     #     'date' : self.invoice_date,
            #     #     'journal_id' : self.env['account.journal'].search([('code', '=', 'BILL')]).id,
            #     #     'move_ids' : [(4, invoice.id) for invoice in in_invoices]
            #     # }
            #     in_refunds_lines = {}
            #     for invoice_line in self.invoice_line_ids:
            #         if not invoice_line.supplier:
            #             continue
            #         lines = self.env['account.move.line'].search([('name', 'like', '%' + invoice_line.name), ('id', '!=', invoice_line.id)])
            #         for line in lines:
            #             if line.move_id.move_type == 'in_refund' and line.move_id.state == 'draft':
            #                 # line.update({
            #                 #     'price_unit' : invoice_line.price_unit,
            #                 #     'other_tax' : invoice_line.other_tax,
            #                 # })

            #                 # line._onchange_other_tax()
            #                 # line.update(line._get_price_total_and_subtotal())
            #                 # line.update(line._get_fields_onchange_subtotal())

            #                 if line.move_id not in in_refunds_lines:
            #                     in_refunds_lines[line.move_id] = []

            #                 in_refunds_lines[line.move_id].append([0, 0, {
            #                     'name' : line.name,
            #                     'passenger' : line.passenger,
            #                     'ticket_number' : line.ticket_number,
            #                     'journey' : line.journey,
            #                     'quantity' : invoice_line.quantity,
            #                     'price_unit' : invoice_line.price_unit,
            #                     'other_tax' : invoice_line.other_tax,
            #                 }])

            #     # Browse refunds and update
            #     refunds = self.env['account.move'].search([('invoice_origin', '=', self.invoice_origin), ('move_type', '=', 'in_refund'), ('state', '=', 'draft')])
            #     for refund in refunds:
            #         if not refund in in_refunds_lines:
            #             refund.unlink()
            #         else:
            #             for refund_line in refund.invoice_line_ids:
            #                 # if not refund_line.id in [line[1] for line in in_refunds_lines[refund]]:
            #                 #     refund_line.unlink()
            #                 refund_line.unlink()

            #             refund.update({'line_ids' : in_refunds_lines[refund]})
            #             for line in refund.invoice_line_ids:
            #                 line.update(line._get_price_total_and_subtotal())
            #                 line.update(line._get_fields_onchange_subtotal())
            #             refund.action_post()

        # Error when confirming out invoice
        return super(AccountMove, self).action_post()

    def button_draft(self):
        if self.state == 'posted':
            super(AccountMove, self).button_draft()
            if self.move_type == 'out_refund':
                for invoice_line in self.invoice_line_ids:
                    if invoice_line.related_in_refund and invoice_line.related_in_refund.state == 'posted':
                        invoice_line.related_in_refund.button_draft()

            elif self.move_type == 'in_refund':
                if self.related_out_refund and self.related_out_refund.state == 'posted':
                    self.related_out_refund.button_draft()

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    related_in_refund = fields.Many2one('account.move', string="Related In Refund")

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    refund_method = fields.Selection(selection=[
            ('refund', 'Partial Refund'),
            ('cancel', 'Full Refund'),
            ('modify', 'Full refund and new draft invoice')
        ], string='Credit Method', required=True,
        help='Choose how you want to credit this invoice. You cannot "modify" nor "cancel" if the invoice is already reconciled.')

    def reverse_moves(self):
        if self.refund_method == 'cancel' and self.journal_id.code == 'INV':
        # if self.journal_id.code == 'INV':
            reversal_dict = {
                'refund_method' : self.refund_method,
                'reason' : self.reason,
                'date_mode' : self.date_mode,
                'date' : self.date,
                'journal_id' : self.env['account.journal'].search([('code', '=', 'BILL')]).id,
                'move_ids' : []
            }

            # Set move_ids (in invoice to be refunded)
            for move in self.move_ids:
                if move.move_type == 'out_invoice':
                    if move.invoice_origin:
                        in_invoices = self.env['account.move'].search([('move_type', '=', 'in_invoice'), ('invoice_origin', '=', move.invoice_origin)])
                        reversal_dict.update({
                            # 'journal_id' : move.
                            'move_ids' : [(4,invoice.id) for invoice in in_invoices],
                        })

                        reversal_instance = self.env['account.move.reversal'].create(reversal_dict)
                        reversal_instance.reverse_moves()
        return super(AccountMoveReversal, self).reverse_moves()
