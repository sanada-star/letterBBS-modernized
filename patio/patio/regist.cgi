#!/usr/local/bin/perl

#┌─────────────────────────────────
#│ WEB PATIO : regist.cgi - 2022/03/26
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

if ($in{mode} eq 'regist') { regist(); }
if ($in{mode} eq 'edit') { edit_log(); }
error("不明な処理です");

#-----------------------------------------------------------
#  記事投稿処理
#-----------------------------------------------------------
sub regist {
	# 投稿チェック
	if ($cf{postonly} && $ENV{REQUEST_METHOD} ne 'POST') {
		error("不正なリクエストです");
	}
	
	# 権限チェック
	if ($cf{authkey} && $au{rank} < 2) {
		error("投稿の権限がありません");
	}
	
	# フォーム入力チェック
	form_check();
	
	# ホスト/時間取得
	my ($host,$addr) = get_host();
	my ($date,$time) = get_time();
	
	# 汚染チェック
	$in{res} =~ s/\D//g;
	
	# 投稿キーチェック
	if ($cf{use_captcha} > 0) {
		require $cf{captcha_pl};
		if ($in{captcha} !~ /^\d{$cf{cap_len}}$/) {
			error("投稿キーが入力不備です。<br>投稿フォームに戻って再読込み後、再入力してください");
		}
		
		# 投稿キーチェック
		# -1 : キー不一致
		#  0 : 制限時間オーバー
		#  1 : キー一致
		my $chk = cap::check($in{captcha},$in{str_crypt},$cf{captcha_key},$cf{cap_time},$cf{cap_len});
		if ($chk == 0) {
			error("投稿キーが制限時間を超過しました。<br>投稿フォームに戻って再読込み後、指定の数字を再入力してください");
		} elsif ($chk == -1) {
			error("投稿キーが不正です。<br>投稿フォームに戻って再読込み後、再入力してください");
		}
	}
	
	# トリップ
	my ($moto,$name) = trip_name($in{name});
	
	# パスワード暗号化
	my $pwd = encrypt($in{pwd}) if ($in{pwd} ne "");
	
	# 初期化
	my ($maxflag,$read_no);
	
	## --- 新規投稿（新規スレッド作成）
	if ($in{res} eq "") {
		
		# indexファイル
		my ($i,$flg,@new,@tmp,@top);
		open(DAT,"+< $cf{datadir}/index1.log") or error("open err: index1.log");
		eval "flock(DAT,2);";
		my $top = <DAT>;
		
		# 連続投稿IPチェック
		my ($no,$hos,$tim) = split(/<>/, $top);
		if ($host eq $hos && $cf{wait} > $time - $tim) {
			close(DAT);
			error("連続投稿はもうしばらく時間をおいて下さい");
		}
		my $new = $no + 1;
		
		# index展開
		while(<DAT>) {
			my ($sub,$key) = (split(/<>/))[1,6];
			$i++;
			
			# スレッド名重複
			if ($sub eq $in{sub}) {
				$flg++;
				last;
			} elsif ($key == 2) {
				push(@top,$_);
				next;
			}
			
			# 規定数オーバーは@tmp代入
			if ($i >= $cf{i_max}) {
				push(@tmp,$_);
			
			# 規定数内は@new代入
			} else {
				push(@new,$_);
			}
		}
		
		# スレッド名重複はエラー
		if ($flg) {
			close(DAT);
			error("<b>「$in{sub}」</b>は既存スレッドと重複しています。<br>別のスレッド名を指定してください");
		}
		
		# ファイルアップ
		my ($upflg,%ex,%w,%h);
		if ($cf{image_upl} && ($in{upfile1} || $in{upfile2} || $in{upfile3})) {
			($ex{1},$w{1},$h{1},$ex{2},$w{2},$h{2},$ex{3},$w{3},$h{3}) = upload($time);
			
			# 画像アップのときはフラグを立てる
			if ($ex{1} || $ex{2} || $ex{3}) { $upflg = $time; }
		}
		
		# 現行index更新
		unshift(@new,"$new<>$in{sub}<>0<>$name<>$date<>$name<>1<>$upflg<>\n");
		unshift(@new,@top) if (@top > 0);
		unshift(@new,"$new<>$host<>$time<>\n");
		seek(DAT,0,0);
		print DAT @new;
		truncate(DAT,tell(DAT));
		close(DAT);
		
		# 過去index更新
		if (@tmp > 0) {
			
			$i = @tmp;
			open(DAT,"+< $cf{datadir}/index2.log") or error("open err: index2.log");
			eval "flock(DAT,2);";
			while(<DAT>) {
				$i++;
				if ($i > $cf{p_max}) {
					my ($delno) = split(/<>/);
					
					open(IN,"$cf{datadir}/log/$delno.cgi");
					my $top = <IN>;
					my $log = <IN>;
					close(IN);
					
					my ($no,$sub,$nam,$eml,$com,$dat,$ho,$pw,$url,$mlo,$myid,$tim,$upl1,$upl2,$upl3) = split(/<>/, $log);
					
					# 画像は削除
					my $n;
					foreach my $upl ($upl1, $upl2, $upl3) {
						my ($ex,$w,$h) = split(/,/,$upl);
						$n++;
						if ($ex) { unlink("$cf{upldir}/$tim-$n$ex"); }
					}
					
					unlink("$cf{datadir}/log/$delno.cgi");
					unlink("$cf{datadir}/log/$delno.dat");
					next;
				}
				push(@tmp,$_);
			}
			seek(DAT,0,0);
			print DAT @tmp;
			truncate(DAT,tell(DAT));
			close(DAT);
		}
		
		# スレッド更新
		open(OUT,"+> $cf{datadir}/log/$new.cgi") or error("write err: $new.cgi");
		print OUT "$new<>$in{sub}<>0<>1<>\n";
		print OUT "0<>$in{sub}<>$name<>$in{email}<>$in{comment}<>$date<>$host<>$pwd<>$in{url}<>$in{mlo}<>$au{id}<>$time<>$ex{1},$w{1},$h{1}<>$ex{2},$w{2},$h{2}<>$ex{3},$w{3},$h{3}<>\n";
		close(OUT);
		
		# 参照ファイル生成
		open(NO,"+> $cf{datadir}/log/$new.dat") or error("write err: $new.dat");
		print NO "0:";
		close(NO);
		
		# パーミッション変更
		chmod(0666, "$cf{datadir}/log/$new.cgi");
		chmod(0666, "$cf{datadir}/log/$new.dat");
		
		# メール通知
		sendmail($name,$date,$host) if ($cf{mailing});
		
		# 記事番を覚えておく
		$read_no = $new;
	
	# --- 返信投稿
	} else {
		
		# 連続投稿チェック
		open(IN,"$cf{datadir}/index1.log") or error("open err: index1.log");
		my $top = <IN>;
		close(IN);
		
		my ($no,$hos2,$tim2) = split(/<>/,$top);
		if ($host eq $hos2 && $cf{wait} > $time - $tim2) {
			error("連続投稿はもうしばらく時間をおいて下さい");
		}
		
		# スレッド読み込み
		open(DAT,"+< $cf{datadir}/log/$in{res}.cgi") or error("open err: $in{res}.cgi");
		eval "flock(DAT,2);";
		my $top = <DAT>;
		my @log = <DAT>;
		
		# 先頭ファイル分解
		my ($no,$sub,$res,$key) = split(/<>/, $top);
		
		# ロックチェック
		if ($key eq '0' || $key eq '2') {
			close(DAT);
			error("このスレッドはロック中のため返信できません");
		}
		
		# 末尾ファイルを分解、重複チェック
		my ($no2,$sb2,$na2,$em2,$co2) = split(/<>/,$log[$#log]);
		if ($name eq $na2 && $in{comment} eq $co2) { error("重複投稿は禁止です"); }
		
		# 採番
		my $newno = $no2 + 1;
		
		# 記事数チェック
		if ($cf{m_max} < $res+1) { error("最大記事数をオーバーしたため投稿できません"); }
		elsif ($cf{m_max} == $res+1) { $maxflag = 1; }
		else { $maxflag = 0; }
		
		# ファイルアップ
		my ($upflg,%ex,%w,%h);
		if ($cf{image_upl} && ($in{upfile1} || $in{upfile2} || $in{upfile3})) {
			($ex{1},$w{1},$h{1},$ex{2},$w{2},$h{2},$ex{3},$w{3},$h{3}) = &upload($time);
			
			# 画像アップのときはフラグを立てる
			if ($ex{1} || $ex{2} || $ex{3}) { $upflg = $time; }
		}
		
		# スレッド更新
		$res++;
		unshift(@log,"$no<>$sub<>$res<>1<>\n");
		push(@log,"$newno<>$in{sub}<>$name<>$in{email}<>$in{comment}<>$date<>$host<>$pwd<>$in{url}<>$in{mlo}<>$au{id}<>$time<>$ex{1},$w{1},$h{1}<>$ex{2},$w{2},$h{2}<>$ex{3},$w{3},$h{3}<>\n");

		seek(DAT,0,0);
		print DAT @log;
		truncate(DAT,tell(DAT));
		close(DAT);
		
		## --- 規定記事数オーバのとき
		if ($maxflag) {
			
			# 過去ログindex読み込み
			open(BAK,"+< $cf{datadir}/index2.log") or error("open err: index2.log");
			eval "flock(BAK, 2);";
			my @log = <BAK>;
			
			# 現行ログindexから該当スレッド抜き出し
			my @new;
			open(DAT,"+< $cf{datadir}/index1.log") or error("open err: index1.log");
			eval "flock(DAT,2);";
			my $top = <DAT>;
			while(<DAT>) {
				chomp;
				my ($no,$sub,$re,$nam,$d,$na2,$key,$upl) = split(/<>/);
				
				if ($in{res} == $no) {
					$re++;
					unshift(@log,"$no<>$sub<>$re<>$nam<>$date<>$na2<>1<>$upl<>\n");
					next;
				}
				push(@new,"$_\n");
			}
			
			# 現行ログindex更新
			unshift(@new,$top);
			seek(DAT,0,0);
			print DAT @new;
			truncate(DAT,tell(DAT));
			close(DAT);
			
			# 過去ログindex更新
			seek(BAK,0,0);
			print BAK @log;
			truncate(BAK,tell(BAK));
			close(BAK);
		
		# --- ソートあり
		} elsif ($in{sort} == 1) {
			
			# indexファイル更新
			my ($flg,$new,@new,@top);
			open(DAT,"+< $cf{datadir}/index1.log") or error("open err: index1.log");
			eval "flock(DAT,2);";
			my $top = <DAT>;
			while(<DAT>) {
				chomp;
				my ($no,$sub,$re,$nam,$da,$na2,$key,$upl) = split(/<>/);
				
				if ($key == 2) {
					push(@top,"$_\n");
					next;
				}
				if ($in{res} == $no) {
					$flg = 1;
					$new = "$in{res}<>$sub<>$res<>$nam<>$date<>$name<>1<>$upl<>\n";
					next;
				}
				push(@new,"$_\n");
			}
			
			if (!$flg) { error("該当のスレッドがindexファイルに見当たりません"); }
			
			my ($no2,$host2,$time2) = split(/<>/,$top);
			unshift(@new,$new);
			unshift(@new,@top) if (@top > 0);
			unshift(@new,"$no2<>$host<>$time<>\n");
			seek(DAT,0,0);
			print DAT @new;
			truncate(DAT,tell(DAT));
			close(DAT);
		
		# --- ソートなし
		} else {
			
			# indexファイル更新
			my ($flg,@new);
			open(DAT,"+< $cf{datadir}/index1.log") or error("open err: index1.log");
			eval "flock(DAT,2);";
			my $top = <DAT>;
			while(<DAT>) {
				chomp;
				my ($no,$sub,$re,$nam,$da,$na2,$key,$upl) = split(/<>/);
				if ($in{res} == $no) {
					$flg = 1;
					$_ = "$in{res}<>$sub<>$res<>$nam<>$date<>$name<>1<>$upl<>";
				}
				push(@new,"$_\n");
			}
			
			if (!$flg) { error("該当のスレッドがindexファイルに見当たりません"); }
			
			my ($no2,$host2,$time2) = split(/<>/,$top);
			unshift(@new,"$no2<>$host<>$time<>\n");
			seek(DAT,0,0);
			print DAT @new;
			truncate(DAT,tell(DAT));
			close(DAT);
		}
		
		# メール送信
		sendmail($name,$date,$host) if ($cf{mailing} == 2);
		
		# 記事番を覚えておく
		$read_no = $in{res};
	}
	
	# クッキー格納
	set_cookie($in{name},$in{email},$in{url},$in{mlo});
	
	# 完了メッセージ
	my $msg = "ご投稿ありがとうございました。<br>\n";
	if ($maxflag) {
		$msg .= qq|ただし１スレッド当りの最大記事数を超えたため、<br>\n|;
		$msg .= qq|このスレッドは<a href="$cf{bbs_cgi}?mode=past">過去ログ</a>へ移動しました。\n|;
	}
	message($msg,$read_no);
}

#-----------------------------------------------------------
#  記事編集
#-----------------------------------------------------------
sub edit_log {
	# 投稿チェック
	if ($cf{postonly} && $ENV{REQUEST_METHOD} ne 'POST') {
		error("不正なリクエストです");
	}
	
	# チェック
	error("パスワードが未入力です") if ($in{pwd} eq '');
	
	# 汚染チェック
	$in{art} =~ s/\D//g;
	$in{no}  =~ s/\D//g;
	
	# --- 削除
	if ($in{job} eq "dele") {
		
		# スレッドより削除記事抽出
		my ($flg,$last_nam,$last_dat,@new);
		open(DAT,"+< $cf{datadir}/log/$in{art}.cgi") or error("open err: $in{art}.cgi");
		eval "flock(DAT,2);";
		my $top = <DAT>;
		while(<DAT>) {
			my ($no,$sub,$nam,$eml,$com,$dat,$ho,$pw,$url,$mlo,$myid,$tim,$upl1,$upl2,$upl3) = split(/<>/);
			
			if ($in{no} == $no) {
				$flg = 1;
				
				# パス照合
				if (decrypt($in{pwd},$pw) != 1) {
					$flg = -1;
					last;
				}
				
				# スレッドヘッダのレス個数を調整
				my ($num,$sub2,$res,$key) = split(/<>/,$top);
				$res--;
				$top = "$num<>$sub2<>$res<>$key<>\n";
				
				# 画像削除
				my $n;
				foreach my $upl ($upl1,$upl2,$upl3) {
					$n++;
					my ($ex) = (split(/,/,$upl))[0];
					if (-e "$cf{upldir}/$tim-$n$ex") {
						unlink("$cf{upldir}/$tim-$n$ex");
					}
				}
				# スキップ
				next;
			}
			push(@new,$_);
			
			# 最終記事の投稿者と時間を覚えておく
			$last_nam = $nam;
			$last_dat = $dat;
		}
		
		# 不認証
		error("認証できません") if ($flg <= 0);
		
		# スレッド更新
		unshift(@new,$top);
		seek(DAT,0,0);
		print DAT @new;
		truncate(DAT,tell(DAT));
		close(DAT);
		
		# index展開
		@new = ();
		my (@sort,@top);
		open(DAT,"+< $cf{datadir}/index1.log") or error("open err: index1.log");
		eval "flock(DAT,2);";
		my $top = <DAT>;
		while(<DAT>) {
			chomp;
			my ($no,$sub,$res,$nam,$dat,$na2,$key,$upl) = split(/<>/);
			
			if ($key == 2) {
				push(@top,"$_\n");
				next;
			}
			if ($in{art} == $no) {
				# indexのレス個数を調整し、最終投稿者と時間を置換
				$res--;
				$na2 = $last_nam;
				$dat = $last_dat;
				$_ = "$no<>$sub<>$res<>$nam<>$dat<>$na2<>$key<>$upl<>";
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
		unshift(@new,$top);
		seek(DAT,0,0);
		print DAT @new;
		truncate(DAT,tell(DAT));
		close(DAT);
		
		# 完了メッセージ
		message("記事は正常に削除されました。");
	
	# --- ロック
	} elsif ($in{job} eq "lock") {
		
		if ($in{no} != 0) { error("ロック処理は親記事のみです"); }
		
		# スレッドより削除記事抽出
		open(DAT,"+< $cf{datadir}/log/$in{art}.cgi") or error("open err: $in{art}.cgi");
		eval "flock(DAT,2);";
		my $top = <DAT>;
		my @log = <DAT>;
		
		my ($no,$sub,$res,$key) = split(/<>/,$top);
		my $pw = (split(/<>/,$log[0]))[7];
		
		# 照合
		if (&decrypt($in{pwd},$pw) != 1) {
			close(DAT);
			error("パスワードが認証できません");
		}
		
		unshift(@log,"$no<>$sub<>$res<>0<>\n");
		seek(DAT,0,0);
		print DAT @log;
		truncate(DAT,tell(DAT));
		close(DAT);
		
		# index展開
		my ($flg,@log);
		open(DAT,"+< $cf{datadir}/index1.log") or error("open err: index1.log");
		eval "flock(DAT,2);";
		my $top = <DAT>;
		while(<DAT>) {
			chomp;
			my ($no,$sub,$res,$nam,$dat,$na2,$key,$upl) = split(/<>/);
			
			if ($in{art} == $no) {
				$flg++;
				$_ = "$no<>$sub<>$res<>$nam<>$dat<>$na2<>0<>$upl<>";
			}
			push(@log,"$_\n");
		}
		
		if (!$flg) {
			close(DAT);
			error("該当記事が見当たりません");
		}
		
		unshift(@log,$top);
		seek(DAT,0,0);
		print DAT @log;
		truncate(DAT,tell(DAT));
		close(DAT);
		
		# 完了メッセージ
		message("スレッドをロックしました。");
	
	# --- 編集
	} else {
		
		# 入力チェック
		form_check() if ($in{job} eq 'edit2');
		
		my ($flg,@log,@new);
		open(DAT,"+< $cf{datadir}/log/$in{art}.cgi") or error("open err: $in{art}.cgi");
		eval "flock(DAT,2);";
		my $top = <DAT>;
		while(<DAT>) {
			chomp;
			my ($no,$sub,$nam,$eml,$com,$dat,$hos,$pw,$url,$mlo,$myid,$tim,$upl1,$upl2,$upl3) = split(/<>/);
			
			if ($in{no} == $no) {
				$flg = 1;
				
				# パスワード未設定
				if ($pw eq '') { $flg = -1; last; }
				
				# パスワード照合
				if (!decrypt($in{pwd},$pw)) { $flg = -2; last; }
				
				if ($in{job} eq 'edit') {
					@log = ($sub,$nam,$eml,$com,$url,$mlo,$tim,$upl1,$upl2,$upl3);
				}
				
				# トリップ
				my ($moto,$name);
				unless ($in{name} =~ /◆/ && $in{name} eq $nam) {
					($moto,$name) = trip_name($in{name});
				} else {
					$name = $in{name};
				}
				
				# 添付拡張子
				my $ex1 = (split(/,/,$upl1))[0];
				my $ex2 = (split(/,/,$upl2))[0];
				my $ex3 = (split(/,/,$upl3))[0];
				
				# 添付削除
				if ($in{del1}) {
					$upl1 = '';
					unlink("$cf{upldir}/$tim-1$ex1");
				}
				if ($in{del2}) {
					$upl2 = '';
					unlink("$cf{upldir}/$tim-2$ex2");
				}
				if ($in{del3}) {
					$upl3 = '';
					unlink("$cf{upldir}/$tim-3$ex3");
				}
				
				# 親記事＆添付アップ
				if ($cf{image_upl} && ($in{upfile1} || $in{upfile2} || $in{upfile3})) {
					
					if ($tim eq "") { error("この記事はアップロードできません"); }
					
					my ($e1,$w1,$h1,$e2,$w2,$h2,$e3,$w3,$h3) = upload($tim);
					if ($e1) {
						$upl1 = "$e1,$w1,$h1";
						if ($ex1 && $ex1 ne $e1) {
							unlink("$cf{upldir}/$tim-1$ex1");
						}
					}
					if ($e2) {
						$upl2 = "$e2,$w2,$h2";
						if ($ex2 && $ex2 ne $e2) {
								unlink("$cf{upldir}/$tim-2$ex2");
						}
					}
					if ($e3) {
						$upl3 = "$e3,$w3,$h3";
						if ($ex3 && $ex3 ne $e3) {
							unlink("$cf{upldir}/$tim-3$ex3");
						}
					}
				}
				$_ = "$no<>$in{sub}<>$name<>$in{email}<>$in{comment}<>$dat<>$hos<>$pw<>$in{url}<>$in{mlo}<>$myid<>$tim<>$upl1<>$upl2<>$upl3<>";
			}
			push(@new,"$_\n");
		}
		
		error("認証できません") if ($flg <= 0);
		
		# フォーム表示のとき
		if ($in{job} eq 'edit') { edit_form(@log); }
		
		# ヘッダ
		my ($num,$sub2,$res2,$key) = split(/<>/,$top);
		
		# 親記事の場合は題名を更新
		if (!$in{no}) { $sub2 = $in{sub}; }
		
		# 更新
		unshift(@new,"$num<>$sub2<>$res2<>$key<>\n");
		seek(DAT,0,0);
		print DAT @new;
		truncate(DAT,tell(DAT));
		close(DAT);
		
		# 最終投稿者名
		my ($last_nam) = (split(/<>/,$new[$#new]))[2];
		
		# index展開
		my @data;
		open(DAT,"+< $cf{datadir}/index1.log") or error("open err: index1.log");
		eval "flock(DAT,2);";
		my $top = <DAT> if (!$in{bakfile});
		while(<DAT>) {
			chomp;
			my ($no,$sub,$res,$nam,$da,$na2,$key2,$upl) = split(/<>/);
			
			if ($in{art} == $no) {
				
				# 親記事修正のとき
				if (!$in{no}) {
					
					# 親ログ
					my ($tim,$upl1,$upl2,$upl3) = (split(/<>/,$new[1]))[11..14];
					my ($ex1) = split(/,/,$upl1);
					my ($ex2) = split(/,/,$upl2);
					my ($ex3) = split(/,/,$upl3);
					if ($ex1 || $ex2 || $ex3) { $upl = $tim; } else { $upl = ''; }
					
					my ($moto,$name);
					unless ($in{name} =~ /◆/ && $in{name} eq $nam) {
						($moto,$name) = trip_name($in{name});
					} else {
						$name = $in{name};
					}
					if ($res2 == 0) { $na2 = $name; }
					$_ = "$no<>$in{sub}<>$res<>$name<>$da<>$na2<>$key<>$upl<>";
				
				# レス記事修正のとき
				} else {
					$_ = "$no<>$sub<>$res<>$nam<>$da<>$last_nam<>$key<>$upl<>";
				}
			}
			push(@data,"$_\n");
		}
		
		# index更新
		unshift(@data,$top) if (!$in{bakfile});
		seek(DAT,0,0);
		print DAT @data;
		truncate(DAT,tell(DAT));
		close(DAT);
		
		# 完了
		message("記事を修正しました",$in{art});
	}
}

#-----------------------------------------------------------
#  メール送信
#-----------------------------------------------------------
sub sendmail {
	my ($name,$date,$host) = @_;
	
	# メールタイトル定義
	require './lib/jacode.pl';
	my $msub = mime_unstructured_header("BBS: $in{sub}");
	
	# コメント内の改行復元
	my $com = $in{comment};
	$com =~ s/<br>/\n/g;
	$com =~ s/&lt;/>/g;
	$com =~ s/&gt;/</g;
	$com =~ s/&quot;/"/g;
	$com =~ s/&amp;/&/g;
	$com =~ s/&#39;/'/g;
	
	# メール本文を定義
	my $mbody = <<EOM;
掲示板に投稿がありました。

投稿日：$date
ホスト：$host

件名  ：$in{sub}
お名前：$name
E-mail：$in{email}
URL   ：$in{url}

$com
EOM

	# JISコード変換
	my $body;
	for my $tmp ( split(/\n/,$mbody) ) {
		jcode::convert(\$tmp,'jis','utf8');
		$body .= "$tmp\n";
	}
	
	# メールアドレスがない場合は管理者メールに置き換え
	my $email = $in{email} ? $in{email} : $cf{mailto};
	
	# sendmailコマンド
	my $scmd = "$cf{sendmail} -t -i";
	if ($cf{sendm_f}) { $scmd .= " -f $email"; }
	
	# 送信
	open(MAIL,"| $scmd") or error("送信失敗");
	print MAIL "To: $cf{mailto}\n";
	print MAIL "From: $email\n";
	print MAIL "Subject: $msub\n";
	print MAIL "MIME-Version: 1.0\n";
	print MAIL "Content-type: text/plain; charset=ISO-2022-JP\n";
	print MAIL "Content-Transfer-Encoding: 7bit\n";
	print MAIL "X-Mailer: $cf{version}\n\n";
	print MAIL "$body\n";
	close(MAIL);
}

#-----------------------------------------------------------
#  トリップ機能
#-----------------------------------------------------------
sub trip_name {
	my $name = shift;
	$name =~ s/◆/◇/g;
	
	if ($in{name} =~ /#/) {
		my ($handle,$trip) = split(/#/,$name,2);
		
		my $enc = crypt($trip,$cf{trip_key}) || crypt ($trip,'$1$' . $cf{trip_key});
		$enc =~ s/^..//;
		
		return ($name,"$handle◆$enc");
	} else {
		return ($name,$name);
	}
}

#-----------------------------------------------------------
#  禁止ワードチェック
#-----------------------------------------------------------
sub no_wd {
	my $flg;
	foreach ( split(/,/,$cf{no_wd}) ) {
		if (index("$in{name} $in{sub} $in{comment}", $_) >= 0) {
			$flg = 1;
			last;
		}
	}
	if ($flg) { error("禁止ワードが含まれています"); }
}

#-----------------------------------------------------------
#  日本語チェック
#-----------------------------------------------------------
sub jp_wd {
	if ($in{comment} !~ /(?:[\xC0-\xDF][\x80-\xBF]|[\xE0-\xEF][\x80-\xBF]{2}|[\xF0-\xF7][\x80-\xBF]{3})/x) {
		error("メッセージに日本語が含まれていません");
	}
}

#-----------------------------------------------------------
#  URL個数チェック
#-----------------------------------------------------------
sub urlnum {
	my $com = $in{comment};
	my ($num) = ($com =~ s|(https?://)|$1|ig);
	if ($num > $cf{urlnum}) {
		error("コメント中のURLアドレスは最大$cf{urlnum}個までです");
	}
}

#-----------------------------------------------------------
#  フォーム入力チェック
#-----------------------------------------------------------
sub form_check {
	# 改行カット
	$in{sub}  =~ s/<br>//g;
	$in{name} =~ s/<br>//g;
	$in{pwd}  =~ s/<br>//g;
	$in{captcha} =~ s/<br>//g;
	$in{comment} =~ s/(<br>)+$//g;
	
	# チェック
	if ($cf{no_wd}) { no_wd(); }
	if ($cf{jp_wd}) { jp_wd(); }
	if ($cf{urlnum} > 0) { urlnum(); }
	
	# 未入力の場合
	$in{sub} ||= '無題';
	if ($in{url} eq 'http://') { $in{url} = ''; }
	
	# 投稿内容チェック
	my $err;
	if ($in{name} eq "") { $err .= "名前は記入必須です<br>"; }
	if ($in{email} ne '' && $in{email} !~ /^[\w\.\-]+\@[\w\.\-]+\.[a-zA-Z]{2,6}$/) {
		$err .= "E-mailの入力内容が不正です<br>";
	}
	if ($in{url} ne '' && $in{url} !~ /^https?:\/\/[\w-.!~*'();\/?:\@&=+\$,%#]+$/) {
		$err .= "URL情報が不正です<br>";
	}
	if ($in{comment} eq "") { $err .= "コメントの内容がありません<br>"; }
	elsif (count_str($in{comment}) > $cf{max_msg}) {
		$err .= "コメントは$cf{max_msg}文字以内で記述してください<br>";
	}
	error($err) if ($err);
}

#-----------------------------------------------------------
#  アクセス制限
#-----------------------------------------------------------
sub get_host {
	# IP/ホスト取得
	my $host = $ENV{REMOTE_HOST};
	my $addr = $ENV{REMOTE_ADDR};
	if ($cf{gethostbyaddr} && ($host eq "" || $host eq $addr)) {
		$host = gethostbyaddr(pack("C4", split(/\./, $addr)), 2);
	}
	
	# IPチェック
	my $flg;
	foreach ( split(/\s+/,$cf{deny_addr}) ) {
		s/\./\\\./g;
		s/\*/\.\*/g;
		
		if ($addr =~ /^$_/i) { $flg = 1; last; }
	}
	if ($flg) {
		error("アクセスを許可されていません");
	
	# ホストチェック
	} elsif ($host) {
		
		foreach ( split(/\s+/,$cf{deny_host}) ) {
			s/\./\\\./g;
			s/\*/\.\*/g;
			
			if ($host =~ /$_$/i) { $flg = 1; last; }
		}
		if ($flg) {
			error("アクセスを許可されていません");
		}
	}
	if ($host eq "") { $host = $addr; }
	return ($host,$addr);
}

#-----------------------------------------------------------
#  時間取得
#-----------------------------------------------------------
sub get_time {
	# 時間取得
	my $time = time;
	my ($min,$hour,$mday,$mon,$year,$wday) = (localtime($time))[1..6];
	my @wk = ('Sun','Mon','Tue','Wed','Thu','Fri','Sat');
	my $date = sprintf("%04d/%02d/%02d(%s) %02d:%02d",
				$year+1900,$mon+1,$mday,$wk[$wday],$hour,$min);
	
	return ($date,$time);
}

#-----------------------------------------------------------
#  完了画面
#-----------------------------------------------------------
sub message {
	my ($msg,$read) = @_;
	
	open(IN,"$cf{tmpldir}/mesg.html") or error("open err: mesg.html");
	my $tmpl = join('',<IN>);
	close(IN);
	
	$tmpl =~ s/!bbs_cgi!/$cf{bbs_cgi}/g;
	$tmpl =~ s/!message!/$msg/g;
	$tmpl =~ s/!read!/$read/g;
	$tmpl =~ s|!bbs_css!|$cf{cmnurl}/style.css|g;
	$tmpl =~ s/!bbs_title!/$cf{bbs_title}/g;
	
	print "Content-type: text/html; charset=utf-8\n\n";
	print $tmpl;
	exit;
}

#-----------------------------------------------------------
#  画像アップロード
#-----------------------------------------------------------
sub upload {
	my $no = shift;
	
	# サムネイル機能
	require './lib/thumb.pl' if ($cf{thumbnail});
	
	my @ret;
	foreach my $i (1 .. 3) {
		
		# mimeタイプ
		my $mime = $cgi->param_mime("upfile$i");
		
		# ファイル名
		my $fname = $cgi->param_filename("upfile$i");
		if ($fname =~ /(\.jpe?g|\.png|\.gif)$/i) {
			my $ex = $1;
			$ex =~ tr/A-Z/a-z/;
			if ($ex eq '.jpeg') { $ex = '.jpg'; }
			
			# 整合性チェック
			unless (($mime =~ /^image\/gif$/i and $ex eq '.gif') or ($mime =~ /^image\/p?jpe?g$/i and $ex eq '.jpg') or ($mime =~ /^image\/(x-)?png$/i and $ex eq '.png')) {
				push(@ret,('','',''));
				next;
			}
			
			# アップファイル定義
			my $imgfile = "$cf{upldir}/$no-$i$ex";
			
			# 書き込み
			open(OUT,"+> $imgfile") or error("画像アップ失敗");
			binmode(OUT);
			print OUT $in{"upfile$i"};
			close(OUT);
			
			# パーミッション変更
			chmod(0666,$imgfile);
			
			# 画像サイズ取得
			my ($w,$h);
			if ($ex eq ".jpg") { ($w,$h) = j_size($imgfile); }
			elsif ($ex eq ".gif") { ($w,$h) = g_size($imgfile); }
			elsif ($ex eq ".png") { ($w,$h) = p_size($imgfile); }
			
			# サムネイル作成
			if ($cf{thumbnail}) {
				($w,$h) = resize($w,$h);
				my $thumb = "$cf{upldir}/$no-s-$i$ex";
				make_thumb($imgfile,$thumb,$w,$h);
			}
			
			push(@ret,($ex,$w,$h));
		} else {
			push(@ret,('','',''));
		}
	}
	# 返り値
	return @ret;
}

#-----------------------------------------------------------
#  JPEGサイズ認識
#-----------------------------------------------------------
sub j_size {
	my $jpg = shift;
	
	my ($h,$w,$t);
	open(IMG,"$jpg");
	binmode(IMG);
	read(IMG,$t,2);
	while (1) {
		read(IMG, $t, 4);
		my ($m,$c,$l) = unpack("a a n", $t);
		
		if ($m ne "\xFF") {
			$w = $h = 0;
			last;
		} elsif ((ord($c) >= 0xC0) && (ord($c) <= 0xC3)) {
			read(IMG, $t, 5);
			($h,$w) = unpack("xnn",$t);
			last;
		} else {
			read(IMG,$t,($l - 2));
		}
	}
	close(IMG);
	
	return ($w,$h);
}

#-----------------------------------------------------------
#  GIFサイズ認識
#-----------------------------------------------------------
sub g_size {
	my $gif = shift;
	
	my $data;
	open(IMG,"$gif");
	binmode(IMG);
	sysread(IMG, $data, 10);
	close(IMG);
	
	if ($data =~ /^GIF/) { $data = substr($data, -4); }
	my $w = unpack("v", substr($data,0,2));
	my $h = unpack("v", substr($data,2,2));
	
	return ($w,$h);
}

#-----------------------------------------------------------
#  PNGサイズ認識
#-----------------------------------------------------------
sub p_size {
	my $png = shift;
	
	my $data;
	open(IMG,"$png");
	binmode(IMG);
	read(IMG,$data,24);
	close(IMG);
	
	my $w = unpack("N", substr($data,16,20));
	my $h = unpack("N", substr($data,20,24));
	
	return ($w,$h);
}

#-----------------------------------------------------------
#  crypt暗号
#-----------------------------------------------------------
sub encrypt {
	my $in = shift;
	
	my @wd = ('a'..'z', 'A'..'Z', 0..9, '.', '/');
	srand;
	my $salt = $wd[int(rand(@wd))] . $wd[int(rand(@wd))];
	crypt($in,$salt) || crypt ($in,'$1$' . $salt);
}

#-----------------------------------------------------------
#  crypt照合
#-----------------------------------------------------------
sub decrypt {
	my ($in,$dec) = @_;
	
	my $salt = $dec =~ /^\$1\$(.*)\$/ ? $1 : substr($dec, 0, 2);
	if (crypt($in,$salt) eq $dec || crypt($in,'$1$' . $salt) eq $dec) {
		return 1;
	} else {
		return 0;
	}
}

#-----------------------------------------------------------
#  編集フォーム
#-----------------------------------------------------------
sub edit_form {
	my ($sub,$nam,$eml,$com,$url,$mlo,$tim,$up1,$up2,$up3) = @_;
	$url ||= 'http://';
	my %up = (1 => $up1, 2 => $up2, 3 => $up3);
	$com =~ s/<br>/\n/g;
	
	# テンプレート読み込み
	open(IN,"$cf{tmpldir}/edit.html") or error("open err: edit.html");
	my $tmpl = join('',<IN>);
	close(IN);
	
	# 画像フォーム
	if (!$cf{image_upl}) {
		$tmpl =~ s|<!-- upfile -->.+?<!-- /upfile -->||s;
	} else {
		$tmpl =~ s/<!-- edit:([1-3]) -->/upf_edit($1,$tim,$up{$1})/ge;
	}
	
	# アイコン
	my $smile;
	my @smile = split(/\s+/, $cf{smile});
	for (0 .. $#smile) {
		$smile .= qq|<a href="javascript:face('{ico:$_}')"><img src="$cf{cmnurl}/$smile[$_]" class="icon"></a>|;
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
	
	# 文字置換
	$tmpl =~ s|!bbs_css!|$cf{cmnurl}/style.css|g;
	$tmpl =~ s/!bbs_title!/$cf{bbs_title}/g;
	$tmpl =~ s/!sub!/$sub/g;
	$tmpl =~ s/!name!/$nam/g;
	$tmpl =~ s/!email!/$eml/g;
	$tmpl =~ s/!url!/$url/g;
	$tmpl =~ s/!art!/$in{art}/g;
	$tmpl =~ s/!no!/$in{no}/g;
	$tmpl =~ s/!comment!/$com/g;
	$tmpl =~ s/!pwd!/$in{pwd}/g;
	$tmpl =~ s/!([a-z]+_cgi)!/$cf{$1}/g;
	$tmpl =~ s|!ico:(\w+\.\w+)!|<img src="$cf{cmnurl}/$1" alt="">|g;
	$tmpl =~ s/!smile!/$smile/g;
	$tmpl =~ s/<!-- op_mlo -->/$op_mlo/g;
	
	# 画面表示
	print "Content-type: text/html; charset=utf-8\n\n";
	print $tmpl;
	exit;
}

#-----------------------------------------------------------
#  アップファイル編集ボタン
#-----------------------------------------------------------
sub upf_edit {
	my ($num,$tim,$upl) = @_;
	my ($ex) = split(/,/,$upl);
	
	# 拡張子がない場合
	return if (!$ex);
	
	my $btn = <<EOM;
<input type="checkbox" name="del$num" value="1">削除
[<a href="$cf{uplurl}/$tim-$num$ex" target="_blank">添付$num</a>]
EOM
	
	return $btn;
}

#-----------------------------------------------------------
#  認証モード
#-----------------------------------------------------------
sub authent {
	# セッションモジュール取り込み
	require $cf{session_pl};
	
	# セッション管理
	session("$cf{datadir}/ses",$cf{bbs_cgi});
}

#-----------------------------------------------------------
#  クッキー発行
#-----------------------------------------------------------
sub set_cookie {
	my @data = @_;
	
	my ($sec,$min,$hour,$mday,$mon,$year,$wday,undef,undef) = gmtime(time + 60*24*60*60);
	my @mon  = qw|Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec|;
	my @week = qw|Sun Mon Tue Wed Thu Fri Sat|;
	
	# 時刻フォーマット
	my $gmt = sprintf("%s, %02d-%s-%04d %02d:%02d:%02d GMT",
				$week[$wday],$mday,$mon[$mon],$year+1900,$hour,$min,$sec);
	
	# URLエンコード
	my $cook;
	foreach (@data) {
		s/(\W)/sprintf("%%%02X", unpack("C", $1))/eg;
		$cook .= "$_<>";
	}
	
	print "Set-Cookie: $cf{cookie_id}=$cook; expires=$gmt\n";
}

#-----------------------------------------------------------
#  mimeエンコード
#  [quote] http://www.din.or.jp/~ohzaki/perl.htm#JP_Base64
#-----------------------------------------------------------
sub mime_unstructured_header {
  my $oldheader = shift;
  jcode::convert(\$oldheader,'euc','utf8');
  my ($header,@words,@wordstmp,$i);
  my $crlf = $oldheader =~ /\n$/;
  $oldheader =~ s/\s+$//;
  @wordstmp = split /\s+/, $oldheader;
  for ($i = 0; $i < $#wordstmp; $i++) {
    if ($wordstmp[$i] !~ /^[\x21-\x7E]+$/ and
	$wordstmp[$i + 1] !~ /^[\x21-\x7E]+$/) {
      $wordstmp[$i + 1] = "$wordstmp[$i] $wordstmp[$i + 1]";
    } else {
      push(@words, $wordstmp[$i]);
    }
  }
  push(@words, $wordstmp[-1]);
  foreach my $word (@words) {
    if ($word =~ /^[\x21-\x7E]+$/) {
      $header =~ /(?:.*\n)*(.*)/;
      if (length($1) + length($word) > 76) {
	$header .= "\n $word";
      } else {
	$header .= $word;
      }
    } else {
      $header = add_encoded_word($word, $header);
    }
    $header =~ /(?:.*\n)*(.*)/;
    if (length($1) == 76) {
      $header .= "\n ";
    } else {
      $header .= ' ';
    }
  }
  $header =~ s/\n? $//mg;
  $crlf ? "$header\n" : $header;
}
sub add_encoded_word {
  my ($str, $line) = @_;
  my $result;
  my $ascii = '[\x00-\x7F]';
  my $twoBytes = '[\x8E\xA1-\xFE][\xA1-\xFE]';
  my $threeBytes = '\x8F[\xA1-\xFE][\xA1-\xFE]';
  while (length($str)) {
    my $target = $str;
    $str = '';
    if (length($line) + 22 +
	($target =~ /^(?:$twoBytes|$threeBytes)/o) * 8 > 76) {
      $line =~ s/[ \t\n\r]*$/\n/;
      $result .= $line;
      $line = ' ';
    }
    while (1) {
      my $encoded = '=?ISO-2022-JP?B?' .
      b64encode(jcode::jis($target,'euc','z')) . '?=';
      if (length($encoded) + length($line) > 76) {
	$target =~ s/($threeBytes|$twoBytes|$ascii)$//o;
	$str = $1 . $str;
      } else {
	$line .= $encoded;
	last;
      }
    }
  }
  $result . $line;
}
# [quote] http://www.tohoho-web.com/perl/encode.htm
sub b64encode {
    my $buf = shift;
    my ($mode,$tmp,$ret);
    my $b64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                . "abcdefghijklmnopqrstuvwxyz"
                . "0123456789+/";

    $mode = length($buf) % 3;
    if ($mode == 1) { $buf .= "\0\0"; }
    if ($mode == 2) { $buf .= "\0"; }
    $buf =~ s/(...)/{
        $tmp = unpack("B*", $1);
        $tmp =~ s|(......)|substr($b64, ord(pack("B*", "00$1")), 1)|eg;
        $ret .= $tmp;
    }/eg;
    if ($mode == 1) { $ret =~ s/..$/==/; }
    if ($mode == 2) { $ret =~ s/.$/=/; }
    
    return $ret;
}

#-----------------------------------------------------------
#  文字数カウント for UTF-8
#-----------------------------------------------------------
sub count_str {
	my ($str) = @_;
	
	# UTF-8定義
	my $byte1 = '[\x00-\x7f]';
	my $byte2 = '[\xC0-\xDF][\x80-\xBF]';
	my $byte3 = '[\xE0-\xEF][\x80-\xBF]{2}';
	my $byte4 = '[\xF0-\xF7][\x80-\xBF]{3}';
	
	my $i = 0;
	while ($str =~ /($byte1|$byte2|$byte3|$byte4)/gx) {
		$i++;
	}
	return $i;
}

