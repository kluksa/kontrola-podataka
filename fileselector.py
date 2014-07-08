# -*- coding: utf-8 -*-
"""
Created on Wed Jul  2 11:51:42 2014

@author: velimir
"""

from PyQt4 import QtGui, QtCore, uic
import sys, os

class FileSelector(QtCore.QAbstractListModel):
    """
    Model to hold filenames
    """
    def __init__(self,files=[],folder=None,parent=None):
        QtCore.QAbstractListModel.__init__(self,parent)    
        self.__files = files
        self.__folder = folder
    
    def rowCount(self,index):
        """
        returns the number of data in list
        """
        return len(self.__files)
    
    def data(self,index,role):
        """
        for each index and role returns specific value
        """
        if role == QtCore.Qt.ToolTipRole:
            return "Doubleclick to open file or expand folder"
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            return str(self.__files[row])
        if role == QtCore.Qt.DecorationRole:
            row = index.row()
            fullName = os.path.join(str(self.__folder), str(self.__files[row]))
            if os.path.isdir(fullName):
                #directory decoration
                icon = QtGui.QIcon("folder.png")
                return icon
            if os.path.isfile(fullName):
                #file decoration
                if len(fullName) >= 4:
                    if fullName[-3:] == "csv":
                        icon = QtGui.QIcon("csv_file.png")
                        return icon
                    else:
                        icon = QtGui.QIcon("basic_file.png")
                        return icon
            if str(self._files[row]) == "...":
                #move to previous folder
                icon = QtGui.QIcon("document-icon.png")
                return icon
        
    def flags(self, index):
        """
        sets the flags of items, making them enabled and selectable
        """
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
    
#load the UI file with uic module
base, form = uic.loadUiType('fileview.ui')
class SelectorWindow(base, form):
    """
    Initialize gui window from ui file at runtime
    """
    def __init__(self, parent=None):
        super(base, self).__init__(parent)
        self.setupUi(self)
        
        #generic object for emiting signals
        self._sig = QtGui.QWidget()
        
        #make proxy model for sorting and filtering
        self._proxyModel = QtGui.QSortFilterProxyModel()
        self._proxyModel.setDynamicSortFilter(True)
        self._proxyModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        
        self._files = []
        self._folder = None
        
        #connections
        self.uiFilter.textChanged.connect(self._proxyModel.setFilterRegExp)
        self.uiListView.doubleClicked.connect(self.dbl_click_item)
        self.uiFolder.editingFinished.connect(self.get_files)
        
        #set the current directory to the same directory from wich application is running
        self.uiFolder.setText(str(os.path.dirname(sys.argv[0])))
        self.uiFolder.editingFinished.emit()
        
    def get_files(self):
        folder = str(self.uiFolder.text())
        
        if os.path.isdir(folder):
            self._files = []
            self._folder = folder
            for file in os.listdir(folder):
                self._files.append(str(file))
            sorted(self._files)
            #back one level
            self._upFolder = str(os.path.dirname(self._folder))
            #do not insert up folder if there is no parent folder            
            if self._folder != self._upFolder:
                self._files.insert(0,"...")
            
            """
            Connect the model to proxy model.
            Connect proxymodel to listview of our UI.
            """
            self._model = FileSelector(self._files, self._folder)
            self._proxyModel.setSourceModel(self._model)
            self.uiListView.setModel(self._proxyModel)
    
    def dbl_click_item(self, listViewItem):
        """
        NAvigation and selection of csv files
        """
        #case 1, clicked on '...'
        if listViewItem.data() == "...":
            self._folder = os.path.dirname(self._folder)
            self.uiFolder.clear()
            self.uiFolder.setText(self._folder)
            self.get_files()
        else:
            #case 2, clicked on folder
            directory = str(os.path.abspath(self._folder))
            clicked = os.path.join(directory, str(listViewItem.data()))
            if os.path.isdir(clicked):
                self._folder = clicked
                self.uiFolder.clear()
                self.uiFolder.setText(self._folder)
                self.get_files()
            #case 3, clicked on csv file
            if os.path.isfile(clicked) and clicked[-3:] == "csv":
                #implement a signal to transmit selection
                lista=[clicked]
                self._sig.emit(QtCore.SIGNAL('read-lista(PyQt_PyObject)'),lista)
                
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = SelectorWindow()
    window.show()
    sys.exit(app.exec_())