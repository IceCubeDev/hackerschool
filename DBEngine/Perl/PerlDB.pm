package PerlDB;
use warnings;
use strict;
use Fcntl;

sub new($$) {
    my $class = shift;
    my $path = shift;
    
    my $self = bless {
        tables => [],
        current_db => undef
    }, $class;
    
    return $self;
}

sub select_db($$) {
    my $self = shift;
    my $db = shift;
    
    opendir(my $dir, "Databases/".$db) or die "Unable to select database: ".$!;
    $self->{current_db} = $db;
    
    while (my $file = readdir($dir)) {
        if (not substr($file,0,1) eq "." and $file =~ m/(.*).schema/) {
            push $self->{tables}, lc $1;
        }
    }
    
    print "SELECT DATABASE\n";
}

sub create_db($$$) {
    my $self = shift;
    my $name = shift;
    my $encoding = shift;
    
    my $path = "Databases/".$name;
    if (mkdir ($path, 0755)) {
        sysopen(my $fh, $path."/".$name.".engine", O_WRONLY | O_CREAT, 0755) or
            die "Unable to open ".$path."/".$name.".engine";
        
        print "Database '".$name."' created!\n";
        print $fh "encoding=".$encoding."\n";
        close $fh;
    } else {
        print "[ERROR]Failed to create database '".$name."': ".$!."\n";
        return 0;
    }
    
    print "CREATE DATABASE\n";
    return 1;
}

sub create_table($$$) {
    my ($self, $table, $schema) = @_;
    
    if (!defined $self->{current_db}) {
        print "[ERROR] No database selected!\n";
        return 0;
    }
    
    my ($key, $value);
    
    my $path = lc "Databases\\".$self->{current_db}."\\".$table.".schema";
    
    if (-e $path) {
        print "[ERROR] Table '$table' already exists!\n";
        return 0;
    }
    
    sysopen(my $fh, $path, O_WRONLY | O_CREAT, 0755) or
        die "Unable to open ".$path;
    
    # Write number of columns as a 16-bit unsigned short
    syswrite($fh, pack('v', scalar(@$schema), 2));
    
    foreach my $column (values $schema) {
        if (lc $column->{'column_type'} eq "int") {
            syswrite($fh, pack('v', 0), 2);
        }
        if (lc $column->{'column_type'} eq "text") {
            syswrite($fh, pack('v', 1), 2);
        }
        
        my $name_len = length $column->{'column_name'};
        syswrite($fh, pack('v', $name_len), 2);
        syswrite($fh, lc $column->{'column_name'}, $name_len);
    }
    close $fh;
    
    $path = lc "Databases/".$self->{current_db}."/".$table.".data";
    sysopen($fh, $path, O_RDONLY | O_CREAT, 0755) or
        die "Unable to open ".$path;
    
    close $fh;
    print "CREATE TABLE(".scalar(@$schema).")\n";
    return 1;
}

sub read_schema($$) {
    my ($self, $table) = @_;
    
    if (!defined $self->{current_db}) {
        print "[ERROR] No database selected!\n";
        return 0;
    }
    
    my $schema = lc "Databases/".$self->{current_db}."/".$table.".schema";
    
    # Read the schema from the file
    sysopen(my $fh, $schema, O_RDONLY, 0755)
        or die "Unable to open ".$schema;
    
    my $num_columns;
    sysread($fh, $num_columns, 2);
    $num_columns = unpack('v', $num_columns);
    
    my @columns;
    for (my $i = 0; $i < $num_columns; $i++) {
        my ($column_type, $column_name_length, $column_name);
        sysread($fh, $column_type, 2);
        sysread($fh, $column_name_length, 2);
        $column_name_length = unpack('v', $column_name_length);
        sysread($fh, $column_name, $column_name_length);
        
        push @columns, {'column_type'=> unpack('v', $column_type),
                        'column_name'=> $column_name};
    }
    close $fh;
    
    return \@columns;
}

sub insert($$$) {
    my ($self, $table, $values) = @_;
    
    if (!defined $self->{current_db}) {
        print "[ERROR] No database selected!\n";
        return 0;
    }
    
    my $path = lc "Databases/".$self->{current_db}."/".$table.".data";
    
    my $columns = $self->read_schema($table);
    my $num_columns = scalar(@$columns);
    
    # Insert the data at the end of the file
    my $fh;
    sysopen($fh, $path, O_WRONLY | O_APPEND, 0755)
        or die "Unable to open file '$path': ".$!."\n";
        
    foreach my $row (@$values) {
        # Deleted flag (2)
        syswrite($fh, pack('v', 0), 2);
        for (my $i = 0; $i < $num_columns; $ i++) {
            # Length(2) Value(4)
            if (@$columns[$i]->{'column_type'} eq 0) {
                syswrite($fh, pack('v', 4), 2);
                syswrite($fh, pack('V', @$row[$i]), 4);
            }
            # Length(2) Value(Length)
            if (@$columns[$i]->{'column_type'} eq 1) {
                my $strlen = length @$row[$i];
                syswrite($fh, pack('v', $strlen), 2);
                syswrite($fh, @$row[$i], $strlen);
            }
        }
    }
    
    close $fh;
    my $num_insert = scalar(@$values);
    print "INSERT($num_insert)\n";
    
    return 1;
}

sub read_record($$) {
    my ($self, $fh, $table_columns) = @_;
    
    my (%record, $deleted);
    # Deleted flag (2)
    my $read = sysread($fh, $deleted, 2);
    $deleted = unpack('v', $deleted);
    #End of file
    if ($read eq 0) {
        return undef;
    }
    print $deleted."\n";
    if (!$deleted) {
        foreach my $column (values @$table_columns) {
            my ($length, $value);
            sysread($fh, $length, 2);
            $length = unpack('v', $length);
            sysread($fh, $value, $length);
            if ($column->{'column_type'} eq 0) {
                $value = unpack('V', $value);
            }
            
            #print $column->{'column_name'}." ".$value."\n";
            $record{$column->{'column_name'}} = $value;
        }
    }
    
    return \%record;
}

sub check_record($$$$) {
    my ($self, $record, $table_columns, $where) = @_;
    my $criteria = 0;
        
    foreach my $column (values @$table_columns) {
        if (exists $where->{$column->{'column_name'}}) {
            if ($record->{$column->{'column_name'}} eq $where->{$column->{'column_name'}}) {
                $criteria += 1;
            }
        }
    }
    
    if ($criteria eq scalar(keys %$where)) {
        return 1;
    } 
    
    return 0;
}

sub select($$$) {
    my ($self, $table, $where) = @_;
    
    if (!defined $self->{current_db}) {
        print "[ERROR] No database selected!\n";
        return 0;
    }
    
    my $table_columns = $self->read_schema($table);
    my $path = lc "Databases/".$self->{current_db}."/".$table.".data";
    
    sysopen(my $fh, $path, O_RDONLY, 0755)
        or die "Unable to open file '$path': ".$!."\n";
    
    print "SELECT\n";
    RECORD:
    while (1) {
        my $record = $self->read_record($fh, $table_columns);
        if (!defined $record) {
            last;
        }
        #if ($self->check_record($record, $table_columns, $where)) {
            foreach my $column (values @$table_columns) {
                print $record->{$column->{'column_name'}}." ";
            }
            print "\n";
        #}
    }
        
    close $fh;
}

sub delete($$$){
    my ($self, $table, $where) = @_;
    
    my $table_columns = $self->read_schema($table);
    my $path = lc "Databases/".$self->{current_db}."/".$table.".data";
    sysopen(my $fh, $path, O_RDWR, 0755)
        or die "Unable to open file '$path': ".$!."\n";
    
    while (1) {
        my $record = $self->read_record($fh, $table_columns);
        
        if (!defined $record) {
            last;
        }
        
        if ($self->check_record($record, $table_columns, $where)) {
            # Deleted flag
            my $offset = 2;
            foreach my $column (values @$table_columns) {
                # Length(2) + Int Value(4)
                if ($column->{'column_type'} eq 0) {
                    $offset += 6;
                }
                # Length(2) + String
                if ($column->{'column_type'} eq 1) {
                   $offset += 2 + length ($record->{$column->{'column_name'}});
                }
            }
            
            my $cur = sysseek($fh, 0, 1);
            print $cur." ".$offset."\n";
            sysseek($fh, $cur - $offset, 0);
            print syswrite($fh, pack('v', 1), 2)."bytes changed\n";
            sysseek($fh, $cur, 0);
            print "Deleting ... "."\n";
        }
    }
    
    close $fh;
    print "DELETE\n";
}

sub update($$$$) {
    my ($self, $table, $where, $new) = @_;
    $self->delete($table, $where);
    $self->insert($table, $new);
}
1;