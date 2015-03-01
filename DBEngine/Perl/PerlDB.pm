package PerlDB;
#use warnings;
#use strict;

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
    
    $path = "Databases/".$name;
    if (mkdir ($path, 0755)) {
        open(my $fh, '> '.$path."/".$name.".engine") or
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
    
    my $path = lc "Databases/".$self->{current_db}."/".$table.".schema";
    
    if (-e $path) {
        print "[ERROR] Table '$table' already exists!\n";
        return 0;
    }
    
    open(my $fh, '> '.$path) or
        die "Unable to open ".$path;
    
    # Write number of columns as a 16-bit unsigned short
    syswrite($fh, pack('v', scalar(@$schema)));
    
    foreach my $column (values $schema) {
        if (lc $column->{'column_type'} eq "int") {
            syswrite($fh, pack('v', 0));
        }
        if (lc $column->{'column_type'} eq "text") {
            syswrite($fh, pack('v', 1));
        }
        
        my $name_len = length $column->{'column_name'};
        syswrite($fh, pack('v', $name_len));
        syswrite($fh, lc $column->{'column_name'});
    }
    close $fh;
    
    $path = lc "Databases/".$self->{current_db}."/".$table.".data";
    open($fh, '> '.$path) or
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
    open(my $fh, '< '.$schema)
        or die "Unable to open ".$path;
    
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
    open($fh, '>> '.$path)
        or die "Unable to open file '$path': ".$!."\n";
        
    foreach my $row (@$values) {
        for (my $i = 0; $i < $num_columns; $ i++) {
            syswrite($fh, pack('v', 0));
            if (@$columns[$i]->{'column_type'} eq 0) {
                syswrite($fh, pack('v', 4));
                syswrite($fh, pack('V', @$row[$i]));
            }
            if (@$columns[$i]->{'column_type'} eq 1) {
                my $strlen = length @$row[$i];
                syswrite($fh, pack('v', $strlen));
                syswrite($fh, @$row[$i], $strlen);
            }
        }
    }
    
    close $fh;
    my $num_insert = scalar(@$values);
    print "INSERT($num_insert)\n";
    
    return 1;
}

sub select($$$) {
    my ($self, $table, $keys) = @_;
    
    if (!defined $self->{current_db}) {
        print "[ERROR] No database selected!\n";
        return 0;
    }
    
    my $table_columns = $self->read_schema($table);
    my $path = lc "Databases/".$self->{current_db}."/".$table.".data";
    
    open($fh, '< '.$path)
        or die "Unable to open file '$path': ".$!."\n";
    
    print "SELECT\n";
    RECORD:
    while (1) {
        my @record;
        my $criteria = 0;
        foreach $column (values @$table_columns) {
            my ($deleted, $length, $value);
            #End of file
            my $read = sysread($fh, $deleted, 2);
            if ($read eq 0) {
                last RECORD;
            }
            
            $deleted = unpack('v', $deleted);
            sysread($fh, $length, 2);
            $length = unpack('v', $length);
            sysread($fh, $value, $length);
            if ($column->{'column_type'} eq 0) {
                $value = unpack('V', $value);
            }
            
            push @record, $value;
            if (exists $keys->{$column->{'column_name'}}) {
                if ($value eq $keys->{$column->{'column_name'}}) {
                    $criteria += 1;
                }
            }
        }
        if ($criteria eq scalar(keys %$keys)) {
            foreach $value (@record) {
                print $value." ";
            }
            print "\n";
        }
    }
        
    close $fh;
}
1;