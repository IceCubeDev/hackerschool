__author__ = 'Ivan Dortulov'

from QueryGenerator import *

gen = QueryGenerator('localhost', 'postgres', 'postgres', '1234')
gen.build_table_graph()
#gen.generate_query('countries')
