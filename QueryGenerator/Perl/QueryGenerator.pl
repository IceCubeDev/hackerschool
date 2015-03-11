#!/usr/bin/perl

use strict;
use warnings;
use DBI;
use Storable qw(dclone);

my $list_tables_query = <<END;
    SELECT
        tbls.table_name, clms.column_name, clms.is_nullable, tbls.table_schema, clms.data_type
    FROM
        information_schema.tables AS tbls
    LEFT JOIN
        (SELECT
            column_name, table_name, is_nullable, data_type
         FROM
            information_schema.columns) as clms
    ON
        tbls.table_name = clms.table_name
    WHERE
        tbls.table_schema NOT IN ('pg_catalog', 'information_schema');
END

my $list_foreign_keys = <<END;
    SELECT
        tc.constraint_name, tc.table_name, kcu.column_name, 
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name 
    FROM 
        information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
    WHERE constraint_type = 'FOREIGN KEY';
END

sub generate_schema {
    # connect
    my $dbh = DBI->connect('DBI:Pg:dbname=WorkDatabase;host=localhost','postgres','postgres')
        or die "Unable to connect: ".$DBI::errstr;

    # Obtain a list of tables in the database
    my $query = $dbh->prepare($list_tables_query)
        or die "Couldn't prepare statement: " . $dbh->errstr;
    $query->execute()
        or die "Couldn't execute statement: " . $dbh->errstr;

    my %tables;
    my $table;
    # iterate through the resultset and build a list of tables with their columns
    while(my $ref = $query->fetchrow_hashref()) {
        if (!exists $tables{$ref->{'table_name'}}) {
            my %table;
            $table{'columns'} = [];
            $table{'table_name'} = $ref->{'table_name'};
            $tables{$ref->{'table_name'}} = \%table;
        } 
        
        my $table = $tables{$ref->{'table_name'}};
        push $table->{'columns'}, {'column_name' => $ref->{'column_name'},
                                   'is_nullable' => $ref->{'is_nullable'},
                                   'data_type'   => $ref->{'data_type'}}; 
    }
    
    # Obtain a list of all foreign keys
    $query = $dbh->prepare($list_foreign_keys) or
        die "Couldn't prepare statement: " . $dbh->errstr;
    $query->execute() or
        die "Couldn't execute statement: " . $dbh->errstr;
    
    my $table_name;
    my @columns;
    while (my $ref = $query->fetchrow_hashref()) {
        $table_name = $ref->{'table_name'};
        $table = $tables{$table_name};

        foreach my $column (values $table->{'columns'}) {
            if ($column->{'column_name'} eq $ref->{'column_name'}) {
                $column->{'fk'} = [$ref->{'foreign_table_name'}, $ref->{'foreign_column_name'}];
            } 
        }
    }
    
    # Clean up
    $dbh->disconnect();
    
    return \%tables;
}

sub generate_query($$) {
    my ($graph, $node) = @_;
    my $start = $graph->{$node};
    my $query = "SELECT * FROM $start->{'table_name'} AS _$start->{'table_name'}";
    
    foreach my $table (values %$graph) {
        $table->{'visited'} = 0;
    }
    
    $query.= traverse_graph_helper($graph,
                                   $start,
                                   "_".$start->{'table_name'},
                                   ($start));
    return $query.";";
}

sub traverse_graph_helper($$$@);
sub traverse_graph_helper($$$@) {
    my ($graph, $cur, $prev, @cur_path) = @_;
    $cur->{'visited'} += 1;
    my $query = "";

    foreach my $col (values $cur->{'columns'}) {
        if (defined $col->{'fk'}) {
            my $w = $graph->{$col->{'fk'}[0]};
            #print "cur:".$w->{'table_name'}."\n";
            my $new;
            
            if (scalar(@cur_path) > 1) {}
            if ($cur_path[0] eq $cur_path[-1] or $cur_path[-1] eq $cur) {
                if ($w->{'visited'} > 4) {
                    return "";
                }
            }
            $new = ($cur->{'table_name'} x $w->{'visited'})."_".$w->{'table_name'};
            
            if ($col->{'is_nullable'} eq 'NO') {
                $query .= " JOIN $w->{'table_name'} AS ".$new;
                $query .= " ON ".$prev.".".$col->{'column_name'}."=".$new.".".$col->{'fk'}[1];
            } else {
                $query .= " LEFT JOIN $w->{'table_name'} AS ".$new;
                $query .= " ON ".$prev.".".$col->{'column_name'}."=".$new.".".$col->{'fk'}[1];
            }
                
            my @path = (@cur_path, ($w));
            #print "path(".$w->{'table_name'}.", ", $new.")";
            $query .= traverse_graph_helper($graph, $w, $new, @path);
        }
    }
    
    return $query;
}

my $test = generate_schema();
print generate_query(dclone($test), "blue");