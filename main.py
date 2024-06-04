# -*- coding: utf-8 -*-
## music-lrc-match
### github.com/ravelloh/music-lrc-match
#### MICENCE: MIT
##### By: RavelloH
##### 更新于2023/09/03

logo='''
                      _             _                                 _       _     
                     (_)           | |                               | |     | |    
  _ __ ___  _   _ ___ _  ___ ______| |_ __ ___ ______ _ __ ___   __ _| |_ ___| |__  
 | '_ ` _ \| | | / __| |/ __|______| | '__/ __|______| '_ ` _ \ / _` | __/ __| '_ \ 
 | | | | | | |_| \__ \ | (__       | | | | (__       | | | | | | (_| | || (__| | | |
 |_| |_| |_|\__,_|___/_|\___|      |_|_|  \___|      |_| |_| |_|\__,_|\__\___|_| |_|
                                                                                        
'''
version='Version: 2023/09/03 by RavelloH'

import os
import time
from urllib.request import Request, urlopen
from urllib import parse
import json
import difflib
import re
try:
    import tqdm
    tqdm = True
except:
    tqdm = False

## 初始化
search_api_list=['http://cloud-music.pl-fe.cn', ## 第三方API，访问快，稳定性未知
                 'https://music.api.ravelloh.top',## 个人自建API，访问慢，稳定性好
                 'https://music.api.coderace.top',
                 'https://neteaseapi.imgugu.ink',
                 ]
search_method='/search?limit=3&type=1&keywords='
translate_method='/lyric?id='
lrc_api='https://music.163.com/api/song/media?id='
errorlist = []
lrcnamelist = []
abso_music_list = []
warning_list = []
success_list = []
api1error,api2error =1,1
load = 0
downloads = 0
abso_music = 0
music_type = ['mp3','wma','wav','ape','flac','ogg','aac']
music_list = []
lrc_list = []
log_template='''[setting]>>

[absolute music]>>

[wrong file]>>

[update history]>>

[raw log]>>

'''

## 输出预设
success = '\033[0;32m[+]\033[0m'
error = '\033[0;31m[x]\033[0m' 
warning = '\033[0;33m[!]\033[0m'
done = '\033[0;36m[>]\033[0m'
separator = '\n================================\n'

## 屏幕宽度预设 
try:
    width = os.get_terminal_size().columns
except:
    width = 50
## 相似度检查
def similar(s1, s2):
    return round((difflib.SequenceMatcher(None, s1, s2).quick_ratio())*100,1)

## 依赖检查
def check():
    if tqdm==False:
        print(warning+'tqdm库引用失败，进度条将不可用。使用命令行执行pip install tqdm以启用\n')
        
    print(done+'正在检查api连接，请稍候')
    global listnum
    listnum = 0
    checksearchapi()
    checklrcapi()
    return

def checksearchapi():
    global api1error
    global listnum
    global search_api
    search_api=search_api_list[listnum]
    if listnum >= len(search_api_list)-1:
        print(error+'搜索API组全部异常，可回车继续下一轮API组重试或在下方输入相同格式的替代API:')
        option = input('>')
        if option != '':
            search_api = option
            print(done+'API地址已切换为'+option+'，即将继续重试')
        else:
            print(done+'API地址未改变，即将继续重试')
        api1error = 1
        listnum = 0
        checksearchapi()
        return                
    if api1error >=4:
        print(error+'搜索API异常，当前使用的API地址为'+search_api+'，可回车更换下一API，或输入retry重试:')
        option = input('>')
        if option == 'retry':
            print(done+'再次尝试当前API')
        else:
            listnum += 1
            print(done+'搜索API已切换 - '+search_api_list[listnum])
        api1error = 1
        checksearchapi()
        return
        
    try:
        t = time.perf_counter()
        urlopen(search_api+search_method+'neko').read() 
        print(f'{success}搜索API连接正常，延迟:{round((time.perf_counter() - t)*1000,2)}毫秒')
    except:
        print(warning+'搜索API异常,即将重试，重试次数:'+str(api1error))
        api1error += 1
        checksearchapi()
        return
        

def checklrcapi():
    global api2error  
    global lrc_api
    if api2error >=4:
        print(error+'歌词API异常，当前使用的API地址为'+lrc_api+'，可回车继续重试或在下方输入相同格式的替代API:')
        option = input('>')
        if option != '':
            lrc_api = option
            print(done+'API地址已切换为'+option+'，即将继续重试')
        else:
            print(done+'API地址未改变，即将继续重试')
        api2error = 1
        checklrcapi()
        return
        
    try:
        t = time.perf_counter()
        urlopen(lrc_api+'1828376623').read() 
        print(f'{success}歌词API连接正常，延迟:{round((time.perf_counter() - t)*1000,2)}毫秒')
    except:
        print(warning+'歌词API异常,即将重试，重试次数:'+str(api2error))
        api2error += 1
        checklrcapi()
        return
        
## 日志路径设置
def setlog():
    global log_file
    print('输入日志文件(musicinfo.log)存放的目录(输入skip以跳过，直接换行以使用程序当前目录):\n----(日志用于保存运行进度及记录运行情况，下次运行时可自动导入运行设置)')
    log_file=input('>')
    if log_file == 'skip':
        print(done+'日志检查已跳过')
        return
    elif log_file == '':
        log_file = os.getcwd()
        print(done+'使用当前工作目录:'+log_file)
        
    if log_file[-1] != '/':
        log_file += '/'
    
    if os.path.isdir(log_file) == False:
        print(warning+'此目录不存在，是否创建？(y/n)')
        option=input('>')
        if option == 'y':
            try:
                os.makedirs(log_file)
                print(success+'已创建新目录')
            except:
                print(error+'目录创建失败:无权限。将重试：')
                setlog()
                return
        else:
            print(error+'目录打开失败:目录不存在。将重试：')
            setlog()
            return
            
    if os.path.isfile(log_file+'musicinfo.log') == False:
        print(warning+'未在此目录中发现musicinfo.log，是否创建? (y/n)')
        option2 = input('>')
        if option2 == 'y':
            try:
                open(log_file+'musicinfo.log','x') 
                print(success+'已创建新文件')
            except:
                print(error+'文件创建失败:无权限')
                setlog()
                return
        else:
            print(error+'未发现文件存储。将重试：')
            setlog()
            return
    log_file += 'musicinfo.log'
    print(done+'已发现log文件:'+log_file)


## 日志导入
def importlog():
    global log_setting
    global log_abso_music
    global log_wrong_music
    global log_history
    global log_raw
    log_setting = []
    log_abso_music = []
    log_wrong_music = []
    log_history = []
    log_raw = []
    if log_file == 'skip':
        print(done+'日志导入已跳过')
        return
    else:
        try:
            with open(log_file,'r',encoding='utf-8') as read_file:
                log_content = read_file.readlines()
                if log_content == []:
                    initlog()
                    print(done+'log为空，已初始化')
                    importlog()
                    return
                ## 去除后缀
                for i in range(len(log_content)):
                    log_content[i] = log_content[i].replace('\n','')
                num = 0
                ## 遍历寻找关键锚点
                for i in log_content:
                    if i == '[setting]>>':
                        num1 = num
                    if i == '[absolute music]>>':
                        num2 = num
                    if i == '[wrong file]>>':
                        num3 = num
                    if i == '[update history]>>':
                        num4 = num
                    if i == '[raw log]>>':
                        num5 = num
                    num += 1 
                ## 分区分类
                for i in range(num1+1,num2):
                    log_setting.append(log_content[i])
                for i in range(num2+1,num3):
                    log_abso_music.append(log_content[i])
                for i in range(num3+1,num4):
                    log_wrong_music.append(log_content[i])
                for i in range(num4+1,num5):
                    log_history.append(log_content[i])
                for i in range(num5+1,len(log_content)):
                    log_raw.append(log_content[i])
                if log_setting == ['']:                    
                    print(done+'log未记录设置内容，将手动配置：')
                else:
                    print(success+'成功从log中导入了过往%s次记录中的%s个纯音乐和%s个错误音乐' %(str(len(log_history)-1),str(len(log_abso_music)-1),str(len(log_wrong_music)-1)))
                return
        except:
            print(warning+'日志解析失败...将初始化')
            initlog()
            print(done+'已初始化，将重新解析')
            importlog()
            return
                        
## 日志初始化
def initlog():
    ## 覆写
    with open(log_file,'w+',encoding='utf-8') as write_file:
        write_file.write(log_template)
    return
    
def setup():
    global origin_file
    global target_file
    global music_list
    global lrc_list
    music_list = []
    lrc_list = []
    if log_setting != [''] and log_file != 'skip':
        origin_file = log_setting[0]
        print(done+'已从log中导入了待处理文件夹:'+origin_file)
    else:
        origin_file = input('输入存放待处理歌曲的文件夹:\n>')
    try: 
        for file_name in os.listdir(origin_file):
            if file_name[file_name.rfind('.')+1:].lower() in music_type:
                music_list.append(file_name)
    except:
        print(error+'无法打开路径:\'%s\',请确认路径正确\n' %(origin_file))
        setup()
        return
         
    if music_list == []:
        print(error+'未找到音频文件,支持的音频文件有:'+str(music_type)+'\n')
        setup()
        return
    else:
        print(success+'载入%s个音频文件' %(len(music_list)))
        
    if log_setting != [''] and log_file != 'skip':
        target_file = log_setting[1]
        print(done+'已从log中导入了lrc保存文件夹:'+origin_file)
    else:
        target_file = input('输入存放lrc保存目录的文件夹:(不输入则使用歌曲目录保存)\n>')
    if target_file == '':
        target_file = origin_file
    if os.path.isdir(target_file) == False:
        print(warning+'此目录不存在，是否创建？(y/n)')
        option=input('>')
        if option == 'y':
            try:
                os.makedirs(target_file)
                print(success+'已创建新目录')
            except:
                print(error+'目录创建失败:无权限。将重试：')
                setup()
                return
        else:
            print(error+'目录打开失败:目录不存在。将重试：')
            setup()
            return
    try:
        for file_name in os.listdir(target_file):
            if '.lrc' in file_name:
                lrc_list.append(file_name)
        print(success+'已在此目录找到%s个lrc文件' %(len(lrc_list)))
        
    except:
        print(error+'无法打开路径:\'%s\',请确认路径正确\n' %(origin_file))
        setup()
        return
    
## 检查lrc覆盖
def checkfile():
    global done_list
    global todo_list
    global todo_files
    todo_files = []
    cache_music_list = music_list.copy()
    cache_lrc_list = lrc_list.copy()
    cache_abso_list = log_abso_music.copy()
    checked_cache_abso_list = []
    ## 去后缀
    for i in range(len(cache_music_list)):
        cache_music_list[i] = os.path.splitext(cache_music_list[i])[0]
    for i in range(len(cache_lrc_list)):
        cache_lrc_list[i] = os.path.splitext(cache_lrc_list[i])[0]
    ## 取交集
    cache_done_list = list(set(cache_lrc_list).intersection(set(cache_music_list)))
    ## 验证日志中记录的时效性
    for i in cache_abso_list:
        if i in cache_music_list:
            checked_cache_abso_list.append(i) 
    ## 取并集
    done_list = list(set(cache_done_list).union(checked_cache_abso_list))
    print(done+'检查目录中发现了'+str(len(cache_done_list))+'个有匹配lrc文件的歌曲，'+str(len(checked_cache_abso_list))+'个日志中记录的纯音乐，将在运行时跳过')
    ## 确定目标列表
    todo_list = list(set(cache_music_list).difference(set(done_list)))
    ## 定位目标文件
    for i in music_list:
        if os.path.splitext(i)[0] in todo_list:
            todo_files.append(i)
    print(success+'已定位%s个需要处理的文件' %(len(todo_files)))
    if todo_files == []:
        print(warning+'未发现需处理文件，主进程跳过')
        return
    setting()
    return
    
def setting():
    global optionlang
    if log_setting != [''] and log_file != 'skip':
        print(done+'已从log中导入了语言偏好:')
        optionlang = log_setting[2]
    else:
        print('歌词语言设置:下载原文或尽可能翻译？(输入 原文 或 翻译 进行选择)')
        optionlang = input('>')
    if optionlang == '原文':
        print(success+'已选择原文')
        main()
        return        
    elif optionlang == '翻译':
        print(success+'已选择翻译')
        main()
        return        
    else:
        print(warning+'输入无效，请输入 原文 或 翻译 进行选择')
        setting()
        return
        
def search(inner):
    global search_result
    global search_error
    search_result = ''
    if search_error >= 3:
        return
    try:
        search_result=urlopen(search_api_list[listnum]+search_method+parse.quote(inner)).read()
    except:
        time.sleep(0.3)
        search_error += 1
        search(file_name)
        return
        
def search_parse():
    global songid
    try:
        text = json.loads(search_result)
        t = text['result']
        t = text['result']['songs']
        t = text['result']['songs'][0]
        songid = text['result']['songs'][0]['id']
        songname = text['result']['songs'][0]['name']
        artist = ''
        for i in range(len(text['result']['songs'][0]['artists'])):
            artist = artist + ' ' + str(text['result']['songs'][0]['artists'][i]['name'])
        artist = artist[1:]
        cachename = artist+' - '+songname
        standard_cachename = re.sub(u"\\(.*?\\)|\\（.*?）|\\[.*?]", "", cachename)
        standard_file_name = re.sub(u"\\(.*?\\)|\\（.*?）|\\[.*?]", "", file_name)
        
        ## 尝试第二搜索结果
        try:
            t = text['result']
            t = text['result']['songs']
            t = text['result']['songs'][0]
            songid2 = text['result']['songs'][1]['id']
            songname2 = text['result']['songs'][1]['name'] 
            artist2 = ''
            for k in range(len(text['result']['songs'][1]['artists'])):
                artist2 = artist2 + ' ' + str(text['result']['songs'][1]['artists'][k]['name'])
            artist2 = artist2[1:]
            cachename2 = artist2+' - '+songname2
            standard_cachename2 = re.sub(u"\\(.*?\\)|\\（.*?）|\\[.*?]", "", cachename2)
            standard_file_name2 = re.sub(u"\\(.*?\\)|\\（.*?）|\\[.*?]", "", file_name)
            
            ## 决策
            if similar(standard_file_name2,standard_cachename2) > similar(standard_file_name,standard_cachename):
                    songid = songid2
                    songname = songname2
                    artist = artist2
                    cachename=cachename2
                    standard_cachename = standard_cachename2
        except:
           pass
        
        ## 判定相似度
        if similar(standard_file_name,standard_cachename) > 75.0:
            print(success+'搜索-'+str(similar(standard_file_name,standard_cachename))+'%'+' %s <=> %s' %(standard_file_name,standard_cachename))
        else:
            print(warning+'搜索-'+str(similar(standard_file_name,standard_cachename))+'%'+' %s <=> %s' %(standard_file_name,standard_cachename))
            print(warning+'歌曲信息匹配度过低，已跳过')
            songid = '000000'
            return
    except:
        print(error+'解析失败: '+file_name)

def lrc():
    global lrc_result
    global lrc_error
    lrc_result = ''
    if lrc_error >= 3:
        return
    try:
        lrc_result=urlopen(lrc_api+str(songid)).read()
    except:
        time.sleep(0.3)
        lrc_error += 1
        lrc()
        return
        
def trans_lrc():
    global lrc_result
    global lrc_error
    lrc_result = ''
    if lrc_error >= 3:
        return
    try:
        lrc_result=urlopen(search_api_list[listnum]+translate_method+str(songid)).read()
    except:
        time.sleep(0.3)
        lrc_error += 1
        trans_lrc()
        return

def getlrc():
    global lrc_error
    lrc_error = 0
    lrc()
    if lrc_result == '':
        errorlist.append(music_file)
        print(error+'lrc获取失败: '+file_name)
        return
    else:
        lrc_make()
    
    
    
def getlrc_translate():
    global lrc_error
    lrc_error = 0
    trans_lrc()
    if lrc_result == '':
        errorlist.append(music_file)
        print(error+'lrc获取失败: '+file_name)
        return
    else:
        trans_lrc_make()
        
def lrc_make():
    try:
        lrc_json=json.loads(lrc_result,strict=False)
    except:
        errorlist.append(music_file)
        print(error+'lrc解析失败: '+music_file)
        return
    try:
        if 'nolyric' in lrc_json or '"nolyric":true' in lrc_json:
            abso_music_list.append(music_file)
            print(done+'检测到纯音乐: '+file_name)
        else:
            with open(target_file+'/'+file_name+'.lrc','w+',encoding='utf-8') as f:
                f.write(lrc_json['lyric'])  
            print(success+'LRC写入成功: '+file_name)
            success_list.append(music_file)
    except:   	
        errorlist.append(music_file)
        os.remove(target_file+'/'+file_name+'.lrc')
        print(error+'lrc写入失败: '+music_file)
        return
                
    
def trans_lrc_make():
    try:
        lrc_json=json.loads(lrc_result,strict=False)
    except:
        errorlist.append(music_file)
        print(error+'lrc解析失败: '+music_file)
        return
    try:
        if '纯音乐，' in str(lrc_json): 
            abso_music_list.append(music_file) 
            print(done+'检测到纯音乐: '+file_name)
        else:
            with open(target_file+'/'+file_name+'.lrc','w+',encoding='utf-8') as f:
                f.write(lrc_json['tlyric']['lyric'])  
            print(success+'LRC写入成功: '+file_name)
            success_list.append(music_file)
            	
    except:
        errorlist.append(music_file)
        os.remove(target_file+'/'+file_name+'.lrc','w+')
        print(error+'lrc写入失败: '+music_file)
        return
        
    
def main():
    print('')
    print(done+'主进程启动')
    global search_error
    global file_name
    global music_file
    global load
    for music_file in todo_files:
        load += 1
        file_name=os.path.splitext(music_file)[0]
        search_error = 0
        search(file_name)
        if search_result == '':
            errorlist.append(music_file)
            print(error+'搜索错误: '+music_file)
        else:
            search_parse()
            if songid == '000000':
                warning_list.append(music_file)
                print('')
                continue
            if optionlang == '原文':
                getlrc()
            if optionlang == '翻译':
                getlrc_translate()
        load_=str(load).zfill(3)
        todo_=str(len(todo_files)).zfill(3)
        success_=str(len(success_list)).zfill(3)
        fail_ = str(len(errorlist)).zfill(3)
        abso_ = str(len(abso_music_list)).zfill(3)
        warning_ = str(len(warning_list)).zfill(3)
        percent_ =str(int(load*100/len(todo_files))).zfill(3)
        print('%s/%s-[%s%s]%s%% \033[0;32m%s\033[0m \033[0;31m%s\033[0m \033[0;33m%s\033[0m \033[0;36m%s\033[0m' %(load_,todo_,'|'*int((load/len(todo_files))*(width-31)),' '*((width-31)-int((load/len(todo_files))*(width-31))),percent_,success_,fail_,warning_,abso_),end='\r')
        time.sleep(0.1)
        print(' '*(width-1),end="",flush=True)
    load_=str(load).zfill(3)
    todo_=str(len(todo_files)).zfill(3)
    success_=str(len(success_list)).zfill(3)
    fail_ = str(len(errorlist)).zfill(3)
    abso_ = str(len(abso_music_list)).zfill(3)
    warning_ = str(len(warning_list)).zfill(3)
    percent_ =str(int(load*100/len(todo_files))).zfill(3)
    print(success+'主程序已完成') 
    print(done+'共提交%s个任务，其中处理了%s个，实际写入了%s个lrc文件，有%s个纯音乐，%s次警告，%s个错误' %(int(todo_),int(load_),int(success_),int(abso_),int(warning_),int(fail_)))
    
def writelog():
    print('')
    print(success+'主程序已完成，等待日志写入中:')
    if log_file != 'skip':
        # 加入新模板
        with open(log_file,'a+',encoding='utf-8') as f:
            f.seek(0)
            f.write(separator)
            
        with open(log_file,'a+',encoding='utf-8') as f:
            f.seek(0)
            f.write(log_template)
            
        
        # 处理数据
        with open(log_file,'r',encoding='UTF-8') as f1:
            data = f1.read()
            # [setting]>>
            data = data.replace('[setting]>>','[setting]>>\n'+origin_file+'\n'+target_file+'\n'+optionlang+'\n',2)
            # [absolute music]>>
            absoS = ''
            for i in abso_music_list:
                absoS = absoS + os.path.splitext(i)[0] +'\n'
            data = data.replace('[absolute music]>>','[absolute music]>>\n'+absoS,2)

            # [wrong file]>>
            wrongS = ''
            for i in errorlist:
                wrongS = wrongS + i + '\n'
            data = data.replace('[wrong file]>>','[wrong file]>>\n'+wrongS,2)

            # [update history]>>
            data = data.replace('[update history]>>','[update history]>>\n'+time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())+'\n',2)
            
            # [raw log]>>
            
        # 开始写入
        with open(log_file,'w',encoding='UTF-8') as f2: 
            f2.write(data)
        print(success+'日志已写入,保存于'+log_file)
    else:
        print(done+'日志写入已跳过')
        
        
## 启动器
print(logo+version+'\n')
check()
setlog()
importlog()
setup()
checkfile()
writelog()