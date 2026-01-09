#!/usr/local/bin/perl

#┌─────────────────────────────────
#│ WEB PATIO : patio.cgi - 2022/03/26
#│ copyright (c) kentweb, 1997-2022
#│ https://www.kent-web.com/
#└─────────────────────────────────

# モジュール宣言
use strict;
use CGI::Carp qw(fatalsToBrowser);
use lib "./lib";
use CGI::Minimal;

# 設定ファイル認識
require "./init.cgi";
my %cf = set_init();

# データ受理
CGI::Minimal::max_read_size($cf{maxdata});
my $cgi = CGI::Minimal->new;
error('容量オーバー') if ($cgi->truncated);
my %in = parse_form($cgi);

# 認証モード
my %au = authent() if ($cf{authkey});

# 処理分岐
if ($in{read}) { read_log(); }
if ($in{edit}) { pwd_form(); }
if ($in{mode} eq 'form') { form_page(); }
if ($in{mode} eq 'find') { find_page(); }
if ($in{mode} eq 'note') { note_page(); }
if ($in{mode} eq 'past') { past_page(); }
if ($in{mode} eq 'manual') { manual_page(); }
if ($in{mode} eq 'find_owner') { find_owner(); }
bbs_list();

#-----------------------------------------------------------
#  メニュー部表示
#-----------------------------------------------------------
sub bbs_list {
	# アラーム数定義
	my $alarm = int ($cf{m_max} * 0.9);
	
	# ページ数
	my $pg = $in{pg} || 0;
	
	# スレッド表示
	my ($i,@log);
	open(IN,"$cf{datadir}/index1.log") or error("open err: index1.log");
	my $top = <IN>;
	while (<IN>) {
		$i++;
		next if ($i < $pg + 1);
		next if ($i > $pg + $cf{pgmax_now});
		
		push(@log,$_);
	}
	close(IN);
	
	# 繰越ボタン作成
	my $page_btn = make_pgbtn($i,$pg,$cf{pgmax_now});
	
	# テンプレート読込
	open(IN,"$cf{tmpldir}/bbs.html") or error("open err: bbs.html");
	my $tmpl = join('',<IN>);
	close(IN);
	
	if ($cf{authkey}) {
		$tmpl =~ s/!login-name!/$au{name}/g;
	} else {
		$tmpl =~ s|<!-- auth -->.+?<!-- /auth -->||sg;
	}
	$tmpl =~ s|!bbs_css!|$cf{cmnurl}/style.css|g;
	$tmpl =~ s|!bbs_js!|$cf{cmnurl}/bbs_v4.js|g;
	$tmpl =~ s/!([a-z]+_cgi)!/$cf{$1}/g;
	$tmpl =~ s/!bbs_title!/$cf{bbs_title}/g;
	$tmpl =~ s/!homepage!/$cf{homepage}/g;
	$tmpl =~ s|!ico:(\w+\.\w+)!|<img src="$cf{cmnurl}/$1" alt="$1" class="icon">|g;
	$tmpl =~ s/!page-btn!/$page_btn/g;
	
	# テンプレート分割
	my ($head,$loop,$foot) = $tmpl =~ m|(.+)<!-- loop -->(.+?)<!-- /loop -->(.+)|s
			? ($1,$2,$3)
			: error("テンプレート不正");
	
	# 認証クッキー
	if ($cf{authkey} && $in{mode} eq 'login') {
		set_cookie('CGISESSID',$au{sid});
	}
	
	# 画面表示
	print "Content-type: text/html; charset=utf-8\n\n";
	print $head;
	
	for (@log) {
		chomp;
		my ($num,$sub,$res,$nam,$upd,$last,$key,$upl) = split(/<>/);
		my $ukey = $upl ? 1 : 0;
		
		# 参照カウンタ
		open(NO,"$cf{datadir}/log/$num.dat");
		my $data = <NO>;
		close(NO);
		my ($cnt) = (split(/:/,$data))[0];
		
		my $tmp = $loop;
		$tmp =~ s/!ico!/icon_img($key,$res,$alarm,$upl)/eg;
		$tmp =~ s/!url!/$cf{bbs_cgi}?read=$num&amp;ukey=$ukey/g;
		$tmp =~ s/!sub!/$sub/g;
		$tmp =~ s/!name!/$nam/g;
		$tmp =~ s/!res!/$res/g;
		$tmp =~ s/!total!/($res+1)/eg; # 親記事含めた合計
		$tmp =~ s/!count!/$cnt/g;
		$tmp =~ s/!update!/$upd/g;
		$tmp =~ s/!last!/$last/g;
		print $tmp;
	}
	
	# フッター
	footer($foot);
}

#-----------------------------------------------------------
#  フォルダーアイコン
#-----------------------------------------------------------
sub icon_img {
	my ($key,$res,$alarm,$upl) = @_;
	
	# アイコン判断
	my $ico;
	if ($key eq '0') { $ico = 0; }
	elsif ($key == 2) { $ico = 2; }
	elsif ($res >= $alarm) { $ico = 'alerm'; }
	elsif ($upl) { $ico = 'image'; }
	else { $ico = 1; }
	
	return qq|<img src="$cf{cmnurl}/$cf{fld_icon}{$ico}" alt="$cf{fld_icon}{$ico}" class="icon">|;
}

#-----------------------------------------------------------
#  記事閲覧
#-----------------------------------------------------------
sub read_log {
	# クッキー取得
	my ($ck_nam,$ck_eml,$ck_url,$ck_mlo) = get_cookie();
	$ck_url ||= 'http://';
	
	# アイコン
	my $smile;
	my @smile = split(/\s+/,$cf{smile});
	for (0 .. $#smile) {
		$smile .= qq|<a href="javascript:face('{ico:$_}')"><img src="$cf{cmnurl}/$smile[$_]" alt="$smile[$_]"></a>|;
	}
	
	# アラーム数定義
	my $alarm = int ($cf{m_max} * 0.9);
	
	# ページ数定義
	my $pg = $in{pg} || 0;
	
	# スレッド読み込み
	$in{read} =~ s/\D//g;
	my @log;
	open(IN,"$cf{datadir}/log/$in{read}.cgi") or error("open err: $in{read}.cgi");
	my $top = <IN>;
	my $par = <IN>;
	my ($no,$sub,$res,$key) = split(/<>/,$top);
	
	my $i = 0;
	while(<IN>) {
		$i++;
		next if ($i <= $res - $cf{pg_max} - $pg);
		last if ($i > $res - $pg);
		
		unshift(@log,$_);
	}
	close(IN);
	
	# 返信フォーム
	my $resfm = 1;
	if ($key != 1 || $in{log} eq 'past') {
		$resfm = 0;
	}
	
	# 繰越ボタン作成
	my $page_btn = make_pgbtn($res,$pg,$cf{pg_max},"read=$in{read}");
	
	# テンプレート読込
	open(IN,"$cf{tmpldir}/read.html") or error("open err: read.html");
	my $tmpl = join('',<IN>);
	close(IN);
	
	$tmpl =~ s|!bbs_css!|$cf{cmnurl}/style.css|g;
	$tmpl =~ s|!bbs_js!|$cf{cmnurl}/bbs.js|g;
	$tmpl =~ s/!bbs_title!/$cf{bbs_title}/g;
	$tmpl =~ s|<!-- past -->.+?<!-- /past -->||s if ($in{log} ne 'past');
	
	# ミニ表示モード対応 (Floating Form)
	if ($in{view} eq 'mini' || $in{mini}) {
		$tmpl =~ s/<body\b[^>]*>/<body class="mini-mode">/i;
		$tmpl .= "<!-- debug: mini-mode applied -->";
	}
	
	# 画像認証作成
	my ($str_plain,$str_crypt);
	if ($cf{use_captcha} > 0 && $resfm) {
		require $cf{captcha_pl};
		($str_plain, $str_crypt) = cap::make( $cf{captcha_key}, $cf{cap_len} );
	} else {
		$tmpl =~ s|<!-- captcha -->.+?<!-- /captcha -->||s;
	}
	
	# email表示
	my $op_mlo;
	my @mlo = ('非表示','表示');
	foreach (1,0) {
		if ($ck_mlo eq $_) {
			$op_mlo .= qq|<option value="$_" selected>$mlo[$_]\n|;
		} else {
			$op_mlo .= qq|<option value="$_">$mlo[$_]\n|;
		}
	}
	
	# 親記事
	my ($no2,$sub,$nam,$eml,$com,$date,$ho,$pw,$url,$mlo,$myid,$tim,$up1,$up2,$up3) = split(/<>/, $par);
	$nam = qq|<a href="mailto:$eml">$nam</a>| if ($eml && $mlo);
	$url &&= qq|<a href="$url" target="_blank">$url</a>|;
	$com =~ s|\{ico:(\d+)\}|<img src="$cf{cmnurl}/$smile[$1]" alt="$smile[$1]" class="icon s">|g;
	$com = autolink($com) if ($cf{autolink});
	
	# 画像
	$com = image($com,$tim,$up1,$up2,$up3);
	
	# フォーム用件名
	my $resub = $sub =~ /^Re:/ ? $sub : "Re: $sub";
	
	# 文字置き換え
	$tmpl =~ s/!([a-z]+_cgi)!/$cf{$1}/g;
	$tmpl =~ s/!ico!/icon_img($key,$res,$alarm,$in{ukey})/eg;
	$tmpl =~ s/!sub!/$sub/g;
	$tmpl =~ s/!date!/$date/g;
	$tmpl =~ s/!name!/$nam/g;
	$tmpl =~ s/!url!/$url/g;
	$tmpl =~ s/!comment!/$com/g;
	$tmpl =~ s|!ico_edit!|<a href="$cf{bbs_cgi}?edit=$in{read}&amp;no=0"><img src="$cf{cmnurl}/pg_edit.gif" alt="編集" class="icon"></a>|g;
	$tmpl =~ s/!page_btn!/$page_btn/g;
	$tmpl =~ s/!res!/$in{read}/g;
	
	# 認証モード
	if ($cf{authkey}) {
		$tmpl =~ s/!id!/$myid/g;
	} else {
		$tmpl =~ s|<!-- id -->.+?<!-- /id -->||s;
	}
	
	# 返信フォーム/編集ボタン
	if (!$resfm) {
		$tmpl =~ s|<!-- resform -->.+?<!-- /resform -->||sg;
		$tmpl =~ s|<!-- edit -->.+?<!-- /edit -->||sg;
	} else {
		$tmpl =~ s/!str_crypt!/$str_crypt/g;
		$tmpl =~ s/!fm_sub!/$resub/g;
		$tmpl =~ s/!fm_name!/$ck_nam/g;
		$tmpl =~ s/!fm_email!/$ck_eml/g;
		$tmpl =~ s/!fm_url!/$ck_url/g;
		$tmpl =~ s/!smile!/$smile/g;
		$tmpl =~ s/<!-- op_mlo -->/$op_mlo/g;
	}
	
	# テンプレート分割
	my ($head,$loop,$foot) = $tmpl =~ m|(.+)<!-- loop -->(.+?)<!-- /loop -->(.+)|s
			? ($1,$2,$3)
			: error("テンプレート不正");
	
	# ヘッダ表示
	print "Content-type: text/html; charset=utf-8\n\n";
	print $head;
	
	# レス記事
	foreach (@log) {
		my ($no,$sub,$nam,$eml,$com,$date,$ho,$pw,$url,$mlo,$myid,$tim,$up1,$up2,$up3) = split(/<>/);
		$nam = qq|<a href="mailto:$eml">$nam</a>| if ($eml && $mlo);
		$url &&= qq|<a href="$url" target="_blank">$url</a>|;
		$com =~ s|\{ico:(\d+)\}|<img src="$cf{cmnurl}/$smile[$1]" alt="$smile[$1]" class="icon s">|g;
		$com = autolink($com) if ($cf{autolink});
		
		# 画像
		$com = image($com,$tim,$up1,$up2,$up3);
		
		my $tmp = $loop;
		$tmp =~ s|!ico:(\w+\.\w+)!|<img src="$cf{cmnurl}/$1" alt="$1" class="icon">|g;
		$tmp =~ s/!res_sub!/$sub/g;
		$tmp =~ s/!res_date!/$date/g;
		$tmp =~ s/!res_name!/$nam/g;
		$tmp =~ s/!res_url!/$url/g;
		$tmp =~ s/!res_com!/$com/g;
		$tmp =~ s|!res_ico_edit!|<a href="$cf{bbs_cgi}?edit=$in{read}&amp;no=$no"><img src="$cf{cmnurl}/pg_edit.gif" alt="編集" class="icon"></a>|g;
		
		# 認証モード
		if ($cf{authkey}) {
			$tmp =~ s/!res_id!/$myid/g;
		} else {
			$tmp =~ s|<!-- id -->.+?<!-- /id -->||s;
		}
		
		print $tmp;
	}
	
	# カウントアップ
	count_up();
	
	# フッター
	footer($foot);
}

#-----------------------------------------------------------
#  認証フォーム
#-----------------------------------------------------------
sub pwd_form {
	# 汚染チェック
	$in{edit} =~ s/\D//g;
	$in{no} =~ s/\D//g;
	
	# 記事
	my ($name,$pwd);
	open(IN,"$cf{datadir}/log/$in{edit}.cgi") or error("open err: $in{edit}.cgi");
	my $top = <IN>;
	while(<IN>) {
		my ($no,$sub,$nam,$eml,$com,$dat,$ho,$pw,$url,$mlo,$myid,$tim,$upl1,$upl2,$upl3) = split(/<>/);
		
		if ($in{no} == $no) {
			$name = $nam;
			$pwd = $pw;
			last;
		}
	}
	close(IN);
	
	# パスワード未設定
	error("この記事はパスワード未設定のため編集できません") if ($pwd eq '');
	
	# 処理選択オプション
	my $op_job = qq|<option value="edit" selected>記事を編集\n|;
	if ($in{no} == 0) {
		$op_job .= qq|<option value="lock">スレッドをロック\n|;
		} else {
		$op_job .= qq|<option value="dele">記事を削除\n|;
	}
	
	# 記事情報データ分解
	my ($no,$sub,$res,$key) = split(/<>/,$top);
	
	# テンプレート読み込み
	open(IN,"$cf{tmpldir}/pwd.html") or error("open err: pwd.html");
	my $tmpl = join('',<IN>);
	close(IN);
	
	# 文字置換
	$tmpl =~ s/!bbs_title!/$cf{bbs_title}/g;
	$tmpl =~ s|!bbs_css!|$cf{cmnurl}/style.css|g;
	$tmpl =~ s/!sub!/$sub/g;
	$tmpl =~ s/!name!/$name/g;
	$tmpl =~ s/!art!/$in{edit}/g;
	$tmpl =~ s/!no!/$in{no}/g;
	$tmpl =~ s/!([a-z]+_cgi)!/$cf{$1}/g;
	$tmpl =~ s|!ico:(\w+\.\w+)!|<img src="$cf{cmnurl}/$1" alt="$1" class="icon">|g;
	$tmpl =~ s/<!-- op_job -->/$op_job/g;
	
	# 画面表示
	print "Content-type: text/html; charset=utf-8\n\n";
	print $tmpl;
	exit;
}

#-----------------------------------------------------------
#  留意事項表示
#-----------------------------------------------------------
sub note_page {
	# テンプレート読み込み
	open(IN,"$cf{tmpldir}/note.html") or error("open err: note.html");
	my $tmpl = join('',<IN>);
	close(IN);
	
	# 文字置換
	$tmpl =~ s|!bbs_css!|$cf{cmnurl}/style.css|g;
	$tmpl =~ s|!bbs_js!|$cf{cmnurl}/bbs.js|g;
	$tmpl =~ s/!bbs_title!/$cf{bbs_title}/g;
	$tmpl =~ s/!maxdata!/$cf{maxdata}バイト/g;
	$tmpl =~ s/!max_w!/$cf{max_img_w}/g;
	$tmpl =~ s/!max_h!/$cf{max_img_h}/g;
	
	# 画面表示
	print "Content-type: text/html; charset=utf-8\n\n";
	print $tmpl;
	exit;
}

#-----------------------------------------------------------
#  画像表示
#-----------------------------------------------------------
sub image {
	my ($com,$fnam,$up1,$up2,$up3) = @_;
	my %img = (1 => $up1, 2 => $up2, 3 => $up3);
	
	my $img;
	for my $i (1 .. 3) {
		my ($ex,$w,$h) = split(/,/,$img{$i});
		if ($ex) {
			($w,$h) = &resize($w,$h);
			my $pic = -e "$cf{uplurl}/$fnam-s-$i$ex" ? "$fnam-s-$i$ex" : "$fnam-$i$ex";
			$img .= qq|<a href="$cf{uplurl}/$fnam-$i$ex" target="_blank"><img src="$cf{uplurl}/$pic" width="$w" height="$h" class="image" alt="$pic"></a>|;
		}
	}
	if ($img) {
		return "$com<p>$img</p>";
	} else {
		return $com;
	}
}

#-----------------------------------------------------------
#  投稿フォーム
#-----------------------------------------------------------
sub form_page {
	# クッキー取得
	my ($ck_nam,$ck_eml,$ck_url,$ck_mlo) = get_cookie();
	$ck_url ||= 'http://';
	
	# アイコン
	my $smile;
	my @smile = split(/\s+/,$cf{smile});
	foreach (0 .. $#smile) {
		$smile .= qq|<a href="javascript:face('{ico:$_}')"><img src="$cf{cmnurl}/$smile[$_]" alt="$smile[$_]"></a>|;
	}
	
	# テンプレート読み込み
	open(IN,"$cf{tmpldir}/form.html") or error("open err: form.html");
	my $tmpl = join('',<IN>);
	close(IN);
	
	# email表示
	my $op_mlo;
	my @mlo = ('非表示','表示');
	foreach (1,0) {
		if ($ck_mlo eq $_) {
			$op_mlo .= qq|<option value="$_" selected>$mlo[$_]\n|;
		} else {
			$op_mlo .= qq|<option value="$_">$mlo[$_]\n|;
		}
	}
	
	# 画像認証作成
	my ($str_plain,$str_crypt);
	if ($cf{use_captcha} > 0) {
		require $cf{captcha_pl};
		($str_plain, $str_crypt) = cap::make( $cf{captcha_key}, $cf{cap_len} );
	} else {
		$tmpl =~ s|<!-- captcha -->.+?<!-- /captcha -->||s;
	}
	
	# 文字置換
	$tmpl =~ s/!bbs_title!/$cf{bbs_title}/g;
	$tmpl =~ s|!bbs_css!|$cf{cmnurl}/style.css|g;
	$tmpl =~ s|!bbs_js!|$cf{cmnurl}/bbs.js|g;
	$tmpl =~ s/!([a-z]+_cgi)!/$cf{$1}/g;
	$tmpl =~ s/!ico:(\w+\.\w+)!/<img src="$cf{cmnurl}\/$1" alt="$1" class="icon">/g;
	$tmpl =~ s/!str_crypt!/$str_crypt/g;
	$tmpl =~ s/!name!/$ck_nam/g;
	$tmpl =~ s/!email!/$ck_eml/g;
	$tmpl =~ s/!url!/$ck_url/g;
	$tmpl =~ s/!smile!/$smile/g;
	$tmpl =~ s/<!-- op_mlo -->/$op_mlo/g;
	
	# 画面表示
	print "Content-type: text/html; charset=utf-8\n\n";
	print $tmpl;
	exit;
}

#-----------------------------------------------------------
#  検索画面
#-----------------------------------------------------------
sub find_page {
	# テンプレート読み込み
	open(IN,"$cf{tmpldir}/find.html") or error("open err: find.html");
	my $tmpl = join('',<IN>);
	close(IN);
	
	# 条件
	if ($in{cond} eq '') { $in{cond} = 1; }
	my $op_cond;
	my %cond = (1 => 'AND', 0 => 'OR');
	foreach (1,0) {
		if ($in{cond} == $_) {
			$op_cond .= qq|<option value="$_" selected>$cond{$_}\n|;
		} else {
			$op_cond .= qq|<option value="$_">$cond{$_}\n|;
		}
	}
	# 範囲
	$in{area} ||= 1;
	my %area = (1 => '現行ログ', 2 => '過去ログ');
	my $area;
	foreach (1,2) {
		if ($in{area} == $_) {
			$area .= qq|<input type="radio" name="area" value="$_" checked>$area{$_}\n|;
		} else {
			$area .= qq|<input type="radio" name="area" value="$_">$area{$_}\n|;
		}
	}
	
	# 文字置換
	$tmpl =~ s/!bbs_title!/$cf{bbs_title}/g;
	$tmpl =~ s|!bbs_css!|$cf{cmnurl}/style.css|g;
	$tmpl =~ s/!([a-z]+_cgi)!/$cf{$1}/g;
	$tmpl =~ s/!ico:(\w+\.\w+)!/<img src="$cf{cmnurl}\/$1" alt="$1" class="icon">/g;
	$tmpl =~ s/<!-- op_cond -->/$op_cond/g;
	$tmpl =~ s/!area!/$area/g;
	$tmpl =~ s/!word!/$in{word}/g;
	
	# 検索実行
	if ($in{word} ne '') {
		my ($head,$loop,$foot) = $tmpl =~ m|(.+)<!-- search -->(.+?)<!-- /search -->(.+)|s
				? ($1,$2,$3)
				: error("テンプレートが不正です$tmpl");
		
		# 画面表示
		print "Content-type: text/html; charset=utf-8\n\n";
		print $head;
		search($loop);
		print $foot;
		exit;
	
	# 検索前
	} else {
		$tmpl =~ s|<!-- search -->.+?<!-- /search -->||s;
		
		# 画面表示
		print "Content-type: text/html; charset=utf-8\n\n";
		print $tmpl;
		exit;
	}
}

#-----------------------------------------------------------
#  検索実行
#-----------------------------------------------------------
sub search {
	my $loop = shift;
	$loop =~ m|(.+)<!-- loop -->(.+?)<!-- /loop -->(.+)|s;
	my ($head,$loop,$foot) = ($1,$2,$3);
	
	$in{word} =~ s/　/ /g;
	my @wd = split(/\s+/,$in{word});
	
	# 対象範囲/引数
	my ($idx,$param);
	if ($in{area} == 1) {
		$idx = "$cf{datadir}/index1.log";
	} else {
		$idx = "$cf{datadir}/index2.log";
		$param = "&amp;log=past";
	}
	
	# UTF-8定義
	my $byte1 = '[\x00-\x7f]';
	my $byte2 = '[\xC0-\xDF][\x80-\xBF]';
	my $byte3 = '[\xE0-\xEF][\x80-\xBF]{2}';
	my $byte4 = '[\xF0-\xF7][\x80-\xBF]{3}';
	
	# indexオープン
	my @find;
	open(IN,"$idx") or error("open err: $idx");
	my $top = <IN>;
	while(<IN>) {
		my ($num,$sub,$res,$nam,$upd,$last,$key,$upl) = split(/<>/);
		
		# 各スレッド読み込み
		open(LOG,"$cf{datadir}/log/$num.cgi");
		my $log = join('',<LOG>);
		close(LOG);
		
		# スレッド内検索
		my $flg;
		foreach my $wd (@wd) {
			if ($log =~ /^(?:$byte1|$byte2|$byte3|$byte4)*?\Q$wd\E/i) {
				$flg++;
				if ($in{cond} == 0) { last; }
			} else {
				if ($in{cond} == 1) { $flg = 0; last; }
			}
		}
		if ($flg) { push(@find,$_); }
	}
	close(IN);
	
	# ヒット件数
	my $hit = @find;
	$head =~ s/!hit!/$hit/g;
	$foot =~ s/!hit!/$hit/g;
	
	# アラーム数定義
	my $alarm = int ( $cf{m_max} * 0.9 );
	
	# 結果表示
	print $head;
	foreach (@find) {
		my ($num,$sub,$res,$nam,$upd,$last,$key,$upl) = split(/<>/);
		my $ukey = $upl ? 1 : 0;
		
		my $tmp = $loop;
		$tmp =~ s/!icon!/icon_img($key,$res,$alarm,$upl)/eg;
		$tmp =~ s|!sub!|<a href="$cf{bbs_cgi}?read=$num&amp;ukey=$ukey$param">$sub</a>|g;
		$tmp =~ s/!name!/$nam/g;
		$tmp =~ s/!res!/$res/g;
		$tmp =~ s/!update!/$upd<br>$last/g;
		print $tmp;
	}
	print $foot;
}

#-----------------------------------------------------------
#  過去ログページ
#-----------------------------------------------------------
sub past_page {
	# ページ数
	my $pg = $in{pg} || 0;
	
	# スレッド表示
	my ($i,@log);
	open(IN,"$cf{datadir}/index2.log") or error("open err: index2.log");
	while (<IN>) {
		$i++;
		next if ($i < $pg + 1);
		next if ($i > $pg + $cf{pgmax_past});
		
		push(@log,$_);
	}
	close(IN);
	
	# 繰越ボタン作成
	my $page_btn = make_pgbtn($i,$pg,$cf{pgmax_past},"mode=past");
	
	# テンプレート読み込み
	open(IN,"$cf{tmpldir}/past.html") or error("open err: past.html");
	my $tmpl = join('',<IN>);
	close(IN);
	
	# 文字置換
	$tmpl =~ s/!([a-z]+_cgi)!/$cf{$1}/g;
	$tmpl =~ s/!ico:(\w+\.\w+)!/<img src="$cf{cmnurl}\/$1" alt="$1" class="icon">/g;
	$tmpl =~ s/!page-btn!/$page_btn/g;
	$tmpl =~ s|!bbs_css!|$cf{cmnurl}/style.css|g;
	$tmpl =~ s/!bbs_title!/$cf{bbs_title}/g;
	
	my ($head,$loop,$foot) = $tmpl =~ m|(.+)<!-- loop -->(.+?)<!-- /loop -->(.+)|s
			? ($1,$2,$3)
			: error("テンプレート不正");
	
	# 画面表示
	print "Content-type: text/html; charset=utf-8\n\n";
	print $head;
	
	foreach (@log) {
		my ($num,$sub,$res,$nam,$upd,$last,$key,$upl) = split(/<>/);
		
		my $tmp = $loop;
		$tmp =~ s|!icon!|<img src="$cf{cmnurl}/fld_nor.gif" alt="検索" class="icon">|;
		$tmp =~ s|!sub!|<a href="$cf{bbs_cgi}?read=$num&amp;log=past">$sub</a>|g;
		$tmp =~ s/!name!/$nam/g;
		$tmp =~ s/!res!/$res/g;
		$tmp =~ s/!update!/$upd<br>$last/g;
		print $tmp;
	}
	
	# フッター
	footer($foot);
}

#-----------------------------------------------------------
#  フッター
#-----------------------------------------------------------
sub footer {
	my $foot = shift;
	
	# 著作権表記（削除・改変禁止）
	my $copy = <<EOM;
<p style="margin-top:2.5em;text-align:center;font-family:Verdana,Arial,Helvetica;font-size:10px;">
	- <a href="https://www.kent-web.com/" target="_top">WEB PATIO</a> -
</p>
EOM

	if ($foot =~ /(.+)(<\/body[^>]*>.*)/si) {
		print "$1$copy$2\n";
	} else {
		print "$foot$copy\n";
		print "</body></html>\n";
	}
	exit;
}

#-----------------------------------------------------------
#  繰越ボタン作成
#-----------------------------------------------------------
sub make_pgbtn {
	my ($i,$pg,$max,$param) = @_;
	$max ||= 10;
	
	# 引数
	$param &&= "&$param";
	
	# ページ繰越定義
	my $next = $pg + $max;
	my $back = $pg - $max;
	
	# ページ繰越ボタン作成
	my @pg;
	if ($back >= 0 || $next < $i) {
		my $flg;
		my ($w,$x,$y,$z) = (0,1,0,$i);
		while ($z > 0) {
			if ($pg == $y) {
				$flg++;
				push(@pg,qq|<span class="pg-on"><b>$x</b></span>|);
			} else {
				push(@pg,qq|<span class="pg-off"><a href="$cf{bbs_cgi}?pg=$y$param">$x</a></span>|);
			}
			$x++;
			$y += $max;
			$z -= $max;
			
			if ($flg) { $w++; }
			last if ($w >= 5 && @pg >= 10);
		}
	}
	while( @pg >= 11 ) { shift(@pg); }
	my $ret = join('', @pg);
	if ($back >= 0) {
		$ret = qq!<span class="pg-off"><a href="$cf{bbs_cgi}?pg=$back$param">&lt;</a></span>\n! . $ret;
	}
	if ($next < $i) {
		$ret .= qq!<span class="pg-off"><a href="$cf{bbs_cgi}?pg=$next$param">&gt;</a></span>\n!;
	}
	return $ret ne '' ? qq|<div class="page-btn">$ret</div>| : '';
}

#-----------------------------------------------------------
#  カウントアップ
#-----------------------------------------------------------
sub count_up {
	# IP取得
	my $addr = $ENV{REMOTE_ADDR};
	
	# カウントデータオープン
	open(DAT,"+< $cf{datadir}/log/$in{read}.dat") or error("open err: $in{read}.dat");
	eval "flock(DAT,2);";
	my $data = <DAT>;
	my ($cnt,$ip) = split(/:/,$data);
	
	# IPチェック
	if ($addr ne $ip) {
		$cnt++;
		seek(DAT,0,0);
		print DAT "$cnt:$addr";
		truncate(DAT,tell(DAT));
	}
	close(DAT);
}

#-----------------------------------------------------------
#  認証モード
#-----------------------------------------------------------
sub authent {
	# セッションモジュール取り込み
	require $cf{session_pl};
	
	# ログイン
	if ($in{mode} eq 'login') {
		# 入力チェック
		if ($in{id} eq '' || $in{pw} eq '') {
			error("IDまたはパスワードが未入力です");
		}
		# セッション作成
		make_ses($in{id},$in{pw},"$cf{datadir}/memdata.cgi","$cf{datadir}/ses",$cf{authtime});
	
	# ログオフ
	} elsif ($in{mode} eq 'logoff') {
		# セッション削除
		del_ses("$cf{datadir}/ses");
		
		# 入室画面
		enter_form('cook_del');
	
	# 入室画面
	} elsif ($in{mode} eq 'enter') {
		enter_form();
	
	# セッション管理
	} else {
		session("$cf{datadir}/ses",$cf{bbs_cgi});
	}
}

#-----------------------------------------------------------
#  入室画面
#-----------------------------------------------------------
sub enter_form {
	my $ck = shift;
	
	# テンプレート読み込み
	open(IN,"$cf{tmpldir}/enter.html") or error("open err: enter.html");
	my $tmpl = join('',<IN>);
	close(IN);
	
	$tmpl =~ s|!bbs_css!|$cf{cmnurl}/style.css|g;
	$tmpl =~ s/!bbs_title!/$cf{bbs_title}/g;
	
	# 文字置換
	$tmpl =~ s/!bbs_cgi!/$cf{bbs_cgi}/g;
	
	# クッキー排除
	if ($ck eq 'cook_del') { set_cookie('CGISESSID','','del'); }
	
	# 画面表示
	print "Content-type: text/html; charset=utf-8\n\n";
	print $tmpl;
	exit;
}

#-----------------------------------------------------------
#  crypt照合
#-----------------------------------------------------------
sub decrypt {
	my ($in, $dec) = @_;
	
	my $salt = $dec =~ /^\$1\$(.*)\$/ ? $1 : substr($dec, 0, 2);
	if (crypt($in, $salt) eq $dec || crypt($in, '$1$' . $salt) eq $dec) {
		return 1;
	} else {
		return 0;
	}
}

#-----------------------------------------------------------
#  クッキー取得
#-----------------------------------------------------------
sub get_cookie {
	# クッキー取得
	my $cook = $ENV{HTTP_COOKIE};
	
	# 該当IDを取り出す
	my %cook;
	foreach ( split(/;/,$cook) ) {
		my ($key,$val) = split(/=/);
		$key =~ s/\s//g;
		$cook{$key} = $val;
	}
	
	# URLデコード
	my @cook;
	foreach ( split(/<>/,$cook{$cf{cookie_id}}) ) {
		s/%([0-9A-Fa-f][0-9A-Fa-f])/pack("H2", $1)/eg;
		s/[&"'<>]//g;
		
		push(@cook,$_);
	}
	return @cook;
}

#-----------------------------------------------------------
#  クッキー発行
#-----------------------------------------------------------
sub set_cookie {
	my ($key,$val,$del) = @_;
	
	# 時間定義
	my $gtime = $del eq 'del' ? time - 365*24*60*60 : time + 60*24*60*60;
	
	my ($sec,$min,$hour,$mday,$mon,$year,$wday,undef,undef) = gmtime($gtime);
	my @mon  = qw|Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec|;
	my @week = qw|Sun Mon Tue Wed Thu Fri Sat|;
	
	# 時刻フォーマット
	my $gmt = sprintf("%s, %02d-%s-%04d %02d:%02d:%02d GMT",
				$week[$wday],$mday,$mon[$mon],$year+1900,$hour,$min,$sec);
	
	print "Set-Cookie: $key=$val; expires=$gmt\n";
}

#-----------------------------------------------------------
#  自動リンク
#-----------------------------------------------------------
sub autolink {
	my $text = shift;
	
	$text =~ s/(s?https?:\/\/([\w-.!~*'();\/?:\@=+\$,%#]|&amp;)+)/<a href="$1" target="_blank">$1<\/a>/g;
	return $text;
}


#-----------------------------------------------------------
#  名前からスレッドIDを特定（案1 浮遊フォーム用）
#-----------------------------------------------------------
sub find_owner {
	my $target = $in{name};
	error("名前が指定されていません") if ($target eq "");

	my $found_id = "";
	open(IN, "$cf{datadir}/index1.log") or error("open err: index1.log");
	<IN>; # ヘッダー
	while (<IN>) {
		my ($num, $sub, $res, $nam, $upd, $last, $key, $upl) = split(/<>/);
		if ($nam eq $target) {
			$found_id = $num;
			last;
		}
	}
	close(IN);

	print "Content-type: text/plain; charset=utf-8\n\n";
	if ($found_id) {
		print "target_id:$found_id";
	} else {
		print "not_found";
	}
	exit;
}

#-----------------------------------------------------------
#  マニュアルページ表示
#-----------------------------------------------------------
sub manual_page {
	# テンプレート読込
	open(IN,"$cf{tmpldir}/manual.html") or error("open err: manual.html");
	my $tmpl = join('',<IN>);
	close(IN);
	
	$tmpl =~ s|!bbs_css!|$cf{cmnurl}/style.css|g;
	$tmpl =~ s/!([a-z_]+_cgi)!/$cf{$1}/g;
	$tmpl =~ s/!bbs_title!/$cf{bbs_title}/g;
	$tmpl =~ s/!tmpldir!/$cf{tmpldir}/g;
	
	print "Content-type: text/html; charset=utf-8\n\n";
	print $tmpl;
	exit;
}
