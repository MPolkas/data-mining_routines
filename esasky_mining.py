#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on  Sun Jul 11 12:19:16 2021

@author: markos
"""

#from bs4 import BeautifulSoup as bs
#import requests
import time
import scipy.special as scsp
import numpy as np
import astropy.units as u
#from google.colab import files
import astropy.coordinates as coord
from astropy.io import fits
import pandas as pd
from os import path, mkdir, rename, listdir , remove


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
routechrome  =  ChromeDriverManager().install()

#routechrome='/usr/bin/google-chrome' #maybe use  your google-chrome
#routechrome = '/home/markos/bin/chromedriver' #OR download proper version of chromedriver 

route_data =   '/media/Datas/KD_group/SED-fitting/data/'
datafile =  'sample115_22_3_markos.pcl' 
savefolder = 'esasky'  #subfolder of data

fov = None
timeout = 5 # seconds to pause at browser and for .fits download time
scan_filters = ['HST+WFPC2','DSS2+color','2MASS+color+JHK','AllWISE+color']

glx_indices = list(range(115))


#Read sample of galaixes from pickle file
route_save = route_data +savefolder + '/'
if path.isdir(route_save) is False: mkdir(route_save)
file= pd.read_pickle(route_data+datafile)
#%%

def download_image(url, driver, route_save=None,  timeout = 10.0):
    driver.get(url)
    # elem = driver.find_element_by_tag_name('html')
    # scrolls= 1 
    # for nums in range(0,scrolls):
    #             elem.send_keys(Keys.END)
    #             time.sleep(1)
    WebDriverWait(driver,1).until(EC.element_to_be_clickable((By.CLASS_NAME,'welcomeCloseButton'))).click()
    button1 = 'header__screenshotButton'
    time.sleep(timeout)
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.ID,button1))).click()
    button2 = 'screenshotDialogBox'
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CLASS_NAME,button2))).click() #class=\'resultlink\'><i>SMART</i> FITS</a>&nbsp;|&nbsp;'))).click()
    time.sleep(timeout)

    #ACCESS PAGE INFORMATION WITH BEATIFUL SOUP. NOT USED
    #innerHTML = driver.execute_script("return document.body.innerHTML")
    #page_soup = bs(innerHTML, 'html.parser')
    #ps=str(page_soup)
    #ps1=ps.split('\"aperture\"')[5]
    #ps2=ps1.split('<a href=')[1]#all html stored as string
    #ps3 = ps2.strip('\"')
    #aperture_info.append(ps3)
    #print(ps2)
    #rename at path
    
    #driver.close()
    
#%%

#RUN TO DOWNLOAD
spectra_link, links, recovered, not_recovered = [] , [],  [[],]*len(scan_filters), [[],]*len(scan_filters)

for i in glx_indices:
    flt_links = []
    for filt in scan_filters:
        ra,dec = file.iloc[i]['ra'] , file.iloc[i]['dec']
        str_coords = '{:.15f}%20{:.15f}'.format(ra,dec)
        flt_links.append('https://sky.esa.int/?target='+str_coords+'&hips='+filt+'&fov=0.07545695980376196&cooframe=J2000&sci=true&lang=en')
    links.append(flt_links)


if routechrome !=None:
    service= Service(routechrome)
else:
    service = Service('usr/bin/google-chrome')
    print('Default browser used, not chrome driver for selenium')
service.start()
if route_save != None:
    prefs = {'download.default_directory':route_save}
    #driver = webdriver.Remote(service.service_url) 
    chromeOptions = Options()
    chromeOptions.add_experimental_option("prefs",prefs)
    driver = webdriver.Chrome(executable_path = routechrome,chrome_options=chromeOptions)
else:
    driver = webdriver.Chrome(executable_path = routechrome)
    print('Results most likely at /home/user/Downloads')

for i,lk  in enumerate(links):
    for j,sg in enumerate(lk):
            complete = False
            temp_timeout = timeout
            while not complete:
                try:
                    download_image(sg,  driver, route_save, timeout=temp_timeout)
                    complete = True
                    keyword = 'ESASky'
                except:
                    temp_timeout  += 3
                    if temp_timeout> 20: 
                        complete = True
                        keyword = None
                        not_recovered[j].append(i)
                    pass
            if keyword!=None:
                #find the last downloaded image and rename it
                ll = listdir(route_save)
                ll = [route_save + nn for nn in ll if keyword in nn] #call "not named" files to avoid overwritting if download fails
                ll.sort(key=path.getctime)
                if path.getsize(ll[-1])/1024 < 50: #kB, less than that a mere black backgrond is downloaded
                    remove(ll[-1])
                    print('Not Found {} Image, the downloaded screenshot is deleted'.format(scan_filters[j].split('+')[0]))
                    not_recovered[j].append(i)
                else:
                    prev_name = ll[-1] #call last element matching to the last modified file
                    name_save = str(file.iloc[i].name)+'_'+scan_filters[j].split('+')[0]+'.png'
                    rename(prev_name, route_save + name_save)
                    print(str(i)+ ': Image saved with name ',name_save)
                    recovered[j].append(i)
             
#print('\n\n')
#print(str(len(links)-len(not_recovered))+' out of '+ str(len(links))+' galaxy images were recovered')
#for i in not_recovered:
#    print('\n',i, file.iloc[i]['tNames'], links[not_recovered.index(i)])
driver.close()
