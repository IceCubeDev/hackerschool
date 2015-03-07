use strict;
use warnings;
use IO::File;

use constant {
    DELETED => 1,
    INTEGER => 0,
    STRING => 1
};

sub _select($$)  {
    my ($fh, $key) = @_;
    
    #print "SELECT\n";
    while (!$fh->eof()) {
        my $record = read_record($fh);
        if (!defined $record) {
            next;
        }
        
        if (check_record($record, $key)) {
            #print_record($record);
        }
    }
}

sub _insert($$) {
    my ($fh, $values) = @_;
    write_record($fh, $values);
}

sub _delete ($$) {
    my ($fh, $where) = @_;
    
    while (!$fh->eof()) {
        my $start_pos = $fh->tell();
        my $record = read_record($fh);
        if (defined $record) {
            if (check_record($record, $where)) {
                my $size = $fh->tell();
                #print("Found record @ ", $size, "\n");
                $fh->seek($start_pos, SEEK_SET);
                #print("Seek to: ".$fh->tell()."\n");
                $fh->write(pack('S', DELETED));
                $fh->seek($size, SEEK_SET);
                #print("Seek to: ".$fh->tell()."\n");
            }
        }
    }
    
    #print("DELETE\n");
}

sub _update($$$) {
    my ($fh, $where, $values) = @_;
    _delete($fh, $where);
    _insert($fh, $values);
}

sub read_record($) {
    my $fh = shift;
    my ($deleted, $num_cols, $type, $col_len, $value, @record);
    
    # Read deleted flag
    $fh->read($deleted, 2);
    $deleted = unpack('S', $deleted);
    
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
    
    # Write the delete flag (2 bytes)
    $fh->print(pack('S', !DELETED));
    # Write number of columns (2 bytes)
    $fh->print(pack('S', scalar(@$record)));
    
    foreach my $value (values $record) {
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
}

sub check_record($$) {
    my $record = shift;
    my $key = shift;
    
    foreach my $column (values $record) {
        if ($column eq $key) {
            return 1;
        }
    }
    return 0;
}

sub print_record($) {
    my $record = shift;
    
    foreach my $column (values $record) {
        print $column." ";
    }
    print("\n");
}

my $fh = IO::File->new();
if (!$fh->open("+< test.data")) {
    print "[ERROR] Unable to open table test: ".$!."\n";
} else {
	$fh->autoflush(1);
	my $start = time;
	#for (my $i = 0; $i < 40000; $i ++) {
	#    _insert($fh, [["int", $i], ["int", $i], ["int", $i], ["int", $i], ["int", $i],
	#                     ["string", "a" x 1000], ["string", "b" x 10000], ["string", "c" x 100000]]);
	#}
	
	for (my $i = 0; $i < 40000; $i ++) {
		_update($fh, $i, [["int", $i], ["int", $i], ["int", $i], ["int", $i], ["int", $i],
							 ["string", "a" x 1000], ["string", "b" x 10000], ["string", "c" x 100000]]);
	} 
	#for (my $i = 0; $i < 40000; $i ++) {
	#	_delete($fh, $i);
	#} 
	my $duration = time - $start;
	print("Operation took ".$duration." seconds\n");
	$fh->close();
}
