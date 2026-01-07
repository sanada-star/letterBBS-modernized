#!/usr/local/bin/perl

#┌─────────────────────────────────
#│ WEB PATIO : admin.cgi - 2022/03/26
#│ copyright (c) kentweb, 1997-2022
#│ https://www.kent-web.com/
#└─────────────────────────────────

# モジュール宣言
use strict;
use CGI::Carp qw(fatalsToBrowser);
use vars qw(%in %cf);
use lib "./lib";
use CGI::Minimal;
use CGI::Session;
use Digest::SHA::PurePerl qw(sha256_base64);

# 設定ファイル認識
require "./init.cgi";
%cf = set_init();

# データ受理
CGI::Minimal::max_read_size($cf{maxdata});
my $cgi = CGI::Minimal->new;
cgi_err('容量オーバー') if ($cgi->truncated);
%in = parse_form($cgi);

# 認証
require "./lib/login.pl";
auth_login();

# 条件分岐
if ($in{data_now} or $in{data_past}) { data_mgr(); }
if ($in{auth_mgr}) { auth_mgr(); }
if ($in{size_chk}) { size_chk(); }
if ($in{pass_mgr}) { pass_mgr(); }

# メニュー画面
menu_html();

#-----------------------------------------------------------
#  メニュー画面
#-----------------------------------------------------------
sub menu_html {
	header("メニューTOP");
	
	print <<EOM;
<div id="body">
<form action="$cf{admin_cgi}" method="post">
<input type="hidden" name="sid" value="$in{sid}">
<table class="form-tbl" id="menu">
<tr>
	<th>選択</th>
	<th class="w-15">処理メニュー</th>
</tr><tr>
	<td><input type="submit" name="data_now" value="選択"></td>
	<td>現行ログメンテナンス</td>
</tr><tr>
	<td><input type="submit" name="data_past" value="選択"></td>
	<td>過去ログメンテナンス</td>
EOM

	if ($cf{authkey}) {
		print qq|</tr><tr>\n|;
		print qq|<td><input type="submit" name="auth_mgr" value="選択"></td>\n|;
		print qq|<td>会員管理（認証モード）</td>\n|;
	}
	
	print <<EOM;
</tr><tr>
	<td><input type="submit" name="size_chk" value="選択"></td>
	<td>ファイル容量</td>
</tr><tr>
	<td><input type="submit" name="pass_mgr" value="選択"></td>
	<td>パスワード管理</td>
</tr><tr>
	<td><input type="submit" name="logoff" value="選択"></td>
	<td>ログアウト</td>
</tr>
</table>
</form>
</div>
</body>
</html>
EOM
	exit;
}

#-----------------------------------------------------------
#  データ編集
#-----------------------------------------------------------
sub data_mgr {
	# 汚染チェック
	$in{no} =~ s/\D//g;
	
	# index定義
	my ($log,$mode,$subject);
	if ($in{data_now}) {
		$log = "$cf{datadir}/index1.log";
		$subject = "現行ログ";
		$mode = "data_now";
	} else {
		$log = "$cf{datadir}/index2.log";
		$subject = "過去ログ";
		$mode = "data_past";
	}
	
	# スレッド削除
	if ($in{job} eq "del" && $in{no}) {
		del_thread($log);
	
	# スレッドロック開閉
	} elsif ($in{job} eq "lock" && $in{no} && $in{data_now}) {
		lock_thread($log);
	
	# スレッドの管理者コメントモード
	} elsif ($in{job} eq "admin" && $in{no} && $in{data_now}) {
		admin_thread($log);
	
	# スレッド内個別記事
	} elsif ($in{job} eq "art" && $in{no}) {
		article($subject,$mode,$log);
	}
	
	header("データメンテ [ $subject ]");
	back_btn();
	print <<EOM;
<div id="ttl"><img src="$cf{cmnurl}/db_gear.png" alt="" class="icon"> データメンテ [ $subject ]</div>
<form action="$cf{admin_cgi}" method="post">
<input type="hidden" name="sid" value="$in{sid}">
<input type="hidden" name="$mode" value="1">
<div class="ope-btn">
処理
<select name="job">
<option value="art">個別メンテ
<option value="del">スレ削除
EOM

	if ($in{data_now}) {
		print qq|<option value="lock">ロック開閉\n|;
		print qq|<option value="admin">管理者コメ\n|;
	}
	
	print <<EOM;
</select>
<input type="submit" value="送信する">
</div>
<table class="form-tbl" id="list">
<tr>
	<th>選択</th>
	<th>状態</th>
	<th>スレッド</th>
	<th>作成者</th>
	<th>レス数</th>
	<th>備考</th>
</tr>
EOM

	my %stat = (0 => 'ロック中', 2 => '管理コメ');
	
	# スレッド一覧
	open(IN,"$log") or cgi_err("open err: $log");
	my $top = <IN> if ($in{data_now});
	while (<IN>) {
		my ($no,$sub,$res,$nam,$upd,$las,$key,$upl) = split(/<>/);
		
		my $ico;
		if ($key == 2) { $ico = 2; }
		elsif ($upl) { $ico = 'image'; }
		else { $ico = $key; }
		
		print qq|<tr><td class="ta-c"><input type="radio" name="no" value="$no"></td>|;
		print qq|<td class="ta-c"><img src="$cf{iconurl}/$cf{fld_icon}->{$ico}" alt=""></td>|;
		print qq|<td><b>$sub</b></td>|;
		print qq|<td>$nam</td>|;
		print qq|<td class="ta-r">$res</td>|;
		print qq|<td>$stat{$key}<br></td></tr>\n|;
	}
	close(IN);
	
	print <<EOM;
</table>
</form>
</div>
</body>
</html>
EOM
	exit;
}

#-----------------------------------------------------------
#  スレッド削除
#-----------------------------------------------------------
sub del_thread {
	my ($log) = @_;
	
	# indexより削除情報抽出
	my @new;
	open(DAT,"+< $log") or cgi_err("open err: $log");
	eval "flock(DAT,2);";
	my $top = <DAT> if ($in{data_now});
	while(<DAT>) {
		my ($no) = (split(/<>/))[0];
		
		if ($in{no} == $no) {
			
			# ログ展開
			open(DB,"$cf{datadir}/log/$in{no}.cgi");
			while( my $db = <DB> ) {
				my ($no,$sub,$nam,$eml,$com,$dat,$ho,$pw,$url,$mvw,$myid,$tim,$up1,$up2,$up3) = split(/<>/, $db);
				
				# 画像削除
				my $n;
				foreach my $up ($up1,$up2,$up3) {
					$n++;
					my ($ex) = split(/,/, $up);
					next if (!$ex);
					if (-e "$cf{upldir}/$tim-$n$ex") {
						unlink("$cf{upldir}/$tim-$n$ex");
					}
					if (-e "$cf{upldir}/$tim-s-$n$ex") {
						unlink("$cf{upldir}/$tim-s-$n$ex");
					}
				}
			}
			close(DB);
			
			# スレッド削除
			unlink("$cf{datadir}/log/$in{no}.cgi");
			unlink("$cf{datadir}/log/$in{no}.dat");
			
			next;
		}
		push(@new,$_);
	}
	
	# index更新
	unshift(@new,$top) if ($in{data_now});
	seek(DAT,0,0);
	print DAT @new;
	truncate(DAT,tell(DAT));
	close(DAT);
}

#-----------------------------------------------------------
#  スレッドロック開閉
#-----------------------------------------------------------
sub lock_thread {
	my ($log) = @_;
	
	open(DAT,"+< $cf{datadir}/log/$in{no}.cgi") or cgi_err("open err: $in{no}.cgi");
	eval "flock(DAT,2);";
	my $top = <DAT>;
	my @data = <DAT>;
	
	# 先頭記事分解、キー開閉
	my ($num,$sub,$res,$key) = split(/<>/, $top);
	
	# 0=ロック 1=標準 2=管理用
	$key = $key ? 0 : 1;
	
	# スレッド更新
	unshift(@data,"$num<>$sub<>$res<>$key<>\n");
	seek(DAT,0,0);
	print DAT @data;
	truncate(DAT,	tell(DAT));
	close(DAT);
	
	# index読み込み
	@data = ();
	open(DAT,"+< $log") or cgi_err("open err: $log");
	eval "flock(DAT,2);";
	my $top = <DAT>;
	while(<DAT>) {
		chomp;
		my ($no,$sub,$res,$nam,$da,$na2,$key,$upl) = split(/<>/);
		
		if ($in{no} == $no) {
			# 0=ロック 1=標準 2=管理用
			$key = $key ? 0 : 1;
			$_ = "$no<>$sub<>$res<>$nam<>$da<>$na2<>$key<>$upl<>";
		}
		push(@data,"$_\n");
	}
	
	# index更新
	unshift(@data,$top);
	seek(DAT,0,0);
	print DAT @data;
	truncate(DAT,tell(DAT));
	close(DAT);
}

#-----------------------------------------------------------
#  スレッド管理者コメント
#-----------------------------------------------------------
sub admin_thread {
	my ($log) = @_;
	
	open(DAT,"+< $cf{datadir}/log/$in{no}.cgi") or cgi_err("open err: $in{no}.cgi");
	eval "flock(DAT,2);";
	my $top = <DAT>;
	my @data = <DAT>;
	
	# 先頭記事分解、キー開閉
	my ($num,$sub,$res,$key) = split(/<>/,$top);
	
	# 0=ロック 1=標準 2=管理用
	$key = $key < 2 ? 2 : 1;
	
	# スレッド更新
	unshift(@data,"$num<>$sub<>$res<>$key<>\n");
	seek(DAT,0,0);
	print DAT @data;
	truncate(DAT,tell(DAT));
	close(DAT);
	
	# index読み込み
	my ($new,@data);
	open(DAT,"+< $log") or cgi_err("open err: $log");
	eval "flock(DAT,2);";
	my $top = <DAT>;
	while(<DAT>) {
		chomp;
		my ($no,$sub,$res,$nam,$da,$na2,$key,$upl) = split(/<>/);
		
		if ($in{no} == $no) {
			# 0=ロック 1=標準 2=管理用
			if ($key == 2) {
				$_ = "$no<>$sub<>$res<>$nam<>$da<>$na2<>1<>$upl<>";
			} else {
				$new = "$no<>$sub<>$res<>$nam<>$da<>$na2<>2<>$upl<>\n";
				next;
			}
		}
		push(@data,"$_\n");
	}
	
	# index更新
	unshift(@data,$new) if ($new);
	unshift(@data,$top);
	seek(DAT,0,0);
	print DAT @data;
	truncate(DAT,tell(DAT));
	close(DAT);
}

#-----------------------------------------------------------
#  個別記事メンテ
#-----------------------------------------------------------
sub article {
	my ($subject,$mode,$log) = @_;
	
	# レス記事個別削除
	if ($in{act} eq "dele" && $in{art} ne '') {
		
		if ($in{art} eq '0') {
			cgi_err("親記事の削除はできません");
		}
		
		# スレッド内より削除記事を抽出
		my (@new,$last_nam,$last_dat);
		open(DAT,"+< $cf{datadir}/log/$in{no}.cgi");
		eval "flock(DAT,2);";
		my $top = <DAT>;
		my ($num,$sub2,$res,$key) = split(/<>/, $top);
		
		while(<DAT>) {
			my ($no,$sub,$nam,$em,$com,$dat,$ho,$pw,$url,$mvw,$myid,$tim,$up1,$up2,$up3) = split(/<>/);
			if ($no == $in{art}) {
				# 画像削除
				my $n;
				foreach my $up ($up1,$up2,$up3) {
					$n++;
					my ($ex) = split(/,/, $up);
					next if (!$ex);
					if (-e "$cf{upldir}/$tim-$n$ex") {
						unlink("$cf{upldir}/$tim-$n$ex");
					}
					if (-e "$cf{upldir}/$tim-s-$n$ex") {
						unlink("$cf{upldir}/$tim-s-$n$ex");
					}
				}
				next;
			}
			push(@new,$_);
			
			# 最終投稿者名と時間を覚えておく
			$last_nam = $nam;
			$last_dat = $dat;
		}
		
		# レス個数を調整
		$res--;
		$top = "$num<>$sub2<>$res<>$key<>\n";
		
		# スレッド更新
		unshift(@new,$top);
		seek(DAT,0,0);
		print DAT @new;
		truncate(DAT,tell(DAT));
		close(DAT);
		
		# index内容差し替え
		my (@new,@sort,@top);
		open(DAT,"+< $log");
		eval "flock(DAT,2);";
		my $top = <DAT> if ($in{data_now});
		while(<DAT>) {
			chomp;
			my ($no,$sb,$re,$na,$dat,$na2,$key,$upl) = split(/<>/);
			
			if ($key == 2) {
				push(@top,"$_\n");
				next;
			}
			if ($in{no} == $no) {
				# レス個数と最終投稿者名を差替
				$na2 = $last_nam;
				$dat = $last_dat;
				$_ = "$no<>$sb<>$res<>$na<>$dat<>$na2<>$key<>$upl<>";
			}
			push(@new,"$_\n");
			
			# ソート用配列
			$dat =~ s/\D//g;
			push(@sort,$dat);
		}
		
		# 投稿順にソート
		@new = @new[sort {$sort[$b] <=> $sort[$a]} 0 .. $#sort];
		
		# index更新
		unshift(@new,@top) if (@top > 0);
		unshift(@new,$top) if ($in{data_now});
		seek(DAT,0,0);
		print DAT @new;
		truncate(DAT,tell(DAT));
		close(DAT);
	
	# レス記事個別修正フォーム
	} elsif ($in{act} eq "edit" && $in{art} ne '') {
		
		my $data;
		open(DAT,"$cf{datadir}/log/$in{no}.cgi");
		my $top = <DAT>;
		while(<DAT>) {
			my ($no,$sub,$nam,$em,$com,$dat,$ho,$pw,$url,$mvw,$myid,$tim,$up1,$up2,$up3) = split(/<>/);
			
			if ($in{art} == $no) {
				chomp;
				$data = $_;
				last;
			}
		}
		close(DAT);
		
		# スレッドタイトル
		my ($sub2) = (split(/<>/,$top))[1];
		
		# 個別修正フォーム
		edit_form($subject,$mode,$log,$data,$sub2);
	
	# レス記事個別修正実行
	} elsif ($in{act} eq "edit2" && $in{art} ne '') {
		
		my @data;
		open(DAT,"+< $cf{datadir}/log/$in{no}.cgi");
		eval "flock(DAT,2);";
		my $top = <DAT>;
		while(<DAT>) {
			chomp;
			my ($no,$sub,$nam,$em,$com,$dat,$ho,$pw,$url,$mlo,$myid,$tim,$up1,$up2,$up3) = split(/<>/);
			
			if ($in{art} == $no) {
				
				# 画像削除
				if ($in{del1}) {
					my ($ex) = split(/,/,$up1);
					unlink("$cf{upldir}/$tim-1$ex");
					unlink("$cf{upldir}/$tim-s-1$ex") if (-e "$cf{upldir}/$tim-s-1$ex");
					$up1 = '';
				}
				if ($in{del2}) {
					my ($ex) = split(/,/,$up2);
					unlink("$cf{upldir}/$tim-2$ex");
					unlink("$cf{upldir}/$tim-s-2$ex") if (-e "$cf{upldir}/$tim-s-2$ex");
					$up2 = '';
				}
				if ($in{del3}) {
					my ($ex) = split(/,/,$up3);
					unlink("$cf{upldir}/$tim-3$ex");
					unlink("$cf{upldir}/$tim-s-3$ex") if (-e "$cf{upldir}/$tim-s-3$ex");
					$up3 = '';
				}
				
				$_ = "$no<>$in{sub}<>$in{name}<>$in{email}<>$in{comment}<>$dat<>$ho<>$pw<>$in{url}<>$in{mlo}<>$myid<>$tim<>$up1<>$up2<>$up3<>";
			}
			push(@data,"$_\n");
		}
		
		# 親記事の場合
		if ($in{art} == 0) {
			my ($num,$sub2,$res,$key) = split(/<>/, $top);
			$top = "$num<>$in{sub}<>$res<>$key<>\n";
		}
		
		unshift(@data,$top);
		seek(DAT,0,0);
		print DAT @data;
		truncate(DAT,tell(DAT));
		close(DAT);
		
		# 親記事の場合indexも更新する
		if ($in{art} == 0) {
			my $idx = $in{data_now} ? "$cf{datadir}/index1.log" : "$cf{datadir}/index2.log";
			
			my @log;
			open(DAT,"+< $idx") or cgi_err("open err: $idx");
			eval "flock(DAT,2);";
			my $top = <DAT> if ($in{data_now});
			while(<DAT>) {
				chomp;
				my ($no,$sub,$res,$nam,$upd,$las,$key,$upl) = split(/<>/);
				
				if ($in{no} == $no) {
					$_ = "$no<>$in{sub}<>$res<>$nam<>$upd<>$las<>$key<>$upl<>";
				}
				push(@log,"$_\n");
			}
			unshift(@log,$top) if ($in{data_now});
			seek(DAT,0,0);
			print DAT @log;
			truncate(DAT,tell(DAT));
			close(DAT);
		}
	}
	
	open(IN,"$cf{datadir}/log/$in{no}.cgi");
	my $top = <IN>;
	my ($num,$sub,$res) = split(/<>/,$top);
	
	# スレッド内個別閲覧
	header("スレッド内個別閲覧");
	back_btn($mode);
	print <<EOM;
<div id="ttl">
	<img src="$cf{cmnurl}/db_gear.png" alt="" class="icon">
	データメンテ[$subject] &gt; 個別メンテ &gt; スレッド名「$sub」
</div>
<form action="$cf{admin_cgi}" method="post">
<input type="hidden" name="sid" value="$in{sid}">
<input type="hidden" name="$mode" value="1">
<input type="hidden" name="job" value="art">
<input type="hidden" name="no" value="$in{no}">
<ul>
<li>修正又は削除を選択して記事をチェックします。
<li>親記事の削除はできません。
</ul>
<div class="ope-btn">
処理 ：
<select name="act">
<option value="edit">修正
<option value="dele">削除
</select>
<input type="submit" value="送信する">
</div>
<table class="form-tbl" id="list">
<tr>
	<th>選択</th>
	<th>件名</th>
	<th>名前</th>
	<th>日時</th>
	<th>ホスト名</th>
</tr>
EOM

	while (<IN>) {
		my ($no,$sub,$nam,$em,$com,$dat,$hos,$pw,$url,$mvw,$myid) = split(/<>/);
		
		print qq|<tr><td><input type="radio" name="art" value="$no"></td>\n|;
		print qq|<td class="ta-l">[$no] <b class="subcol">$sub</b></td>|;
		print qq|<td><b>$nam</b>|;
		print qq|&nbsp;[ID:$myid]| if ($cf{authkey});
		print qq|</td><td>$dat</td>|;
		print qq|<td>$hos</td></tr>\n|;
	}
	close(IN);
	
	print <<EOM;
</table>
</form>
</div>
</body>
</html>
EOM
	exit;
}

#-----------------------------------------------------------
#  修正フォーム
#-----------------------------------------------------------
sub edit_form {
	my ($subject,$mode,$log,$data,$sub2) = @_;
	my ($no,$sub,$nam,$eml,$com,$dat,$ho,$pw,$url,$mlo,$myid,$tim,$up1,$up2,$up3) = split(/<>/, $data);
	$com =~ s/<br>/\n/g;
	
	# アイコン
	my $smile;
	my @smile = split(/\s+/,$cf{smile});
	foreach (0 .. $#smile) {
		$smile .= qq|<a href="javascript:face('{ico:$_}')"><img src="$cf{iconurl}/$smile[$_]" alt=""></a>|;
	}
	
	# email表示
	my $op_mlo;
	my @mlo = ('非表示','表示');
	foreach (1,0) {
		if ($mlo eq $_) {
			$op_mlo .= qq|<option value="$_" selected>$mlo[$_]\n|;
		} else {
			$op_mlo .= qq|<option value="$_">$mlo[$_]\n|;
		}
	}
	
	header("修正フォーム", "js");
	back_btn($mode);
	print <<EOM;
<div id="ttl">
	<img src="$cf{cmnurl}/log_edit.png" alt="" class="icon">
	データメンテ[現行ログ] &gt; 個別メンテ &gt; スレッド名「$sub2」 &gt; 記事「$sub」</div>
<ul>
<li>修正する箇所のみ変更して送信ボタンを押してください。
</ul>
<form action="$cf{admin_cgi}" method="post" name="bbsform">
<input type="hidden" name="sid" value="$in{sid}">
<input type="hidden" name="$mode" value="1">
<input type="hidden" name="job" value="art">
<input type="hidden" name="no" value="$in{no}">
<input type="hidden" name="art" value="$in{art}">
<input type="hidden" name="act" value="edit2">
<table class="form-tbl" id="list">
<tr>
	<th>名前</th>
	<td><input type="text" name="name" size="30" value="$nam"></td>
</tr><tr>
	<th>Eメール</th>
	<td>
		<input type="text" name="email" size="30" value="$eml">
		<select name="mlo">
		$op_mlo
		</select>
	</td>
</tr><tr>
	<th>件名</th>
	<td><input type="text" name="sub" size="40" value="$sub"></td>
</tr><tr>
	<th>URL</th>
	<td><input type="text" name="url" size="50" value="$url"></td>
EOM

	if ($cf{image_upl}) {
		print qq|</tr><tr>\n|;
		print qq|<th>画像</th><td>\n|;
		
		my ($n,$k);
		foreach my $up ($up1,$up2,$up3) {
			$n++;
			my ($ex) = split(/,/, $up);
			if ($ex) {
				$k++;
				print qq|<input type="checkbox" name="del$n" value="1">削除\n|;
				print qq|[<a href="$cf{uplurl}/$tim-$n$ex" target="_blank">画像$n</a>]<br>\n|;
			}
		}
		print "<br>" if (!$k);
		print qq|</td></td>\n|;
	}
	
	print <<EOM;
</tr><tr>
	<th>本文</th>
	<td class="smile">
		$smile<br>
		<textarea name="comment" cols="55" rows="6">$com</textarea>
	</td>
</tr>
</table>
<div class="ope-btn">
	<input type="submit" value="修正する" class="btn">
</div>
</div>
</form>
</body>
</html>
EOM
	exit;
}

#-----------------------------------------------------------
#  ファイルサイズ
#-----------------------------------------------------------
sub size_chk {
	# 現行ログ
	my $size1 = 0;
	my $file1 = 0;
	my %now;
	open(IN,"$cf{datadir}/index1.log") or cgi_err("open err: index1.log");
	my $top = <IN>;
	while (<IN>) {
		my ($num) = split(/<>/);
		my $tmp = -s "$cf{datadir}/log/$num.cgi";
		$size1 += $tmp;
		$file1++;
		
		$now{$num} = 1;
	}
	close(IN);
	
	# 過去ログ
	my $size2 = 0;
	my $file2 = 0;
	my %pst;
	open(IN,"$cf{datadir}/index2.log") or cgi_err("open err: index2.log");
	while (<IN>) {
		my ($num) = split(/<>/);
		my $tmp = -s "$cf{datadir}/log/$num.cgi";
		$size2 += $tmp;
		$file2++;
		
		$pst{$num} = 1;
	}
	close(IN);
	
	# 画像
	my $img = 0;
	opendir(DIR,"$cf{upldir}");
	while( defined($_ = readdir(DIR)) ) {
		next if (!/^[\d\-]+\.(jpg|gif|png)$/);
		
		$img += -s "$cf{upldir}/$_";
	}
	closedir(DIR);
	
	$size1 = int ($size1 / 1024 + 0.5);
	$size2 = int ($size2 / 1024 + 0.5);
	$img   = int ($img / 1024 + 0.5);
	my $all = $size1 + $size2;
	my $file = $file1 + $file2;
	
	header("ファイル容量");
	back_btn();
	print <<"EOM";
<div id="ttl">
	<img src="$cf{cmnurl}/folder_db.png" alt="" class="icon">
	ログ容量算出
</div>
<ul>
<li>以下は記録ファイルの容量（サイズ）で、小数点以下は四捨五入します。
<li>分類欄のフォームをクリックすると各管理画面に移動します。
<form action="$cf{admin_cgi}" method="post">
<input type="hidden" name="sid" value="$in{sid}">
<table class="form-tbl" id="list">
<tr>
	<th rowspan="2">分類</t>
	<th rowspan="2">ファイル数</t>
	<th colspan="2">サイズ</th>
</tr><tr>
	<th>ログ</th>
 	<th>画像</th>
</tr><tr>
	<td><input type="submit" name="data_now" value="現行ログ"></td>
	<td class="ta-c">$file1</td>
	<td>$size1 KB</td>
	<td rowspan="2">$img KB</td>
</tr><tr>
	<td><input type="submit" name="data_past" value="過去ログ"></td>
	<td class="ta-c">$file2</td>
	<td>$size2 KB</td>
</tr><tr>
	<td class="ta-c">合計</td>
	<td class="ta-c">$file</td>
	<td>$all KB</td>
	<td>$img KB</td>
</tr>
</table>
</form>
</ul>
</div>
</body>
</html>
EOM
	exit;
}

#-----------------------------------------------------------
#  会員管理
#-----------------------------------------------------------
sub auth_mgr {
	return if (!$cf{authkey});
	
	# 新規フォーム
	if ($in{job} eq "new") {
		member_form();
	
	# 新規発行
	} elsif ($in{job} eq "new2") {
		my $err;
		if (!$in{name}) { $err .= "名前が未入力です<br>\n"; }
		if ($in{myid} =~ /\W/) { $err .= "IDは英数字のみです<br>\n"; }
		if (length($in{myid}) < 4 || length($in{myid}) > 8) {
			$err .= "IDは英数字で4～8文字です<br>\n";
		}
		if ($in{mypw} =~ /\W/) { $err .= "パスワードは英数字のみです<br>\n"; }
		if (length($in{mypw}) < 4 || length($in{mypw}) > 8) {
			$err .= "パスワードは英数字で4～8文字です<br>\n";
		}
		if (!$in{rank}) { $err .= "権限が未選択です<br>\n"; }
		cgi_err($err) if ($err);
		
		# パス暗号化
		my $crypt = encrypt($in{mypw});
		
		# IDチェック
		my ($flg,@data);
		open(DAT,"+< $cf{datadir}/memdata.cgi") or cgi_err("open err: memdata.cgi");
		while(<DAT>) {
			my ($id,$pw,$rank,$nam) = split(/<>/);
			
			if ($in{myid} eq $id) { $flg++; last; }
			push(@data,$_);
		}
		
		if ($flg) {
			close(DAT);
			cgi_err("このIDは既に登録済です");
		}
		
		# 更新
		seek(DAT,0,0);
		print DAT "$in{myid}<>$crypt<>$in{rank}<>$in{name}<>\n";
		print DAT @data;
		truncate(DAT,tell(DAT));
		close(DAT);
	
	# 修正フォーム
	} elsif ($in{job} eq "edit" && $in{myid}) {
		my @log;
		open(IN,"$cf{datadir}/memdata.cgi") or cgi_err("open err: memdata.cgi");
		while (<IN>) {
			my ($id,$pw,$rank,$nam) = split(/<>/);
			
			if ($in{myid} eq $id) {
				@log = ($id,$pw,$rank,$nam);
				last;
			}
		}
		close(IN);
		
		member_form(@log);
	
	# 修正実行
	} elsif ($in{job} eq "edit2") {
		my ($err,$crypt);
		if (!$in{name}) { $err .= "名前が未入力です<br>\n"; }
		if ($in{myid} =~ /\W/) { $err .= "IDは英数字のみです<br>\n"; }
		if (length($in{myid}) < 4 || length($in{myid}) > 8) {
			$err .= "IDは英数字で4～8文字です<br>\n";
		}
		if ($in{chg}) {
			if ($in{mypw} =~ /\W/) { $err .= "パスワードは英数字のみです<br>\n"; }
			if (length($in{mypw}) < 4 || length($in{mypw}) > 8) {
				$err .= "パスワードは英数字で4～8文字です<br>\n";
			}
			
			# パス暗号化
			$crypt = encrypt($in{mypw});
		
		} elsif (!$in{chg} && $in{mypw} ne "") {
			$err .= "パスワードの強制変更はチェックボックスに選択してください<br>\n";
		}
		if (!$in{rank}) { $err .= "権限が未選択です<br>\n"; }
		cgi_err($err) if ($err);
		
		my @data;
		open(DAT,"+< $cf{datadir}/memdata.cgi") or cgi_err("open err: memdata.cgi");
		while(<DAT>) {
			my ($id,$pw,$rank,$nam) = split(/<>/);
			
			if ($in{myid} eq $id) {
				if ($crypt) { $pw = $crypt; }
				$_ = "$id<>$pw<>$in{rank}<>$in{name}<>\n";
			}
			push(@data,$_);
		}
		seek(DAT,0,0);
		print DAT @data;
		truncate(DAT,tell(DAT));
		close(DAT);
	
	# 削除
	} elsif ($in{job} eq "dele" && $in{myid}) {
		# 削除情報
		my %del;
		foreach ( $cgi->param('myid') ) {
			$del{$_}++;
		}
		
		my @data;
		open(DAT,"+< $cf{datadir}/memdata.cgi") or cgi_err("open err: memdata.cgi");
		while(<DAT>) {
			my ($id,$pw,$rank,$nam) = split(/<>/);
			next if (defined($del{$id}));
			
			push(@data,$_);
		}
		seek(DAT,0,0);
		print DAT @data;
		truncate(DAT,tell(DAT));
		close(DAT);
	}
	
	header("会員管理");
	back_btn();
	print <<"EOM";
<div id="ttl">
	<img src="$cf{cmnurl}/user.png" alt="" class="icon">
	会員管理
</div>
<form action="$cf{admin_cgi}" method="post">
<input type="hidden" name="sid" value="$in{sid}">
<input type="hidden" name="auth_mgr" value="1">
<div class="ope-btn">
処理 :
<select name="job">
<option value="new">新規
<option value="edit">修正
<option value="dele">削除
</select>
<input type="submit" value="送信する">
</div>
<table class="form-tbl" id="list">
<tr>
  <th>選択</th>
  <th>ログインID</th>
  <th>名前</th>
  <th>ランク</th>
</tr>
EOM

	open(IN,"$cf{datadir}/memdata.cgi") or cgi_err("open err: memdata.cgi");
	while (<IN>) {
		my ($id,$pw,$rank,$nam) = split(/<>/);
		
		print qq|<tr><td class="ta-c"><input type="checkbox" name="myid" value="$id"></td>|;
		print qq|<td>$id</td><td>$nam</td><td class="ta-c">$rank</td></tr>\n|;
	}
	close(IN);
	
	print <<EOM;
</table>
</form>
</div>
</body>
</html>
EOM
	exit;
}

#-----------------------------------------------------------
#  会員フォーム
#-----------------------------------------------------------
sub member_form {
	my ($id,$pw,$rank,$nam) = @_;
	my $job = $in{job} . '2';
	
	header("会員管理 &gt; 登録フォーム");
	print <<EOM;
<div id="body">
<div class="back-btn">
<form action="$cf{admin_cgi}" method="post">
<input type="hidden" name="sid" value="$in{sid}">
<input type="hidden" name="auth_mgr" value="1">
<input type="submit" value="&lt; 前画面">
</form>
</div>
<div id="ttl">
	<img src="$cf{cmnurl}/user.png" alt="" class="icon">
		会員管理 &gt; 登録フォーム
</div>
<form action="$cf{admin_cgi}" method="post">
<input type="hidden" name="sid" value="$in{sid}">
<input type="hidden" name="auth_mgr" value="1">
<input type="hidden" name="job" value="$job">
<table class="form-tbl" id="list">
<tr>
	<th>名前</th>
	<td><input type="text" name="name" size="30" value="$nam"></td>
</tr><tr>
	<th>ログインID</th>
	<td>
EOM

	if ($in{myid}) {
		print qq|<b>$in{myid}</b>|;
	} else {
		print qq|<input type="text" name="myid" size="16" value="$id">\n|;
		print qq|（英数字で4～8文字）\n|;
	}
	
	print <<EOM;
	</td>
</tr><tr>
	<th>パスワード</th>
	<td>
		<input type="password" name="mypw" size="16">
		（英数字で4～8文字）
EOM

	if ($in{myid}) {
		print qq|<br><input type="checkbox" name="chg" value="1">\n|;
		print qq|パスワードを強制変更する場合にチェック\n|;
		print qq|<input type="hidden" name="myid" value="$in{myid}">\n|;
	}
	
	print <<EOM;
	</td>
</tr><tr>
	<th>権限</th>
	<td>
EOM

	my %rank = (1 => "閲覧のみ", 2 => "閲覧&amp;書込OK");
	foreach (1,2) {
		if ($rank == $_) {
			print qq|<input type="radio" name="rank" value="$_" checked>レベル$_ ($rank{$_})<br>\n|;
		} else {
			print qq|<input type="radio" name="rank" value="$_">レベル$_ ($rank{$_})<br>\n|;
		}
	}
	
	print <<EOM;
	</td>
</tr>
</table>
<div class="ope-btn">
	<input type="submit" value="送信する" class="btn">
</div>
</div>
</form>
</body>
</html>
EOM
	exit;
}

#-----------------------------------------------------------
#  戻りボタン
#-----------------------------------------------------------
sub back_btn {
	my ($mode) = @_;
	
	print <<EOM;
<div id="body">
<div class="back-btn">
<form action="$cf{admin_cgi}" method="post">
<input type="hidden" name="sid" value="$in{sid}">
@{[ $mode ? qq|<input type="submit" name="$mode" value="&lt; 前画面">| : '' ]}
<input type="submit" value="▲メニュー">
</form>
</div>
EOM
}

#-----------------------------------------------------------
#  エラー
#-----------------------------------------------------------
sub cgi_err {
	my $err = shift;
	
	header("ERROR");
	print <<EOM;
<div id="body">
<div id="err">
<b>エラー発生</b>
<p>$err</p>
<p><input type="button" value="前画面に戻る" onclick="history.back()"></p>
</div>
</div>
</body>
</html>
EOM
	exit;
}

#-----------------------------------------------------------
#  HTMLヘッダ
#-----------------------------------------------------------
sub header {
	my ($ttl,$js) = @_;
	
	print <<EOM;
Content-type: text/html; charset=utf-8

<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<link href="$cf{cmnurl}/admin.css" rel="stylesheet">
EOM

	if ($js) {
		print qq|<script>\n|;
		print qq|function face(smile) {\n|;
		print qq|bbscom = document.bbsform.comment.value;\n|;
		print qq|document.bbsform.comment.value = bbscom + smile;\n|;
		print qq|}\n</script>\n|;
	}
	
	print <<EOM;
<title>$ttl</title>
</head>
<body>
<div id="head">:: WEB PATIO 管理画面 ::</div>
EOM
}

#-----------------------------------------------------------
#  crypt暗号
#-----------------------------------------------------------
sub encrypt {
	my $in = shift;
	
	my @wd = ('a'..'z', 'A'..'Z', '0'..'9', '.', '/');
	my $salt = $wd[int(rand(@wd))] . $wd[int(rand(@wd))];
	return crypt($in, $salt) || crypt ($in, '$1$' . $salt);
}

