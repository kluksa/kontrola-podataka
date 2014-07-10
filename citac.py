# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 08:01:06 2014

@author: velimir
"""

import pandas as pd
import re

def test_frames(frames1,frames2):
    ukupno = True
    if len(frames1.keys()) == len(frames2.keys()):
        print('OK!, isti broj frejmova')
        ukupno = ukupno and True
    else:
        print('ERROR!, broj frejmova ne odgovara')
        ukupno = ukupno and False
        
    f1=list(frames1.keys())
    f2=list(frames2.keys())
    for frame in f1:
        if frame in f2:
            print('OK!, {0} frame je u obje liste'.format(frame))
            ukupno = ukupno and True
        else:
            print('ERROR!, {0} nije u drugoj listi'.format(frame))
            ukupno = ukupno and False
    if ukupno:
        print('Test OK!')
    else:
        print('Error!')

class WlReader:

#    def __init__(self):
#        self.kanali = {'SO2':'1-SO2-ppb',
#                       'CO':'30-CO-ppm',}
#        """
#        key:regex pattern to match it
#        
#        pretpostavka je da je naziv kompaktan i da sadrži:
#        ime plina i mjernu jedinicu
#
#	pattern je 
#	[0-9]+-xxx-yyy
#
#        """
#        self.regexKanali={'SO2-ug/m3':r'\b\S*so2\S*ug/m3\b',
#                          'NO-ug/m3':r'\b\S*no\S*ug/m3\b',
#                          'NOx-ug/m3':r'\b\S*nox\S*ug/m3\b',
#                          'NO2-ug/m3':r'\b\S*no2\S*ug/m3\b',
#                          'CO-mg/m3':r'\b\S*co\S*mg/m3\b',
#                          'O3-ug/m3':r'\b\S*o3\S*ug/m3\b',
#                          'PM1-ug/m3':r'\b\S*pm1\S*ug/m3\b',
#                          'PM2.5-ug/m3':r'\b\S*(pm2\.5)\S*ug/m3\b',
#                          'PM10-ug/m3':r'\b\S*pm10\S*ug/m3\b'}
#
#    def set_kanali_za_citanje(self, mapa):
#        self.kanali = mapa
#        
#    def dodaj_kanal(self,kljuc,kanal):
#        if kljuc not in self.kanali.keys():
#            self.kanali[kljuc]=kanal
#        else:
#            raise KeyError('Unable to create new key, it already exists')
#   
#    def brisi_kanal(self,dkey):
#        del self.kanali[dkey]

    def citaj(self, path):
        """
        Cita iz CSV filea u data frame objekte
        struktura csv, (sve u uglatim zagradama je opcionalno):
        Name,[status],[flag], ... , NameX,[statusX],[flagx],Flag,Zone
        """
        df = pd.read_csv(
            path,
            na_values = '-999.00',
            index_col = 0,
            parse_dates = [[0,1]],
            dayfirst = True,
            header = 0,
            sep = ',',
            encoding = 'latin-1')
        
        dfShort = df.iloc[:,:-2]
        frejmovi = {}
        indeks = dfShort.index
        defaultSeries = pd.Series(0, index = indeks)
    
        for colName in dfShort:
            match1 = re.search(r'status', colName, re.IGNORECASE)
            match2 = re.search(r'flag', colName, re.IGNORECASE)
            #statusna var, sadrzi prethodno upisani kljuc
            pName = None
            if (not match1) and (not match2):
                pName = colName
                frejmovi[pName] = pd.DataFrame({
                    u'koncentracija':dfShort.loc[:,colName],
                    u'status':defaultSeries,
                    u'flag':defaultSeries},
                    columns =[u'koncentracija',u'status',u'flag'])
            
            if match1 and (pName != None):
                frejmovi[pName][u'status'] = dfShort.loc[:,colName]
            
            if match2 and (pName != None):
                frejmovi[pName][u'flag'] = dfShort.loc[:,colName]
        
        #dodaj flag i zone na u dictionary (kao pandas dataframe objekte)
        frejmovi[u'Flag'] = pd.DataFrame({u'Flag':df.loc[:,u'Flag']})
        frejmovi[u'Zone'] = pd.DataFrame({u'Zone':df.loc[:,u'Zone']})
    
        return frejmovi        
        
    #writer metoda
    def save_work(self,frejmovi,filename):
        """
        funkcija sprema niz frejmova u jedan csv file
        -flag i Zone se moraju dodati na kraju 
        
        konzistencija
        -u pisanju u csv moram rastaviti date_time u 2 stupca da bih mogao koristiti
        istu metodu citaj (u protivnom, citaj "pojede" prvi stupac)
        """
        keys = list(frejmovi.keys())
        for key in keys:
            if (key != u'Flag') and (key != u'Zone'):
                validKey = key
    
        indeks = frejmovi[validKey].index
    
        """
        objasnjenje za skalameriju ispod...
        citac se lomi prilikom citanja saveanog filea zbog tretiranja prvog stupca, tj.
        indeksa. Moram razdvojiti datetime index u date i time stupce...
        """
        datumFix = pd.DataFrame(
            {u'Date':pd.Series(0,index = indeks),
             u'Time':pd.Series(0,index = indeks)},
            index = indeks)
        #ova for petlja pojede jako puno vremena u odnosu na ostatak (priblizno 90%)
        for row in range(len(datumFix.index)):
            datumFix.iloc[row,0] = datumFix.index[row].strftime('%d/%m/%Y')
            datumFix.iloc[row,1] = datumFix.index[row].strftime('%H:%M:%S')
    
        i=1
        for key in keys:
            if (key != u'Flag') and (key != u'Zone'):
                dfTemp = frejmovi[key]
                dfTemp.columns = [key, u'status.{0}'.format(i), u'flag.{0}'.format(i)]
                i += 1
                datumFix = datumFix.join(dfTemp, how='outer')

        #dodaj kljuceve 'Flag', 'Zone'
        datumFix = datumFix.join(frejmovi[u'Flag'], how='outer')
        datumFix = datumFix.join(frejmovi[u'Zone'], how='outer')

        #napisi csv file, bez indeksa
        datumFix.to_csv(filename,
                        na_rep = '-999.00',
                        sep = ',',
                        encoding = 'latin-1',
                        index = False)

    
    def load_work(self,filename):
        """
        cita csv, nakon popravka citaca, ne treba drugu metodu
        """
        frejmovi = self.citaj(filename)
        return frejmovi
#        df=pd.read_csv(
#                    filename,
#                    na_values='-999.00',
#                    index_col=0,
#                    parse_dates=True,
#                    header=0,
#                    sep=',',
#                    encoding='latin-1'
#                    )
#        
#        #sastavljanje frejmova
#        reFlag='status'
#        reStatus='flag'
#        cols=list(df.columns)
#        frejmovi={}
#        keyList=[]
#        for col in cols:
#            match1=re.search(reFlag,col,re.IGNORECASE)
#            match2=re.search(reStatus,col,re.IGNORECASE)
#            #col ne smije matchati niti 'flag' niti 'status'            
#            if (not(match1 or match2)):
#                #col je key
#                keyList.append(col)
#                i=df.columns.get_loc(col)
#                frejmovi[col] = df.iloc[:,i:i+3]
#                tmp=frejmovi[col].columns.values
#                tmp[0]=u'koncentracija'
#                tmp[1]=u'status'
#                tmp[2]=u'flag'
#                frejmovi[col].columns=tmp
#        return frejmovi

    def citaj_listu(self,lista):
        """
        Cita cijelu listu element po element, dodajuci ucitane podatke na jedan
        dataframe.
        -koristi funkciju citaj za citanje jednog elementa
        -spaja datafrejmove po indeksu i svim stupcima
        """
        izlaz={}
        for element in lista:
            frejmovi=self.citaj(element)
            for kljuc in list(frejmovi.keys()):
                if kljuc not in izlaz:
                    izlaz[kljuc]=frejmovi[kljuc]
                else:
                    izlaz[kljuc]=izlaz[kljuc].combine_first[frejmovi[kljuc]]
#                    izlaz[kljuc]=pd.merge(
#                        izlaz[kljuc],
#                        frejmovi[kljuc],
#                        left_index=True,
#                        right_index=True,
#                        how='outer',
#                        on=[u'koncentracija',u'status',u'flag'],
#                        sort=True)
        return izlaz
     
            
if __name__ == "__main__":
    sanity=WlReader()
    data = sanity.citaj('pj.csv')
    sanity.save_work(data,'test_save_work.csv')
    data1 = sanity.load_work('test_save_work.csv')
    test_frames(data,data1)
    
    #data = WlReader().citaj('pj.csv')   
    #save to file
    #WlReader().save_work(dataframe,filename as string)
    #load from csv
    #frejmovi,kljucevi=WlReader().load_work(filename as string)
