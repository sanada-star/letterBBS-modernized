# モジュール宣言/変数初期化
use strict;
my %cf;
#┌─────────────────────────────────
#│ WEB PATIO : init.cgi - 2022/03/26
#│ copyright (c) kentweb, 1997-2022
#│ https://www.kent-web.com/
#└─────────────────────────────────
$cf{version} = 'WebPatio v6.1';
#┌─────────────────────────────────
#│ [注意事項]
#│ 1. このスクリプトはフリーソフトです。このスクリプトを使用した
#│    いかなる損害に対して作者は一切の責任を負いません。
#│ 2. 設置に関する質問はサポート掲示板にお願いいたします。
#│    直接メールによる質問は一切お受けいたしておりません。
#└─────────────────────────────────

#===========================================================
# ■ 基本設定
#===========================================================

# アクセス制限をする
# 0=no 1=yes
$cf{authkey} = 0;

# ログイン有効期間（分）
$cf{authtime} = 60;

# 画像アップを許可する
# 0=no 1=yes
$cf{image_upl} = 0;

# サムネイル画像を作成する（要：Image::Magick）
# → 縮小画像を自動生成し、画像記事の表示速度を軽くする機能
# 0=no 1=yes
$cf{thumbnail} = 0;

# トリップ機能（ハンドル偽造防止）のための変換キー
# →　英数字で2文字
$cf{trip_key} = 'ab';

# タイトル
$cf{bbs_title} = "私書箱";

# 掲示板本体CGI【URLパス】
$cf{bbs_cgi} = './patio.cgi';

# 掲示板投稿CGI【URLパス】
$cf{regist_cgi} = './regist.cgi';

# 掲示板閲覧CGI【URLパス】
$cf{read_cgi} = './read.cgi';

# 掲示板管理CGI【URLパス】
$cf{admin_cgi} = './admin.cgi';

# 認証管理プログラム【サーバパス】
$cf{session_pl} = './lib/session.pl';

# 共通ファイルフォルダ【URLパス】
$cf{cmnurl} = './cmn';

# データディレクトリ【サーバパス】
$cf{datadir} = './data';

# テンプレートディレクトリ【サーバパス】
$cf{tmpldir} = './tmpl';

# 文字コード自動変換を行う (0=no 1=yes)
# → ブラウザは本体の文字コードで投稿するはずなので通常は「0」でOK
$cf{chg_code} = 0;

# 戻り先【URLパス】
$cf{homepage} = '../index.html';

# 画像ディレクトリ（画像アップを許可するとき）
# → 順に、サーバパス、URLパス
$cf{upldir} = './upl';
$cf{uplurl} = './upl';

# 画像ファイルの最大表示の大きさ（単位：ピクセル）
# → これを超える画像は縮小表示します
$cf{max_img_w} = 200;	# 横幅
$cf{max_img_h} = 150;	# 縦幅

# 現行ログ最大スレッド数
# → これを超えると過去ログへ移動
$cf{i_max} = 1000;

# 過去ログ最大スレッド数
# → これを超えると自動削除
$cf{p_max} = 3000;

# 1スレッド当りの「表示」記事数
$cf{pg_max} = 10;

# 1スレッド当りの「最大」記事数
# → これを超えると過去ログへ廻ります
# → 残り90%でアラームを表示
$cf{m_max} = 1000;

# 現行ログ初期メニューのスレッド表示数
$cf{pgmax_now} = 50;

# 過去ログ初期メニューのスレッド表示数
$cf{pgmax_past} = 100;

# コメント入力最大文字数
$cf{max_msg} = 50000;

# URLの自動リンク (0=no 1=yes)
$cf{autolink} = 1;

# スマイルアイコン
# → スペースで区切る
$cf{smile} = 'sml_cool.gif sml_sml.gif sml_yawn.gif sml_q.gif sml_big.gif sml_shm.gif sml_wink.gif sml_cry.gif sml_roll.gif sml_bonk.gif';

# メール送信
# 0 : しない
# 1 : スレッド生成時
# 2 : 投稿記事すべて
$cf{mailing} = 0;

# メール送信先
$cf{mailto} = 'xxx@xxx.xx';

# sendmailパス
$cf{sendmail} = '/usr/lib/sendmail';

# sendmailの -fコマンドが必要な場合
# 0=no 1=yes
$cf{sendm_f} = 0;

# アクセス制限（半角スペースで区切る、アスタリスク可）
#  → 拒否ホスト名を記述（後方一致）【例】*.anonymizer.com
$cf{deny_host} = '';
#  → 拒否IPアドレスを記述（前方一致）【例】210.12.345.*
$cf{deny_addr} = '';

# 記事の更新は method=POST 限定 (0=no 1=yes)
# （セキュリティ対策）
$cf{postonly} = 1;

# 連続投稿の禁止時間（秒）
$cf{wait} = 0;

# 禁止ワード
# → 投稿時禁止するワードをコンマで区切る
$cf{no_wd} = '';

# 日本語チェック（投稿時日本語が含まれていなければ拒否する）
# 0=No  1=Yes
$cf{jp_wd} = 0;

# URL個数チェック
# → 投稿コメント中に含まれるURL個数の最大値
$cf{urlnum} = 2;

# １回当りの最大投稿サイズ (bytes)
# → 例 : 102400 = 100KB
$cf{maxdata} = 5120000;

# クッキーID名（特に変更しなくてよい）
$cf{cookie_id} = "web_patio";

# ホスト取得方法
# 0 : gethostbyaddr関数を使わない
# 1 : gethostbyaddr関数を使う
$cf{gethostbyaddr} = 0;

# 管理パスワードの最大間違い制限
# → この回数以上パスワードを間違うとロックします
$cf{max_failpass} = 10;

# 管理パスワードのロック期間：自動解除を日数で指定
# → この値を 0 にすると自動解除しません。
$cf{lock_days} = 14;

# -------------------------------------------------------------- #
# [ 以下は「画像認証機能」機能を使用する場合の設定 ]
#
# 画像認証機能の使用
# 0 : しない
# 1 : ライブラリ版（pngren.pl）
# 2 : モジュール版（GD::SecurityImage + Image::Magick）→ Image::Magick必須
$cf{use_captcha} = 0;

# 認証用画像生成ファイル【URLパス】
$cf{captcha_cgi} = './captcha.cgi';

# 画像認証プログラム【サーバパス】
$cf{captcha_pl} = './lib/captcha.pl';
$cf{captsec_pl} = './lib/captsec.pl';
$cf{pngren_pl}  = './lib/pngren.pl';

# 画像認証機能用暗号化キー（暗号化/復号化をするためのキー）
# → 適当に変更してください。
$cf{captcha_key} = 'captchapatio';

# 投稿キー許容時間（分単位）
# → 投稿フォーム表示後、送信ボタンが押されるまでの可能時間。
$cf{cap_time} = 30;

# 投稿キーの文字数
# ライブラリ版 : 4～8文字で設定
# モジュール版 : 6～8文字で設定
$cf{cap_len} = 6;

# 画像/フォント格納ディレクトリ【サーバパス】
$cf{bin_dir} = './lib/bin';

# [ライブラリ版] 画像ファイル [ ファイル名のみ ]
$cf{si_png} = "stamp.png";

# [モジュール版] 画像フォント [ ファイル名のみ ]
$cf{font_ttl} = "tempest.ttf";

#===========================================================
# ■ 設定完了
#===========================================================

# フォルダーアイコン
$cf{fld_icon} = {
	0 => 'fld_lock.gif',
	1 => 'fld_nor.gif',
	2 => 'fld_ex.gif',
	alerm => 'fld_bell.gif',
	image => 'fld_img.gif',
	};

# 設定内容を返す
sub set_init { return %cf; }

#-----------------------------------------------------------
#  フォームデコード
#-----------------------------------------------------------
sub parse_form {
	my $cgi = shift;
	
	my %in;
	foreach ( $cgi->param() ) {
		my $val = $cgi->param($_);
		
		if (!/^upfile\d$/) {
			# 無効化
			$val =~ s/&/&amp;/g;
			$val =~ s/</&lt;/g;
			$val =~ s/>/&gt;/g;
			$val =~ s/"/&quot;/g;
			$val =~ s/'/&#39;/g;
			
			# 改行変換
			$val =~ s/\r\n/<br>/g;
			$val =~ s/\n/<br>/g;
			$val =~ s/\r/<br>/g;
		}
		$in{$_} = $val;
	}
	return %in;
}

#-----------------------------------------------------------
#  エラー画面
#-----------------------------------------------------------
sub error {
	my $err = shift;
	
	open(IN,"$cf{tmpldir}/error.html") or die;
	my $tmpl = join('',<IN>);
	close(IN);
	
	$tmpl =~ s/!error!/$err/g;
	$tmpl =~ s/!bbs_title!/$cf{bbs_title}/g;
	$tmpl =~ s|!bbs_css!|$cf{cmnurl}/style.css|g;
	
	print "Content-type: text/html; charset=utf-8\n\n";
	print $tmpl;
	exit;
}

#-----------------------------------------------------------
#  画像リサイズ
#-----------------------------------------------------------
sub resize {
	my ($w,$h) = @_;
	
	# 画像表示縮小
	if ($w > $cf{max_img_w} || $h > $cf{max_img_h}) {
		my $w2 = $cf{max_img_w} / $w;
		my $h2 = $cf{max_img_h} / $h;
		my $key;
		if ($w2 < $h2) { $key = $w2; } else { $key = $h2; }
		$w = int ($w * $key) || 1;
		$h = int ($h * $key) || 1;
	}
	
	return ($w,$h);
}


1;

