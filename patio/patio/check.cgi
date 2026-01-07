#!/usr/local/bin/perl

#┌─────────────────────────────────
#│ WEB PATIO : check.cgi - 2022/03/26
#│ copyright (c) kentweb, 1997-2022
#│ https://www.kent-web.com/
#└─────────────────────────────────

# モジュール宣言
use strict;
use CGI::Carp qw(fatalsToBrowser);

# 外部ファイル取込み
require './init.cgi';
my %cf = set_init();

print <<EOM;
Content-type: text/html; charset=utf-8

<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Check Mode</title>
</head>
<body>
<b>Check Mode: [ $cf{version} ]</b>
<ul>
<li>Perlバージョン : $]
EOM

# ディレクトリ
for ( $cf{datadir}, "$cf{datadir}/log", "$cf{datadir}/ses", "$cf{datadir}/pwd", $cf{upldir} ) {
	if (-d $_) {
		print "<li>$_ ディレクトリパス : OK\n";
		
		if (-r $_ && -w $_ && -x $_) {
			print "<li>$_ ディレクトリパーミッション : OK\n";
		} else {
			print "<li>$_ ディレクトリパーミッション : NG\n";
		}
	} else {
		print "<li>$_ ディレクトリパス : NG\n";
	}
}

# ファイルチェック
for (qw(index1.log index2.log memdata.cgi pass.dat)) {
	if (-f "$cf{datadir}/$_") {
		print "<li>$cf{datadir}/$_ ファイルパス : OK\n";
		
		if (-r "$cf{datadir}/$_" && -w "$cf{datadir}/$_") {
			print "<li>$_ ファイルパーミッション : OK\n";
		} else {
			print "<li>$_ ファイルパーミッション : NG\n";
		}
	} else {
		print "<li>$_ ファイルパス : NG\n";
	}
}

# テンプレート
for (qw(bbs edit enter find note error form mesg pwd past read)) {
	if (-e "$cf{tmpldir}/$_.html") {
		print "<li>テンプレート( $_.html ) : OK\n";
	} else {
		print "<li>テンプレート( $_.html ) : NG\n";
	}
}

# Image-Magick動作確認
eval { require Image::Magick; };
if ($@) {
	print "<li>Image-Magick動作: NG\n";
} else {
	print "<li>Image-Magick動作: OK\n";
}

print <<EOM;
</ul>
</body>
</html>
EOM
exit;

