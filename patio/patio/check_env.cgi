#!/usr/local/bin/perl

use strict;
use warnings;
use CGI::Carp qw(fatalsToBrowser);

print "Content-type: text/html\n\n";
print "<html><body><h1>Environment Check</h1>";

print "<h2>Perl Version</h2><pre>$]</pre>";

# Check Archive::Zip
print "<h3>Archive::Zip</h3>";
eval { require Archive::Zip; };
if ($@) {
    print "<p style='color:red'>NOT Installed: $@</p>";
} else {
    print "<p style='color:green'>Installed. Version: " . $Archive::Zip::VERSION . "</p>";
}

# Check IO::Compress::Zip
print "<h3>IO::Compress::Zip</h3>";
eval { require IO::Compress::Zip; };
if ($@) {
    print "<p style='color:red'>NOT Installed: $@</p>";
} else {
    print "<p style='color:green'>Installed. Version: " . $IO::Compress::Zip::VERSION . "</p>";
}

print "<h2>INC</h2><pre>" . join("\n", @INC) . "</pre>";
print "</body></html>";
