# -*- coding: utf-8 -*-
{
    'name': "Slide Local Video",
 'summary': """
        E-learning local video play 
        """,
    'description': """
        Alhadi Tech comes with a handy feature to upload any local video on eLearning slides as well as online video url of youtube, google drive or anyother 3rd party cloud public url.
    """,

    'author': "Alhaditech",
    'website': "https://www.alhaditech.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',
    'images': ['static/description/images/cover_image.png'],
    # any module necessary for this one to work correctly
    'depends': ['base', 'website_slides'],

    # always loaded
    'data': [
        'views/assets.xml',
        'views/custom_slides_view.xml',
        'views/website_slides.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
