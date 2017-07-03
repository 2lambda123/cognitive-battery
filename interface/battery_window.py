import os
import sys
import random
import datetime
import pygame
import pandas as pd

from PyQt5 import QtCore, QtGui, QtWidgets
from utils import display
from designer import battery_window_qt
from interface import about_dialog, settings_window
from tasks import ant, mrt, sart, ravens, digitspan_backwards, sternberg


class BatteryWindow(QtWidgets.QMainWindow, battery_window_qt.Ui_CognitiveBattery):
    def __init__(self, base_dir, project_dir, res_width, res_height):
        super(BatteryWindow, self).__init__()

        # Setup the main window UI
        self.setupUi(self)

        # Set app icon
        self.setWindowIcon(QtGui.QIcon(os.path.join('images', 'icon_sml.png')))

        self.github_icon = os.path.join('images', 'github_icon.png')
        self.actionDocumentation.setIcon(QtGui.QIcon(self.github_icon))
        self.actionLicense.setIcon(QtGui.QIcon(self.github_icon))
        self.actionContribute.setIcon(QtGui.QIcon(self.github_icon))
        self.actionBrowse_Issues.setIcon(QtGui.QIcon(self.github_icon))
        self.actionReport_Bug.setIcon(QtGui.QIcon(self.github_icon))
        self.actionRequest_Feature.setIcon(QtGui.QIcon(self.github_icon))

        # Get screen resolution
        self.project_dir = project_dir
        self.res_width = res_width
        self.res_height = res_height

        # Create/open settings file with no registry fallback  
        self.settings_file = os.path.join(self.project_dir, "battery_settings.ini")
        self.settings = QtCore.QSettings(self.settings_file, QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)

        # If first run, store some default settings
        # FIXME this is messy when adding new tasks (see issue #16)
        if not os.path.isfile(self.settings_file):
            # Main window size and position
            self.save_main_window_settings(self.size(), QtCore.QPoint(100, 100))

            # Settings - Task Windows
            self.settings.beginGroup("TaskWindows")
            self.settings.setValue('fullscreen', "false")
            self.settings.setValue('borderless', "false")
            self.settings.setValue('width', 1280)
            self.settings.setValue('height', 1024)
            self.settings.endGroup()

            # Settings - Attentional Network Test
            self.settings.beginGroup("AttentionNetworkTest")
            self.settings.setValue('numBlocks', 3)
            self.settings.endGroup()

        # Set initial window size/pos from saved settings
        self.settings.beginGroup("MainWindow")
        self.resize(self.settings.value("size"))
        self.move(self.settings.value("pos"))
        self.settings.endGroup()

        # Initialize task settings
        self.task_fullscreen = None
        self.task_borderless = None
        self.task_width = None
        self.task_height = None

        # Keep reference to the about and settings window objects
        self.about = None
        self.settings_window = None

        # Initialize pygame screen
        self.pygame_screen = None

        # Define URLs
        self.LINKS = {
            "github": "https://github.com/sho-87/cognitive-battery",
            "license": "https://github.com/sho-87/"
                       "cognitive-battery/blob/master/LICENSE",
            "develop": "https://github.com/sho-87/"
                       "cognitive-battery/tree/develop",
            "issues": "https://github.com/sho-87/cognitive-battery/issues",
            "new_issue": "https://github.com/sho-87/"
                         "cognitive-battery/issues/new"
        }

        # Get base directory for battery
        self.base_dir = base_dir

        # Make data folder if it doesnt exist
        self.dataPath = os.path.join(self.project_dir, "data")
        if not os.path.isdir(self.dataPath):
            os.makedirs(self.dataPath)

        # Handle menu bar item click events
        self.actionExit.triggered.connect(self.close)
        self.actionSettings.triggered.connect(self.show_settings)
        self.actionDocumentation.triggered.connect(self.show_documentation)
        self.actionLicense.triggered.connect(self.show_license)
        self.actionContribute.triggered.connect(self.show_contribute)
        self.actionBrowse_Issues.triggered.connect(self.show_browse_issues)
        self.actionReport_Bug.triggered.connect(self.show_new_issue)
        self.actionRequest_Feature.triggered.connect(self.show_new_issue)
        self.actionAbout.triggered.connect(self.show_about)

        # Bind button events
        self.cancelButton.clicked.connect(self.close)
        self.startButton.clicked.connect(self.start)
        self.randomOrderCheck.clicked.connect(self.random_order_selected)
        self.selectAllButton.clicked.connect(self.select_all)
        self.deselectAllButton.clicked.connect(self.deselect_all)
        self.upButton.clicked.connect(self.move_up)
        self.downButton.clicked.connect(self.move_down)

    # Open web browser to the documentation page
    def show_documentation(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.LINKS["github"]))

    # Open web browser to the license page
    def show_license(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.LINKS["license"]))

    # Open web browser to the github develop branch for contribution
    def show_contribute(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.LINKS["develop"]))

    # Open web browser to the github issues page
    def show_browse_issues(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.LINKS["issues"]))

    # Open web browser to the github new issue post
    def show_new_issue(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.LINKS["new_issue"]))

    # Create a new SettingsWindow object and display it
    def show_settings(self):
        # If the settings window does not exist, create one
        if self.settings_window is None:
            self.settings_window = settings_window.SettingsWindow(self, self.settings)
            self.settings_window.show()
            self.settings_window.finished.connect(
                lambda: setattr(self, 'settings_window', None))
        # If settings window exists, bring it to the front
        else:
            self.settings_window.activateWindow()
            self.settings_window.raise_()

    # Create a new AboutDialog object and display it
    def show_about(self):
        # If the about dialog does not exist, create one
        if self.about is None:
            self.about = about_dialog.AboutDialog(self)
            self.about.show()
            self.about.finished.connect(lambda: setattr(self, 'about', None))
        # If about dialog exists, bring it to the front
        else:
            self.about.activateWindow()
            self.about.raise_()

    def error_dialog(self, message):
        QtWidgets.QMessageBox.warning(self, 'Error', message)

    def random_order_selected(self):
        if self.randomOrderCheck.isChecked():
            self.upButton.setEnabled(False)
            self.downButton.setEnabled(False)
            return True
        else:
            self.upButton.setEnabled(True)
            self.downButton.setEnabled(True)
            return False

    def select_all(self):
        for index in range(self.taskList.count()):
            self.taskList.item(index).setCheckState(2)

    def deselect_all(self):
        for index in range(self.taskList.count()):
            self.taskList.item(index).setCheckState(0)

    def move_up(self):
        current_row = self.taskList.currentRow()
        current_item = self.taskList.takeItem(current_row)
        self.taskList.insertItem(current_row - 1, current_item)
        self.taskList.setCurrentItem(current_item)

    def move_down(self):
        current_row = self.taskList.currentRow()
        current_item = self.taskList.takeItem(current_row)
        self.taskList.insertItem(current_row + 1, current_item)
        self.taskList.setCurrentItem(current_item)

    # Save window size/position to settings file
    def save_main_window_settings(self, size, pos):
        self.settings.beginGroup("MainWindow")
        self.settings.setValue('size', size)
        self.settings.setValue('pos', pos)
        self.settings.endGroup()

    # Get task window settings from file
    def get_settings(self):
        # Task window settings
        self.settings.beginGroup("TaskWindows")

        if self.settings.value("fullscreen") == "true":
            self.task_fullscreen = True
        else:
            self.task_fullscreen = False

        if self.settings.value("borderless") == "true":
            self.task_borderless = True
        else:
            self.task_borderless = False

        self.task_width = int(self.settings.value("width"))
        self.task_height = int(self.settings.value("height"))

        self.settings.endGroup()

        # ANT settings
        self.settings.beginGroup("AttentionNetworkTest")
        self.ant_blocks = int(self.settings.value("numBlocks"))
        self.settings.endGroup()

    # Override the closeEvent method
    def closeEvent(self, event):
        self.save_main_window_settings(self.size(), self.pos())
        
        event.accept()
        sys.exit(0)  # This closes any open pygame windows

    def start(self):
        # Store input values
        sub_num = self.subNumBox.text()
        condition = self.conditionBox.text()
        age = self.ageBox.text()
        ra = self.raBox.text()
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        if self.maleRadio.isChecked():
            sex = 'male'
        else:
            sex = 'female'

        # Get *selected* tasks and task order
        selected_tasks = []
        for index in range(self.taskList.count()):
            # State 2 is set when item is selected
            if self.taskList.item(index).checkState() == 2:
                # Add selected task to task list
                selected_tasks.append(str(self.taskList.item(index).text()))

        # Check to see if a random order is desired
        # If so, shuffle tasks
        if self.random_order_selected():
            random.shuffle(selected_tasks)

        # Check for required inputs
        if not selected_tasks:
            self.error_dialog('No tasks selected')
        elif not ra:
            self.error_dialog('Please enter RA name...')
        elif not sub_num:
            self.error_dialog('Please enter a subject number...')
        elif not condition:
            self.error_dialog('Please enter a condition number...')
        elif not age:
            self.error_dialog('Please enter an age...')
        elif not self.maleRadio.isChecked() and not \
                self.femaleRadio.isChecked():
            self.error_dialog('Please select a sex...')
        else:
            # Store subject info into a dataframe
            subject_info = pd.DataFrame(
                data=[(str(current_date), str(sub_num),
                       str(condition), int(age), str(sex), str(ra),
                       ', '.join(selected_tasks))],
                columns=['datetime', 'sub_num', 'condition',
                         'age', 'sex', 'RA', 'tasks']
            )

            # Set the output file name
            data_file_name = "%s_%s.xls" % (sub_num, condition)

            # Check if file already exists
            output_file = os.path.join(self.dataPath, data_file_name)
            if os.path.isfile(output_file):
                self.error_dialog('Data file already exists')
            else:
                # Create the excel writer object and save the file
                writer = pd.ExcelWriter(output_file)
                subject_info.to_excel(writer, 'info', index=False)
                writer.save()

                # Minimize battery UI
                self.showMinimized()

                # Get most recent task settings from file
                self.get_settings()

                # Center all pygame windows if not fullscreen
                if not self.task_fullscreen:
                    pos_x = str(self.res_width / 2 - self.task_width / 2)
                    pos_y = str(self.res_height / 2 - self.task_height / 2)

                    os.environ['SDL_VIDEO_WINDOW_POS'] = \
                        "%s, %s" % (pos_x, pos_y)

                # Initialize pygame
                pygame.init()

                # Set pygame icon image
                image = os.path.join(self.base_dir, "images", "icon_sml.png")
                icon_img = pygame.image.load(image)
                pygame.display.set_icon(icon_img)

                # Create primary task window
                # pygame_screen is passed to each task as the display window
                if self.task_fullscreen:
                    self.pygame_screen = pygame.display.set_mode(
                        (0, 0), pygame.FULLSCREEN)
                else:
                    if self.task_borderless:
                        self.pygame_screen = pygame.display.set_mode(
                            (self.task_width, self.task_height),
                            pygame.NOFRAME)
                    else:
                        self.pygame_screen = pygame.display.set_mode(
                            (self.task_width, self.task_height))

                background = pygame.Surface(self.pygame_screen.get_size())
                background = background.convert()

                # Run each task
                # Return and save their output to dataframe/excel
                for task in selected_tasks:
                    if task == "Attention Network Test (ANT)":
                        # Set number of blocks for ANT
                        ant_task = ant.ANT(self.pygame_screen, background,
                                           blocks=self.ant_blocks)
                        # Run ANT
                        ant_data = ant_task.run()
                        # Save ANT data to excel
                        ant_data.to_excel(writer, 'ANT', index=False)
                    elif task == "Mental Rotation Task":
                        mrt_task = mrt.MRT(self.pygame_screen, background)
                        # Run MRT
                        mrt_data = mrt_task.run()
                        # Save MRT data to excel
                        mrt_data.to_excel(writer, 'MRT', index=False)
                    elif task == "Sustained Attention to Response Task (SART)":
                        sart_task = sart.SART(self.pygame_screen, background)
                        # Run SART
                        sart_data = sart_task.run()
                        # Save SART data to excel
                        sart_data.to_excel(writer, 'SART', index=False)
                    elif task == "Digit Span (backwards)":
                        digitspan_backwards_task = \
                            digitspan_backwards.DigitspanBackwards(
                                self.pygame_screen, background)
                        # Run Digit span (Backwards)
                        digitspan_backwards_data = \
                            digitspan_backwards_task.run()
                        # Save digit span (backwards) data to excel
                        digitspan_backwards_data.to_excel(
                            writer, 'Digit span (backwards)', index=False)
                    elif task == "Raven's Progressive Matrices":
                        ravens_task = ravens.Ravens(
                            self.pygame_screen, background,
                            start=9, numTrials=12)
                        # Run Raven's Matrices
                        ravens_data = ravens_task.run()
                        # Save ravens data to excel
                        ravens_data.to_excel(writer, 'Ravens Matrices',
                                             index=False)
                    elif task == "Sternberg Task":
                        sternberg_task = sternberg.Sternberg(
                            self.pygame_screen, background)
                        # Run Sternberg Task
                        sternberg_data = sternberg_task.run()
                        # Save sternberg data to excel
                        sternberg_data.to_excel(writer, 'Sternberg',
                                                index=False)

                    # Save excel file
                    writer.save()

                # End of experiment screen
                pygame.display.set_caption("Cognitive Battery")
                pygame.mouse.set_visible(1)

                background.fill((255, 255, 255))
                self.pygame_screen.blit(background, (0, 0))

                font = pygame.font.SysFont("arial", 30)
                display.text(self.pygame_screen, font, "End of Experiment",
                             "center", "center")

                pygame.display.flip()

                display.wait_for_space()

                # Quit pygame
                pygame.quit()

                print "--- Experiment complete"
                self.close()