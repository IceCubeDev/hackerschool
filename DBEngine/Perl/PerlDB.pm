package PerlDB;
use warnings;
use strict;
use Fcntl;
use Fcntl 'SEEK_CUR';
use Fcntl 'SEEK_SET';
use Fcntl 'SEEK_END';

sub new($$) {
    my $class = shift;
    my $path = shift;
    
    my $self = bless {
        tables => [],
        current_db => undef,
        fh => undef
    }, $class;
    
    return $self;
}

sub select_db($$) {
    my $self = shift;
    my $db = shift;
    my $dir;
    if (!opendir($dir, "Databases/".$db)) {
        print "[ERROR] Unable to select database '$db': ".$!;
        return undef;
    }
    $self->{current_db} = lc $db;
    
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
    
    my $path = "Databases/".lc $name;
    if (mkdir ($path, 0755)) {
        if (!sysopen($self->{fh}, $path."/".$name.".engine", O_WRONLY | O_CREAT, 0755)){
            print "[ERROR] Unable to create database '$name': ".$!."\n";
            return undef;
        }
        
        syswrite($self->{fh}, $encoding);
        close $self->{fh};
    } else {
        print "[ERROR] Unable to create database '$name': ".$!."\n";
        return undef;
    }
    
    print "CREATE DATABASE\n";
    return $name;
}

sub create_table($$$) {
    my ($self, $table, $schema) = @_;
    
    if (!defined $self->{current_db}) {
        print "[ERROR] No database selected!\n";
        return undef;
    }
    
    my $schema_path = "Databases\\".$self->{current_db}."\\".lc $table.".schema";
    if (-e $schema_path) {
        print "[ERROR] Table '$table' already exists!\n";
        return 0;
    }
    
    if (!sysopen($self->{fh}, $schema_path, O_WRONLY | O_CREAT, 0755)) {
       print "[ERROR] Unable to create table '$table': ".$!."\n";
       return undef;
    }
    
    # Write number of columns as a 16-bit unsigned short
    syswrite($self->{fh}, pack('S', scalar(@$schema), 2));
    
    # Foreach column
    foreach my $column (values $schema) {
        # Write the type of the column as a 16-bit unsidned short
        if (lc $column->{'column_type'} eq "int") {
            syswrite($self->{fh}, pack('S', 0), 2);
        }
        if (lc $column->{'column_type'} eq "text") {
            syswrite($self->{fh}, pack('S', 1), 2);
        }
        
        # Write the length of the column name as a 16bit unsigned short
        my $name_len = length $column->{'column_name'};
        syswrite($self->{fh}, pack('S', $name_len), 2);
        
        # Write the column name as a series of bytes
        syswrite($self->{fh}, $column->{'column_name'}, $name_len);
    }
    close $self->{fh};
    $self->{fh} = undef;
    
    # Create the data file
    my $path = "Databases/".$self->{current_db}."/".lc $table.".data";
    if (!sysopen($self->{fh}, $path, O_RDONLY | O_CREAT, 0755)) {
        print "[ERROR] Unable to create the data file for table '$table': ".$!."\n";
        unlink $schema_path;
        return undef;
    }
    
    close $self->{fh};
    $self->{fh} = undef;
    
    print "CREATE TABLE(".scalar(@$schema).")\n";
    return 1;
}

sub read_schema($$) {
    my ($self, $table) = @_;
    
    if (!defined $self->{current_db}) {
        print "[ERROR] No database selected!\n";
        return undef;
    }
    
    my $schema = "Databases/".$self->{current_db}."/".lc $table.".schema";
    
    # Read the schema from the file
    if (!sysopen($self->{fh}, $schema, O_RDONLY, 0755)) {
        print "[ERROR] Unable to read schema for table '$table' ($schema): ".$!."\n";
        $self->{fh} = undef;
        return undef;
    }
    
    my $num_columns;
    if (!defined sysread($self->{fh}, $num_columns, 2)) {
        return undef;
    }
    $num_columns = unpack('S', $num_columns);
    
    my @columns;
    for (my $i = 0; $i < $num_columns; $i++) {
        my ($column_type, $column_name_length, $column_name);
        # Column type (2)
        if (!defined sysread($self->{fh}, $column_type, 2)) {
            return undef;
        }
        $column_type = unpack('S', $column_type);
        
        # Column length (2)
        if (!defined sysread($self->{fh}, $column_name_length, 2)) {
            return undef;
        }
        $column_name_length = unpack('S', $column_name_length);
        
        # Column value (length)
        if (!defined sysread($self->{fh}, $column_name, $column_name_length)){
            return undef;
        }
        
        push @columns, {'column_type'=> $column_type,
                        'column_name'=> $column_name};
    }
    close $self->{fh};
    $self->{fh} = undef;
    
    return \@columns;
}

sub insert($$$) {
    my ($self, $table, $values) = @_;
    
    if (!defined $self->{current_db}) {
        print "[ERROR] No database selected!\n";
        return undef;
    }
    
    my $path = "Databases/".$self->{current_db}."/".lc $table.".data";
    my $columns = $self->read_schema($table);
    if (!defined $columns) {
        print("[ERROR] Unable to read schema '$table': ".$!."\n");
        return undef;
    }
    
    my $num_columns = scalar(@$columns);
    
    # Insert the data at the end of the file
    if (!sysopen($self->{fh}, $path, O_WRONLY | O_APPEND, 0755)) {
        print "[ERROR] Unable to open file '$path' for writing: ".$!."\n";
        return undef;
    }
        
    foreach my $row (@$values) {
        # Deleted flag (2)
        syswrite($self->{fh}, pack('S', 0), 2);
        
        for (my $i = 0; $i < $num_columns; $ i++) {
            # Length(2) Value(4)
            if (@$columns[$i]->{'column_type'} eq 0) {
                syswrite($self->{fh}, pack('S', 4), 2);
                syswrite($self->{fh}, pack('l', @$row[$i]), 4);
            }
            # Length(2) Value(Length)
            if (@$columns[$i]->{'column_type'} eq 1) {
                my $strlen = length @$row[$i];
                syswrite($self->{fh}, pack('S', $strlen), 2);
                syswrite($self->{fh}, @$row[$i], $strlen);
            }
        }
    }
    
    close $self->{fh};
    $self->{fh} = undef;
    
    my $num_insert = scalar(@$values);
    print "INSERT($num_insert)\n";
    
    return $num_insert;
}

sub read_record($$) {
    my ($self, $table_columns) = @_;
    if (!defined $self->{fh}) {
        return undef;
    }
    
    my (%record, $deleted);
    # Read deleted flag (16 bit unsigned short)
    my $read = sysread($self->{fh}, $deleted, 2);
    $deleted = unpack('S', $deleted);
    
    #End of file
    if ($read eq 0) {
        return undef;
    }
    
    if (!$deleted) {
        foreach my $column (values @$table_columns) {
            my ($length, $value);
            # Read length of column value (16 bit unsigned short)
            sysread($self->{fh}, $length, 2);
            $length = unpack('S', $length);
            
            # Read the column value (length bytes)
            sysread($self->{fh}, $value, $length);
            
            # If this is an integer we must unpack (32 bit signed long)
            if ($column->{'column_type'} eq 0) {
                $value = unpack('l', $value);
            }
            
            # Add column to result
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
    if (!defined $table_columns) {
        print "[ERROR] Error while reading table schema '$table': ".$!."\n";
        return undef;
    }
    
    my $path = lc "Databases/".$self->{current_db}."/".lc $table.".data";
    
    if (!sysopen($self->{fh}, $path, O_RDONLY, 0755)) {
        print "[ERROR] Error reading table '$table' records: ".$!."\n";
        return undef;
    }
    
    print "SELECT\n";
    RECORD:
    while (1) {
        my $record = $self->read_record($table_columns);
        if (!defined $record) {
            last;
        }
        if ($self->check_record($record, $table_columns, $where)) {
            foreach my $column (values @$table_columns) {
                print $record->{$column->{'column_name'}}." ";
            }
            print "\n";
        }
    }
        
    close $self->{fh};
    $self->{fh} = undef;
}

sub delete($$$){
    my ($self, $table, $where) = @_;
    
    my $table_columns = $self->read_schema($table);
    if (!defined $table_columns) {
        print "[ERROR] Unable to read table $table schema: ".$!."\n";
        return undef;
    }
    
    my $path = lc "Databases/".$self->{current_db}."/".$table.".data";
    if (!sysopen($self->{fh}, $path, O_RDWR, 0755)) {
        print "[ERROR] Unable to open table '$table' for reading: ".$!."\n";
        return undef;
    }
    
    while (1) {
        my $record = $self->read_record($table_columns);
        if (!defined $record) {
            last;
        }
        
        if ($self->check_record($record, $table_columns, $where)) {
            # Deleted flag (16 bit unsigned short)
            my $offset = 2;
            foreach my $column (values @$table_columns) {
                # Length(16 bit unsigned short) + Int Value(32 bit signed long)
                if ($column->{'column_type'} eq 0) {
                    $offset += 6;
                }
                # Length(16 bit unsigned short) + String (length bytes)
                if ($column->{'column_type'} eq 1) {
                   $offset += 2 + length ($record->{$column->{'column_name'}});
                }
            }
            
            my $cur = sysseek($self->{fh}, 0, SEEK_CUR);
            print $cur." ".$offset."\n";
            sysseek($self->{fh}, $cur - $offset, SEEK_SET);
            print syswrite($self->{fh}, pack('S', 1), 2)." bytes changed\n";
            sysseek($self->{fh}, $cur, SEEK_SET);
        }
    }
    
    close $self->{fh};
    $self->{fh} = undef;
    print "DELETE\n";
}

sub update($$$$) {
    my ($self, $table, $where, $new) = @_;
    $self->delete($table, $where);
    $self->insert($table, $new);
}
1;