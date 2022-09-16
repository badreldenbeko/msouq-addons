# -*- coding: utf-8 -*-
# from odoo import http


# class SlideLocalVideo(http.Controller):
#     @http.route('/slide_local_video/slide_local_video/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/slide_local_video/slide_local_video/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('slide_local_video.listing', {
#             'root': '/slide_local_video/slide_local_video',
#             'objects': http.request.env['slide_local_video.slide_local_video'].search([]),
#         })

#     @http.route('/slide_local_video/slide_local_video/objects/<model("slide_local_video.slide_local_video"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('slide_local_video.object', {
#             'object': obj
#         })
