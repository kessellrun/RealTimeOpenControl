import os
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5 import QtCore
import time

from data.scriptHelpWidget import ScriptHelpWidget
from data.scriptSubWidget import ScriptSubWidget

class ScriptWidget(QtWidgets.QWidget):
    def __init__(self, logger):
        super(ScriptWidget, self).__init__()
        uic.loadUi("data/ui/scriptWidget.ui", self)

        self.logger = logger
        self.scripts = []
        self.activeScript = 0

        self.help = ScriptHelpWidget(self)
        self.help.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self.loadScriptButton.clicked.connect(self.loadScriptAction)
        self.saveScriptButton.clicked.connect(self.saveScriptAction)
        self.helpButton.clicked.connect(self.toggleHelpAction)
        self.tabWidget.currentChanged.connect(self.changeActiveScript)

    def openFile(self, fileName):
        if os.path.exists(fileName):
            try:
                with open(fileName, "r") as file:
                    text = file.read()
                head, tail = os.path.split(fileName)
                self.openScript(text,tail, fileName)
                self.logger.config["lastScript"]=fileName
            except:
                self.openScript(self.tr("Fehler beim laden der Datei ")+fileName,self.tr("Fehler"), "")
                self.logger.config["lastScript"]=""
        else:
            self.openScript(self.tr("Datei ")+fileName+ self.tr(" nicht gefunden"),self.tr("Fehler"), "")

    def openScript(self, scriptstr = "", name = "", filepath = ""):
        self.scripts.append(ScriptSubWidget(self.logger, scriptstr, filepath))
        self.scripts[-1].modifiedCallback = self.scriptModifiedCallback
        self.tabWidget.insertTab(len(self.scripts)-1, self.scripts[len(self.scripts)-1], name)
        self.tabWidget.setCurrentIndex(len(self.scripts)-1)

    def scriptModifiedCallback(self, edited, newtext=None):
        if edited:
            text = self.tabWidget.tabText(self.activeScript)+"*"
            self.tabWidget.setTabText(self.activeScript,text)
        else:
            if newtext!=None:
                text=newtext
            else:
                text = self.tabWidget.tabText(self.activeScript)[:-1]
            self.tabWidget.setTabText(self.activeScript,text)

    def closeScript(self, idx):
        if idx < len(self.scripts):
            self.scripts[idx].close()
            if self.scripts[idx].run == False:
                self.tabWidget.removeTab(idx)
                self.scripts.pop(idx)
                if len(self.scripts)==0:
                    self.openScript("", self.tr("Unbenannt"))

    def changeActiveScript(self):
        self.activeScript = self.tabWidget.currentIndex()
        if self.activeScript == len(self.scripts):
            self.openScript("", self.tr("Unbenannt"))

    def addTextToScriptEdit(self, strung):
        self.scripts[self.activeScript].addTextToScriptEdit(strung)

    def saveScriptAction(self):
        self.scripts[self.activeScript].saveScript()

    def loadScriptAction(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        fileBrowser = QtWidgets.QFileDialog(self)
        fileBrowser.setDirectory(dir_path)
        fileBrowser.setNameFilters(["Python (*.py)"])
        fileBrowser.selectNameFilter("")
        fname, mask = fileBrowser.getOpenFileName(
            self, self.tr("Skript laden"), dir_path, "Python (*.py)")
        # if fileBrowser.exec_():
        if fname:
            fileName = fname
            if mask == 'Python (*.py)':
                text = ""
                with open(fileName, "r") as file:
                    text = file.read()
                head, tail = os.path.split(fileName)
                self.openScript(text,tail, fileName)
                self.logger.config["lastScript"]=fileName

    def toggleHelpAction(self):
        if self.helpButton.isChecked():
            self.help.show()
        else:
            self.help.hide()

    def updateListWidget(self):
        self.help.updateListWidget()
        for script in self.scripts:
            script.triggerWidget.triggerSignals.clear()
            for element in self.logger.signalNames:
                script.triggerWidget.triggerSignals.addItem(".".join(element))

    def executedCallback(self, ok, text):
        self.scripts[0].executedCallback(ok, text)

    def triggeredScriptCallback(self, devicename, signalname):
        for script in self.scripts:
            if script.triggerMethod == "signal":
                script.handleScript(devicename, signalname)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        quitAction = menu.addAction(self.tr("Schließen"))
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == quitAction:
            self.closeScript(self.activeScript)

    def clear(self):
        # self.scriptEdit.clear()
        self.help.signalListWidget.clear()
        for script in self.scripts:
            script.triggerWidget.triggerSignals.clear()
        self.updateListWidget()

    def closeEvent(self, event):
        for script in self.scripts:
            #script.run=False
            script.close()
            if script.run == True:
                break;