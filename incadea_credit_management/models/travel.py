# ############################################################################################################
#                                   This module was created by Muriel Rémi                                   #
#                                      Creation date: 25 Septembre 2021                                      #
# ############################################################################################################
# -*- coding: utf-8 -*-

from odoo import fields, api, models, _
from odoo.exceptions import UserError

import ftplib
import os
import pandas as pd
import json
from cryptography.fernet import Fernet
from io import BytesIO
from datetime import datetime as dt

class TravelOrder(models.Model):
    _inherit = "travel.order"

    button_to_show = fields.Selection([
        ('none', 'None'), 
        ('confirm', 'Confirm'), 
        ('confirm_confirm', 'Confirm confirm')
    ], string="Button to show", store=False, compute="_get_button_to_show")

    def _get_button_to_show(self):
        if not self.env.user.can_confirm_quotation:
            self.button_to_show = 'none'
        else:
            if self.partner_id.credit_limit == 0:
                self.button_to_show = 'confirm'
            else:
                if self.partner_id.customer_type == 'passing':
                    self.button_to_show = 'confirm'
                else:
                    if self.partner_id.general_credit < self.partner_id.credit_limit:
                        self.button_to_show = 'confirm'
                    else:
                        if self.env.user.can_confirm_quotation_account_client:
                            self.button_to_show = 'confirm_confirm'
                        else:
                            self.button_to_show = 'confirm'


    def action_confirm_confirm(self):
        return super(TravelOrder, self).action_confirm()

    def action_confirm(self):
        if not self.env.user.can_confirm_quotation:
            raise UserError(_("You don't have the right to confirm a quotation"))
        else:
            if self.partner_id.customer_type == 'passing':
                return super(TravelOrder, self).action_confirm()
            elif self.partner_id.credit_limit == 0:
                raise UserError(_("Quotation cannot be confirmed, credit limit undefined for %s") % self.partner_id.name)
            else:
                if self.partner_id.general_credit < self.partner_id.credit_limit:
                    return super(TravelOrder, self).action_confirm()
                else:
                    if self.env.user.can_confirm_quotation_account_client:
                        return self.action_confirm_confirm()
                    else:
                        alert_msg = _("Can't confirm this quotation!\n" + \
                                        "* Incadea Credit : %s\n" + \
                                        "* General Credit : %s\n" + \
                                        "* This Credit : %s\n" + \
                                        "* Number of Quotation in Credit : %s\n") % (self.partner_id.incadea_credit, self.partner_id.general_credit, self.amount_total, len(self.search([('partner_id', '=', self.partner_id.id), ('state', '=', 'quotation')]))
                        )
                        raise UserError(alert_msg)

class ResPartner(models.Model):
    _inherit = "res.partner"

    credit_limit = fields.Float(string="Credit Limit")
    incadea_credit = fields.Float(string="Incadea Credit")
    general_credit = fields.Float(string="Credit", default=0, compute="_compute_general_credit")

    def _compute_general_credit(self):
        for record in self:
            unpaid_quotes = self.env['travel.order'].search(['&', ('partner_id', '=', record.id), ('state', 'in', ('quotation', 'accepted'))])
            record.general_credit = sum([quote.amount_total for quote in unpaid_quotes]) + record.incadea_credit

    def get_credit_infos(self):
        __dir__ = os.path.dirname(__file__)

        static_folder_path = os.path.join(os.path.dirname(__dir__), "static")
        _KEY_ = b'_Eb-ez6gdiB8bU89Y8cwl9LlGFC_0Mbv1CbLS8qNVio='

        with open(static_folder_path + "/config.json") as json_data_file:
            _CONFIG_ = json.load(json_data_file)

        fernet = Fernet(_KEY_)

        ftp_host = _CONFIG_['ftp']['host']
        ftp_user = _CONFIG_['ftp']['username']
        ftp_pwd = fernet.decrypt(bytes(_CONFIG_['ftp']['password'], 'utf-8')).decode('utf-8')
        data_source_folder = _CONFIG_['data']['source']
        processed_data_folder = _CONFIG_['data']['processed']
        logfile_location = _CONFIG_['logfile']['location']

        
        # ------------------------------------------------------------------------------------
        # Connection to the ftp
        # ------------------------------------------------------------------------------------
        state, session = False, None
        logs = []

        try:
            session = ftplib.FTP(ftp_host, ftp_user, ftp_pwd)
            state = True
        except Exception as e:
            print("Error : Impossible to connect to the FTP server\n{}".format(e))

        # ------------------------------------------------------------------------------------
        # Retrieving files from the FTP server
        # ------------------------------------------------------------------------------------
        if state:
            session.cwd(data_source_folder)

            contents = session.nlst()

            if any(['CREDITLIMIT_D_INCADEA' in content for content in contents]):
                # session.cwd(logfile_location)
                # log_byte = BytesIO()
                # session.retrbinary('RETR server.log', log_byte.write)
                # log_byte.seek(0)

                # logs = [log_byte.read()]
                logs = []

                logs.append(bytes("\
                    #####################################################################################################################################\n\
                    #                                                                                                                                   #\n\
                    #                                                      Import Credits from Incadea                                                  #\n\
                    #                                                                                                                                   #\n\
                    #####################################################################################################################################\n",
                'utf-8'))

                logs.append(bytes("%s: INFO successfully connected to the FTP server\n" % dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), 'utf-8'))


                columns = ["no_g", "credit", "limit"]

                dfs = []
                success_import = []
                failure_import = {}

                for content in contents:
                    if 'CREDITLIMIT_D_INCADEA' in content:
                        byte = BytesIO()
                        session.retrbinary('RETR ' + content, byte.write)
                        byte.seek(0)

                        df = pd.read_csv(byte, dtype=str, encoding='latin1', sep=';', names=columns)
                        if df.empty:
                            session.rename(data_source_folder + "/" + content, processed_data_folder + "/" + content)
                            logs.append(bytes("%s: WARNING Empy file: %s was successfully moved to %s\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), content, processed_data_folder), 'utf-8'))
                            continue
                        df = df.fillna("")
                        df["source"] = content
                        dfs.append(df)

                        byte.close()

                if len(dfs):
                    credits_data = pd.concat(dfs)

                    for index, row in credits_data.iterrows():
                        no_g = row['no_g']
                        record = self.search([('no_g', '=', no_g)])

                        if len(record.ids) > 1:
                            logs.append(bytes("%s: WARNING Aborting Import: Duplicate record found for Account N° %s (%s)\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g, ", ".join([item.name for item in record])), 'utf-8'))
                            if row['source'] not in failure_import:
                                failure_import[row['source']] = []

                            failure_import[row['source']].append({'no_g' : no_g, 'reason' : 'Duplicated'})

                            continue

                        contact = {
                            'credit_limit' : float(row['limit'].replace(' ', '').replace(',', '.')),
                            'incadea_credit' : float(row['credit'].replace(' ', '').replace(',', '.')),
                        }
                        
                        if len(record.ids) == 1:
                            # Check if there was any modification in the contact
                            change = False
                            updates = {}
                            for key in contact:
                                if contact[key] != record[key]:
                                    updates[key] = {'old' : record[key], 'new' : contact[key]}
                                    change = True


                            # If so, update the contact, do nothing otherwise
                            if change:
                                record.write(contact)
                                message_body = ""
                                for key in updates:
                                    message_body += "%s: %s → %s<br/>" % (key, updates[key]['old'], updates[key]['new'])
                                record.message_post(body=message_body)
                                logs.append(bytes("%s: INFO Customer N° %s Credit Infos successfully updated (updates : %s)\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g, updates), 'utf-8'))
                            else:
                                logs.append(bytes("%s: INFO No Update for No_G = %s with file %s\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g, row['source']), 'utf-8'))
                        else:
                            logs.append(bytes("%s: WARNING recored with No_G = %s not found! (source file %s)\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g, row['source']), 'utf-8'))
                            # if row['source'] not in failure_import:
                            #     failure_import[row['source']] = []
                            # failure_import[row['source']].append({'no_g' : no_g, 'reason' : 'Record not found'})

                        if row['source'] not in success_import:
                            success_import.append(row['source'])

                for filename in success_import:
                    if filename not in failure_import:
                        session.rename(data_source_folder + "/" + filename, processed_data_folder + "/" + filename)
                        logs.append(bytes("%s: INFO %s successfully moved to %s\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), filename, processed_data_folder), 'utf-8'))

                log = b''.join(logs)
                session.cwd(logfile_location)
                session.storbinary('STOR credit_infos_import%s.log' % dt.strftime(dt.now(), '%Y%m%d%H%M%S'), BytesIO(log))
                # log_byte.close()
            session.quit()

        else:
            raise UserError('Unable to connect to the ftp server')

class ResUsers(models.Model):
    _inherit = "res.users"

    can_confirm_quotation = fields.Boolean(string="Can confirm quotation", default=False)
    # can_confirm_quotation_even_credit_limit_is_reached = fields.Boolean(string="Can confirm quotation even when credit limit is reached", default=False)
    can_confirm_quotation_account_client = fields.Boolean(string="Can confirm quotation even when credit limit is reached", default=False)
    # can_confirm_quotation_account_client = fields.Boolean(string="Can confirm quotation of account client", default=False)
    # can_confirm_quotation_passing_client = fields.Boolean(string="Can confirm quotation of passing client", default=False)

    @api.onchange('can_confirm_quotation')
    def _set_no_right(self):
        if not self.can_confirm_quotation:
            self.update({
                # 'can_confirm_quotation_even_credit_limit_is_reached' : False,
                # 'can_confirm_quotation_passing_client' : False,
                'can_confirm_quotation_account_client' : False,
            })

    # @api.onchange('can_confirm_quotation_even_credit_limit_is_reached')
    # def _set_right1(self):
    #     if self.can_confirm_quotation_even_credit_limit_is_reached:
    #         self.update({'can_confirm_quotation' : False})

    @api.onchange('can_confirm_quotation_account_client')
    def _set_right2(self):
        if self.can_confirm_quotation_account_client:
            self.update({
                'can_confirm_quotation' : True,
                # 'can_confirm_quotation_even_credit_limit_is_reached' : True
            })

    # @api.onchange('can_confirm_quotation_passing_client')
    # def _set_right3(self):
    #     if self.can_confirm_quotation_passing_client:
    #         self.update({
    #             'can_confirm_quotation' : True,
    #             # 'can_confirm_quotation_even_credit_limit_is_reached' : True,
    #             'can_confirm_quotation_account_client' : True
    #         })