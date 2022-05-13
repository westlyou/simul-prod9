# ############################################################################################################
#                                   This module was created by Muriel Rémi                                   #
#                                         Creation date: 19 May 2021                                         #
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

class ResPartner(models.Model):

    _inherit = "res.partner"
    id_incadea = fields.Char(string="ID Incadea")
    # no_g = fields.Char(string="No G")

    def import_from_incadea(self):
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

            session.cwd(logfile_location)

            state = True
        except Exception as e:
            print("Error : Impossible to connect to the FTP server\n{}".format(e))

        # ------------------------------------------------------------------------------------
        # Retrieving files from the FTP server
        # ------------------------------------------------------------------------------------
        if state:
            # log_byte = BytesIO()
            # session.retrbinary('RETR server.log', log_byte.write)
            # log_byte.seek(0)

            # logs = [log_byte.read()]

            session.cwd(data_source_folder)

            contents = session.nlst()
            if any(['CLIENTS_D_INCADEA' in content or 'FOURNISSEURS__D_INCADEA' in content for content in contents]):
                logs = []

                logs.append(bytes("\
                    #####################################################################################################################################\n\
                    #                                                                                                                                   #\n\
                    #                                              Import Customers / Suppliers from Incadea                                            #\n\
                    #                                                                                                                                   #\n\
                    #####################################################################################################################################\n",
                'utf-8'))

                logs.append(bytes("%s: INFO successfully connected to the FTP server\n" % dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), 'utf-8'))

                # filename = 'CLIENTS_INCADEA.csv'

                customer_columns = [
                    'EntryNo_G', 
                    'OrderType_G', 
                    'No_G', 
                    'LastName_G', 
                    'FirstName_G', 
                    'Address_G', 
                    'Address2_G', 
                    'City_G', 
                    'Contact_G', 
                    'PhoneNo_G', 
                    'CustomerPostingGroup_G', 
                    'LanguageCode_G', 
                    'PaymentTermsCode_G', 
                    'Blocked_G', 
                    'InvoiceDiscCode_G', 
                    'CountryCode_G', 
                    'PaymentMethodCode_G', 
                    'ApplicationMethod_G', 
                    'AllowQuantityDisc_G', 
                    'PricesIncludingVAT_G', 
                    'LocationCode_G', 
                    'FaxNo_G', 
                    'GenBusPostingGroup_G', 
                    'PostCode_G', 
                    'County_G', 
                    'EMail_G', 
                    'ReminderTermsCode_G', 
                    'VATBusPostingGroup_G', 
                    'Reserve_G', 
                    'HomePhoneNo_G', 
                    'MobilePhoneNo_G', 
                    'AddressSalutationCode_G', 
                    'LetterSalutationCode_G', 
                    'TitleCode_G', 
                    'CustomerType_G', 
                    'LaborPriceGroup_G', 
                    'ExtServicePriceGroup_G', 
                    'VehicleSalesPriceGroup_G', 
                    'ItemSalesPriceGroup_G', 
                    'HomeMobilePhoneNo_G', 
                    'ShowDiscount_G', 
                    'OptionSalesPriceGroup_G', 
                    'AddServiceSurcharges_G', 
                    'ProposalForAlternativePart_G', 
                    'AdditionalTax_G', 
                    'THIRDPARTYNo_G', 
                    'STAT',
                    'NIF',
                ]

                supplier_columns = [
                    'EntryNo_G', 
                    'OrderType_G', 
                    'No_G', 
                    'LastName_G', 
                    'FirstName_G', 
                    'Address_G', 
                    'Address2_G', 
                    'City_G', 
                    'Contact_G', 
                    'PhoneNo_G', 
                    'VendorPostingGroup_G', 
                    'LanguageCode_G', 
                    'PaymentTermsCode_G', 
                    'Blocked_G', 
                    'InvoiceDiscCode_G', 
                    'CountryCode_G', 
                    'PaymentMethodCode_G', 
                    'ApplicationMethod_G', 
                    'PricesIncludingVAT_G', 
                    'FaxNo_G', 
                    'GenBusPostingGroup_G', 
                    'PostCode_G', 
                    'County_G', 
                    'EMail_G', 
                    'VATBusPostingGroup_G', 
                    'Reserve_G', 
                    'MobilePhoneNo_G', 
                    'AddressSalutationCode_G', 
                    'LetterSalutationCode_G', 
                    'TitleCode_G', 
                    'CustomerType_G', 
                    'CurrencyCode_G', 
                    'PaytoVendorNo_G', 
                    'AdditionalTax_G', 
                    'FiscalIdCode_G', 
                    'VendorGroupCode_G', 
                    'VendorOfImportation_G', 
                ]

                customer_dfs = []
                supplier_dfs = []
                success_import = []
                failure_import = {}

                for content in contents:
                    if 'CLIENTS_D_INCADEA' in content or 'FOURNISSEURS__D_INCADEA' in content:
                        byte = BytesIO()
                        session.retrbinary('RETR ' + content, byte.write)
                        byte.seek(0)

                        if 'CLIENTS_D_INCADEA' in content:
                            df = pd.read_csv(byte, dtype=str, encoding='latin1', sep=';', names=customer_columns)
                            if df.empty:
                                session.rename(data_source_folder + "/" + content, processed_data_folder + "/" + content)
                                logs.append(bytes("%s: WARNING Empy file: %s was successfully moved to %s\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), content, processed_data_folder), 'utf-8'))
                                continue
                            df = df.fillna("")
                            df["source"] = content
                            customer_dfs.append(df)
                        else:
                            df = pd.read_csv(byte, dtype=str, encoding='latin1', sep=';', names=supplier_columns)
                            if df.empty:
                                session.rename(data_source_folder + "/" + content, processed_data_folder + "/" + content)
                                logs.append(bytes("%s: WARNING Empy file: %s was successfully moved to %s\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), content, processed_data_folder), 'utf-8'))
                                continue
                            df = df.fillna("")
                            df["source"] = content
                            supplier_dfs.append(df)

                        byte.close()

                if len(customer_dfs):
                    customers_data = pd.concat(customer_dfs)

                    # Import  of clients
                    for index, row in customers_data.iterrows():
                        no_g = row['No_G']
                        record = self.search([('no_g', '=', no_g)])
                        if len(record.ids) > 1:
                            logs.append(bytes("%s: WARNING Aborting Import: Duplicate record found for Account N° %s (%s)\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g, ", ".join([item.name for item in record])), 'utf-8'))
                            if row['source'] not in failure_import:
                                failure_import[row['source']] = []

                            failure_import[row['source']].append({'no_g' : no_g, 'reason' : 'Duplicated'})

                            continue
                        c_name = ' '.join((row['FirstName_G'] + ' ' + row['LastName_G']).split())
                        if not c_name:
                            logs.append(bytes("%s: WARNING Aborting Import: Empty name for Account N° %s (file source : %s)\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g, row['source']), 'utf-8'))
                            continue
                        contact = {
                            'id_incadea' : row['EntryNo_G'],
                            'name' : c_name,
                            'street' : ' '.join(row['Address_G'].split()),
                            'street2' : ' '.join(row['Address2_G'].split()),
                            'city' : ' '.join(row['City_G'].split()),
                            'phone' : ' '.join(row['Contact_G'].split()),
                            'mobile' : ' '.join(row['PhoneNo_G'].split()),
                            'c_posting_group' : row['CustomerPostingGroup_G'],
                            'lang' : 'fr_FR' if row['LanguageCode_G'] == 'FR' else 'en_US' if row['LanguageCode_G'] == 'EN' else '',
                            'country_id': self.env['res.country'].search([('code', '=', row['CountryCode_G'])]).id,
                            'c_gen_bus_pg' : ' '.join(row['GenBusPostingGroup_G'].split()),
                            # 'in_group' : ' '.join(row['GenBusPostingGroup_G'].split()) == 'C10',
                            'email' : ' '.join(row['EMail_G'].split()),
                            'c_vat_bus_pg' : ' '.join(row['VATBusPostingGroup_G'].split()),
                            'company_type' : 'person' if row['CustomerType_G'] == 'Homme' else 'company',
                            'nif' : ' '.join(row['NIF'].replace("'", "").split()),
                            'stat' : ' '.join(row['STAT'].replace("'", "").split()),
                            'customer_rank' : 1,
                            'supplier_rank' : record.supplier_rank or 0,
                        }
                        
                        if len(record.ids) == 1:
                            # Check if there was any modification in the contact
                            change = False
                            updates = {}
                            for key in contact:
                                if key != 'country_id':
                                    if contact[key] != record[key]:
                                        updates[key] = {'old' : record[key], 'new' : contact[key]}
                                        change = True
                                else:
                                    if contact[key] != record.country_id.id:
                                        updates[key] = {'old' : record.country_id.id, 'new' : contact[key]}
                                        change = True

                            # # If so, update the contact, do nothing otherwise
                            if change:
                                record.write(contact)
                                message_body = ""
                                for key in updates:
                                    message_body += "%s: %s → %s<br/>" % (key, updates[key]['old'], updates[key]['new'])
                                record.message_post(body=message_body)
                                logs.append(bytes("%s: INFO Customer N° %s successfully updated (updates : %s)\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g, updates), 'utf-8'))
                            else:
                                logs.append(bytes("%s: INFO No Update for No_G = %s with file %s\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g, row['source']), 'utf-8'))
                        else:
                            contact['no_g'] = no_g
                            self.create(contact)
                            logs.append(bytes("%s: INFO Customer N° %s successfully created\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g), 'utf-8'))

                        if row['source'] not in success_import:
                            success_import.append(row['source'])

                if len(supplier_dfs):
                    suppliers_data = pd.concat(supplier_dfs)

                    # Import of suppliers
                    for index, row in suppliers_data.iterrows():
                        no_g = row['No_G']
                        record = self.search([('no_g', '=', no_g)])
                        if len(record.ids) > 1:
                            logs.append(bytes("%s: WARNING Aborting Import: Duplicate record found for Account N° %s (%s)\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g, ", ".join([item.name for item in record])), 'utf-8'))
                            if row['source'] not in failure_import:
                                failure_import[row['source']] = []

                            failure_import[row['source']].append({'no_g' : no_g, 'reason' : 'Duplicated'})
                            continue

                        s_name = ' '.join((row['FirstName_G'] + ' ' + row['LastName_G']).split())
                        if not s_name:
                            logs.append(bytes("%s: WARNING Aborting Import: Empty name for Account N° %s (file source : %s)\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g, row['source']), 'utf-8'))
                            continue
                        contact = {
                            'id_incadea' : row['EntryNo_G'],
                            'name' : s_name,
                            'street' : ' '.join(row['Address_G'].split()),
                            'street2' : ' '.join(row['Address2_G'].split()),
                            'city' : ' '.join(row['City_G'].split()),
                            'phone' : ' '.join(row['Contact_G'].split()),
                            'mobile' : ' '.join(row['PhoneNo_G'].split()),
                            's_posting_group' : ' '.join(row['VendorPostingGroup_G'].split()),
                            'lang' : 'fr_FR' if row['LanguageCode_G'] == 'FR' else 'en_US' if row['LanguageCode_G'] == 'EN' else '',
                            'country_id': self.env['res.country'].search([('code', '=', row['CountryCode_G'])]).id,
                            's_gen_bus_pg' : ' '.join(row['GenBusPostingGroup_G'].split()),
                            # 'in_group' : ' '.join(row['GenBusPostingGroup_G'].split()) == 'C10',
                            'email' : ' '.join(row['EMail_G'].split()),
                            's_vat_bus_pg' : ' '.join(row['VATBusPostingGroup_G'].split()),
                            'company_type' : 'person' if row['CustomerType_G'] == 'Homme' else 'company',
                            'supplier_rank' : 1,
                            'customer_rank' : record.customer_rank or 0,
                        }
                        
                        if len(record.ids) == 1:
                            # Check if there was any modification in the contact
                            change = False
                            updates = {}
                            for key in contact:
                                if key != 'country_id':
                                    if contact[key] != record[key]:
                                        updates[key] = {'old' : record[key], 'new' : contact[key]}
                                        change = True
                                else:
                                    if contact[key] != record.country_id.id:
                                        updates[key] = {'old' : record.country_id.id, 'new' : contact[key]}
                                        change = True

                            # # If so, update the contact, do nothing otherwise
                            if change:
                                record.write(contact)
                                message_body = ""
                                for key in updates:
                                    message_body += "%s: %s → %s<br/>" % (key, updates[key]['old'], updates[key]['new'])
                                record.message_post(body=message_body)
                                logs.append(bytes("%s: INFO Supplier N° %s successfully updated (updates : %s)\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g, updates), 'utf-8'))
                            else:
                                logs.append(bytes("%s: INFO No Update for No_G = %s with file %s\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g, row['source']), 'utf-8'))
                        else:
                            contact['no_g'] = no_g
                            self.create(contact)
                            logs.append(bytes("%s: INFO Supplier N° %s successfully created\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), no_g), 'utf-8'))

                        if row['source'] not in success_import:
                            success_import.append(row['source'])

                for filename in success_import:
                    if filename not in failure_import:
                        session.rename(data_source_folder + "/" + filename, processed_data_folder + "/" + filename)
                        logs.append(bytes("%s: INFO %s successfully moved to %s\n" % (dt.strftime(dt.now(), '%Y-%m-%d %H:%M:%S'), filename, processed_data_folder), 'utf-8'))

                log = b''.join(logs)
                session.cwd(logfile_location)
                session.storbinary('STOR contacts_import%s.log' % dt.strftime(dt.now(), '%Y%m%d%H%M%S'), BytesIO(log))
                # log_byte.close()
            session.quit()
        else:
            raise UserError('Unable to connect to the ftp server')