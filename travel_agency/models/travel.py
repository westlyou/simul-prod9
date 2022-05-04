# ############################################################################################################
#                                   This module was created by Muriel Rémi                                   #
#                                       Creation date: 09 December 2021                                      #
# ############################################################################################################
# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.exceptions import UserError

from datetime import datetime as dt

from functools import partial
from odoo.tools.misc import formatLang

from lxml import etree

class TravelOrder(models.Model):
    _name = 'travel.order'
    _description = "Travel Order"

    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Number', default=lambda self: _('New') , copy=False, readonly=True)
    partner_id = fields.Many2one('res.partner',
        string="Customer", 
        domain=[('id_incadea', '!=', False)]
    )

    customer_type = fields.Char(string="Customer type", compute="_get_customer_type")
    customer_name = fields.Char(string="Customer name")
    customer_address = fields.Char(string="Customer address")
    customer_nif = fields.Char(string="Customer NIF")
    customer_stat = fields.Char(string="Customer STAT")
    customer_cif = fields.Char(string="Customer CIF")

    user_id = fields.Many2one(
        'res.users', string='Person', index=True, tracking=2, default=lambda self: self.env.user,
        domain=lambda self: [('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)])

    date_order = fields.Date(string="Date", default=dt.strftime(dt.now().date(), '%Y-%m-%d'))
    # date_from = fields.Date(string="From", default=dt.strftime(dt.now().date(), '%Y-%m-%d'), state={'quotation' : [('readonly', False)], 'accepted' : [('readonly', True)], 'confirmed' : [('readonly', True)], 'canceled' : [('readonly', True)]})
    # date_to = fields.Date(string="To", state={'quotation' : [('readonly', False)], 'accepted' : [('readonly', True)], 'confirmed' : [('readonly', True)], 'canceled' : [('readonly', True)]})
    company_id = fields.Many2one('res.company', string="Company")

    transmitter = fields.Char(string="Transmitter", default="MERCURE")
    transmit_date = fields.Date(string="Date of Issue")
    followed_by = fields.Many2one('hr.employee', string="Followed by", default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]))
    ref = fields.Char(string="Reference")
    global_label = fields.Text(string="Global Label")

    state = fields.Selection([
        ('quotation', 'Quotation'), 
        ('supp_invoiced', 'Supplier invoice generated'),
        ('accepted', 'Accepted'),
        ('confirmed', 'Confirmed'), 
        ('enclosed', 'Enclosed'),
        ('canceled', 'Canceled'),
    ], string="State", default='quotation')

    to_state = fields.Selection(string="TO states", related='state')
    amadeus_state = fields.Selection(string="Ticketing states", related='state')

    order_line = fields.One2many('travel.order.line', 'order_id', string="Travel Order Lines", auto_join=True, copy=True)

    amount_untaxed = fields.Monetary(string="Amount Untaxed", store=True, readonly=True, compute="_amount_all", tracking=5)
    amount_tax = fields.Monetary(string="Amount Tax", store=True, compute="_amount_all")
    amount_tva = fields.Monetary(string="Amount TVA on Fees", store=True, readonly=True, compute="_amount_all")
    amount_total = fields.Monetary(string="Amount Total", store=True, readonly=True, compute="_amount_all", tracking=4)
    amount_by_group = fields.Binary(string="Tax amount by group", compute="_amount_by_group", help="type : [(name, amount, base, formated amount, formated base)]")

    currency_id = fields.Many2one(related='pricelist_id.currency_id', depends=["pricelist_id"], string="Currency", readonly=True, required=True)

    company_id = fields.Many2one('res.company', string="Company")

    purchase_invoice_count = fields.Integer(string="Purchase Invoice Count", compute="_get_invoiced", readonly=True)
    sale_invoice_count = fields.Integer(string="Sale Invoice Count", compute="_get_invoiced", readonly=True)
    purchase_invoice_ids = fields.Many2many('account.move', string='Purchase Invoices', compute='_get_invoiced', readonly=True, copy=False)
    sale_invoice_ids = fields.Many2many('account.move', string='Sale Invoices', compute='_get_invoiced', readonly=True, copy=False)

    document_type = fields.Selection([('amadeus', 'Ticketing'), ('to', 'Tour Operator')], string="Document Type", required=True)



    partner_shipping_id = fields.Many2one(
        'res.partner', string='Delivery Address', readonly=True,
        states={'quotation' : [('readonly', False)], 'confirmed' : [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )

    pricelist_id = fields.Many2one(
        'product.pricelist', string="Pricelist", check_company=True, # Unrequired company
        required=True, readonly=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="If you change the pricelist, only newly added lines will be affected."
    )

    signature = fields.Image('Signature', help='Signature received through the portal.', copy=False, attachment=True, max_width=1024, max_height=1024)

    @api.model
    def _default_note(self):
        return self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.env.company.invoice_terms or ''

    note = fields.Text('Terms and conditions', default=_default_note)

    payment_term_id = fields.Many2one(
        'account.payment.term', string='Payment Terms', check_company=True, # Unrequired company
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )

    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string="Fiscal Position",
        domain="[('company_id', '=', company_id)]", check_company=True,
        help="Fiscal positions are used to adapt taxes and accounts for particular customers or travels orders/invoices."
        "The default value comes from the customer."
    )

    other_infos = fields.Text(string="Other Infos")

    num_pnr = fields.Char(
        string="Number PNR", 
        copy=True, 
    )
    folder_number = fields.Char(
        string="Folder Number", 
        copy=True, 
    )

    purchases_count = fields.Integer(string="Purchases", compute="_get_purchases", readonly=True)
    purchases_id = fields.Many2many('purchase.order', string="Purchases ID", compute="_get_purchases", readonly=True, copy=False)

    record_locator = fields.Char(string="Record Locator")
    agent_sign_booking = fields.Char(string="Agent Sign Booking")
    change_date = fields.Date(string="Change Date")
    last_transaction_date = fields.Date(string="Last Transaction Date")
    orig_city = fields.Char(string="Original City")
    dest_city = fields.Char(string="Destination City")
    service_carrier = fields.Char(string="Service Carrier")
    bkg_class = fields.Char(string="Bkg Class")
    airport_name_origin = fields.Char(string="Airport Name Origin")
    ama_name_origin = fields.Char(string="Ama Name Origin")
    country_origin = fields.Many2one('res.country', string="Country Origin")
    airport_code_destination = fields.Char(string="Airport Code Destination")
    ama_name_destination = fields.Char(string="Ama Name Destination")
    country_destination = fields.Many2one('res.country', string="Country Destination")
    airport_code_origin = fields.Char(string="Airport Code Origin")
    ama_name = fields.Char(string="Ama Name")
    ac_rec_loc = fields.Char(string="Ac Rec Loc")
    action_date = fields.Datetime(string="Action Date")

    ticket_count = fields.Integer(string="Ticket Count", compute="_count_tickets")

    partner_account_number = fields.Char(string="Account number")

    prestation = fields.Float(string="Prestation")

    commission = fields.Float(string="Commission", compute="_compute_commission")
    commission_vat = fields.Float(string="Commission VAT", compute="_compute_commission")

    all_supplier_invoice_generated = fields.Boolean(string="Hide generate supplier invoice button", compute="_compute_all_supplier_invoice_generated")

    @api.onchange('amount_untaxed')
    def onchange_amount_untaxed(self):
        for record in self:
            if not record.prestation or record.prestation < record.amount_untaxed:
                record.prestation = record.amount_untaxed

    @api.depends('partner_id.customer_type')
    def _get_customer_type(self):
        for record in self:
            record.customer_type = record.partner_id.customer_type

    @api.depends('order_line.supplier_invoice_generated')
    def _compute_all_supplier_invoice_generated(self):
        for record in self:
            record.all_supplier_invoice_generated = all([line.supplier_invoice_generated for line in record.order_line])

    @api.depends('amount_untaxed', 'prestation')
    def _compute_commission(self):
        for record in self:
            com_ht = com_vat = 0
            if record.document_type == 'to':
                com_ttc = record.prestation - record.amount_untaxed
                com_ht = com_ttc / 1.2

                prod_com = self.env['product.template'].search([('name', '=', 'COMMISSION')])
                if prod_com:
                    com_vat = com_ht * prod_com.taxes_id.amount / 100
                else:
                    com_vat = 0

            record.update({
                'commission' : com_ht,
                'commission_vat' : com_vat,
            })

    @api.depends('order_line', 'order_line.ticket_number')
    def _count_tickets(self):
        for record in self:
            tickets = []
            for line in record.order_line:
                if line.product_type == 'ticket' and line.ticket_number and line.ticket_number not in tickets:
                    tickets.append(line.ticket_number)
            record.ticket_count = len(tickets)

    @api.depends('order_line.price_subtotal', 'order_line.amount_tax', 'order_line.amount_tva', 'commission', 'commission_vat', 'prestation')
    def _amount_all(self):
        """
            Compute the total amounts of Travel Order
        """
        for order in self:
            amount_total = amount_untaxed = amount_tax = amount_tva = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal - line.amount_tax
                # amount_untaxed += line.price_subtotal
                amount_tva += line.amount_tva
                amount_tax += line.amount_tax

            amount_total = (amount_untaxed + amount_tva + amount_tax) if order.document_type == 'amadeus' else order.prestation

            order.update({
                'amount_untaxed' : amount_untaxed,
                'amount_tva' : amount_tva,
                'amount_tax' : amount_tax,
                'amount_total' : amount_total,
                # 'amount_total' : amount_untaxed + amount_tva + amount_tax,
            })

    def _amount_by_group(self):
        for order in self:
            currency = order.currency_id or order.company_id.currency_id
            fmt = partial(formatLang, self.with_context(lang=order.partner_id.lang).env, currency_obj=currency)
            res = {}
            for line in order.order_line:
                price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
                taxes = line.tax_ids.compute_all(price_reduce, quantity=line.quantity * line.number, product=line.product_id, partner=order.partner_shipping_id)['taxes']
                for tax in line.tax_ids:
                    group = tax.tax_group_id
                    res.setdefault(group, {'amount' : 0.0, 'base' : 0.0})
                    for t in taxes:
                        if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                            res[group]['amount'] += t['amount']
                            res[group]['base'] += t['base']

            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group = [(
                l[0].name, l[1]['amount'], l[1]['base'],
                fmt(l[1]['amount']), fmt(l[1]['base']),
                len(res),
            ) for l in res]

    def _get_purchases(self):
        for order in self:
            purchases = self.env['purchase.order'].search([('travel_order_id', '=', order.id)])
            order.update({
                'purchases_count' : len(purchases),
                'purchases_id' : purchases,
            })

    def _get_invoiced(self):
        for order in self:
            # Purchase Invoices
            purchase_invoices = self.env['account.move'].search([('invoice_origin', '=', order.name), ('move_type', 'in', ('in_invoice', 'in_refund'))])
            order.purchase_invoice_ids = purchase_invoices
            order.purchase_invoice_count = len(purchase_invoices)

            # Sale Invoices
            sale_invoices = self.env['account.move'].search([('invoice_origin', '=', order.name), ('move_type', 'in', ('out_invoice', 'out_refund'))])
            order.sale_invoice_ids = sale_invoices
            order.sale_invoice_count = len(sale_invoices)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('travel.order.%s' % vals['document_type'])
        # vals['name'] = 'travel.order.%s' % vals['document_type']

        # -----------------------------------------------------
        # Create name of each travel order lines
        # -----------------------------------------------------
        # raise UserError(str(vals))
        # if 'order_line' in vals:
        #     for line in vals['order_line']:
        #         values = line[2]
        #         name_elements = [
        #             '' if not 'journey' in values else values['journey'], 
        #             '' if not 'ticket_number' in values else values['ticket_number'], 
        #             '' if not 'passenger' in values else values['passenger'], 
        #             '' if not 'custom_descri' in values else values['custom_descri']
        #         ]
        #         name_elements = [item for item in name_elements if item]
        #         if any(name_elements):
        #             values.update({'name' : ' - '.join(name_elements)})
        #         else:
        #             values.update({'name' : self.env['product.product'].browse(values['product_id']).name})
        # -----------------------------------------------------

        return super(TravelOrder, self).create(vals)

    def write(self, vals):
        # -----------------------------------------------------
        # Create name of each travel order lines
        # -----------------------------------------------------
        if 'order_line' in vals:
            for line in vals['order_line']:
                values = line[2]
                if not values:
                    continue

                if 'product_id' in values:
                    if line[0] == 0:        # New line
                        tol = self.env['travel.order.line']
                    else:
                        tol = self.env['travel.order.line'].browse(line[1])

                    name_elements = [
                        ('' if not 'journey' in values else values['journey']) or tol.journey, 
                        ('' if not 'ticket_number' in values else values['ticket_number']) or tol.ticket_number, 
                        ('' if not 'passenger' in values else values['passenger']) or tol.passenger, 
                        ('' if not 'custom_descri' in values else values['custom_descri']) or tol.custom_descri, 
                    ]

                    name_elements = [item for item in name_elements if item]
                    if any(name_elements):
                        values.update({'name' : ' - '.join(name_elements)})
                    else:
                        values.update({'name' : self.env['product.product'].browse(values['product_id']).name})
        # -----------------------------------------------------
        return super(TravelOrder, self).write(vals)

    def unlink(self):
        for record in self:
            if record.state in ('accepted', 'confirmed'):
                raise UserError(_("You cannot delete document that has been %s!") % (_("accepted") if record.state == 'accepted' else _("confirmed")))
            else:
                super(TravelOrder, record).unlink()

    @api.onchange('partner_account_number')
    def onchange_partner_account_number(self):
        if self.partner_account_number:
            partner = self.env['res.partner'].search([('no_g', '=', self.partner_account_number)])
            if not partner:
                raise UserError(_("Account number not found"))
            else:
                self.partner_id = partner.id

    @api.onchange('partner_id')
    def onchange_partner(self):
        if self.partner_id:
            self.partner_account_number = self.partner_id.no_g
        """
            Update the following fields when the partner is changed:
            - Pricelist
            - Payment terms
            - Invoice address
            - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_shipping_id' : False,
                'fiscal_position_id' : False
            })
            return

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id

        values = {
            'pricelist_id' : self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id' : self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_shipping_id' : addr['delivery'],
        }
        user_id = partner_user.id

        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.uid
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param('account.user_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        self.update(values)

    # @api.onchange('prestation')
    # def onchange_prestation(self):
    #     self.state = 'supp_invoiced'

    def action_enclose(self):
        if not self.ref:
            raise UserError(_("Would you fill the ref field please!"))
        if not self.all_supplier_invoice_generated:
            self.generate_supplier_invoice()

        # ------------------------------------------------------
        # Create Customer Invoices and confirm them
        # ------------------------------------------------------
        invoice_values = {
            'partner_id' : self.partner_id.id,
            'invoice_date' : dt.strftime(dt.now().date(), '%Y-%m-%d'),
            'global_label' : self.global_label,
            'move_type' : 'out_invoice',
            'order_ref' : self.ref,
            'journal_id' : 1,
            # 'company_id' : self.company_id.id,
            'currency_id' : self.currency_id.id,
            'invoice_origin' : self.name,
            'invoice_origin_id' : self.id,
            'origin_type' : self.document_type,
            'invoice_payment_term_id' : self.payment_term_id.id,
            'invoice_line_ids' : [],
        }

        for line in self.order_line:
            invoice_line = (0,0,{
                'product_id' : line.product_id.id,
                'name' : line.supplier_invoice_ref,
                'supplier_invoice_ref' : line.supplier_invoice_ref,
                'quantity' : line.quantity * line.number,
                'price_unit' : line.price_unit,
                # 'tax_ids' : line.tax_ids,
                'supplier' : line.supplier,
                # 'other_tax' : line.amount_tax,
            })

            invoice_values['invoice_line_ids'].append(invoice_line)

        # -----------------------------#
        # Append line commission
        # -----------------------------#

        # Search for product commission
        commission_product = self.env['product.product'].search([('name', '=', "COMMISSION")])

        if not commission_product :
            commission_product = self.env['product.product'].create({'name':'COMMISSION'})

        # Compute amount commission
        
        # amount_commission_total = self.amount_total - sum([line.price_unit for line in self.order_line ]) 
        # amount_commission_unit = amount_commission_total - self.amount_tva
        commission_line = (0,0,{
            'product_id' : commission_product.id,
            'name' : commission_product.name,
            'quantity' : 1,
            'price_unit' : self.commission,
            'tax_ids' : commission_product.taxes_id,
            # 'other_tax' : line.amount_tax,
        })
        invoice_values['invoice_line_ids'].append(commission_line)


        customer_invoice = self.env['account.move'].create(invoice_values)
        customer_invoice.action_post()

        # ------------------------------------------------------
        old_state = dict(self._fields['state'].selection).get(self.state)
        self.update({'state' : 'enclosed'})
        new_state = dict(self._fields['state'].selection).get(self.state)

        message_body = _("State : %s → %s") % (old_state, new_state)

        self.message_post(body=message_body)

    def generate_supplier_invoice(self):
        # ------------------------------------------------------
        # Create purchase order
        # ------------------------------------------------------
        purchase_orders = {}
        # supplier_invoice_ref = {}
        for line in self.order_line:
            if line.supplier:
                if not line.supplier_invoice_generated:
                    # Get invoice reference of each line to verify if
                    # two lines of same supplier have different reference
                    # if not line.supplier in supplier_invoice_ref:
                    #     supplier_invoice_ref[line.supplier] = []

                    # if line.supplier_invoice_ref and line.supplier_invoice_ref not in supplier_invoice_ref[line.supplier]:
                    #     supplier_invoice_ref[line.supplier].append(line.supplier_invoice_ref)


                    # Prepare supplier invoice and its lines
                    if not line.supplier in purchase_orders:
                        purchase_orders[line.supplier] = {
                            'partner_id' : line.supplier.id,
                            'currency_id' : line.currency_id.id,
                            'date_order' : dt.strftime(dt.now().date(), '%Y-%m-%d'),
                            'travel_order_id' : self.id,
                            'origin_type' : self.document_type,
                            'ref' : self.ref,
                            'order_line' : []
                        }

                    purchase_orders[line.supplier]['order_line'].append((0,0,{
                        'product_id' : line.product_id.id,
                        'name' : line.supplier_invoice_ref,
                        'supplier_invoice_ref' : line.supplier_invoice_ref,
                        'product_qty' : line.quantity * line.number,
                        'price_unit' : line.price_unit,
                        'other_tax' : line.amount_tax,
                        'taxes_id' : None,
                    }))

                    line.update({'supplier_invoice_generated' : True})

        # if two lines of same supplier have different invoice reference
        # raise user error
        # if any([len(supplier_invoice_ref[supplier]) > 1 for supplier in supplier_invoice_ref]):
        #     details = ""
        #     for supplier in supplier_invoice_ref:
        #         if len(supplier_invoice_ref[supplier]) > 1:
        #             details += _("*   Supplier : %s\n") % supplier.name
        #             details += _("     References : %s\n\n") % ", ".join(supplier_invoice_ref[supplier])
        #     raise UserError(_("Lines of same supplier should have same supplier invoice reference! Please choose one.\n\n%s") % details)
        # else:
        supplier_invoices = []
        for partner in purchase_orders:
            # if len(supplier_invoice_ref[partner]):
            #     purchase_orders[partner].update({'partner_ref' : supplier_invoice_ref[partner][0]})

            purchase_order = self.env['purchase.order'].create(purchase_orders[partner])
            purchase_order.button_confirm()

            supplier_invoice = purchase_order.action_create_invoice()
            supplier_invoices.append(supplier_invoice)

            supplier_invoice = self.env['account.move'].browse(supplier_invoice['res_id'])

            supplier_invoice.update({
                'ref' : _("Travel Invoice : %s") % self.name, 
                'invoice_date' : dt.strftime(dt.now().date(), '%Y-%m-%d'), 
                'global_label' : self.global_label, 
                'invoice_origin' : self.name,
                'invoice_origin_id' : self.id,
                'origin_type' : self.document_type
            })

            supplier_invoice.action_post()

        # Update state
        old_state = dict(self._fields['state'].selection).get(self.state)
        self.update({'state' : 'supp_invoiced'})
        new_state = dict(self._fields['state'].selection).get(self.state)

        if old_state != new_state:
            message_body = _("State : %s → %s") % (old_state, new_state)

            self.message_post(body=message_body)

        # references = ", ".join([supplier_invoice_ref[supplier][0] for supplier in supplier_invoice_ref])
        # message_body = _("Generated supplier invoice references : %s") % references

        # self.message_post(body=message_body)

    def action_accept(self):
        # ------------------------------------------------------
        # Create purchase order
        # ------------------------------------------------------
        purchase_orders = {}
        for line in self.order_line:
            if line.supplier:
                if not line.supplier in purchase_orders:
                    purchase_orders[line.supplier] = {
                        'partner_id' : line.supplier.id,
                        'currency_id' : line.currency_id.id,
                        'date_order' : dt.strftime(dt.now().date(), '%Y-%m-%d'),
                        'travel_order_id' : self.id,
                        'origin_type' : self.document_type,
                        'ref' : self.ref,
                        'order_line' : []
                    }

                purchase_orders[line.supplier]['order_line'].append((0,0,{
                    'product_id' : line.product_id.id,
                    'name' : line.name,
                    'product_qty' : line.quantity * line.number,
                    'price_unit' : line.price_unit,
                    'other_tax' : line.amount_tax,
                    'supplier_invoice_ref' : line.supplier_invoice_ref,
                    'passenger' : line.passenger_fullname,
                    'ticket_number' : line.ticket_number,
                    'journey' : line.journey,
                    'taxes_id' : None,
                }))

        for partner in purchase_orders:
            purchase_order = self.env['purchase.order'].create(purchase_orders[partner])
            purchase_order.button_confirm()
        # ------------------------------------------------------
        old_state = dict(self._fields['state'].selection).get(self.state)
        self.update({'state' : 'accepted'})
        new_state = dict(self._fields['state'].selection).get(self.state)

        message_body = _("State : %s → %s") % (old_state, new_state)

        self.message_post(body=message_body)

    def action_confirm(self):
        # --------------------------------------------------------
        # Check if any tickets in lines has already been invoiced
        # --------------------------------------------------------
        tickets = [line.ticket_number for line in self.order_line]
        invoiced_tickets = [line.ticket_number for invoiced_order in self.env['travel.order'].search([('state', '=', 'confirmed')]) for line in invoiced_order.order_line]

        duplicated_tickets = [ticket for ticket in tickets if ticket and ticket in invoiced_tickets]

        if len(duplicated_tickets):
            raise UserError(_("Ticket N° %s already invoiced") % ",".join(duplicated_tickets))

        # ------------------------------------------------------
        # Create Customer Invoices and confirm them
        # ------------------------------------------------------
        invoice_values = {
            'partner_id' : self.partner_id.id,
            'invoice_date' : dt.strftime(dt.now().date(), '%Y-%m-%d'),
            'global_label' : self.global_label,
            'move_type' : 'out_invoice',
            'order_ref' : self.ref,
            'customer_name' : self.customer_name,
            'customer_address' : self.customer_address,
            'journal_id' : 1,
            # 'company_id' : self.company_id.id,
            'invoice_origin' : self.name,
            'origin_type' : self.document_type,
            'currency_id' : self.currency_id.id,
            'invoice_origin_id' : self.id,
            'invoice_payment_term_id' : self.payment_term_id.id,
            'invoice_line_ids' : [],
        }

        if self.document_type == 'to' :
            for line in self.order_line:
                invoice_line = (0,0,{
                    'product_id' : line.product_id.id,
                    'name' : line.name,
                    'quantity' : line.quantity * line.number,
                    'price_unit' : line.price_unit,
                    'tax_ids' : line.tax_ids,
                    'supplier' : line.supplier,
                    # 'other_tax' : line.amount_tax,
                })

                invoice_values['invoice_line_ids'].append(invoice_line)

            # -----------------------------#
            # Append line commission
            # -----------------------------#

            # Search for product commission
            commission_product = self.env['product.product'].search([('name', '=', "COMMISSION")])

            if not commission_product :
                commission_product = self.env['product.product'].create({'name':'COMMISSION'})

            # Compute amount commission
            
            amount_commission_total = self.amount_total - sum([line.price_unit for line in self.order_line ]) 
            amount_commission_unit = amount_commission_total - self.amount_tva
            commission_line = (0,0,{
                    'product_id' : commission_product.id,
                    'name' : commission_product.name,
                    'quantity' : 1,
                    'price_unit' : amount_commission_unit,
                    'tax_ids' : self.order_line[0].tax_ids,
                    # 'other_tax' : line.amount_tax,
                })
            invoice_values['invoice_line_ids'].append(commission_line)

        else :
            for line in self.order_line:
                invoice_line = (0,0,{
                    'product_id' : line.product_id.id,
                    'name' : line.name,
                    'quantity' : line.quantity * line.number,
                    'price_unit' : line.price_unit,
                    'tax_ids' : line.tax_ids,
                    'other_tax' : line.amount_tax,
                    'supplier' : line.supplier,
                    'passenger' : line.passenger_fullname,
                    'flight_num' : line.flight_num,
                    'flight_class' : line.flight_class,
                    'ticket_number' : line.ticket_number,
                    'journey' : line.journey
                })

                invoice_values['invoice_line_ids'].append(invoice_line)

        customer_invoice = self.env['account.move'].create(invoice_values)
        customer_invoice.action_post()
        # ------------------------------------------------------

        # ------------------------------------------------------
        # Create invoice for the suppliers and confirm them
        # ------------------------------------------------------
        # supplier_invoices = {}
        # for line in self.order_line:
        #     if line.supplier:
        #         if not line.supplier in supplier_invoices:
        #             supplier_invoices[line.supplier] = {
        #                 'partner_id' : line.supplier.id,
        #                 'ref' : _("Travel Invoice : %s") % self.name,
        #                 'move_type' : 'in_invoice',
        #                 'invoice_date' : dt.strftime(dt.now().date(), '%Y-%m-%d'),
        #                 'currency_id' : self.currency_id,
        #                 'invoice_origin' : self.name,
        #                 'invoice_line_ids' : []
        #             }

        #         supplier_invoices[line.supplier]['invoice_line_ids'].append((0,0,{
        #             'product_id' : line.product_id.id,
        #             'name' : line.name,
        #             'quantity' : line.quantity,
        #             'price_unit' : line.price_unit,
        #             'tax_ids' : line.tax_ids,
        #             'other_tax' : line.amount_tax,
        #         }))

        # for partner in supplier_invoices:
        #     purchase_invoice = self.env['account.move'].create(supplier_invoices[partner])
        #     purchase_invoice.action_post()
        # ------------------------------------------------------

        # ------------------------------------------------------
        # Confirm invoice of corresponding purchase order
        # ------------------------------------------------------
        related_PO = self.env['purchase.order'].search([('travel_order_id', '=', self.id), ('state', '=', 'purchase')])
        for po in related_PO:
            supplier_invoice = po.action_create_invoice()

            # raise UserError(str(supplier_invoice))

            supplier_invoice = self.env['account.move'].browse(supplier_invoice['res_id'])

            supplier_invoice.update({
                'ref' : _("Travel Invoice : %s") % self.name, 
                'invoice_date' : dt.strftime(dt.now().date(), '%Y-%m-%d'), 
                'global_label' : self.global_label, 
                'invoice_origin' : self.name,
                'invoice_origin_id' : self.id,
                'origin_type' : self.document_type
            })

            supplier_invoice.action_post()

            # raise UserError(str(supplier_invoices))

            # for invoice in supplier_invoices:
            #     invoice.update({'ref' : _("Travel Invoice : %s") % self.name, 'invoice_date' : dt.strftime(dt.now().date(), '%Y-%m-%d'), 'global_label' : self.global_label, 'invoice_origin' : self.name})
        # ------------------------------------------------------
        old_state = dict(self._fields['state'].selection).get(self.state)
        self.update({'state' : 'confirmed'})
        new_state = dict(self._fields['state'].selection).get(self.state)

        message_body = _("State : %s → %s") % (old_state, new_state)

        self.message_post(body=message_body)
        # else:
        #     raise UserError(_("You don't have the right to confirm a quotation!"))

    def action_cancel(self):
        # if not self.env.user.can_confirm_quotation_passing_client:
        if not self.env.user.can_confirm_quotation_account_client:
            raise UserError(_("You don't have the right to cancel an order!"))
        else:
            related_PO = self.env['purchase.order'].search([('travel_order_id', '=', self.id)])
            related_PO.button_cancel()
            related_PO.unlink()

            old_state = dict(self._fields['state'].selection).get(self.state)
            self.update({'state' : 'canceled'})
            new_state = dict(self._fields['state'].selection).get(self.state)

            message_body = _("State : %s → %s") % (old_state, new_state)

            self.message_post(body=message_body)

    def action_make_quotation(self):
        # if not self.env.user.can_confirm_quotation_passing_client:
        if not self.env.user.can_confirm_quotation_account_client:
            raise UserError(_("You don't have the right to do this action!"))
        else:
            old_state = dict(self._fields['state'].selection).get(self.state)
            self.update({'state' : 'quotation'})
            new_state = dict(self._fields['state'].selection).get(self.state)

            message_body = _("State : %s → %s") % (old_state, new_state)

            self.message_post(body=message_body)

    def action_view_purchases(self):
        purchases = self.mapped('purchases_id')
        action = self.env.ref('purchase.purchase_rfq').read()[0]

        if len(purchases) > 1:
            action['domain'] = [('id', 'in', purchases.ids)]
        elif len(purchases) == 1:
            form_view = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view

            action['res_id'] = purchases.id

        else:
            action = {'type' : 'ir.actions.act_window_close'}

        return action

    def action_view_purchase_invoice(self):
        purchase_invoices = self.mapped('purchase_invoice_ids')
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]

        if len(purchase_invoices) > 1:
            action['domain'] = [('id', 'in', purchase_invoices.ids)]
        elif len(purchase_invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view

            action['res_id'] = purchase_invoices.id
        else:
            action = {'type' : 'ir.actions.act_window_close'}

        context = {
            'default_type' : 'in_invoice',
        }

        if len(self) == 1:
            context.update({
                'default_partner_id' : self.partner_id.id,
                # 'default_partner_shipping_id' : self.partner_shipping_id.id,
                # 'default_invoice_payment_term_id' : self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
                'default_invoice_origin' : self.mapped('name'),
                # 'default_user_id' : self.user_id.id,
            })

        action['context'] = context

        return action

    def action_view_sale_invoice(self):
        sale_invoices = self.mapped('sale_invoice_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]

        if len(sale_invoices) > 1:
            action['domain'] = [('id', 'in', sale_invoices.ids)]
        elif len(sale_invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view

            action['res_id'] = sale_invoices.id
        else:
            action = {'type' : 'ir.actions.act_window_close'}

        context = {
            'default_type' : 'out_invoice',
        }

        if len(self) == 1:
            context.update({
                'default_partner_id' : self.partner_id.id,
                # 'default_partner_shipping_id' : self.partner_shipping_id.id,
                # 'default_invoice_payment_term_id' : self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
                'default_invoice_origin' : self.mapped('name'),
                # 'default_user_id' : self.user_id.id,
            })

        action['context'] = context

        return action

    def print_quotation_order(self):
        return self.env.ref('travel_agency.action_report_travelorder').report_action(self)

    def print_proforma(self):
        return self.env.ref('travel_agency.action_report_travelorder_proforma').report_action(self)

class TravelOrderLine(models.Model):
    _name = 'travel.order.line'
    _description = 'Travel Order Line'
    _order = 'sequence, id'

    product_type = fields.Selection(
        [
            ('ticket', 'Ticket'),
            ('fees', 'Fees'),
            ('voucher', 'Voucher'),
            ('app_fees', 'Application Fees')
        ],
        string="Product Type"
    )
    # product_id = fields.Many2one('product.product', string="Product", domain="[('active_product', '=', True)]")
    product_id = fields.Many2one('product.product', string="Product", domain=lambda self: [('category', '=', self.product_type)])
    name = fields.Char(string="Description", compute="_compute_name")
    # supplier = fields.Many2one('res.partner', string="Supplier", domain="[('supplier_rank', '=', 1)]")
    passenger = fields.Char(string="Passenger")
    ticket_number = fields.Char(string="Ticket Number")
    custom_descri = fields.Char(string="Custom Description")
    number = fields.Integer(string="Number of nights", default=1)
    quantity = fields.Integer(string="Quantity", default=1)
    price_unit = fields.Float(string="Price Unit")
    percent_commission = fields.Float(string="Commission (%)")
    amount_commission = fields.Float(string="Commission (Amount)", compute='compute_amount_commission')
    discount = fields.Float(string="Discount (%)", digits="Discount", default=0.0)
    tax_ids = fields.Many2many('account.tax', string="VAT")
    amount_tax = fields.Float(string="Other Taxes")
    amount_tva = fields.Float(string="Amount TVA", compute="_compute_amount", compute_sudo=True)
    price_subtotal = fields.Float(string="Subtotal", compute="_compute_amount", compute_sudo=True)
    price_total = fields.Float(string="Total", compute="_compute_amount", compute_sudo=True)
    price_tax = fields.Float(string="Total Tax", compute="_compute_amount", compute_sudo=True, readonly=True, store=True)

    order_id = fields.Many2one('travel.order', string="Order Reference", ondelete="cascade", readonly=True)

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")
    ], default=False, help="Technical field for UX purpose.")

    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id.currency_id'], store=True, string='Currency', readonly=True)

    day = fields.Many2one('res.day', string="Day")

    supplier = fields.Many2one('res.partner', string="Supplier", domain="[('no_g', '!=', False)]")

    status = fields.Selection([
        ('issued', 'Issued'),
        ('reissued', 'Reissued'),
        ('refund', 'Refund'),
        ('void', 'Void')
    ], string="Status")

    flight_class = fields.Char(string="Flight Class")
    flight_num = fields.Char(string="Flight Number")

    # date_from = fields.Date(string="Departure Date")
    # departure_time = fields.Char(string="Departure Time")
    departure_datetime = fields.Datetime(string="Departure date")

    # date_to = fields.Date(string="Arrival Date")
    # arrival_time = fields.Char(string="Arrival Time")
    arrival_datetime = fields.Datetime(string="Arrival date")

    passenger_title = fields.Selection([
        ('mr', 'MR'),
        ('mrs', 'MRS'),
        ('mss', 'MS'),
        ('chd', 'CHD'),
        ('inf', 'INF'),
    ], string="Passenger Title")
    passenger_firstname = fields.Char(string="Passenger's Firstname")
    passenger_lastname = fields.Char(string="Passenger's Lastname")
    passenger_fullname = fields.Char(string="Passenger's Fullname", compute="_compute_fullname", readonly=True)

    start_point = fields.Char(string="Departure")
    transit = fields.Char(string="Transit")
    end_point = fields.Char(string="Arrival")
    journey = fields.Char(string="Journey", compute="_compute_journey", readonly=True)

    baggage_allow = fields.Char(string="Baggage Allow")
    terminal_check_in = fields.Char(string="Terminal Check In")
    terminal_arrival = fields.Char(string="Terminal Arrival")
    due_date = fields.Date(string="Due Date")
    creation_date = fields.Date(string="Creation Date")

    supplier_invoice_ref = fields.Char(string="Supplier invoice reference")

    supplier_invoice_generated = fields.Boolean(string="Supplier invoice has been generated", default=False, copy=False)

    sequence = fields.Integer(string="Sequence", default=10)

    company_code = fields.Char(string="Company Code")

    @api.onchange('company_code')
    def onchange_company_code(self):
        if self.company_code:
            self.company_code = self.company_code.upper()
            if not (self.supplier and self.supplier.supplier_type == 'subcontracting'):
                company = self.env['res.partner'].search([('company_code', '=', self.company_code)])

                if company:
                    self.supplier = company.id

    @api.onchange('supplier')
    def onchange_supplier(self):
        if self.supplier and not self.supplier.supplier_type == 'subcontracting':
            self.company_code = self.supplier.company_code

    @api.depends('journey', 'ticket_number', 'passenger_fullname', 'custom_descri', 'product_id', 'supplier_invoice_ref')
    def _compute_name(self):
        for record in self:
            name = []
            if record.journey:
                name.append(record.journey)
            if record.ticket_number:
                name.append(record.ticket_number)
            if record.passenger_fullname:
                name.append(record.passenger_fullname)
            if record.custom_descri:
                name.append(record.custom_descri)

            if name:
                record.name = " - ".join(name)
            elif record.supplier_invoice_ref:
                record.name = record.supplier_invoice_ref
            elif record.supplier:
                record.name = record.supplier.name
            elif record.product_id:
                record.name = record.product_id.name
            else:
                record.name = ""


    @api.depends('start_point', 'transit', 'end_point')
    def _compute_journey(self):
        for record in self:
            # points = [record.start_point, record.transit, record.end_point] if record.transit else [record.start_point, record.end_point]
            points = [record.start_point, record.transit, record.end_point]
            points = [item for item in points if item]
            # record.journey = ' - '.join(points) if all(points) else ''
            record.journey = ' - '.join(points)

    @api.depends('passenger_title', 'passenger_firstname', 'passenger_lastname')
    def _compute_fullname(self):
        for record in self:
            record.passenger_fullname = ' '.join([item for item in (record.passenger_firstname, record.passenger_lastname) if item])
            if record.passenger_fullname:
                # record.passenger_fullname = ' '.join([item in [dict(record._fields['passenger_title'].selection).get(self.record), record.passenger_fullname] if item])
                record.passenger_fullname = ' '.join([item for item in (dict(record._fields['passenger_title'].selection).get(record.passenger_title), record.passenger_fullname) if item])
            else:
                record.passenger_fullname = ''

    # --------------------------------------------------------
    # Compute amount commission value
    # --------------------------------------------------------
    @api.depends('price_unit','percent_commission')
    def compute_amount_commission(self):
        # if self.percent_commission < 0 :
        #     raise UserError('Invalid percent commission value.')
        # else :
        for line in self :
            line.amount_commission = (line.price_unit * line.percent_commission) / 100.0

    # --------------------------------------------------------
    # Name Auto setting
    # --------------------------------------------------------
    @api.onchange('product_id')
    def onchange_product(self):
        if self.order_id.document_type == 'to' and not self.product_id:
            self.product_id = self.env['product.product'].search([('name', '=', 'TO')]).id

        # Set tax_ids field if needed
        self.update({'tax_ids' : self.product_id.taxes_id})

        # Filter supplier
        active_suppliers = [seller.name for seller in self.product_id.seller_ids]
        suppliers = self.env['res.partner'].search([('id_supplier_incadea', '!=', False)])

        for supplier in suppliers:
            if self.product_id:
                supplier.write({'active_supplier' : supplier in active_suppliers})
            else:
                supplier.write({'active_supplier' : True})

        # self.percent_commission = self.product_id.commission
        self.tax_ids = self.product_id.taxes_id

        # Set product_type if not set
        if self.product_id and not self.product_type:
            self.product_type = self.product_id.category


    @api.onchange('product_type')
    def onchange_producttype(self):
        for record in self:
            products = self.env['product.product'].search([])

            for product in products:
                product.active_product = True if not record.product_type else product.category == record.product_type

            active_products = self.env['product.product'].search([('category', '=', record.product_type)])

            if len(active_products) == 1:
                record.product_id = active_products.id

    # @api.onchange('supplier')
    # def onchange_supplier(self):
    #     # Filter product
    #     seller = self.env['product.supplierinfo'].search([('name', '=', self.supplier.id)])

    #     products = self.env['product.product'].search([])

    #     for product in products:
    #         if self.supplier:
    #             product.write({'active_product' : seller in product.seller_ids})
    #         else:
    #             product.write({'active_product' : True})

    @api.onchange('passenger_firstname')
    def onchange_firstname(self):
        self.passenger_firstname = '' if not self.passenger_firstname else self.passenger_firstname.upper()
        # name = []
        # if self.journey:
        #     name.append(self.journey)
        # if self.ticket_number:
        #     name.append(self.ticket_number)
        # if self.passenger_fullname:
        #     name.append(self.passenger_fullname)
        # if self.custom_descri:
        #     name.append(self.custom_descri)
        # self.name = " - ".join(name)

    @api.onchange('passenger_lastname')
    def onchange_lastname(self):
        self.passenger_lastname = '' if not self.passenger_lastname else self.passenger_lastname.upper()
        # name = []
        # if self.journey:
        #     name.append(self.journey)
        # if self.ticket_number:
        #     name.append(self.ticket_number)
        # if self.passenger_fullname:
        #     name.append(self.passenger_fullname)
        # if self.custom_descri:
        #     name.append(self.custom_descri)
        # self.name = " - ".join(name)

    # @api.onchange('ticket_number')
    # def onchange_ticket_number(self):
    #     name = []
    #     if self.journey:
    #         name.append(self.journey)
    #     if self.ticket_number:
    #         name.append(self.ticket_number)
    #     if self.passenger_fullname:
    #         name.append(self.passenger_fullname)
    #     if self.custom_descri:
    #         name.append(self.custom_descri)
    #     self.name = " - ".join(name)

    @api.onchange('start_point')
    def onchange_departure(self):
        self.start_point = '' if not self.start_point else self.start_point.upper()
        # name = []
        # if self.journey:
        #     name.append(self.journey)
        # if self.ticket_number:
        #     name.append(self.ticket_number)
        # if self.passenger_fullname:
        #     name.append(self.passenger_fullname)
        # if self.custom_descri:
        #     name.append(self.custom_descri)
        # self.name = " - ".join(name)

    @api.onchange('transit')
    def onchange_transit(self):
        self.transit = '' if not self.transit else self.transit.upper()

    @api.onchange('end_point')
    def onchange_arrival(self):
        self.end_point = '' if not self.end_point else self.end_point.upper()
        # name = []
        # if self.journey:
        #     name.append(self.journey)
        # if self.ticket_number:
        #     name.append(self.ticket_number)
        # if self.passenger_fullname:
        #     name.append(self.passenger_fullname)
        # if self.custom_descri:
        #     name.append(self.custom_descri)
        # self.name = " - ".join(name)

    

    # @api.onchange('custom_descri')
    # def onchange_custom_descri(self):
    #     name = []
    #     if self.journey:
    #         name.append(self.journey)
    #     if self.ticket_number:
    #         name.append(self.ticket_number)
    #     if self.passenger_fullname:
    #         name.append(self.passenger_fullname)
    #     if self.custom_descri:
    #         name.append(self.custom_descri)
    #     self.name = " - ".join(name)
    # --------------------------------------------------------

    @api.depends('quantity', 'number', 'discount', 'price_unit', 'tax_ids', 'amount_tax', 'amount_commission')
    def _compute_amount(self):
        """
            Compute the amounts of the Travel Order Line
        """
        for line in self:
            price = line.amount_commission if line.mapped('order_id').document_type == 'to' else line.price_unit # * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_ids.compute_all(price, line.order_id.currency_id, line.quantity * line.number, product=line.product_id, partner=line.order_id.partner_shipping_id)

            line.update({
                'amount_tva' : sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_tax' : sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])) + line.amount_tax,
                'price_total' : taxes['total_included'] + line.amount_tax + (line.quantity *line.number * line.price_unit) if line.mapped('order_id').document_type == 'to' else taxes['total_included'] + line.amount_tax ,
                'price_subtotal' : taxes['total_excluded'] + line.amount_tax + (line.quantity * line.number * line.price_unit) if line.mapped('order_id').document_type == 'to' else taxes['total_excluded'] + line.amount_tax ,
                # 'price_subtotal' : taxes['total_excluded'] + (line.quantity * line.number * line.price_unit) if line.mapped('order_id').document_type == 'to' else taxes['total_excluded'] ,
            })

    def duplicate(self):
        copy = self.copy(default={'order_id' : self.order_id.id})