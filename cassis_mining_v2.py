#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  2 11:28:01 2021

@author: markos
"""

#Uncomment if installed in new environment
!pip install webdriver_manager
!pip install selenium

#!pip install astroquery

#from bs4 import BeautifulSoup as bs
#import requests
import os
import time
import scipy.special as scsp
import numpy as np
#from google.colab import files
#from astropy.io import fits
#import pandas as pd
from os import path, mkdir, rename, listdir, chmod


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#routechrome =   '/home/markos/bin/chromedriver' #OR download proper version of chromedriver
#Solution if no proper chromedriver is install for selenium
from webdriver_manager.chrome import ChromeDriverManager
routechrome  =  ChromeDriverManager().install()


#catalogues from which to search spectra. Check structure and secondary options
route_data =      '/home/markos/Desktop/catalogs/'
list_datafiles = ['goods_N.tbl'] 

#where to save data
savefolder =     '/goods_n'  #subfolder of data


search_radius =     10.0     #arcsec
SECONDARY     =     True    #Allow for downloading extended source spectrum too
timeout =           2.0     #Seconds to pause at browser for finding keyword or changing to download page
plus_time =         3.0     #Seconds, adjust to your internet and cpu speed
listing_method =   'all'    # 'astroquery': searches at irs_enhanced catalogue to estimate the number of sources detected
                            # 'all': tries to find spectra for all galaxies

#Secondary options  | defaults for GOODs catalogue. Check with your 'datafile' format    
id_name_column_index = 1 #0 for name / 1 for id 
ra_column_index      = 2 
dec_column_index     = 3



#Read sample of galaixes from pickle file
route_save = route_data +savefolder + '/'
if path.isdir(route_save) is False: mkdir(route_save)

for datafile in list_datafiles:
    file= open(route_data+datafile,'r')#pd.read_pickle(route_data+datafile)
    sfile = file.readlines()
    col0 , col1 , col2 = [] , []  , []
    for i,line in enumerate(sfile):
        if line[0] not in [r'\ '[0] ,"|"]:
            temp1 = line.replace('\n','')
            temp2 = [ x.strip() for x in temp1.split(' ') if x != '']
            #if len(temp1.split(' '*3)[0])>0:
              # temp2 = temp1.split('   ')[0]
              #   temp3 = temp2.split(' ')
              #  col1.append(temp3[2])
              #  col2.append(temp3[3])
           # else:
               # temp2 = temp1.split('   ')[1]
              #  temp3 = temp2.split(' ')
            col0.append(temp2[id_name_column_index])
            col1.append(temp2[ra_column_index])
            col2.append(temp2[dec_column_index])

RA = np.array(col1).astype(np.float64)
DEC = np.array(col2).astype(np.float64)


#PRE-RUN IN ASTROQUERY TO FIND CATALOGUED GALAXIES

found , found_indices , listf , listc  = [ ] ,  [ ] , [ ] ,  [ ]
#N = len(sfile)-1 # -1 because of the last objecte being unidentified in the sample 115
N = len(col0)

for i in range(N):
    if listing_method == 'astroquery':
        from   astroquery.irsa import Irsa
        import astropy.coordinates as coord
        import astropy.units as u

        #Find in IRSA Astroquery , catalogue selected above
        ra, dec = RA[i],DEC[i]
        name = col0[i]
        #search in astroquery default options
        Radius_arcsec = 25 #for searching object NOT spectra , provide large enough area  ( > search_radius )
        ctlg  = "irs_enhv211"  #choose a catalogue that provides galaxies with IR spectra
        example_result_coords = Irsa.query_region(coord.SkyCoord(ra,dec,unit=(u.deg,u.deg),frame='fk5'),\
                                catalog=ctlg, spatial="Cone", radius= Radius_arcsec * u.arcsec)
        if len(example_result_coords) != 0:
            found.append(name)
            found_indices.append(i)
    
    elif listing_method == 'all':
        found_indices.append(i)
    else:
        print('Incorrect mode')
    
    #Compare with galaxies having IRS or IRAS points in their SED data
    #for j in file.iloc[i]['NED_SED_obs']:
     #   for k in file.iloc[i]['NED_SED_obs'][j].values():
       #     if 'irs' in str(k).casefold() or 'iras' in str(k).casefold():
      #          if i not in listf:
       #             listf.append(i)
        #            if i not in found_indices:
     #                   listc.append(i)
                    #print(i)

input_indices = found_indices
#if listing_method not in ['astroquery' , 'all']:
 #   input_indices = listf
#else:
print('Found in catalogue ('+listing_method+'):\t '+str(len(found_indices)))
#print('Found in NED with string-search at labels:\t'+str(len(listf)))



def download_spectra_cassis(url ,route_save =None, routechrome = None,  timeout = 2.0, plus_time= 3.0, secondary=False):
    if routechrome !=None:
        service = Service(routechrome)
    else:
        service = Service('usr/bin/google-chrome')
        print('Default browser used, not chrome driver for selenium')
    service.start()
    if route_save != None:
        prefs = {'download.default_directory':route_save}
        #driver = webdriver.Remote(service.service_url) 
        chromeOptions = Options()
        chromeOptions.add_experimental_option("prefs",prefs)
        driver = webdriver.Chrome(executable_path = routechrome, options=chromeOptions)
    else:
        driver = webdriver.Chrome(executable_path = routechrome ,options=chromeOptions)
        print('Results most likely at /home/user/Downloads')
    driver.get(url)
    #scroll
    elem = driver.find_element_by_tag_name('html')
    scrolls= 1 
    for nums in range(0,scrolls):
                elem.send_keys(Keys.END)
                time.sleep(0.5)
    #switch to download page
    next_page_string =    'Download alternate versions' 
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT,next_page_string))).click() #class=\'resultlink\'><i>SMART</i> FITS</a>&nbsp;|&nbsp;'))).click()
    #click on downloading spectra
    spectra_string , pos = 'DEFAULT' , 15  #count the downloadable links to the desired location
    POSITIONS = [pos]
    if secondary: POSITIONS = [pos, pos + 4]
    for pos in POSITIONS:
        spectra_string = "(//*[@class='downlink'])["+str(pos)+"]"
        WebDriverWait(driver, timeout+plus_time).until(EC.element_to_be_clickable((By.XPATH,spectra_string))).click() #class=\'resultlink\'><i>SMART</i> FITS</a>&nbsp;|&nbsp;'))).click()    time.sleep(timeout)
    driver.close()
    
    
    
#RUN TO DOWNLOA
links, recovered, not_recovered  , recovered_sg, not_recovered_sg = [] , [] , [] , [] , []

for i in input_indices:
    # ra,dec = file.iloc[i]['ra'] , file.iloc[i]['dec']
    ra, dec = RA[i], DEC[i]
    name = col0[i]
    temp_link   = 'https://cassis.sirtf.com/atlas/cgi/radec.py?ra='+str(ra)+'&dec='+str(dec)+'&radius='+str(search_radius)
    links.append(temp_link)

    
n1  = 30  #default 0 
n2 =  40 #default len(links) + 1

for i,sg in zip(input_indices[n1:n2], links[n1:n2]):
    try:
        download_spectra_cassis(sg, route_save , routechrome, timeout=timeout, plus_time = plus_time, secondary=SECONDARY)
        ll = listdir(route_save)
        ll = [route_save + nn for nn in ll if 'cassis_' in nn] #call "not named" files to avoid overwritting if download fails
        ll.sort(key=path.getctime)
        prev_name = ll[-1-SECONDARY*1] #call last element matching to the last modified file
        #name_save = str(file.iloc[i].name)+'_'+file.iloc[i]['tNames'].split('|')[0].strip('_')+OPTIMAL*'_optimal'+'.fits'
        name_save = col0[i]+'.tbl'
        rename(prev_name, route_save + name_save)
        print(str(i)+ ' Saved with name ',name_save)
        if SECONDARY:
            prev_name_B = ll[-1] #call last element matching to the last modified file
            name_save_B = col0[i]+'_extended.tbl'
            rename(prev_name_B, route_save + name_save_B)
            #print(str(i)+ ' Saved extended source spectra with name ',name_save_B)
        recovered.append(i)
        recovered_sg.append(sg)
        
        #ACCESS PAGE INFORMATION WITH BEATIFUL SOUP. NOT USED
        #innerHTML = driver.execute_script("return document.body.innerHTML")
        #page_soup = bs(innerHTML, 'html.parser')
        #ps=str(page_soup)
        #ps1=ps.split('\"resultlink\"')[5]
        #ps2=ps1.split('<a href=')[1]#all html stored as string
        #ps3 = ps2.strip('\"')
        #spectra_link.append(ps3)
        #print(ps2)
        #rename at path
    except:
        print('Failed at ', col0[i],' : ',  sg)#file.iloc[i].name , ' : ',  sg)
        not_recovered.append(i)
        not_recovered_sg.append(sg)
        pass
print('\n\n')
print(str(len(recovered))+' out of '+ str(len(links[n1:n2]))+' galaxy spectras were recovered')
print('\n Check the website of cassis of the following objects to find the problem \n')

with open(route_data + '/norecovered.txt', 'w') as f:
    for i,s in enumerate(not_recovered_sg):
        f.write(col0[i]+', '+s +'\n')

with open(route_data + '/recovered.txt', 'w') as f:
    for i,s in enumerate(recovered_sg):
        f.write(col0[i]+'\n')
#for i in not_recovered: 
#  print('\n',i, col0[i], links[not_recovered.index(i)])#file.iloc[i]['tNames'], links[not_recovered.index(i)])