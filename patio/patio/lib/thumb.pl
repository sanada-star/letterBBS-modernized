#┌─────────────────────────────────
#│ 画像縮小モジュール : thumb.pl - 2011/09/26
#│ Copyright (c) KentWeb
#│ http://www.kent-web.com/
#└─────────────────────────────────

# モジュール取り込み
use strict;
use Image::Magick;

#-----------------------------------------------------------
#  サムネイル作成
#-----------------------------------------------------------
sub make_thumb {
	my ($image,$thumb,$w,$h) = @_;
	
	# アップ画像読み込み
	my $img = Image::Magick->new();
	$img->Read($image);
	
	# サムネイル作成
	$img->Resize(width => $w, height => $h);
	$img->Write($thumb);
	
	# 画像パーミッション変更
	chmod(0666,$thumb);
}



1;

