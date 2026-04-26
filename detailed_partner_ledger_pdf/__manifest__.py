{
    'name': 'Partner Ledger PDF',
    'version': '18.0.1.0.0',
    'summary': 'Partner Ledger PDF report with invoice-line detail, plus expandable product lines on the standard Partner Ledger report',
    'description': '''
        Advanced Partner Ledger Report with expandable invoice lines and product details.
        Features detailed transaction history, multi-currency support, flexible filtering options,
        and professional PDF output. Includes wizard for customized date range, partner type,
        journals, and reconciliation settings. Perfect for AR, AP, and audit departments.
    ''',
    'category': 'Accounting/Accounting',
    'license': 'LGPL-3',
    'author': 'Tarek Ashry',
    'depends': ['account', 'account_reports'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/partner_ledger_wizard_views.xml',
        'report/partner_ledger_report.xml',
        'report/partner_ledger_template.xml',
    ],
    'installable': True,
    'application': False,
}
