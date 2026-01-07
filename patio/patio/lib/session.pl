#┌─────────────────────────────────
#│ WEB PATIO : session.pl - 2011/08/15
#│ Copyright (c) KentWeb
#│ http://www.kent-web.com/
#└─────────────────────────────────

# モジュール取り込み
use strict;
use CGI::Session;

#-----------------------------------------------------------
#  セッション作成
#-----------------------------------------------------------
sub make_ses {
	my ($uid,$upw,$file,$dir,$autime) = @_;
	
	# 初期化
	my %au;
	
	# 会員ファイルオープン
	my $flg;
	open(IN,"$file") or &error("open err: $file");
	while (<IN>) {
		my ($id,$pw,$rank,$nam) = split(/<>/);
		
		if ($uid eq $id) {
			$flg = 1;
			
			# 照合
			if (&decrypt($upw,$pw) == 1) {
				$flg = 2;
				#$data = "$rank\t$nam";
				$au{name} = $nam;
				$au{rank} = $rank;
			}
			last;
		}
	}
	close(IN);
	
	# 照合不可
	&error("認証できません") if ($flg != 2);
	
	# 新規セッション発行
	my $ses = new CGI::Session(undef,undef,{Directory => $dir}) or die CGI::Session->errstr;
	
	# データ格納
	$ses->param(-name => 'id',   -value => $uid);
	$ses->param(-name => 'name', -value => $au{name});
	$ses->param(-name => 'rank', -value => $au{rank});
	
	# 有効時間
	my $jobtime = $autime * 60;
	$ses->expire($jobtime);
	
	# セッションID
	$au{sid} = $ses->id();
	
	# ログインID
	$au{id} = $uid;
	
	# 返り値
	return %au;
}

#-----------------------------------------------------------
#  ログアウト
#-----------------------------------------------------------
sub del_ses {
	my $dir = shift;
	
	# セッション認識
	my $ses = CGI::Session->load(undef,undef,{Directory => $dir}) or die;
	$ses->delete();
}

#-----------------------------------------------------------
#  セッション確認
#-----------------------------------------------------------
sub session {
	my ($dir,$bbs) = @_;
	
	# セッション認識
	my $ses = CGI::Session->load(undef,undef,{Directory => $dir}) or die;
	
	# セッションなし
	if ($ses->is_empty) {
		&enter_form;
	}
	
	# 期限切れ
	if ($ses->is_expired) {
		my $msg = qq|タイムアウトです。再度ログインしてください。\n|;
		$msg .= qq|<p>[<a href="$bbs?mode=enter">ログインする</a>]</p>\n|;
		&error($msg);
   	}
	
	# データ回収
	my %au;
	$au{id}   = $ses->param('id');
	$au{name} = $ses->param('name');
	$au{rank} = $ses->param('rank');
	
	# 返り値
	return %au;
}



1;

