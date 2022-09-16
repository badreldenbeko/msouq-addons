
import base64
import datetime
import io
import re
import requests
import PyPDF2
import json

from dateutil.relativedelta import relativedelta
from PIL import Image
from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import Warning, UserError, AccessError
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import url_for
from odoo.tools import sql
import os
from twilio.rest import Client
from odoo.exceptions import ValidationError

class slideCustomChannel(models.Model):
    _inherit = 'slide.channel'

    nbr_url = fields.Integer('Videos', compute='_compute_slides_statistics', store=True)
    channel_id = fields.Integer()
    @api.model
    def getUserGroupId(self):
        try:
            hr_employee = self.env['hr.employee'].search([('is_coach','=',True)])
            user_id = []
            for i in hr_employee:
                if i.user_id:
                    user_id.append(i.user_id.id)
            return [('id', 'in', user_id)]
        except Exception as e:
            pass
    user_id = fields.Many2one('res.users', required=True,string='Coach',domain=getUserGroupId)
    def _action_add_members(self, target_partners, **member_values):
        """ Add the target_partner as a member of the channel (to its slide.channel.partner).
        This will make the content (slides) of the channel available to that partner.

        Returns the added 'slide.channel.partner's (! as sudo !)
        """
        to_join = self._filter_add_members(target_partners, **member_values)
        if to_join:
            existing = self.env['slide.channel.partner'].sudo().search([
                ('channel_id', 'in', self.ids),
                ('partner_id', 'in', target_partners.ids)
            ])
            existing_map = dict((cid, list()) for cid in self.ids)
            for item in existing:
                existing_map[item.channel_id.id].append(item.partner_id.id)

            to_create_values = [
                dict(channel_id=channel.id, partner_id=partner.id, **member_values)
                for channel in to_join
                for partner in target_partners if partner.id not in existing_map[channel.id]
            ]
            #if self.env["slide.channel.partner"].search([("partner_id",'=',target_partners.ids),("channel_id","=",self.ids)])
            #slide_partners_sudo = self.env['slide.channel.partner'].sudo().create(to_create_values)
            #to_join.message_subscribe(partner_ids=target_partners.ids, subtype_ids=[self.env.ref('website_slides.mt_channel_slide_published').id])
            #return slide_partners_sudo
        return self.env['slide.channel.partner'].sudo()

    @api.onchange("user_id",'name')
    def create_update_channel(self):
        if self.user_id.id != 0 and self.channel_id !=0:

            channel = self.env['mail.channel'].search([('id','=',self.channel_id)])
            if channel:
                self.env['mail.channel'].write({
                    'name': str(self.name)+" "+ self.user_id.name if self.user_id else '' ,
                    'channel_type': "channel",
                    'public': "private",
                    'description': self.description,

                })
                try:
                    self.env['mail.channel.partner'].create({
                        "partner_id": self.user_id.partner_id.id,
                        "channel_id": channel.id,
                        "partner_email": self.user_id.partner_id.email,
                    })
                except Exception as e:
                    pass

    @api.model
    def create(self, vals):
        coach = super(slideCustomChannel,self).create(vals)
        if coach.channel_id != 0:
            channel = self.env['mail.channel'].search([("id","=",coach.channel_id)])
            channel.write({
                    'name': str(coach.name) + " " + coach.user_id.name if coach.user_id else '',
                    'channel_type': "channel",
                    'public': "private",
                    'description': coach.description,
                })
            try:
                self.env['mail.channel.partner'].create({
                    "partner_id": coach.user_id.partner_id.id,
                    "channel_id": channel.id,
                    "partner_email": coach.user_id.partner_id.email,
                })
            except Exception as e:
                pass
        else:
            channel = self.env['mail.channel'].create({
                'name': str(coach.name) + " " + coach.user_id.name if coach.user_id else '',
                'public': "private",
                'description': coach.description,
                'channel_type': "channel",
            })
            coach.channel_id = channel.id
            try:
                self.env['mail.channel.partner'].create({
                    "partner_id": coach.user_id.partner_id.id,
                    "channel_id": channel.id,
                    "partner_email": coach.user_id.partner_id.email,
                })

            except Exception as e:
                pass
        return coach

    def action_done_show_wizard(self):
        production_ids = self.env['slide.channel.partner'].browse(self.channel_partner_ids)
        lines = []
        for line in production_ids:
            vals = (0, 0, {
                'name': line.id.partner_id.id,
                'email': line.id.partner_id.email
            })
            lines.append(vals)
        return {'type': 'ir.actions.act_window',
                'name': _('Send WhatsApp Message'),
                'res_model': 'student.whatsapp',
                'target': 'new',
                'view_id': self.env.ref('e_learning_custom.view_student_whatsapp_wizard').id,
                'view_mode': 'form',
                'context': {'default_partner_id': lines}
                }

    def action_done_show_wizard_sms(self):
        production_ids = self.env['slide.channel.partner'].browse(self.channel_partner_ids)
        lines = []
        for line in production_ids:
            vals = (0, 0, {
                'name': line.id.partner_id.id,
                'email': line.id.partner_id.email
            })
            lines.append(vals)
        return {'type': 'ir.actions.act_window',
                'name': _('Send Sms Message'),
                'res_model': 'student.sms',
                'target': 'new',
                'view_id': self.env.ref('e_learning_custom.view_student_sms_wizard').id,
                'view_mode': 'form',
                'context': {'default_partner_id': lines}
                }

    def open_discuss_app(self):
        if self.channel_id !=0:

            base_url = re.sub(r"[^/]*(\?.*)?$", "", self.website_url)
            if "slides" in base_url:
                base_url = base_url.replace("slides/","")
            return {
                'type': 'ir.actions.act_url',
                # "web?#action=114&active_id=mail.channel_"+str(self.channel_id)+"&cids=1&menu_id=91"
                'url': str(base_url)+"web?#action=114&active_id=mail.channel_"+str(self.channel_id)+"&cids=1&menu_id=91",
                'target': 'self',
            }
        else:
            raise ValidationError(_('No channel found'))

class slideCustom(models.Model):
    _inherit = 'slide.slide'

    slide_type = fields.Selection(selection_add=[('url', 'Url')], ondelete={'url': 'set default'})
    nbr_url = fields.Integer("Number of Videos", compute='_compute_slides_statistics', store=True)
    is_pdf = fields.Boolean(default=False)

    @api.model
    def _parse_google_document(self, document_id, only_preview_fields):
        def get_slide_type(vals):
            # TDE FIXME: WTF ??
            slide_type = 'presentation'
            if vals.get('image_1920'):
                image = Image.open(io.BytesIO(base64.b64decode(vals['image_1920'])))
                width, height = image.size
                if height > width:
                    return 'document'
            return slide_type

        # Google drive doesn't use a simple API key to access the data, but requires an access
        # token. However, this token is generated in module google_drive, which is not in the
        # dependencies of website_slides. We still keep the 'key' parameter just in case, but that
        # is probably useless.
        params = {}
        params['projection'] = 'BASIC'
        if 'google.drive.config' in self.env:
            access_token = self.env['google.drive.config'].get_access_token()
            if access_token:
                params['access_token'] = access_token
        if not params.get('access_token'):
            params['key'] = self.env['website'].get_current_website().website_slide_google_app_key

        fetch_res = self._fetch_data('https://www.googleapis.com/drive/v2/files/%s' % document_id, params, "json")
        if fetch_res.get('error'):
            return {'error': self._extract_google_error_message(fetch_res.get('error'))}

        google_values = fetch_res['values']
        if only_preview_fields:
            return {
                'url_src': google_values['thumbnailLink'],
                'title': google_values['title'],
            }

        values = {
            'name': google_values['title'],
            'image_1920': self._fetch_data(google_values['thumbnailLink'].replace('=s220', ''), {}, 'image')['values'],
            'mime_type': google_values['mimeType'],
            'document_id': document_id,
        }
        if google_values['mimeType'].startswith('video/'):
            # values['slide_type'] = 'video'
            pass
        elif google_values['mimeType'].startswith('image/'):
            # values['slide_type'] = 'infographic'
            values['datas'] = values['image_1920']
        elif google_values['mimeType'].startswith('application/vnd.google-apps'):
            # values['slide_type'] = get_slide_type(values)
            if 'exportLinks' in google_values:
                values['datas'] = self._fetch_data(google_values['exportLinks']['application/pdf'], params, 'pdf')[
                    'values']
        elif google_values['mimeType'] == 'application/pdf':
            # TODO: Google Drive PDF document doesn't provide plain text transcript
            values['datas'] = self._fetch_data(google_values['webContentLink'], {}, 'pdf')['values']
            # values['slide_type'] = get_slide_type(values)

        return {'values': values}

    def _parse_youtube_document(self, document_id, only_preview_fields):
        """ If we receive a duration (YT video), we use it to determine the slide duration.
        The received duration is under a special format (e.g: PT1M21S15, meaning 1h 21m 15s). """

        key = self.env['website'].get_current_website().website_slide_google_app_key
        fetch_res = self._fetch_data('https://www.googleapis.com/youtube/v3/videos',
                                     {'id': document_id, 'key': key, 'part': 'snippet,contentDetails',
                                      'fields': 'items(id,snippet,contentDetails)'}, 'json')
        if fetch_res.get('error'):
            return {'error': self._extract_google_error_message(fetch_res.get('error'))}

        values = {'document_id': document_id}
        items = fetch_res['values'].get('items')
        if not items:
            return {'error': _('Please enter valid Youtube or Google Doc URL')}
        youtube_values = items[0]

        youtube_duration = youtube_values.get('contentDetails', {}).get('duration')
        if youtube_duration:
            parsed_duration = re.search(r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', youtube_duration)
            values['completion_time'] = (int(parsed_duration.group(1) or 0)) + \
                                        (int(parsed_duration.group(2) or 0) / 60) + \
                                        (int(parsed_duration.group(3) or 0) / 3600)

        if youtube_values.get('snippet'):
            snippet = youtube_values['snippet']
            if only_preview_fields:
                values.update({
                    'url_src': snippet['thumbnails']['high']['url'],
                    'title': snippet['title'],
                    'description': snippet['description']
                })

                return values

            values.update({
                'name': snippet['title'],
                'image_1920': self._fetch_data(snippet['thumbnails']['high']['url'], {}, 'image')['values'],
                'description': snippet['description'],
                'mime_type': False,
            })
        return {'values': values}

    @api.onchange('datas')
    def _on_change_datas(self):
        """ For PDFs, we assume that it takes 5 minutes to read a page.
            If the selected file is not a PDF, it is an image (You can
            only upload PDF or Image file) then the slide_type is changed
            into infographic and the uploaded dataS is transfered to the
            image field. (It avoids the infinite loading in PDF viewer)"""
        if self.datas:
            data = base64.b64decode(self.datas)
            if data.startswith(b'%PDF-'):
                pdf = PyPDF2.PdfFileReader(io.BytesIO(data), overwriteWarnings=False)
                self.completion_time = (5 * len(pdf.pages)) / 60
                self.is_pdf = True
            elif data.find(b'mp4') != -1:
                pass
            else:
                # self.slide_type = 'infographic'
                self.image_1920 = self.datas
                self.datas = None

    @api.depends('document_id', 'slide_type', 'mime_type')
    def _compute_embed_code(self):
        base_url = request and request.httprequest.url_root or self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        if base_url[-1] == '/':
            base_url = base_url[:-1]
        for record in self:
            if record.datas and record.slide_type in ['video']:
                # record.embed_code = '<video width="%s" height="%s" autoplay="" controls=""><source src="%s" type="video/mp4"/></video>' % (
                #     320, 240, "data:video/webm;base64," + str(record.datas).replace('b','').replace("'",''))
                ir_attachment_id = self.env['ir.attachment'].search([('res_model', '=', 'slide.slide'), ('res_field', '=', 'datas'), ('res_id', '=', record.id)])
                record.embed_code = '<video width="%s" height="%s" autoplay="" controls=""><source src="%s" type="video/mp4"/></video>' % (
                    320, 240, "/web/content/slide.slide/" + str(record.id) + "/datas")
            elif record.datas and (not record.document_id or record.slide_type in ['document', 'presentation']):
                slide_url = base_url + url_for('/slides/embed/%s?page=1' % record.id)
                record.embed_code = '<iframe src="%s" class="o_wslides_iframe_viewer" allowFullScreen="true" height="%s" width="%s" frameborder="0"></iframe>' % (
                slide_url, 315, 420)
            elif record.slide_type in ['video', 'url'] and record.document_id:
                if not record.mime_type:
                    # embed youtube video
                    query = urls.url_parse(record.url).query
                    query = query + '&theme=light' if query else 'theme=light'
                    record.embed_code = '<iframe src="//www.youtube-nocookie.com/embed/%s?%s" allowFullScreen="true" frameborder="0"></iframe>' % (
                    record.document_id, query)
                else:
                    # embed google doc video
                    record.embed_code = '<iframe src="//drive.google.com/file/d/%s/preview" allowFullScreen="true" frameborder="0"></iframe>' % (
                        record.document_id)
            else:
                record.embed_code = False

    @api.model
    def create(self, values):
        # if values.get('datas') and not values.get('image_1920'):
        data = False
        if self.datas:
            data = base64.b64decode(self.datas).startswith(b'%PDF-')
            if values.get('slide_type') in ['url', 'video', 'infographic'] and not values.get('image_1920')\
                    or (not data and values.get('slide_type') in ['document'] and not values.get('is_pdf')):
                values['image_1920'] = values['datas']
        slide = super(slideCustom, self).create(values)
        return slide