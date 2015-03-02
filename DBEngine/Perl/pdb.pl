use strict;
use warnings;
use IO::File;

use constant {
    DELETED => 0,
    INTEGER => 0,
    STRING => 1
};

sub read_record($) {
    my $fh = @_;
    my ($deleted, $rec_len, $num_cols, $type, $col_len, $value, @record);
    
    # Read deleted flag
    $fh->read($deleted, 2);
    $deleted = unpack('S', $deleted);
    
    # Read the record length
    $fh->read($rec_len, 4);
    $rec_len = unpack('l', $rec_len);
    
    # Read number of columns (16 unsigned short)
    $fh->read($num_cols, 2);
    $num_cols = unpack('S', $num_cols);
    
    # Read each column value
    for (my $i = 0; $i < $num_cols; $i ++) {
        # Read the type of the data stored in the column
        $fh->read($type, 2);
        $type = unpack('S', $type);
        # Read the length of the column data 
        $fh->read($col_len, 2);
        $col_len = unpack('S', $col_len);
        # Read the column data
        $fh->read($value, $col_len);
           
        if ($type eq INTEGER) {
            $value = unpack('l', $value);
        }
        
        push @record, $value;
    }
    
    if ($deleted) {
        return undef;
    }
    
    return \@record;
}

sub write_record($$) {
    my ($fh, $record) = @_;
}

sub _select($$)  {
    my ($table, $key) = @_;
    
    my $fh = IO::File->new();
    if (!$fh->open("< ".lc $table.".data")) {
        print "[ERROR] Unable to open table '$table': ".$!."\n";
        return undef;
    }
    
    print "SELECT\n";
    while (!$fh->eof()) {
        my $record = read_record($fh);
        if (!defined $record) {
            next;
        }
        
        foreach my $column (@$record) {
            if ($column eq $key) {
                print $column." ";
            }
        }  
    }
    
    $fh->close();
}

sub insert($$) {
    my ($table, $values) = @_;
    
    my $fh = IO::File->new();
    if (!$fh->open(">> ".lc $table.".data")) {
        print "[ERROR] Unable to open table '$table': ".$!."\n";
        return undef;
    }
    
    # Write the delete flag
    $fh->print(pack('S', !DELETED));
    # Write number of columns
    $fh->print(pack('S', scalar(@$values)));
    
    foreach my $value (values @$values) {
        if (@$value[0] eq "int") {
            $fh->print(pack('S', INTEGER));
            $fh->print(pack('S', 4));
            $fh->print(pack('l', @$value[1]));
        }
        if (@$value[0] eq "string") {
            my $len = length @$value[1];
            $fh->print(pack('S', STRING));
            $fh->print(pack('S', $len));
            $fh->print(@$value[1]);
        }
    }
    
    $fh->close();
}

sub delete ($$) {
    
}

#for (my $i = 0; $i < 100; $i ++) {
#    insert("test", [["int", 1], ["string", "Ivan"]]);
#}
#
#for (my $i = 0; $i < 100; $i ++) {
#    _select("test", 1);
#}
