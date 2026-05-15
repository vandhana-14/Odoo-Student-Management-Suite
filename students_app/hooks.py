def pre_init_hook(cr):
    # Normalize existing values to a valid selection value expected by base (e.g., 'ask')
    cr.execute("""
        UPDATE res_partner
        SET autopost_bills = 'ask'
        WHERE autopost_bills IS NULL
           OR autopost_bills NOT IN ('ask', 'always', 'never')
    """)


def post_init_hook(cr, registry):
    # Safety: also clean any NULL after module install/upgrade
    cr.execute("""
        UPDATE res_partner
        SET autopost_bills = 'ask'
        WHERE autopost_bills IS NULL
           OR autopost_bills NOT IN ('ask', 'always', 'never')
    """)
