#!/usr/local/bin/perl
print "Content-type: text/plain\n\n";
print "--- File Checklist ---\n";

sub check {
    my $path = shift;
    if (-e $path) {
        my $mode = (stat($path))[2];
        printf "FOUND: %-30s (Perm: %04o)\n", $path, $mode & 07777;
        if (-d $path) {
            opendir(my $dh, $path);
            while (my $f = readdir($dh)) {
                next if $f =~ /^\./;
                check("$path/$f") if $path eq "./lib" || $path eq "./lib/CGI";
            }
            closedir($dh);
        }
    } else {
        printf "MISSING: %-30s\n", $path;
    }
}

check("./init.cgi");
check("./lib");
check("./lib/CGI");
check("./lib/CGI/Minimal.pm");
