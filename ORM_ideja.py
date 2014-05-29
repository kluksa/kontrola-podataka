# -*- coding: utf-8 -*-
"""
Created on Thu May 29 08:10:43 2014

@author: velimir

DB/ORM pristup spremanju podataka u jedan lokalni file.
"""

import citac

from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy import Sequence
from sqlalchemy import func
from sqlalchemy import Column, Integer, String, DateTime, Float

from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

#alternativna deklaracija
#engine = create_engine('sqlite:///foo.db')
#engine = create_engine('sqlite:////absolute/path/to/foo.db')

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()

#ORM class declaration
class Stanica(Base):
    __tablename__ = 'stanice'
    id = Column(Integer, Sequence('stanica_id_seq'), primary_key=True)
    ime = Column(String(50), unique=True, nullable=False)
    lokacija = Column(String(100),nullable=False)
    
    def __repr__(self):
        return "<Stanica(id={0}, ime={1}, lokacija={2})>"\
        .format(self.id, self.ime, self.lokacija)


class Mjerenje(Base):
    __tablename__ = 'mjerenja'
    id = Column(Integer, Sequence('mjerenje_id_seq'), primary_key=True)
    ime = Column(String(30),nullable=False)
    stanica_id = Column(Integer, ForeignKey('stanice.id'))
    
    stanica = relationship("Stanica",backref=backref('mjerenja',lazy='joined'))
    
    def __repr__(self):
        return "<Mjerenje(id={0}, ime={1}, stanica_id={2})>"\
        .format(self.id, self.ime, self.stanica_id)


class Podatak(Base):
    __tablename__ = 'podaci'
    vrijeme = Column(DateTime, primary_key=True)
    vrijednost = Column(Float)
    status = Column(Float)
    flag = Column(Float)
    mjerenje_id = Column(Integer, ForeignKey('mjerenja.id'),primary_key=True)
    
    mjerenje = relationship("Mjerenje",backref=backref('podaci'))
    
    def __repr__(self):
        return "<Podatak(mjerenje_id={0}, vrijeme={1}, vrijednost={2})>"\
        .format(self.mjerenje_id, self.vrijeme, self.vrijednost)


#create tables...
Base.metadata.create_all(engine)

#testni primjer
#bind session factory to specific engine, and make a session instance
Session = sessionmaker(bind=engine)
session = Session()

#ucitaj podatke u pandas dataframe
data=citac.WlReader().citaj('pj.csv')
#napravi neku stanicu
pj=Stanica(ime='testna stanica',lokacija='negdje')
session.add(pj)
session.commit()

#napraviti mjerenja za stanicu (iz kljuceva dicta)
listaMjerenja = []
stanica = session.query(Stanica).filter(Stanica.ime=='testna stanica').one()

for kljuc in list(data.keys()):
    listaMjerenja.append(Mjerenje(ime=kljuc,stanica_id=stanica.id))
session.add_all(listaMjerenja)
session.commit()



#sada treba razvrstati podatke prema mjerenjima (S02, NOX, PM...)
for kljuc in list(data.keys()):
    df=data[kljuc]
    tempListaObjekata=[]
    #treba otkriti mjerenje_id za kombinaciju stanica-ključ
    mjerenje=session.query(Mjerenje).join(Stanica)\
    .filter(Stanica.ime==stanica.ime).filter(Mjerenje.ime==kljuc).one()
    #tocan id je mjerenje.id    
    
    for ind in list(df.index):
        tempListaObjekata.append(Podatak(vrijeme=ind,
                                         vrijednost=df.loc[ind,u'koncentracija'],
                                         status=df.loc[ind,u'status'],
                                         flag=df.loc[ind,u'flag'],
                                         mjerenje_id=mjerenje.id))
    session.add_all(tempListaObjekata)
    session.commit()


session.close()
#za daljne queryje... narpavi novu instancu sessiona