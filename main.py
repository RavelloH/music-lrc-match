# coding=UTF-8
# Author:RavelloH
# licence:MIT
# 有bug请到github.com/ravelloh/music-lrc-match反馈
import os
import time
from urllib.request import Request, urlopen
from urllib import parse
import json

## 确定目录
origin_file = input(print('输入歌曲所在文件夹:\n')) #/storage/4A21-0000/music
count_lrc = 0
count_file = 0
errorlist = []
lrcnamelist = []
for file_name in os.listdir(origin_file):
    count_file += 1
print('共检索到%s个文件' %(count_file))
target_file = input(print('输入IRC存放的文件夹:\n'))
os.makedirs(target_file,exist_ok=True)
if target_file[-1] == '/':
    target_file=target_file[:-1]
for lrc_name in os.listdir(target_file):
    if 'lrc' in lrc_name:
        print(lrc_name[:-4])
        lrcnamelist.append(lrc_name[:-4])
        count_lrc += 1
print(lrcnamelist)
print('共检索到%s个歌词文件\n即将开始匹配...' %(count_lrc))

##写入lrc
load = 0
abso_music = 0
for musicfile in os.listdir(origin_file):
    # 删去后缀名
    while '.' in musicfile:
        musicfile = musicfile[:-1]
    if 'lrc' not in musicfile:
        if musicfile in lrcnamelist:
            print('[下载任务%s已被取消:对应的lrc已存在]' %(musicfile))
        else:    
            load += 1
            print('%s - %s/%s' %(musicfile,load,count_file))
            # 搜索模块
            try:
                search_result=urlopen('http://cloud-music.pl-fe.cn/search?keywords='+parse.quote(musicfile)).read()
            except:
                print('    搜索请求失败')
                pass
            # 等待防止被禁
            time.sleep(0.5)
            # 搜索信息解析
            try:    
                text = json.loads(search_result)
                songid = text['result']['songs'][0]['id']
                songname = text['result']['songs'][0]['name']
                artist = ''
                for i in range(len(text['result']['songs'][0]['artists'])):
                    artist = artist + '-' + str(text['result']['songs'][0]['artists'][i]['name'])
                artist = artist[1:]
                print('    %s | %s _ id:%s' %(artist,songname,songid))
            except:
                print('    解析失败')
            # 歌词写入模块
            try:
                lrc_origin = urlopen('https://music.163.com/api/song/media?id='+str(songid)).read()
                lrc_json=json.loads(lrc_origin,strict=False)
                if 'nolyric' in lrc_json:
                    f = open(target_file+'/'+musicfile+'.lrc','w+')
                    f.write('[00:00.00] 纯音乐，请欣赏') # 防止纯音乐返回空歌词
                    f.close
                else:
                    abso_music += 1
                    f = open(target_file+'/'+musicfile+'.lrc','w+')
                    f.write(lrc_json['lyric'])
                    f.close
            except:
                print('    [下载失败，自动替换为纯音乐]')
                errorlist.append(str(musicfile))
                f = open(target_file+'/'+musicfile+'.lrc','w+')
                f.write('[00:00.00] 纯音乐，请欣赏') # 下载失败先替换
                f.close
print('下载完毕，共提交%s个下载任务，下载%s个lrc，其中有%s个纯音乐已自动替换，%s个需要注意的下载任务' %(count_file,load,abso_music,len(errorlist)))
