import os

import tables
import pyfits
import sys

def Enhance(cls,kw):
    for k,v in kw:
        print k,v
        cls.columns[k] = eval(v)

def UnEnhance(cls):
    cls.columns = {}

FITSNAME = '/media/980d0181-4160-4bbf-8c3d-3d370f24fefd/data/AGBT10C_045_01/AGBT10C_045_01.raw.acs.fits'

# get a handle to the fits file
fitsfile = pyfits.open(FITSNAME, memmap=1, mode='readonly')

# change the extension of the fits file to h5 for the new output name
base,ext = os.path.splitext(os.path.basename(FITSNAME))
h5name = '.'.join((base,'h5'))

class TableData(tables.IsDescription):
    pass

colname = False
coltype = False
coldefs = []

def h5type(fitstype):
    if fitstype.endswith('L'):
        return 'tables.BoolCol()'
    elif fitstype.endswith('B'):
        return 'tables.UInt8Col()'
    elif fitstype.endswith('I'):
        return 'tables.Int16Col()'
    elif fitstype.endswith('J'):
        return 'tables.Int32Col()'
    elif fitstype.endswith('A'):
        colsize = fitstype[:-1]
        return 'tables.StringCol('+colsize+')'
    elif fitstype.endswith('E'):
        colsize = (fitstype[:-1])
        return 'tables.Float32Col(shape='+colsize+')'
    elif fitstype.endswith('D'):
        return 'tables.Float64Col()'
    elif fitstype.endswith('C'):
        return 'tables.ComplexCol()'
    elif fitstype.endswith('M'):
        return 'tables.ComplexCol()'
    elif fitstype.endswith('P'):
        return ''
    elif fitstype.endswith('X'):
        return ''
    else:
        print 'ERROR: UNSUPPORTED type',fitstype
        return ''
  
# create the hdf5 output file
h5file = tables.openFile( h5name, mode='w', title='' )
root = h5file.root

for extension in fitsfile:
    UnEnhance(TableData)
    print '----------------------------------------'
    print extension.name
    print '----------------------------------------'
    cards = extension.header.ascardlist()
    for card in cards:
        if card.key.startswith('TTYPE'):
            colname = card.value#.replace('-','_')
        elif card.key.startswith('TFORM'):
            coltype = h5type(card.value)
        if colname and coltype:
            print colname,card.value
            coldefs.append([colname,coltype])
            colname = False
            coltype = False

    print coldefs
    if coldefs:
        Enhance(TableData,coldefs)
        tablename = extension.name.lower().replace(' ','')
        table = h5file.createTable( root, tablename, TableData, extension.name )

        coldefs = []
        
        for card in cards:
            if not (card.key.startswith('TTYPE') or
                    card.key.startswith('TFORM') or
                    card.key.startswith('TUNIT') ):
                table.setAttr(card.key,card.value)

        for name in table.attrs._v_attrnames:
            print 'name: %s, value: %s' % (name,table.getAttr(name))
        
        for idx,fitsrow in enumerate(extension.data):
            for name in table.colnames:
                spectrum = table.row
                spectrum[name] = fitsrow[name]
            spectrum.append()
            if idx%500 == 0:
                table.flush()
        table.close()

print h5file

h5file.close()
fitsfile.close()
