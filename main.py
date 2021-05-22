from PIL import Image
import os, sys
from PyQt5.QtWidgets import QApplication, QAction, QFileDialog, QLabel, QPushButton, QMainWindow, QMessageBox, QComboBox, QProgressBar
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from ftplib import FTP
from datetime import datetime

if not os.path.exists('./log'):
    os.mkdir('./log/')


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

        self.f = open(f"./log/log_{str(int(datetime.now().timestamp()*1000))}.txt", 'w')

    def initUI(self):
        self.setWindowTitle('Plants Image Uploader')
        self.setWindowIcon(QIcon('leaf.png'))

        openFile = QAction(QIcon('folder.png'), 'select folder', self)
        # openFile.setShortcut('Ctrl+O')
        openFile.triggered.connect(self.showDialog)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        filemenu = menubar.addMenu('&File')
        filemenu.addAction(openFile)

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

    def showDialog(self):
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
                self.show_message('Message', 'This program only support (*png, *jpg) extensions.', False)

        elif len(item_list) == 0:
            # no file.
            self.show_message('Message', 'Image files not exist in this path.', False)

        return False

    def show_message(self, title, text, exit_sys):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setWindowIcon(QIcon('leaf.png'))
        msg_box.setText(text)
        msg_box.show()
        msg_box.exec_()
        if exit_sys:
            sys.exit()

    def upload_images(self, filtered_list):
        try:
            # set ftp.
            ftp = FTP()
            ftp.connect(self.settings['ip'], 21)
            ftp.login(self.settings['user'], self.settings['pass'])
            ftp.encoding = 'utf-8'
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
            time_mark = str(int(datetime.now().timestamp()*1000))

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
