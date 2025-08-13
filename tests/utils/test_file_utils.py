from utu.utils import FileUtils

web_url = "http://www.pthxx.com/b_audio/pthxx_com_mp3/01_langdu/02.mp3"
local_url = "/Users/frankshi/Downloads/02.mp3"


def test_ext():
    assert FileUtils.get_file_ext(web_url) == ".mp3"
    assert FileUtils.is_web_url(web_url)

    assert FileUtils.get_file_ext(local_url) == ".mp3"
    assert not FileUtils.is_web_url(local_url)


def test_md5():
    md5_web = FileUtils.get_file_md5(web_url)
    md5_local = FileUtils.get_file_md5(local_url)
    print(md5_web, md5_local)
    assert md5_web == md5_local
