__author__ = 'Ivan Dortulov'

from QueryGenerator import *

gen = QueryGenerator('localhost', 'postgres', 'postgres', '1234')
gen.generate_query('countries')
