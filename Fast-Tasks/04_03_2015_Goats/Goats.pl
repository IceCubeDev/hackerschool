#!/usr/bin/perl -w
use strict;
use warnings;
use POSIX;
use Data::Dumper;
use Clone;

# ============> INPUT <============
my $N;
my $K;
($N, $K) = split ' ', <STDIN>;
my @goats = split ' ', <STDIN>;

@goats = sort { $a <=> $b } @goats;

my @groups = [];
my $max = pop @goats;
my $min_capacity = $goats[0] + $max;
push @goats, $max;

while (1) {
    @groups = [];
    my $copy = dclone(@goats);
    
    for (my $i = 0; $i < $K; $i ++) {
        my $score = 0;
        my $size = scalar(@$copy);
        for (my $j = 0; $j < $size; $j ++) {
            my $max = @$copy[$size - $j - 1];
            
            if ($score + $max <= $min_capacity) {
                push $groups[$i], $max;
                $score += $max;
                delete @$copy[$i];
            } 
        }
    }
}