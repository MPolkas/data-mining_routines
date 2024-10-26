#!/usr/bin/env python3
"""
## YOUTUBE DOWNLOADER ##
Author: Markos Polkas 2021-11-06

"""
#Dependencies
#!pip install youtube_dl 
#!pip3 install eyed3
#!pip install bs4
#!pip install selenium
#!pip install webdriver_manager
#import youtube_dl
import yt_dlp as youtube_dl
from eyed3 import id3
from os import rename, system, getcwd ,listdir, path
from bs4 import BeautifulSoup as bs
#import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import time
"""
Author Markos Polkas , first release 2021
# If not sure, set download_dic = {'Name_of_channel':[]}, and use search_playlist_in_channels() 
# to scan music of channel 'Name_of_channel' or use search_playlist_by_titles() with two title keywords to find it online,
# provided its uniqueness and popularity

# Also, you can provide the channel name and the playlist name and the algorithm will try to find the playlist
# There is also a function for retrieving the songs of a facebook friend post-wall or your post-wall
# with get_links_from_facebook() and storing the output links to a playlist

# Finally, with the function search_playlist_by_titles() you can use a yt search with two strings to find interesting playlists
# e.g. . Simplicity ,or comprehensible words, will help the yt algorithm
# The function returns a dictionary of users with playlists found with these keywords and the playlist themselves stored
# then you can use search_playlist_in_channels() to discover more playlists at each channel
# and finally main() with download_dic the loaded dictionary to download all tha music
"""


download_dic = {'Markos':[
                        ['UD15',   #name of playlist
                         'https://youtube.com/playlist?list=PLqWwpZed6nYNiX2B6UXMYuE4LYG9NbA97&si=zcF-dBGSA9eGw7Gf',  #link to playlist
                        'Not recorded', #titles stored here
                        'Not recorded', #uploaders here
                        'Not recorded'  #links to videos 
                        ]]}

route_music = '/home/investigator/Music/' #where to save your music

#%% MAIN
def main():
    global download_dic
    global route_music
    global success
    global fail
    global tempfile
    success, fail = [], []
    tempfile = f'temp.mp4'
    options={'format':'bestaudio',
        'keepvideo':False,
        'outtmpl': tempfile,
        'noplaylist':True,
        'ignoreerrors':True}
    download_dic = read_playlists(download_dic)
    with youtube_dl.YoutubeDL(options) as ydl:
        for k in list(download_dic):
            download_channel(k,ydl,download_dic, OVERWRITE=False, TAG=True)
    #AUTO move to save folder
    # if getcwd()+'/'!=route_music:
    #     for song in success:
    #         system('cp \"'+song+'.mp3\" '+route_music) #move to saving directory
    print('\n\n Check Failed')
    print(fail)
    

def download_channel(channel,ydl,dic={},saveroute='./' , OVERWRITE=False, TAG=False):
    if dic=={}: 
        dic = search_playlist_in_channels(dic,single_channel=channel)
    suc,fat = [], []
    for i, plst in enumerate(dic[channel]):
        if len(plst)==1:
            dic0= search_playlists_by_titles(channel,plst[0],{})
            dic0 = search_playlists_in_channels(dic0)
            print('Trying to search for playlist name +channel name,because no link is provided for the playlist.\n The first choice is automatically selected')
            try:         
                download_playlist(dic[channel][0],ydl,saveroute, OVERWRITE=OVERWRITE) 
            except:
                print('failed')
        elif len(plst)<5:
            print('two columns are missing. We assume no past history therefore append "Not recorded"')
            while len(plst)!=5:
                plst.append('Not recorded')
        elif len(plst)>5:
                print('additional columns in playlist array are neglected')
        else:
            s, f = download_playlist(plst,ydl,saveroute, OVERWRITE=OVERWRITE)
            suc.append(s)
            fat.append(f)
    #return suc, fat


def download_playlist(plst, ydl,saveroute='./', OVERWRITE=False, TAG=False):
    global artist, title
    global success 
    global fail
    success, fail = [], []
    for j, url in enumerate(plst[-1]):
        #edit title and artist
        title = plst[2][j]
        artist = plst[3][j]
        title = title.replace('///','-').replace('|','-').replace('/','-')
        title = title.replace('–','-').replace('--','-')
        if ' - ' in title:
            artist = title.split(' - ',1)[0]
            title = title.split(' - ',1)[1]
            if artist in title:
                temp_artist = artist
                artist = title
                title  = temp_artist
                print('Reversed artist/title: Artist: '+artist+' \t Title: '+title)
        if 'Official' in artist:
            artist = artist.split('Official')[0]
            artist = artist[0:-1]
                
        if 'Official' in title:
            title = title.split('Official')[0]
            title = title[0:-1]
        artist = artist.lstrip().rstrip().title()
        title = title.lstrip().rstrip().title()
        if ' ' not in artist: 
            artist = artist.capitalize()
        for exc in ['A','An','To','At','Of','With','So','And','Or' ]:
            spexc = ' '+exc+' '
            if spexc in artist: artist.replace(spexc,spexc.lower())
            if spexc in title: title.replace(spexc, spexc.lower())
        song = artist + ' - ' + title
        #Simple download options
        if  (not path.isfile('./'+song+'.mp3') and not path.isfile('./'+song+'.mp4')) or OVERWRITE:
            print('\n\n Now downloading: '+song)
            ydl.download([url])  # [video_info['webpage_url']])
            if path.isfile('temp.mp4'):
                convert_files(convert_name=tempfile,new_name=song,TAG=TAG)
                print('DONE \t'+song)
                success.append(song)
            else:
                print('Failed at '+song)
                fail.append(song)
    print('FINISHED at playlist '+plst[0])
    print('{}% success. Successfull downloads , tagged and moved to save folder'.format(
        int(len(success)/(len(fail)+len(success))*100)))
    return success, fail

def convert_files(Last_N_created_files=1, fromformat='.mp4',toformat='.mp3', convert_name = False, new_name = False, TAG=False, search_dir='./'):
    if convert_name:
        files = [convert_name]
        Last_N_created_files = 1
    else:
        files =  listdir(search_dir)
        if Last_N_created_files>len(files): Last_N_created_files=len(files)
        files.sort(key=lambda x: path.getmtime(x))
        files = [f for f in files if '.'+f.split('.')[-1] in [fromformat] and f[0]!='.']
    if new_name and Last_N_created_files>1: 
        print('No convertion. Renaming is used only for a single file')
    else:
        for temp in files[-Last_N_created_files::]:
            new_name = new_name.replace('"','\"').replace('/',',')
            if new_name==False: 
                rename_name = temp.split(fromformat)[0]+toformat
            else:
                rename(temp, new_name+fromformat)
                temp =  new_name+fromformat
                rename_name = new_name+toformat
            comm = u'ffmpeg -i \"{}\" \"{}\"'.format(temp,rename_name)
            system(u"{}".format(comm))
            if TAG:
                #encrypt on tags
                tag = id3.Tag()
                tag.parse(new_name)
                artist = temp.split(' - ',1)[0]
                title = temp.split(' - ',1)[1]
                tag.artist = u"{}".format(artist)
                tag.title = u"{}".format(title)
                tag.save()
            if not path.isfile(search_dir+rename_name) :
                comm = u"ffmpeg -i \'{}\' \'{}\'".format(temp,rename_name)
                print('ERROR in renaming, probably stayed an .mp4')                
    


def search_playlists_by_titles(word1,word2, dic):
    new_ch = 0  # new channel counter
    new_pl = 0  # new playlists counter
    #load page virtually
    service = Service(routechrome)
    service.start()
    driver = webdriver.Remote(service.service_url)
    searchurl = 'https://www.youtube.com/results?search_query='+word1+'+'+word2+'&sp=EgIQAw%253D%253D'
    driver.get(searchurl)
    #scroll down doesn't work
    elem = driver.find_element(by='tag name', value='html')
    scrolls = 2  # X20
    for nums in range(0, scrolls):
               elem.send_keys(Keys.END)
               time.sleep(1)
    innerHTML = driver.execute_script("return document.body.innerHTML")
    page_soup = bs(innerHTML, 'html.parser')
    sp = str(page_soup)  # all html stored as string
    driver.close()
    """Processing """
    sp2 = sp.split('"playlistId":')
    ids, plsts, titlepl, channelpl, linkpl = [], [], [], [], []
    for i in sp2[1::]:
        ii = i.split('"')
        j = ii[1]
        k = ii[7]
        if j not in ids:
            ids.append(j)
            plsts.append('https://www.youtube.com/playlist?list='+j)
            titlepl.append(k)
        if 'longBylineText' in i:
            n = ii[ii.index('longBylineText')+6]
            l = ii[ii.index('longBylineText')+20]
            if n not in channelpl:
                channelpl.append(n)
                linkpl.append('https://www.youtube.com'+l)
    #####
    for pl in range(0, len(channelpl)):
           if channelpl[pl] not in list(dic):
                dic[channelpl[pl]] = [linkpl[pl], [titlepl[pl],
                    plsts[pl],  'Not recorded', 'Not recorded']]
                print('\n'+titlepl[pl]+' by '+channelpl[pl]+':\t'+linkpl[pl])
                new_ch += 1
                new_pl += 1
                # if ' - Topic' in channelpl[pl]:
                #     print('"Topic", ejected from dictionary')
                #     dic.pop(channelpl[pl])
           else:
                ls = dic[list(dic)[pl]][1::]
                lb = [i[1] for i in ls]
                if plsts[pl] not in lb:
                    temp = dic[channelpl[pl]]
                    temp.append([titlepl[pl], plsts[pl],  'Not recorded','Not recorded'])
                    dic[channelpl[pl]] = temp
                    new_pl += 1
                else:
                    pass
    #####
    print('\n Total: detected '+str(len(ids))+' Playlists\n')
    print('\n New channels: \t'+str(new_ch))
    print('\n New playlists: \t'+str(new_pl))
    return dic

def search_playlists_in_channels(dic, single_channel=None):
    if single_channel !=None: 
        listdic = [single_channel]
    else:
        listdic = list(dic)
    for ch in listdic:
        new_pl = 0 #new playlists counter
        url = dic[ch][0]+'/playlists?view=1&flow=grid'
        expls = [pl[1] for pl in dic[ch][1::]]
        extls = [pl[0] for pl in dic[ch][1::]]
        ####
        #load page virtually
        service = Service(routechrome)
        service.start()
        driver = webdriver.Remote(service.service_url)
        driver.get(url)
        elem = driver.find_element(by='tag name',value='html')
        scrolls = 2 #*20
        for nums in range(0, scrolls):
                   elem.send_keys(Keys.END)
                   time.sleep(1)
        innerHTML = driver.execute_script("return document.body.innerHTML")
        page_soup = bs(innerHTML, 'html.parser')
        sp = str(page_soup) #all html stored as string
        driver.close()
        """Processing """
        sp2 = sp.split('"playlistId":')[1::]
        sp3 = sp.split('id="video-title" title=')[1::]
        ids , plsts , titlepl , channelpl, linkpl = [], [],[],[],[]
        it = 0
        for i in sp2:
            ii = i.split('"')
            j = ii[1]
            k = 'https://www.youtube.com/playlist?list='+j
            if j not in ids and k not in expls:
                ids.append(j)
                plsts.append(k)
                titlepl.append(sp3[it].split('"')[1])
                it += 1
        for pl in range(0, len(plsts)):
                   if plsts[pl] not in expls:
                        temp = dic[ch]
                        temp.append([titlepl[pl], plsts[pl],  'Not recorded','Not recorded','Not recorded'])
                        dic[ch] = temp
                        new_pl += 1
                   else:
                        pass
        print('\n Channel '+ch)
        print('\n Added \t'+str(new_pl)+' new playlists')
    return dic


def read_playlists(dicpl):
    channelpl = list(dicpl)
    for ipl in range(0, len(list(dicpl))):
        cpl = channelpl[ipl]
        lpl = dicpl[cpl][0]
        num_pl = 0
        for nn in range(0, len(dicpl[cpl])):
            if dicpl[cpl][nn][2] =='Not recorded' or dicpl[cpl][nn][3]=='Not recorded' or dicpl[cpl][nn][4]=='Not recorded':
                tpl = dicpl[cpl][nn][0]
                pl = dicpl[cpl][nn][1]
                #read initially
                service = Service(routechrome)
                service.start()
                driver = webdriver.Remote(service.service_url)
                driver.get(pl)
                str_xpath = '//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/form[2]'
                box = driver.find_element(by='xpath',value=str_xpath)
                box.click() 
                innerHTML = driver.execute_script("return document.body.innerHTML")
                page_soup = bs(innerHTML, 'html.parser')
                #####
                #count videos
                #old <Nov 2022
                #number_videos_container = page_soup.findAll('yt-formatted-string',
                number_videos_container = page_soup.findAll('yt-formatted-string',\
                                {'class':'byline-item style-scope ytd-playlist-byline-renderer'})
                str_number = number_videos_container[0].text #number_videos_container[1].text    # next lines clean up the string to make it a real number
                #end_of_number = str_number.find(' ')
                number_videos = int(str_number.split()[0])#int(str_number[:end_of_number].replace('.', '').replace(',', ''))
                print('\n For '+tpl+' found initially:\t'+str(number_videos)+' from playlist')
                times_scroll_down = int((number_videos/100) + 1)
                #scroll down
                elem = driver.find_element(by='tag name',value='html')
                for nums in range(times_scroll_down+1):
                    elem.send_keys(Keys.END)
                    time.sleep(1)
                #read again after scrolling down
                innerHTML = driver.execute_script("return document.body.innerHTML")
                page_soup = bs(innerHTML, 'html.parser')
                res = page_soup.find_all('a', {'class': 'yt-simple-endpoint style-scope ytd-playlist-video-renderer'})
                driver.close()
                titles, uploaders, links = [], [], []
                resB = page_soup.find_all('tp-yt-paper-tooltip',class_='style-scope ytd-channel-name')

                for i,video in enumerate(res):
                    ttl = video.get('title')
                    href = 'https://www.youtube.com'+video.get('href')
                    titles.append((video.get('title')))
                    links.append(href)
                #for i, video in enumerate(len(links)):
                    if ttl != None and ttl not in ['[Deleted video]', '[Private video]']:
                        #print(str(resB))
                        ss = str(resB[i]).split('\n')[2].strip()
                        print(ss)
                        # for i in ss.split():
                        #     try:
                        #         k = int(i)
                        #         if k:
                        #             br = list(ss).index(i)
                        #             ss = ss[0:br].strip(' ')
                        #             break
                        #     except:
                        #         pass
                        if len(ss) > 8 and ss[-8::] == ' - Topic': ss = ss[0:-8]
                        uploaders.append(ss)
                    else:
                        uploaders.append(None)
                uploaders = [j for j in uploaders if titles[uploaders.index(j)]]
                links = [j for j in links if titles[links.index(j)]]
                titles = [i for i in titles if i]
                dicpl[cpl][nn] = [tpl,pl,titles, uploaders, links]               
                num_pl += 1
                print('Listed titles, without Deleted/Private Videos:'+str(len(titles)))
        print(str(num_pl)+' playlists added for channel '+str(cpl))
    return dicpl


#%%
% Routine to get your posted 

def get_links_from_facebook(href_friend, fbuser,fbpsw,scrolls=10):
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    #function that takes input facebook.com/ "person" and returns a list of songs that the user has shared
    option = Options()
    option.add_argument("--disable-infobars")
    option.add_argument("--disable-extensions")
    # Pass the argument 1 to allow and 2 to block
    option.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 1})
    driver = webdriver.Chrome(chrome_options=option, executable_path=routechrome)
    url = 'https://www.facebook.com'
    #load page virtually
    #service= Service(routechrome)
    #service.start()
    #driver = webdriver.Remote(service.service_url)
    driver.get(url)
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@data-testid="cookie-policy-banner-accept"]'))).click()
    #Login facebook as yourself
    usr = fbusr
    pwd = fbpsw
    print('Opened Facebook, will try login automatically')
    username_box = driver.find_element(by='id',value='email')
    username_box.send_keys(usr)
    print ("Email Id entered")
    password_box = driver.find_element(by='id',value='pass')
    password_box.send_keys(pwd)
    print ("Password entered")
    login_box = driver.find_element(by='name',value='login')
    login_box.click()
    time.sleep(1)
    fburl = 'https://www.facebook.com/'+href_friend
    driver.get(fburl)
    #scroll down doesn't work
    elem = driver.find_element(by='tag name',value='html')
    for nums in range(0, scrolls):
               elem.send_keys(Keys.END)
               time.sleep(1)
    innerHTML = driver.execute_script("return document.documentElement.innerHTML")
    page_soup = bs(innerHTML, 'html.parser')
    sp = str(page_soup) #all html stored as string
    #sp=driver.page_source
    driver.close()
    initlink = 'https://l.facebook.com/l.php?u=https%3A%2F%2Fwww.youtube'
    sp1 = sp.split(initlink)[1::]
    links = []
    for el in range(0, len(sp1)):
        sp2 = initlink+sp1[el].split('"')[0]
        if sp2 not in links and el%3 ==0:
            links.append(sp2)
    print('Detected : \t'+str(len(links))+'links')
    return links

#%%
main()
