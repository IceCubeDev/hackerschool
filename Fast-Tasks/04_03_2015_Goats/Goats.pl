#!/usr/bin/perl -w
use strict;
use warnings;
use POSIX;
use Data::Dumper;
use Storable qw(dclone);

# ============> INPUT <============
my $N;
my $K;
($N, $K) = split ' ', <STDIN>;
my @input_values = split ' ', <STDIN>;

# ============> SOLUTION <============
sub simulate($$);

my @goats;
foreach my $value (@input_values) {
    push(@goats, int($value));
}
@goats = sort { $b <=> $a } @goats;
my $min_capacity = $goats[0];
print simulate($min_capacity, \@goats);

sub simulate($$) {
    my ($min_score, $goats_ref) = @_;
    my $groups = [];
    my $goats_copy = [@{$goats_ref}];
    
    print "Boat size: ".$min_score."\n";
    print (Dumper $goats_ref);
    
    for (my $i = 0; $i < $K; $i ++) {
        push $groups, [];
        my $group_score = 0;
        my @remaining;
        my $group = @$groups[$i];
    
        while (scalar(@$goats_copy) > 0) {
            my $biggest_goat = shift ($goats_copy);
            print("Pop: ".$biggest_goat."\n");
            
            if ($group_score + $biggest_goat <= $min_score) {
                push ($group, $biggest_goat);
                $group_score += $biggest_goat;
                print("\tAdd to group ".$i." ");
                print(Dumper $group);
                print("\n");
            } else {
                print("\tAdd to remaining.\n");
                push(@remaining, $biggest_goat);
                print("\tRemaining: ", Dumper \@remaining);
                print "\n";
            }
        }
        
        print("Still left for transport: ", scalar(@remaining).": ", Dumper \@remaining);
        $goats_copy = \@remaining;
        print("Group ".$i."\n");
        print(Dumper $group);
    }
    
    print("Unable to transport: ", Dumper $goats_copy, "\n");
    
    print (Dumper $goats_ref);
    if (scalar(@$goats_copy) <= 0) {
        return $min_score;
    } else {
        print("Increasing boat size ...\n");
        return simulate($min_score + 1, $goats_ref);
    }
}