## Sid Meier's Civilization 4
## Copyright Firaxis Games 2005
from CvPythonExtensions import *
#import string
#from time import time
#from copy import deepcopy
from threading import Timer
import re

import CvUtil
from CvWBDesc import CvPlayerDesc
import Popup as PyPopup
import ScreenInput
import CvScreenEnums
import CvScreensInterface

# For overriding
import CvGameInterface
import CvGameUtils
import CvEventInterface

import ModUpdater

# globals
gc = CyGlobalContext()
ArtFileMgr = CyArtFileMgr()
localText = CyTranslator()

# Substitute {A:B} with A or B
def mehrzahl(text, val):
    m = r"\2"
    if int(val) == 1:
        m = r"\1"
    return re.sub("{([^:]*):([^}]*)}", m, text)

class CvModUpdaterScreen:

    def __init__(self):
        self.mode = "start"

        self.MOD_UPDATER_SCREEN_NAME = "ModUpdaterScreen"
        self.INTERFACE_ART_INFO = "SCREEN_BG_OPAQUE"

        self.WIDGET_ID = "ModUpdaterWidget"
        self.BG_DDS_NAME = "ModUpdaterBG"
        self.PANEL_NAME = "ModUpdaterPanel"

        self.BORDER = 60
        # self.HEADLINE_HEIGHT = 55  # Main menu height
        # self.Y_TITLE = 8
        self.HEADLINE_HEIGHT = 40
        self.Y_TITLE = 4

        self.X_EXIT = 994
        self.Y_EXIT = 730

        self.nWidgetCount = 0

        self.ID_OFFSET = 22222
        self.events = {
            "start": 0,
            "set_startup_search": 1,
            "search": 3,
            "update": 4,
            "exit": 10,
            }
        self.mode_background_heights = {
                "start": 3 * 30,
                "info_none": 2 * 30,
                "info_fail": 3 * 30,
                "info_up_to_date": 1 * 30,
                }
                
        self.updater = ModUpdater.ModUpdater()
        
        self.BULLET = "-"
        self.MOD_NAME = u"<font=3>" + self.updater.get_mod_name() + "</font>"

    def getScreen(self):
        return CyGInterfaceScreen(self.MOD_UPDATER_SCREEN_NAME, CvScreenEnums.MODUPDATER_SCREEN)

    def showScreen(self, bForce=False):
        self.initScreen()
        screen = self.getScreen()
        self.deleteAllWidgets()
        bNotActive = (not screen.isActive())
        if bNotActive or bForce:
            self.setCommonWidgets()

    def initScreen(self):

        if self.updater.check_for_updates():
            if self.updater.has_pending_updates():
                self.mode = "info_avail_updates"
            else:
                 self.mode = "info_up_to_date"
        else:
            self.mode = "info_none"

        # Optional. Allow http-Links as pedia link targets
        #self.wrap_pedia_method()

    def setCommonWidgets(self):

        screen = self.getScreen()
        #screen = CyGInterfaceScreen( "MainInterface", CvScreenEnums.MAIN_INTERFACE )
        # Bildschirm-Auflösung
        self.SCREEN_RES = [screen.getXResolution(), screen.getYResolution()]
        # Abmaße des nicht verdeckbaren Hauptmenüs
        self.MAIN_MENU_RES = [700, 400]

        # Rechteck für Menu in der Form [X,Y,W,H]
        self.MOD_MENU_DIM = [
            self.SCREEN_RES[0]-250,
            25,
            250,
            self.SCREEN_RES[1] - 200
        ]


        nU = len(self.updater.PendingUpdates)
        # print("Num of available updates: %d" % (nU,))
        # This fails (C++ Exception) at early initialisation stages of Civ4!
        # CyTranslator.getText can not handle variables until the main menu is shown...
        #self.UPDATER_AVAIL = u"<font=3>" + localText.getText("TXT_KEY_UPDATER_AVAIL", (nU,)).upper() + "</font>"
        # As workaround, create string by hand
        avail_txt = localText.getText("TXT_KEY_UPDATER_AVAIL_WORKAROUND", ())
        self.UPDATER_AVAIL = u"<font=3>%d %s</font>" % (nU, mehrzahl(avail_txt, nU).upper(),)

        # Create a new screen
        screen = self.getScreen()
        screen.setRenderInterfaceOnly(False);
        screen.setScreenGroup(0) # ?
        # Similar to CvPediaMain.py
        #screen.setRenderInterfaceOnly(True)
        #screen.setPersistent(True) # nix
        #screen.showWindowBackground( False )
        screen.showScreen(PopupStates.POPUPSTATE_IMMEDIATE, False)

        # Hintergrund-Höhe von Text unter der Headline.
        body_height = 0 * 30
        if self.mode == "info_avail_updates":
            body_height = (nU + 1) * 30
        elif self.mode in self.mode_background_heights:
            body_height = self.mode_background_heights[self.mode]

        bg_height = body_height + self.HEADLINE_HEIGHT

        screen.addDDSGFC(self.BG_DDS_NAME, ArtFileMgr.getInterfaceArtInfo("SCREEN_BG_OPAQUE").getPath(),
                         self.MOD_MENU_DIM[0], self.MOD_MENU_DIM[1], self.MOD_MENU_DIM[2], bg_height,
                         WidgetTypes.WIDGET_GENERAL, -1, -1 )

        # Hintergrund von Headline
        screen.addPanel(self.PANEL_NAME, u"", u"", True, False,
                        self.MOD_MENU_DIM[0], self.MOD_MENU_DIM[1], self.MOD_MENU_DIM[2], self.HEADLINE_HEIGHT,
                        PanelStyles.PANEL_STYLE_TOPBAR )


        if self.mode == "start":
            screen.setText(self.getNextWidgetName(), "Background", self.MOD_NAME, CvUtil.FONT_CENTER_JUSTIFY,
                    self.MOD_MENU_DIM[0] + self.MOD_MENU_DIM[2]/2, self.MOD_MENU_DIM[1] + self.Y_TITLE, 0, FontTypes.TITLE_FONT,
                    WidgetTypes.WIDGET_GENERAL, self.ID_OFFSET+self.events["search"], -1)
            textPos = [self.MOD_MENU_DIM[0] + 20, self.MOD_MENU_DIM[1] + self.HEADLINE_HEIGHT + 0*20]
            multiHeight = 2 * 30 # == body_height - 30
            screen.addMultilineText(self.getNextWidgetName(), localText.getText("TXT_KEY_UPDATER_SEARCH2", ()),
                    textPos[0], textPos[1], self.MOD_MENU_DIM[2] - 40, multiHeight,
                    WidgetTypes.WIDGET_GENERAL,
                    self.ID_OFFSET+self.events["start"], -1, CvUtil.FONT_LEFT_JUSTIFY)
            textPos[1] += multiHeight
            if 0 != int(self.updater.get_config().get("check_at_startup", 0)):
                screen.setText(self.getNextWidgetName(), "Background", self.UPDATER_STARTUP_DISABLE, CvUtil.FONT_LEFT_JUSTIFY,
                        textPos[0], textPos[1], 0, FontTypes.TITLE_FONT,
                        WidgetTypes.WIDGET_GENERAL, self.ID_OFFSET+self.events["set_startup_search"], 0)
            else:
                screen.setText(self.getNextWidgetName(), "Background", self.UPDATER_STARTUP_ENABLE, CvUtil.FONT_LEFT_JUSTIFY,
                        textPos[0], textPos[1], 0, FontTypes.TITLE_FONT,
                        WidgetTypes.WIDGET_GENERAL, self.ID_OFFSET+self.events["set_startup_search"], 1)


        if self.mode == "info_avail_updates":
            screen.setText(self.getNextWidgetName(), "Background", self.UPDATER_AVAIL, CvUtil.FONT_CENTER_JUSTIFY,
                    self.MOD_MENU_DIM[0] + self.MOD_MENU_DIM[2]/2, self.MOD_MENU_DIM[1] + self.Y_TITLE, 0, FontTypes.TITLE_FONT,
                    WidgetTypes.WIDGET_GENERAL, self.ID_OFFSET+self.events["start"], -1)

            textPos = [self.MOD_MENU_DIM[0] + 20, self.MOD_MENU_DIM[1] + self.HEADLINE_HEIGHT + 0*20]
            for u in self.updater.PendingUpdates:
                u_text = u"<font=3>%s %s</font>" % (self.BULLET, u["name"])
                screen.setLabel(self.getNextWidgetName(), "Background", u_text, CvUtil.FONT_LEFT_JUSTIFY,
                                textPos[0], textPos[1], 0, FontTypes.TITLE_FONT,
                                WidgetTypes.WIDGET_GENERAL, -1, -1)
                textPos[1] += 30

            screen.setText(self.getNextWidgetName(), "Background", localText.getText("TXT_KEY_UPDATER_START", ()), CvUtil.FONT_CENTER_JUSTIFY,
                        self.MOD_MENU_DIM[0] + self.MOD_MENU_DIM[2]/2, textPos[1], 0, FontTypes.TITLE_FONT,
                        WidgetTypes.WIDGET_GENERAL, self.ID_OFFSET+self.events["update"], 0)


        if self.mode == "info_up_to_date":
            screen.setText(self.getNextWidgetName(), "Background", self.MOD_NAME, CvUtil.FONT_CENTER_JUSTIFY,
                        self.MOD_MENU_DIM[0] + self.MOD_MENU_DIM[2]/2, self.MOD_MENU_DIM[1] + self.Y_TITLE, 0, FontTypes.TITLE_FONT,
                        WidgetTypes.WIDGET_GENERAL, self.ID_OFFSET+self.events["exit"], 0)
            textPos = [self.MOD_MENU_DIM[0] + 20, self.MOD_MENU_DIM[1] + self.HEADLINE_HEIGHT + 0*20]
            screen.addMultilineText(self.getNextWidgetName(), localText.getText("TXT_KEY_UPDATER_NONE", ()),
                    textPos[0], textPos[1], self.MOD_MENU_DIM[2] - 40, body_height,
                    WidgetTypes.WIDGET_GENERAL,
                    self.ID_OFFSET+self.events["start"], -1, CvUtil.FONT_LEFT_JUSTIFY)


        if self.mode == "info_none":
            screen.setText(self.getNextWidgetName(), "Background", self.MOD_NAME, CvUtil.FONT_CENTER_JUSTIFY,
                        self.MOD_MENU_DIM[0] + self.MOD_MENU_DIM[2]/2, self.MOD_MENU_DIM[1] + self.Y_TITLE, 0, FontTypes.TITLE_FONT,
                        WidgetTypes.WIDGET_GENERAL, self.ID_OFFSET+self.events["exit"], 0)
            textPos = [self.MOD_MENU_DIM[0] + 20, self.MOD_MENU_DIM[1] + self.HEADLINE_HEIGHT + 0*20]
            screen.addMultilineText(self.getNextWidgetName(), localText.getText("TXT_KEY_UPDATER_NO_INFO", ()),
                    textPos[0], textPos[1], self.MOD_MENU_DIM[2] - 40, body_height,
                    WidgetTypes.WIDGET_GENERAL,
                    self.ID_OFFSET+self.events["start"], -1, CvUtil.FONT_LEFT_JUSTIFY)


        if self.mode == "info_fail":
            screen.setText(self.getNextWidgetName(), "Background", self.MOD_NAME, CvUtil.FONT_CENTER_JUSTIFY,
                        self.MOD_MENU_DIM[0] + self.MOD_MENU_DIM[2]/2, self.MOD_MENU_DIM[1] + self.Y_TITLE, 0, FontTypes.TITLE_FONT,
                        WidgetTypes.WIDGET_GENERAL, self.ID_OFFSET+self.events["start"], 0)
            textPos = [self.MOD_MENU_DIM[0] + 20, self.MOD_MENU_DIM[1] + self.HEADLINE_HEIGHT + 0*20]
            visit_url = self.updater.get_config().get("visit_url", "")
            failText = localText.getText("TXT_KEY_UPDATER_FAILED", (visit_url,))
            screen.addMultilineText(self.getNextWidgetName(), failText,
                    textPos[0], textPos[1], self.MOD_MENU_DIM[2] - 40, body_height,
                    WidgetTypes.WIDGET_GENERAL,
                    self.ID_OFFSET+self.events["start"], -1, CvUtil.FONT_LEFT_JUSTIFY)


        if self.mode == "updating":
            screen.setText(self.getNextWidgetName(), "Background", localText.getText("TXT_KEY_UPDATER_RUN", ()), CvUtil.FONT_CENTER_JUSTIFY,
                        self.MOD_MENU_DIM[0] + self.MOD_MENU_DIM[2]/2, self.MOD_MENU_DIM[1] + self.Y_TITLE, 0, FontTypes.TITLE_FONT,
                        WidgetTypes.WIDGET_GENERAL, self.ID_OFFSET+self.events["exit"], 0)


    # returns unique ID for a widget in this screen
    def getNextWidgetName(self):
        szName = self.WIDGET_ID + str(self.nWidgetCount)
        self.nWidgetCount += 1
        return szName

    def deleteAllWidgets(self, startid=-1):
        screen = self.getScreen()
        iNumWidgets = self.nWidgetCount
        if startid == -1:
            screen.deleteWidget(self.BG_DDS_NAME)
            screen.deleteWidget(self.PANEL_NAME)
            startid = 0

        self.nWidgetCount = startid
        for i in range(startid, iNumWidgets):
            screen.deleteWidget(self.getNextWidgetName())

        self.nWidgetCount = startid # getNextWidgetName has increased val..

    def hideAllWidgets(self):
        screen = self.getScreen()
        iNumWidgets = self.nWidgetCount
        self.nWidgetCount = 0
        screen.hide(self.BG_DDS_NAME)
        screen.hide(self.PANEL_NAME)
        for i in range(iNumWidgets):
            screen.hide(self.getNextWidgetName())

    def redraw(self):
        self.initScreen()
        self.hideAllWidgets()

        screen = self.getScreen()
        screen.show(self.BG_DDS_NAME)
        screen.show(self.PANEL_NAME)

        nWidgetCount_Back = self.nWidgetCount
        self.nWidgetCount = 0
        self.setCommonWidgets()
        if nWidgetCount_Back > self.nWidgetCount:
            print("CvModUpdaterScreen: Old widgets still active... Could cause drawing issues.")
            #self.deleteAllWidgets(self.nWidgetCount)

    def handleClick(self, val1, val2):
        # self._handleClick_(val1, val2)
        pass

    def _handleClick_(self, val1, val2):
        screen = self.getScreen()
        if val1 == self.events["start"]:
            self.mode = "start"
            self.deleteAllWidgets()
            self.redraw()
            return
        if val1 == self.events["exit"]:
            self.mode = "start"
            screen.hideScreen()
            self.deleteAllWidgets()  # Clear because mode was changed
            return
        elif val1 == self.events["search"]:
            self.updater.Config = None  # Force re-read of json-file
            if self.updater.check_for_updates():
                if self.updater.has_pending_updates():
                    self.mode = "info_avail_updates"
                else:
                    self.mode = "info_up_to_date"
            else:
                self.mode = "info_none"

            self.deleteAllWidgets()  # Clear because mode was changed
            self.redraw()

        elif val1 == self.events["update"]:
            self.mode = "updating"
            status = self.updater.start_update()
            if status["successful"]:
                self.mode = "info_up_to_date"
                screen.hideScreen()
                self.deleteAllWidgets()  # Clear because mode was changed
                show_popup(localText.getText("TXT_KEY_UPDATER_SUCCESSFUL", ()))
                self.show_info_popups(status)
            else:
                self.mode = "info_fail"
                self.deleteAllWidgets()  # Clear because mode was changed
                self.redraw()
                show_popup(localText.getText("TXT_KEY_UPDATER_FAILED_POPUP", ()))

        elif val1 == self.events["set_startup_search"]:
            self.updater.get_config()["check_at_startup"] = val2
            self.updater.write_config()
            self.redraw()

  # Will handle the input for this screen...
  # Achtung, das funktioniert für WIDGET_GENERAL NICHT vor dem Laden eines Spiels(?!)
  # Nutze handleClick und den Umweg über WIDGET_PEDIA_DESCRIPTION_NO_HELP
    def handleInput (self, inputClass):
        iNotifyCode = inputClass.getNotifyCode()
        # show_popup("HandleInput called")
        if inputClass.getNotifyCode() == NotifyCode.NOTIFY_CLICKED:
            if( inputClass.getData1() >= self.ID_OFFSET and
                    inputClass.getData1() < self.ID_OFFSET + 100 ):
                #show_popup("HandleInput called for event 0")
                self._handleClick_(
                        inputClass.getData1() - self.ID_OFFSET,
                        inputClass.getData2())

        return 1

    def show_info_popups(self, update_status):
        for i in range(len(update_status["updates"])-1, -1, -1):
            desc = update_status["updates"][i]["info"].get("desc")
            if desc and len(desc) > 0:
                #show_popup(str(desc.encode("utf-8")))  # Error Popup.py
                show_popup(desc) # type(desc) is unicode

    def wrap_pedia_method(self):
        # Wrap CvPediaMain.link method with own code to detect html links
        CvScreensInterface.pediaMainScreen.link_orig = CvScreensInterface.pediaMainScreen.link
        def __link__(szLink):
            if szLink.strip().startswith("http"):
                CvUtil.pyPrint("Visit link: " + str(szLink))
                import webbrowser
                webbrowser.open(szLink)
                return
            return CvScreensInterface.pediaMainScreen.link_orig(szLink)
        CvScreensInterface.pediaMainScreen.link = __link__

    def update(self, fDelta):
        return


def show_popup(text):
    popup = PyPopup.PyPopup()
    popup.setHeaderString("Mod Updater")
    popup.setBodyString(text)
    # popup.setBodyString("more text...")
    popup.launch()

