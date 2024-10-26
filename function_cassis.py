#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  2 11:28:01 2021

@author: markos
"""

#Uncomment if installed in new environment
#!pip install webdriver_manager
#!pip install selenium

#!pip install astroquery

#from bs4 import BeautifulSoup as bs
#import requests
import os
import time
import scipy.special as scsp
import numpy as np
from pandas import read_table , read_table
#from google.colab import files
#from astropy.io import fits
#import pandas as pd
from os import path, mkdir, rename, listdir, chmod

from  matplotlib import pyplot as plt

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


def download_spectra_cassis(url ,route_save =None, routechrome = None, 
                            timeout = 3.0, plus_time= 5.0, secondary=False):
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
        WebDriverWait(driver, timeout+plus_time).until(EC.element_to_be_clickable((By.XPATH,spectra_string))).click() #class=\'resultlink\'><i>SMART</i> FITS</a>&nbsp;|&nbsp;'))).click()    
    time.sleep(timeout)
    driver.close()


def read_and_plot(df, i,  route_data, name_save, route_save, new_filename, optimal=False,\
                  use_filters = False,   plot=False,  save_at_file=False, LOGY=False):
    if save_at_file: df_copy  = df.copy()
    iglx = df.iloc[i].name
    fl = read_table(route_save+name_save, comment="\\", delim_whitespace=True,skiprows=116)
    dt = fl    

    #read columns (for low-resolution (SMART FITS))
    wv =      dt[fl.keys()[0]] #wavelength in micra 
    flux =    dt[fl.keys()[1]] #flux in Jy
    errors =  dt[fl.keys()[2]] #RMS + SYS  in Jy
    
    clean_data = no_nans(np.array([wv,flux,errors]).T)
    clean_data = clean_data[clean_data[:, 0].argsort()]
    
    #for low-resolution (SMART FITS)
    color = 'red'
    extra=0
    if optimal:
        err_rms = dt[fl.keys()[4]] #rms only in Jy
        err_sys  =dt[fl.keys()[5]] #systematic only in Jy
        clean_data = no_nans(np.array([wv,flux,errors, err_rms, err_sys]).T)
        color = 'blue'
        extra=1

    #plot
    if plot:
        fig, ax = plt.subplots(figsize=[12,9],num=i+extra)
        plt.errorbar(wv,flux,yerr=errors,fmt='.',color='k', ecolor=color)
        plt.xlabel(r'$\lambda_{obs}$   [$\mu$m]' ,size=15)
        plt.ylabel(r'$F_{\nu}$  [Jy]' ,size=15)
        if LOGY:
            plt.yscale('log')
            plt.ylabel(r'$\log F_{\nu}$  [Jy]' ,size=15)
        plt.title(str(iglx)+optimal*' optimal',size=18)
        ax.tick_params(axis='x', labelsize=14)
        ax.tick_params(axis='y', labelsize=14)
        ax.tick_params(which='major', width=1.2, length=7)
        ax.tick_params(which='minor', width=1.1, length=4)
    if save_at_file:
        df_copy.at[iglx,'CASSIS'] = clean_data
        df_copy.to_pickle(route_data+new_filename,protocol=4)
    
    # if use_filters: #UNDER CONSTRUCTION; Needs better integration for filters ,set false
    #     filtered_data = []
    #     filtered_dic  = {}
    #     for flt in list(filters.keys()):
    #         wl , eff = [] , []
    #         ffile = open(routef+flt+'.dat','r')
    #         for it in ffile:
    #             if it[0]!='#':
    #                 z = it.split(' ')
    #                 z = [x for x in z if x.strip()]
    #                 wl.append(float(z[0])/1e4) #micra
    #                 eff.append(float(z[1].strip('\n')))
    #         wl  , eff  = np.array(wl).astype(np.float64) , np.array(eff).astype(np.float64)
    #         flt_kernel = interp1d(wl,eff)
    #         x , y , yerr  = clean_data[:,0] , clean_data[:,1] , clean_data[:,2]
    #         y  = y[np.where((x > min(wl))&(x<max(wl)))]
    #         yerr  = yerr[np.where((x > min(wl)) &(x<max(wl)))]
    #         x  = x[np.where((x > min(wl)) &(x <max(wl)))]
    #         if len(x)>0:
    #             flux = -simps(flt_kernel(x)*y,3e14/x)*1e-23  #minus because we intergrate from large to small values
    #             flux_err = 0.1*flux
    #             #flux_err = np.max(1/len(y) * np.sqrt(np.sum((flt_kernel(x)*yerr/y)**2)), np.std(flt_kernel(x)*y*3e14/x))#try to compute an error
    #         else:
    #             flux=0.0
    #         if flux > 0.0 and filters[flt]<max(clean_data[:,0]*1e4) and filters[flt]>min(clean_data[:,0]*1e4):
    #             filtered_data.append([3e18/filters[flt],flux, flux_err]) #energy flux as defined here !!
    #             filtered_dic[flt] = {'freq':filtered_data[-1][0] , 'eflux': filtered_data[-1][1] , \
    #                                 'eflux_err': filtered_data[-1][2]}
    #         # add x err and y err here
    #         ffile.close()
    #     filtered_data=np.array(filtered_data)
    #     if plot:  
    #         plt.figure(figsize= [12,9] ,  num=i+1000)
    #         if len(filtered_data)>1:
    #             plt.errorbar(filtered_data[:,0], filtered_data[:,1], yerr=filtered_data[:,2],xerr=1.0,\
    #                          fmt='.',color='tab:orange', ecolor='c', ms=10)
    #         elif len(filtered_data)==1:
    #             print(filtered_data*1e-23)
    #             plt.errorbar(filtered_data[0][0], filtered_data[0][1], yerr=filtered_data[0][2],xerr=1.0,\
    #                         fmt='.', ms=10, color='tab:orange',ecolor='c')
    #         plt.errorbar(3e14/clean_data[:,0], clean_data[:,1]*3e14/clean_data[:,0]*1e-23,\
    #                      yerr = clean_data[:,2]*3e14/clean_data[:,0]*1e-23, fmt='.',color='k', ecolor='y')
    #         plt.xlabel(r'$\nu_{obs}$  [Hz]', size=15)
    #         plt.ylabel(r' Energy Flux  [ erg/s/cm^2]',size=15)
    #         if LOGY: 
    #             plt.yscale('log')
    #             plt.ylabel(r' Energy Flux [ erg/s/cm^2]',size=15)
    #     if save_at_file:
    #         df_copy.at[iglx,'CASSIS_photo'] = filtered_dic
    #         df_copy.to_pickle(route_data+datafile,protocol=4)


def no_nans(x):
    if len(x)==0:
        return np.array([])
    xcor  , ycor , zcor  = [] , [] , []
    if x.shape[0]==1:
        if True in np.isnan(x): return []
    for i in range(len(x[:,0])):
        if not np.isnan(x[i,1]):
            xcor.append(x[i,0])
            ycor.append(x[i,1])
            zcor.append(x[i,2])
    newx=np.array(list(zip(xcor,ycor,zcor)))
    for i in range(len(newx[:,0])):
        if np.isnan(newx[i,2]) or (newx[i,2]==0):
            newx[i,2]=0.1*newx[i,1]
    return newx 

    
    
#RUN TO DOWNLOAD
def get_cassis_spectrum(file,i,route_data, new_filename, 
                        route_save = os.getcwd()+'/data/cassis',  #subfolder of data
                        search_radius =     10.0    , #arcsec
                        SECONDARY     =     True    ,#Allow for downloading extended source spectrum too
                        timeout =           3.0    , #Seconds to pause at browser for finding keyword or changing to download page
                        plus_time =         5.0    , #Seconds, adjust to your internet and cpu speed
                        PLOT          =   True ,
                        SAVE_AT_FILE  =   True ,#if USE_FILTERS , integrated flux will be saved as points
                        USE_FILTERS   =   False ,#Integrate on the catalogued filters , centered within the spectrograph wavelengths
                                               #Combined with SAVE_AT_FILE will save CASSIS_photo column at pickle file
                        LOGY          =   False, #if plotting option is true, use logaxis for flux
                        routechrome= routechrome) :

    # ra,dec = file.iloc[i]['ra'] , file.iloc[i]['dec']
    #Read sample of galaixes from pickle file
    if path.isdir(route_save) is False: mkdir(route_save)
    #Find in IRSA Astroquery , catalogue selected above
    ra, dec = file.iloc[i]['ra'], file.iloc[i]['dec']
    name = file.iloc[i].name
    sg  = 'https://cassis.sirtf.com/atlas/cgi/radec.py?ra='+str(ra)+'&dec='+str(dec)+'&radius='+str(search_radius)
    try:
        download_spectra_cassis(sg, route_save , routechrome, timeout=timeout, plus_time = plus_time, secondary=SECONDARY)
        route_save +='/'
        ll = listdir(route_save)
        ll = [route_save + nn for nn in ll if 'cassis_' in nn] #call "not named" files to avoid overwritting if download fails
        ll.sort(key=path.getctime)
        prev_name = ll[-1-SECONDARY*1] #call last element matching to the last modified file
        #name_save = str(file.iloc[i].name)+'_'+file.iloc[i]['tNames'].split('|')[0].strip('_')+OPTIMAL*'_optimal'+'.fits'
        name_save = '[{}]'.format(name)+'.tbl'
        rename(prev_name, route_save + name_save)
        read_and_plot(file, i,     route_data, name_save,  route_save, new_filename,  optimal=True,\
                  use_filters = USE_FILTERS,   plot=PLOT,  save_at_file=SAVE_AT_FILE, LOGY=LOGY)
        print('Galaxy '+str(i)+ ' Saved with name ',name_save)
        if SECONDARY:
            prev_name_B = ll[-1] #call last element matching to the last modified file
            name_save_B = '[{}]'.format(name)+'_extended.tbl'
            rename(prev_name_B, route_save + name_save_B)
            read_and_plot(file, i,    route_data, name_save_B,  route_save, new_filename, optimal=False,\
                  use_filters = USE_FILTERS,  plot=PLOT,  save_at_file=SAVE_AT_FILE, LOGY=LOGY)
            print('Galaxy '+str(i)+ ' Saved with name ',name_save_B)
            #print(str(i)+ ' Saved extended source spectra with name ',name_save_B)
            
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
    except Exception as e: 
        print(e)        
        print('Failed at ', file.iloc[i].name , ' : ',  sg)
        pass
        


print('\n\n')



#for i in not_recovered: 
#  print('\n',i, col0[i], links[not_recovered.index(i)])#file.iloc[i]['tNames'], links[not_recovered.index(i)])
