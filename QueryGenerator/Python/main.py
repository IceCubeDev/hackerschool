__author__ = 'Ivan Dortulov'

from QueryGenerator import *

gen = QueryGenerator('localhost', 'jointest', 'postgres', 'postgres')
graph = gen.build_table_graph()
print(gen.generate_query(graph, 'a'))
