# pyinstaller --icon=icon.ico --onefile --noconsole main.py
from PIL import Image
import os, sys
from PyQt5.QtWidgets import QApplication, QAction, QFileDialog, QLabel, QPushButton, QMainWindow, QMessageBox, QComboBox, QProgressBar, QVBoxLayout, QPlainTextEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QThread
from PyQt5 import QtWidgets, QtGui
from ftplib import FTP
from datetime import datetime
from collections import Counter

if not os.path.exists('./log'):
    os.mkdir('./log/')


class WorkerThread(QThread):

    def __init__(self, settings, species_list):
        super().__init__()
        self.settings = settings
        self.species_list = species_list

    def run(self):
        # find status.
        self.user_species_counter = Counter()

        try:
            # set ftp.
            ftp = FTP()
            ftp.connect(self.settings['ip'], 21)
            ftp.login(self.settings['user'], self.settings['pass'])
            ftp.encoding = 'cp949'

            # search file names.
            for sp in self.species_list:
                ftp.cwd(self.settings['target_path'] + sp + '/images')
                try:
                    files = ftp.nlst()
                    for f in files:
                        if self.settings['name'] in f:
                            target_degree = f.split('_')[3]
                            self.user_species_counter[f'{sp} - {target_degree}'] += 1
                except:
                    print('no file found.')

        except Exception as e:
            print(e)
            return

        if ftp:
            ftp.close()

        self.quit()


class SearchingStatusDialog(QtWidgets.QDialog):

    def __init__(self, settings, species_list):
        super().__init__()
        self.settings = settings
        self.setWindowTitle('Your status.')
        self.setWindowIcon(QIcon('res/info.png'))
        self.resize(300, 50)

        self.layout = QVBoxLayout()
        self.message = QPlainTextEdit("Wait a moment...")

        self.layout.addWidget(self.message)
        self.setLayout(self.layout)

        self.thread = WorkerThread(self.settings, species_list)
        self.thread.finished.connect(self.show_status)
        self.thread.start()

    def show_status(self):
        print('finish')
        message_temp = f'{self.settings["name"].upper()} current status.\n\n'
        total_val = 0
        for key, value in sorted(self.thread.user_species_counter.items(), reverse=False):
            message_temp += f"{key} : {value} shots\n"
            total_val += value

        message_temp += f'\nTOTAL : {total_val} shots'
        self.message.setPlainText(message_temp)
        self.resize(300, 500)
        self.update()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.image_extension = ['png', 'jpg']
        self.species_list = ['기장', '녹두', '들깨', '땅콩', '수수', '옥수수', '조', '참깨', '콩', '팥']
        self.degree_list = ['0', '45', '90']
        self.setting_options = ['ip', 'user', 'path', 'name']
        self.selected_species = self.species_list[0]
        self.selected_degree = self.degree_list[0]
        self.settings = dict()
        self.image_path = None

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Plants Image Uploader')
        self.setWindowIcon(QIcon('res/leaf.png'))

        openFile = QAction(QIcon('res/folder.png'), 'select folder', self)
        # openFile.setShortcut('Ctrl+O')
        openFile.triggered.connect(self.show_dialog)

        openInfo = QAction(QIcon('res/info.png'), 'Info', self)
        openInfo.triggered.connect(self.show_info)

        openStatus = QAction(QIcon('res/info.png'), 'Status', self)
        openStatus.triggered.connect(self.show_status)

        menubar = self.menuBar()
        menubar.setStyleSheet("background-color: rgb(230,230,230)")
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu('&File')
        filemenu.addAction(openFile)

        infomenu = menubar.addMenu('&Info')
        infomenu.addAction(openInfo)
        infomenu.addAction(openStatus)

        self.label1 = QLabel('Selected path :', self)
        self.label1.move(10, 50)
        self.label2 = QLabel('', self)
        self.label2.move(100, 50)
        self.label2.resize(self.frameGeometry().width() - self.label1.frameGeometry().width(), self.label1.frameGeometry().height())

        self.species = QComboBox(self)
        self.species.move(10, 80)
        self.species.resize(100, 23)
        [self.species.addItem(sp) for sp in self.species_list]
        self.species.activated[str].connect(self.on_activated_species)

        self.degrees = QComboBox(self)
        self.degrees.move(self.species.frameGeometry().width() + 15, 80)
        self.degrees.resize(100, 23)
        [self.degrees.addItem(de) for de in self.degree_list]
        self.degrees.activated[str].connect(self.on_activated_degree)

        self.btn = QPushButton('upload', self)
        self.btn.resize(50, 23)
        self.btn.move(self.species.frameGeometry().width() + self.degrees.frameGeometry().width() + 25, 80)
        self.btn.clicked.connect(self.upload_clicked)

        self.statusBar().setStyleSheet("border-width: 1px;border-top-style : solid;border-color : lightgray;margin : 2px")
        self.statusBar().showMessage('Ready')

        self.progressbar = QProgressBar()
        self.progressbar.setMinimum(0)
        self.progressbar.setMaximum(100)
        self.progressbar.setAlignment(Qt.AlignCenter)
        self.statusBar().addPermanentWidget(self.progressbar)

        # load setting.
        if self.load_setting():

            # setup uploader name.
            self.label0 = QLabel(f'{self.settings["name"].upper()}', self)
            self.label0.move(10, 20)
            font0 = self.label0.font()
            font0.setBold(True)
            font0.setPointSize(12)
            self.label0.setFont(font0)
            self.label0.resize(self.frameGeometry().width(), self.label0.frameGeometry().height())

            # setup ui.
            self.move(300, 300)
            self.resize(600, 134)
            self.setFixedSize(600, 134)
            self.show()

            mes = '[IMPORTANT]\n"setup.bin" 파일을 텍스트 에디터로 열어서 알맞게 수정해주세요.\n\n1. 특정 각도, 한 종류의 식물 사진을 특정 디렉터리로 옮깁니다.\n2. "File - select folder"를 클릭해서 사진이 있는 디렉터리를 선택합니다.\n3. 하단의 식물 종류와 각도를 선택하고 upload를 누릅니다.'
            mes_en = '[IMPORTANT]\nPlease open the "setup.bin" file as a text editor and modify it accordingly.\n\n1. Move a picture of a particular angle, one type of plant, to a particular directory.\n2. Click "File - select folder" to select the directory where the pictures are located.\n3. Select the plant type and angle at the bottom and press upload.'
            self.show_message('Instruction', mes + '\n\n' + mes_en, False)

        else:
            self.show_message('Warning', 'There is a problem with the setup.bin file.\nCheck this file and run again.', True)

    def on_activated_species(self, item):
        self.selected_species = item
        print(item)

    def on_activated_degree(self, item):
        self.selected_degree = item
        print(item)

    def load_setting(self):
        setting_path = './setup.bin'
        if os.path.exists(setting_path):
            f = open(setting_path, 'r')
            settings = f.readlines()
            for item in settings:
                if not item.startswith('//') and '=' in item:
                    setup = list(map(str.strip, item.replace('\n', '').split('=')))
                    self.settings[setup[0]] = setup[1]

            f.close()
            return True
        return False

    def upload_clicked(self):
        if self.image_path:
            print('uploading...')

            # return False or filtered file names.
            filtered = self.is_files_exists()
            if filtered:
                print('start uploading..')
                reply = QMessageBox.question(self,
                                             'Check',
                                             f'Please Check information.\n\n1.Name: {self.settings["name"]}\n2.Species: {self.selected_species}\n3.Degree: {self.selected_degree}',
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

                if reply == QMessageBox.Yes:
                    print('processing....')
                    # upload pictures.
                    self.upload_images(filtered)

                else:
                    print('canceled.')
        else:
            self.show_message('Path Alert', 'Please select the folder first.', False)

    def show_status(self):
        msg = SearchingStatusDialog(self.settings, self.species_list)
        msg.show()
        msg.exec_()

    def show_info(self):
        msgbox = QMessageBox()
        msgbox.setWindowIcon(QIcon('res/info.png'))
        msgbox.setText('Plants data uploader (1.0.1)\n\nIf it\'s useful, put a tip on Jong Hyeok\'s desk... \n(I just love doing lots of homework on Saturdays~****)')
        msgbox.show()
        msgbox.exec_()

    def show_dialog(self):
        get_path = QFileDialog.getExistingDirectory(self, 'select target folder', './')
        if get_path:
            self.image_path = get_path
            self.statusBar().showMessage(f'Path loaded', 3000)
            self.label2.setText(f'{self.image_path}')
            self.update()

    def is_files_exists(self):
        item_list = os.listdir(self.image_path)
        if len(item_list) > 0:
            filtered = [i for i in item_list if len(i.split('.')) == 2 and i.split('.')[1].lower() in self.image_extension]
            if len(filtered) > 0:
                return filtered
            else:
                # miss match extension recognized.
                self.show_message('Message', 'This program only support (*png, *jpg) extensions.\nImage file not found.', False)

        elif len(item_list) == 0:
            # no file.
            self.show_message('Message', 'Image files not exist in this path.', False)

        return False

    def show_message(self, title, text, exit_sys):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setWindowIcon(QIcon('res/info.png'))
        msg_box.setText(text)
        msg_box.show()
        msg_box.exec_()
        if exit_sys:
            sys.exit()

    def upload_images(self, filtered_list):
        self.f = open(f"./log/log_{str(int(datetime.now().timestamp() * 1000))}.txt", 'w')
        try:
            # set ftp.
            ftp = FTP()
            ftp.connect(self.settings['ip'], 21)
            ftp.login(self.settings['user'], self.settings['pass'])
            ftp.encoding = 'cp949'
            ftp.cwd(self.settings['target_path'] + self.selected_species + '/images')
        except Exception as e:
            self.statusBar().showMessage('Upload Error : Connection Failed', 5000)
            self.show_message('Warning', 'Server Connection Failed', False)
            self.f.write('Server Connection Failed\n')
            self.f.write(str(e))
            self.f.close()
            return

        for idx, i_name in enumerate(filtered_list):
            m_path = self.image_path + '/' + i_name
            img = Image.open(m_path)
            try:
                meta_date = img._getexif()[36867].split()[0].replace(':', '-')
            except:
                meta_date = '0000-00-00'
            time_mark = str(int(datetime.now().timestamp() * 1000))

            final_file_name = meta_date + '_' + \
                              self.settings['name'] + '_' + \
                              self.selected_species + '_' + \
                              self.selected_degree + '_' + time_mark + '.' + i_name.split('.')[1]

            self.statusBar().showMessage(f'Uploading: {i_name}')
            self.progressbar.setValue(idx * 100 // (len(filtered_list) - 1))
            print(final_file_name)

            # upload images.

            try:
                m_image = open(m_path, 'rb')
                ftp.storbinary('STOR ' + final_file_name, m_image)
                self.f.write(f'[Success] {m_path},{final_file_name}\n')
            except:
                self.statusBar().showMessage('Upload Error : target_name')
                self.f.write(f'[Fail] {m_path},{final_file_name}\n')
            # upload end.

        if ftp:
            ftp.close()

        self.f.close()
        self.statusBar().showMessage('Finish', 5000)
        self.progressbar.reset()
        self.show_message('Finish', 'Upload finished!', False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
