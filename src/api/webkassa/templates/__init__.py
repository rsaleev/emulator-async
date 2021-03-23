import jinja2
import os
from src.api.webkassa.helpers import format_currency, format_quantity, format_spaces, count_len



PATH =f"{os.getcwd()}/src/api/webkassa/templates"
TEMPLATE_LOADER = jinja2.FileSystemLoader(PATH)
TEMPLATE_ENVIRONMENT = jinja2.Environment(
    autoescape=True,
    loader=TEMPLATE_LOADER,
    line_statement_prefix='#',
    comment_start_string='<!--',
    comment_end_string='-->',
    )
TEMPLATE_ENVIRONMENT.globals.update(f_cur=format_currency, f_qty=format_quantity, f_sp=format_spaces, c_l=count_len)

