use strict;
use warnings;
use PerlDB;

my $db = PerlDB->new();
#$db->create_db("test");
$db->select_db("test");
#$db->create_table("Person", [{'column_name' => 'id',
#                              'column_type' => 'int'},
#                             {'column_name' => 'name',
#                              'column_type' => 'text'}]);
#$db->insert("person", [[1, "Ivan"],
#                       [2, "Zlatin"],
#                       [3, "Ceco"]]);
$db->select("person", {"id"=>1});
$db->select("person", {"id"=>2});
$db->delete("person", {"id"=>1});
$db->select("person", {"id"=>1});
$db->select("person", {"id"=>2});