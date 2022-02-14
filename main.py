from json.tool import main
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog, QWidget, QMessageBox, QFileSystemModel, QTreeView, QVBoxLayout, QProgressBar, QLabel, QFrame, QSplashScreen
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap, QFont
from cv2 import destroyAllWindows
from train import *
import sqlite3 
import sys
import time
from datetime import datetime, date
import cv2
import xlsxwriter
from facenet.face_contrib import *
from validator.validate import *
import keyring
import base64

class WelcomeScreen(QDialog):
    def __init__(self):
        super(WelcomeScreen, self).__init__()
        loadUi("./qt designer/welcomescreen.ui",self)
        self.login.clicked.connect(self.gotologin)
        self.create.clicked.connect(self.gotocreate)

    def gotologin(self):
        login = LoginScreen()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex()+1)

    def gotocreate(self):
        create = CreateAccScreen()
        widget.addWidget(create)
        widget.setCurrentIndex(widget.currentIndex() + 1)
     
class ForgotPassword(QDialog):
    def __init__(self, username):
        super(ForgotPassword, self).__init__()
        loadUi("./qt designer/forgotpassword.ui",self)
        self.btnReset.clicked.connect(self.reset)
        self.tfPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.username = username
    def reset(self):
        # get question and answer of user
        CbQuestion = self.cbQuestion.currentText()
        tfAnswer = self.tfAnswer.text()
        password = self.tfPassword.text()
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT question,answer from account where username = ?", (self.username,))
        
            sqliteConnection.commit()
            record = cursor.fetchone()
            question = record[0]
            answer = record[1]
            cursor.close()         
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
        # insert new password
        if CbQuestion == question:
            if tfAnswer == answer:
                try:
                    sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")
                    encrypt = base64.b85encode(password.encode("utf-8"))
                    cursor.execute("UPDATE account set password = ? where username = ?", (encrypt, self.username))
                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Password reset successfully")
                except sqlite3.Error as error:
                   print("Failed to get data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
            else:
                self.showdialog("Answer is incorrect")
        else:
            self.showdialog("Incorrect question")    
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
       
class LoginScreen(QDialog):
    def __init__(self):
        super(LoginScreen, self).__init__()
        loadUi("./qt designer/login.ui",self)
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.login.clicked.connect(self.loginfunction)
        self.lbForgot.mousePressEvent = self.forgotpassword
        self.MAGIC_USERNAME_KEY = 'im_the_magic_username_key'
        self.service_id = 'IM_YOUR_APP!'
        self.keyring = keyring.get_keyring()
    def loginfunction(self):
        user = self.usernamefield.text()
        password = self.passwordfield.text()
        if len(user)==0 or len(password)==0:
            self.error.setText("Please input all fields.")
        else:
            try:
                conn = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cur = conn.cursor()
                query = 'SELECT password FROM account WHERE username =\''+user+"\'"
                cur.execute(query)
                result_pass =cur.fetchone()[0]
                decrypt = base64.b85decode(result_pass).decode("utf-8")
                conn.close()
                if decrypt == password:
                    print("Successfully logged in.")
                    self.error.setText("")
                    self.keyring.set_password(self.service_id, self.MAGIC_USERNAME_KEY, user)

                    main = Main()
                    widget.addWidget(main)
                    widget.setCurrentIndex(widget.currentIndex()+1)

                else:
                    self.error.setText("Invalid username or password")
            except sqlite3.Error as error:
                print("Failed to get data into sqlite table", error)
            finally:
                if conn:
                    conn.close()
                print("The SQLite connection is closed")
    def forgotpassword(self, event):
        username = self.usernamefield.text()
        # get all username
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT username FROM account")
        
            sqliteConnection.commit()
            records = cursor.fetchall()
            cursor.close()
            if (username,) in records:
                self.error.setText("")
                forgot = ForgotPassword(username)
                widget.addWidget(forgot)
                widget.setCurrentIndex(widget.currentIndex()+1)
            else:
                self.error.setText("Invalid username")
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")

class CreateAccScreen(QDialog):
    def __init__(self):
        super(CreateAccScreen, self).__init__()
        loadUi("./qt designer/createacc.ui",self)
        self.passwordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirmpasswordfield.setEchoMode(QtWidgets.QLineEdit.Password)
        self.signup.clicked.connect(self.signupfunction)

    def signupfunction(self):
        user = self.usernamefield.text()
        password = self.passwordfield.text()
        confirmpassword = self.confirmpasswordfield.text()

        if len(user)==0 or len(password)==0 or len(confirmpassword)==0:
            self.error.setText("Please fill in all inputs.")

        elif password!=confirmpassword:
            self.error.setText("Passwords do not match.")
        else:
            try:
                conn = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cur = conn.cursor()
                encrypt = base64.b85encode(password.encode("utf-8"))
                user_info = [user, encrypt]
                cur.execute('INSERT INTO account (username, password) VALUES (?,?)', user_info)

                conn.commit()
                conn.close()

                login = LoginScreen()
                widget.addWidget(login)
                widget.setCurrentIndex(widget.currentIndex()+1)
            except sqlite3.Error as error:
                print("Failed to get data into sqlite table", error)
            finally:
                if conn:
                    conn.close()
                print("The SQLite connection is closed")

class Main(QDialog):
    def __init__(self):
        super(Main, self).__init__()
        loadUi("./qt designer/interface.ui",self)
        self.styleSheet()
        self.role = self.getRole()
        self.btnExit.clicked.connect(self.exit)
        self.btnStudent.clicked.connect(self.gotostudent)
        self.btnTeacher.clicked.connect(self.gototeacher)
        self.btnSubject.clicked.connect(self.gotosubject)
        self.btnAttendence.clicked.connect(self.gotoattendence)
        self.btnClass.clicked.connect(self.gotoclass)
        self.btnSchedule.clicked.connect(self.gotoschedule)
        self.btnRecognize.clicked.connect(self.gotorecognize)
        self.btnAnalyst.clicked.connect(self.gotoanalyst)
        self.btnProfile.clicked.connect(self.gotoprofile)
        if self.role == "ROLE_USER":
            self.btnStudent.setDisabled(True)
            self.btnTeacher.setDisabled(True)
            self.btnSubject.setDisabled(True)
            self.btnClass.setDisabled(True)
            self.btnSchedule.setDisabled(True)
            self.btnAnalyst.setDisabled(True)
        #Dynamic display time on the label
        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start()

    def styleSheet(self):
        leftHeaderPixmap = QPixmap('D:/code/.vscode/python/simple_facenet/Resources/BestFacialRecognition.jpg')
        self.label.setPixmap(leftHeaderPixmap)
        centerHeaderPixmap = QPixmap('D:/code/.vscode/python/simple_facenet/Resources/facialrecognition.png')
        self.label_2.setPixmap(centerHeaderPixmap)
        rightHeaderPixmap = QPixmap('D:/code/.vscode/python/simple_facenet/Resources/images.jpg')
        self.label_3.setPixmap(rightHeaderPixmap)
        bodyCSS = "QFrame#frame_2{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/backgroud.jpg');}"
        self.frame_2.setStyleSheet(bodyCSS)
        recognizeCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/face_detector1.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnRecognize.setStyleSheet(recognizeCSS)
        studentCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/gettyimages-1022573162.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnStudent.setStyleSheet(studentCSS)
        attendanceCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/attendace.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnAttendence.setStyleSheet(attendanceCSS)
        teacherCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/teacher.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnTeacher.setStyleSheet(teacherCSS)
        subjectCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/subject.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnSubject.setStyleSheet(subjectCSS)
        classCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/class.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnClass.setStyleSheet(classCSS)
        scheduleCSS = "QPushButton{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/schedule.jpg')  0 0 0 0 stretch stretch;} QPushButton:hover {border:1px solid red;}"
        self.btnSchedule.setStyleSheet(scheduleCSS)
        analystCSS = "QPushButton {border-image: url('D:/code/.vscode/python/simple_facenet/Resources/analyst.jpg')} QPushButton:hover{border:1px solid red;}"
        self.btnAnalyst.setStyleSheet(analystCSS)
        profileCSS = "QPushButton {border-image: url('D:/code/.vscode/python/simple_facenet/Resources/help-desk-customer-care-team-icon-blue-square-button-isolated-reflected-abstract-illustration-89657179.jpg')} QPushButton:hover{border:1px solid red;}"
        self.btnProfile.setStyleSheet(profileCSS)
        exitCSS = "QPushButton {border-image: url('D:/code/.vscode/python/simple_facenet/Resources/exit.jpg')} QPushButton:hover{border:1px solid red;}"
        self.btnExit.setStyleSheet(exitCSS)
        self.lbDate.setFont(QFont('Arial', 10))
    def getRole(self):
        login = LoginScreen()
        username = login.keyring.get_password(login.service_id, login.MAGIC_USERNAME_KEY)
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT role FROM account WHERE username = ?", (username,))
        
            sqliteConnection.commit()
            role = cursor.fetchone()[0]
            cursor.close()
            
            return role
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def showTime(self):
        now = datetime.now()
 
        dt_string = now.strftime("%d/%m/%Y")
        t_string = now.strftime("%H:%M:%S")

        self.lbDate.setText(dt_string + "\n " + t_string)

    def gotostudent(self):
        student = Student()
        widget.addWidget(student)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gototeacher(self):
        teacher = Teacher()
        widget.addWidget(teacher)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gotosubject(self):
        subject = Subject()
        widget.addWidget(subject)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gotoattendence(self):
        attendence = Attendence()
        widget.addWidget(attendence)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gotoclass(self):
        lopHoc = LopHoc()
        widget.addWidget(lopHoc)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gotoschedule(self):
        schedule = Schedule()
        widget.addWidget(schedule)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gotorecognize(self):
        recognize = Recognize()
        widget.addWidget(recognize)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gotoanalyst(self):
        analyst = Analyst()
        widget.addWidget(analyst)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def gotoprofile(self):
        profile = Profile()
        widget.addWidget(profile)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def exit(self):
        login = LoginScreen()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex()+1)
        login.keyring.delete_password(login.service_id, login.MAGIC_USERNAME_KEY)
# profile
class Profile(QDialog):
    def __init__(self):
        super(Profile, self).__init__()
        loadUi("./qt designer/profile.ui",self)
        login = LoginScreen()
        self.username = login.keyring.get_password(login.service_id, login.MAGIC_USERNAME_KEY)
        self.styleSheet()
        self.getUserInfor()
        self.btnUpdate.clicked.connect(self.update)
        self.btnExit.clicked.connect(self.exit)
        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start()
    def getUserInfor(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("select * from teachers as t inner join account as a on t.id = a.teacher_id where a.username = ?", (self.username,))
        
            sqliteConnection.commit()
            record = cursor.fetchone()
            self.tfTen.setText(record[1])
            self.tfSDT.setText(record[2])
            self.tfDiaChi.setText(record[3])
            self.tfEmail.setText(record[4])
            self.cbQuestion.setCurrentText(record[10])
            self.tfAnswer.setText(record[11])
            cursor.close()
            
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def update(self):
        if isRequiredFiled(self.tfTen.text()) == False or isRequiredFiled(self.tfSDT.text()) == False or isRequiredFiled(self.tfDiaChi.text()) == False or isRequiredFiled(self.tfEmail.text()) == False or isRequiredFiled(self.cbQuestion.currentText()) == False or  isRequiredFiled(self.tfAnswer) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        elif isValidEmail(self.tfEmail.text()) == False:
            self.showdialog("Email không hợp lệ")
        elif isValidPhone(self.tfSDT.text()) == False:
            self.showdialog("Số điện thoại không hợp lệ")
        else:
            # update profile
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE teachers SET ten = ?, sdt = ?, diaChi = ?, email = ?  WHERE id = (SELECT teacher_id FROM account WHERE username = ?)", (self.tfTen.text(), self.tfSDT.text(), self.tfDiaChi.text(), self.tfEmail.text(), self.username))
            
                sqliteConnection.commit()
                cursor.close()
            except sqlite3.Error as error:
               print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
            # update secret question
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE account SET question = ?, answer = ? WHERE username = ?", (self.cbQuestion.currentText(), self.tfAnswer.text(), self.username))
            
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Cập nhật thành công")
            except sqlite3.Error as error:
               print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def styleSheet(self):
        leftHeaderPixmap = QPixmap('D:/code/.vscode/python/simple_facenet/Resources/BestFacialRecognition.jpg')
        self.label.setPixmap(leftHeaderPixmap)
        centerHeaderPixmap = QPixmap('D:/code/.vscode/python/simple_facenet/Resources/facialrecognition.png')
        self.label_2.setPixmap(centerHeaderPixmap)
        rightHeaderPixmap = QPixmap('D:/code/.vscode/python/simple_facenet/Resources/images.jpg')
        self.label_3.setPixmap(rightHeaderPixmap)
        bodyCSS = "QFrame#frame_2{border-image: url('D:/code/.vscode/python/simple_facenet/Resources/backgroud.jpg');}"
        self.frame_2.setStyleSheet(bodyCSS)
        self.lbDate.setFont(QFont('Arial', 10))
    def showTime(self):
        now = datetime.now()
 
        dt_string = now.strftime("%d/%m/%Y")
        t_string = now.strftime("%H:%M:%S")

        self.lbDate.setText(dt_string + "\n " + t_string)
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
# student
class Student(QDialog):
    def __init__(self):
        super(Student, self).__init__()
        loadUi("./qt designer/thongtinsv.ui",self)
        self.btnRefresh.clicked.connect(self.refresh)
        self.btnSave.clicked.connect(self.save)
        self.btnEdit.clicked.connect(self.edit)
        self.btnLoadAll.clicked.connect(self.loadData)
        self.btnSearch.clicked.connect(self.search)
        self.btnDelete.clicked.connect(self.delete)
        self.btnGetPics.clicked.connect(self.getPics)
        self.btnTrain.clicked.connect(self.training)
        self.btnExit.clicked.connect(self.exit)
        self.loadData()
        self.UiComponents()
    def UiComponents(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM students order by id")
            
            sqliteConnection.commit()
            rows = cursor.fetchall()

            for row in rows:
                self.cbId.addItem(str(row[0]))
            cursor.close()
            self.cbId.activated.connect(self.getInfor)
        except sqlite3.Error as error:
              print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getPics(self):
        model = self.tfModel.text()
        id = self.cbId.currentText()
        if isRequiredFiled(model) == False or isRequiredFiled(id) == False:
            self.showdialog("Vui lòng nhập model và ID sinh viên")
        elif isValidString(model) == False:
            self.showdialog("Model không hợp lệ")
        elif self.checkIfStudentExist() == False:
            self.showdialog("Sinh viên đã có ảnh")
        else:
            # create folder
            self.createFolder(model)
            # open cam and take pics
            cam = cv2.VideoCapture(0)

            cv2.namedWindow("Screenshot")

            img_counter = 1

            while True:
                ret, frame = cam.read()
                if not ret:
                    print("failed to grab frame")
                    break
                cv2.imshow("test", frame)

                k = cv2.waitKey(1)
                if k%256 == 27:
                    # ESC pressed
                    if img_counter == 1:
                        self.showdialog("Vui lòng chụp ảnh")
                    else:
                        print("Escape hit, closing...")
                        break
                elif k%256 == 32:
                    # SPACE pressed
                    number_str = str(img_counter)
                    zero_filled_number = number_str.zfill(4)
                    img_name = "D:/code/.vscode/python/simple_facenet/your_face/{folder}/{folder}_{counter}.jpg".format(folder=model, counter = zero_filled_number)
                    cv2.imwrite(img_name, frame)
                    img_counter += 1

            cam.release()

            cv2.destroyAllWindows()
            # save to db
            self.insertModel(model, id)
    def insertModel(self, model, id):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("INSERT INTO models (ten, student_id) VALUES (?, ?)", (model, id))
        
            sqliteConnection.commit()
            cursor.close()
        except sqlite3.Error as error:
              print("Failed to insert data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def createFolder(self, model):
        directory = model
        parent_dir = "D:/code/.vscode/python/simple_facenet/your_face/"
  
        path = os.path.join(parent_dir, directory)

        os.mkdir(path)
    def checkIfStudentExist(self):
        id = self.cbId.currentText()
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("select s.id from students as s inner join models as m on s.id = m.student_id where s.id = ?", (id,))
        
            sqliteConnection.commit()
            rows = cursor.fetchone()
            if rows == None:
                return True
            else:
                return False
        except sqlite3.Error as error:
              print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def training(self):
        align_mtcnn('your_face', 'face_align')
        train('face_align/', 'models/20180402-114759.pb', 'models/your_model.pkl')
        self.showdialog("Training completed.")
    def getInfor(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT * FROM students WHERE id = ?", (self.cbId.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone();
            cursor.close()

            self.tfTenSV.setText(results[1])
            self.tfCMND.setText(results[2])
            self.tfNgaySinh.setText(results[3])
            self.tfSDT.setText(results[4])
            self.cbGioiTinh.setCurrentText(str(results[5]))
            self.tfEmail.setText(results[6])
            self.tfDiaChi.setText(results[7])
            self.tfNienKhoa.setText(results[8])
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")

    def loadData(self):
        connection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
        cur = connection.cursor()
        sqlquery="select * from students as s inner join course as c on s.course_id = c.id"

        self.tableWidget.setRowCount(50)
        tablerow=0
        for row in cur.execute(sqlquery):
            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))
            self.tableWidget.setItem(tablerow,8,QtWidgets.QTableWidgetItem(row[8]))
            self.tableWidget.setItem(tablerow,9,QtWidgets.QTableWidgetItem(row[11]))
            self.tableWidget.setItem(tablerow,10,QtWidgets.QTableWidgetItem(row[12]))
            tablerow+=1
        connection.close()
    def save(self): 
        ten = self.tfTenSV.text()
        nienKhoa = self.tfNienKhoa.text()
        cmnd = self.tfCMND.text()
        gioiTinh = self.cbGioiTinh.currentText()
        ngaySinh = self.tfNgaySinh.text()
        email = self.tfEmail.text()
        sdt = self.tfSDT.text()
        diaChi = self.tfDiaChi.text()
        cbNganh = self.cbNganh.currentText()
        cbHe = self.cbHe.currentText()
        if isRequiredFiled(ten) == False or isRequiredFiled(nienKhoa) == False or isRequiredFiled(cmnd) == False or isRequiredFiled(ngaySinh) == False or isRequiredFiled(email) == False or isRequiredFiled(sdt) == False or isRequiredFiled(diaChi) == False:
            self.showdialog("Điền đầy đủ các trường.")
        elif isValidID(cmnd) == False:
            self.showdialog("CMND không hợp lệ.")
        elif isValidEmail(email) == False:
            self.showdialog("Email không hợp lệ.")
        elif isValidDate(ngaySinh) == False:
            self.showdialog("Ngày sinh không hợp lệ.")
        elif isValidPhone(sdt) == False:
            self.showdialog("Số điện thoại không hợp lệ.")
        else:
            # lay id cua bang Khoa
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("SELECT id FROM COURSE WHERE he = ? and nganh = ?", (cbHe,cbNganh)) 
                course_id = cursor.fetchone()
               
                sqliteConnection.commit()
        
                cursor.close()
                self.loadData()
                self.refresh()
            except sqlite3.Error as error:
                print("Failed to select data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")

            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO students (ten, cmnd, ngaySinh, sdt ,gioiTinh, email, diaChi, nienKhoa, course_id) values(?, ?, ?, ?, ?, ?, ?, ?, ?)", (ten, cmnd, ngaySinh, sdt, gioiTinh, email, diaChi, nienKhoa, course_id[0]))
        
                sqliteConnection.commit()
                print("Record inserted successfully into SqliteDb_developers table ", cursor.rowcount)
                cursor.close()
                self.showdialog("Lưu thành công.")
                self.loadData()
                self.refresh()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")

    def edit(self):
        id = self.cbId.currentText()
        ten = self.tfTenSV.text()
        nienKhoa = self.tfNienKhoa.text()
        cmnd = self.tfCMND.text()
        gioiTinh = self.cbGioiTinh.currentText()
        ngaySinh = self.tfNgaySinh.text()
        email = self.tfEmail.text()
        sdt = self.tfSDT.text()
        diaChi = self.tfDiaChi.text()
        if(isRequiredFiled(id) == False):
            self.showdialog("Chọn sinh viên cần sửa.")
        if isRequiredFiled(ten) == False or isRequiredFiled(nienKhoa) == False or isRequiredFiled(cmnd) == False or isRequiredFiled(ngaySinh) == False or isRequiredFiled(email) == False or isRequiredFiled(sdt) == False or isRequiredFiled(diaChi) == False:
            self.showdialog("Điền đầy đủ các trường.")
        elif isValidID(cmnd) == False:
            self.showdialog("CMND không hợp lệ.")
        elif isValidEmail(email) == False:
            self.showdialog("Email không hợp lệ.")
        elif isValidDate(ngaySinh) == False:
            self.showdialog("Ngày sinh không hợp lệ.")
        elif isValidPhone(sdt) == False:
            self.showdialog("Số điện thoại không hợp lệ.")
        else:
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE students SET ten = ?, cmnd = ?, ngaySinh = ?, sdt = ?, gioiTinh = ?, email = ?, diaChi = ?, nienKhoa = ? WHERE id = ?", (ten, cmnd, ngaySinh, sdt, gioiTinh, email, diaChi, nienKhoa, id,))
        
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Sửa thành công.")
                self.loadData()
                self.refresh()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")

    def search(self):
        criteria = self.cbSearch.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Chọn trường cần tìm.")
        else:
            if criteria == "ID sinh viên":
                id = self.tfSearch.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Nhập ID sinh viên.")
                elif isValidInteger(id) == False:
                    self.showdialog("ID sinh viên phải là số.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM students as s inner join course as c on s.course_id = c.id WHERE s.id =" + id
                        self.tableWidget.setRowCount(1)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))
                            self.tableWidget.setItem(tablerow,8,QtWidgets.QTableWidgetItem(row[8]))
                            self.tableWidget.setItem(tablerow,9,QtWidgets.QTableWidgetItem(row[11]))
                            self.tableWidget.setItem(tablerow,10,QtWidgets.QTableWidgetItem(row[12]))
                            tablerow+=1
                        sqliteConnection.commit()
            
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Tên sinh viên":
                self.tableWidget.setRowCount(0)
                name = self.tfSearch.text()
                if isRequiredFiled(name) == False:
                    self.showdialog("Nhập tên sinh viên.")
                elif isValidString(name) == False:
                    self.showdialog("Tên sinh viên không hợp lệ.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        self.tableWidget.setRowCount(10)
                        tablerow=0
                        for row in cursor.execute("SELECT * FROM students as s inner join course as c on s.course_id = c.id WHERE s.ten like ?", ("%"+name+"%",)):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))
                            self.tableWidget.setItem(tablerow,8,QtWidgets.QTableWidgetItem(row[8]))
                            self.tableWidget.setItem(tablerow,9,QtWidgets.QTableWidgetItem(row[11]))
                            self.tableWidget.setItem(tablerow,10,QtWidgets.QTableWidgetItem(row[12]))
                            tablerow+=1
                        sqliteConnection.commit()
                
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
    def delete(self): 
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.cbId.currentText()
            if(isRequiredFiled(id) == False):
                self.showdialog("Vui lòng chọn sinh viên cần xóa.")
            else:
                try:          
                    sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM students WHERE id = ?", [id])
            
                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Xóa thành công")
                    self.tableWidget.setRowCount(0)
                    self.loadData()
                    self.refresh()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)
    def refresh(self):
        self.cbId.clear()
        self.tfNienKhoa.setText("")
        self.cbGioiTinh.setCurrentText("Nam")
        self.cbNganh.setCurrentText("CNTT")
        self.cbHe.setCurrentText("Dân sự")
        self.tfTenSV.setText("")
        self.tfCMND.setText("")
        self.tfNgaySinh.setText("")
        self.tfEmail.setText("")
        self.tfSDT.setText("")
        self.tfDiaChi.setText("")
        self.UiComponents()
# teacher
class Teacher(QDialog):
    def __init__(self):
        super(Teacher, self).__init__()
        loadUi("./qt designer/thongtingiangvien.ui",self)
        self.btnSave.clicked.connect(self.save)
        self.btnRefresh.clicked.connect(self.refresh)
        self.btnEdit.clicked.connect(self.edit)
        self.btnLoadAll.clicked.connect(self.loadData)
        self.btnSearch.clicked.connect(self.search)
        self.btnDelete.clicked.connect(self.delete)
        self.btnExit.clicked.connect(self.exit)
        self.tfPassword.setEchoMode(QtWidgets.QLineEdit.Password)
        self.loadData()
        self.UiComponents()
    def UiComponents(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM teachers order by id")
            
            sqliteConnection.commit()
            rows = cursor.fetchall()

            for row in rows:
                self.cbId.addItem(str(row[0]))
            cursor.close()
            self.cbId.activated.connect(self.getInfor)
        except sqlite3.Error as error:
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInfor(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("select * from teachers as t inner join account as a on t.id = a.teacher_id where t.id = ?", (self.cbId.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            decrypt = base64.b85decode(results[8]).decode("utf-8")
            cursor.close()

            self.tfTen.setText(results[1])
            self.tfSDT.setText(results[2])
            self.tfDiaChi.setText(results[3])
            self.tfEmail.setText(results[4])
            self.cbLoai.setCurrentText(str(results[5]))
            self.tfUsername.setText(results[7])
            self.tfPassword.setText(decrypt)
            self.cbRole.setCurrentText(str(results[9]))
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def loadData(self):
        connection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
        cur = connection.cursor()
        sqlquery="select * from teachers"

        self.tableWidget.setRowCount(10)
        tablerow=0
        for row in cur.execute(sqlquery):
            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
            tablerow+=1
        connection.close()
    #save
    def save(self):
        ten = self.tfTen.text()
        sdt = self.tfSDT.text()
        email = self.tfEmail.text()
        diaChi = self.tfDiaChi.text()
        loai = self.cbLoai.currentText()
        username = self.tfUsername.text()
        password = self.tfPassword.text()
        role = self.cbRole.currentText()
        if isRequiredFiled(ten) == False or isRequiredFiled(sdt) == False or isRequiredFiled(email) == False or isRequiredFiled(diaChi) == False or isRequiredFiled(username) == False or isRequiredFiled(password) == False or isRequiredFiled(role) == False:
            self.showdialog("Điền đầy đủ các trường.")
        elif isValidEmail(email) == False:
            self.showdialog("Email không hợp lệ.")
        elif isValidPhone(sdt) == False:
            self.showdialog("Số điện thoại không hợp lệ.")
        elif isValidUsername(username) == False:
            self.showdialog("Tên tài khoản không hợp lệ.")
        elif self.checkIfUsernameExist(username) == True:
            self.showdialog("Tên tài khoản đã tồn tại.")
        elif isValidPassword(password) == False:
            self.showdialog("Mật khẩu không hợp lệ.")
        else:
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO teachers (ten, sdt, diaChi, email, loai) values(?, ?, ?, ?, ?)", (ten, sdt, diaChi, email, loai))
            
                sqliteConnection.commit()
                cursor.close()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
            #save account
            try:
                id = self.getTeacherId(ten)
                encrypt = base64.b85encode(password.encode("utf-8"))
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO account (username, password, role, teacher_id) values(?, ?, ?, ?)", (username, encrypt, role, id))
            
                sqliteConnection.commit()
                self.showdialog("Thêm thành công")
                self.loadData()
                self.refresh()
                cursor.close()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def checkIfUsernameExist(self, username):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("select id from account where username = ?", [username]) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()
            if results is None:
                return False
            else:
                return True
        except sqlite3.Error as error:
              print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getTeacherId(self, name):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("select id from teachers where ten = ?", (name,))
        
            sqliteConnection.commit()
            rows = cursor.fetchone()
            cursor.close()
            return rows[0]
        except sqlite3.Error as error:
              print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def edit(self):
        id = self.cbId.currentText()
        ten = self.tfTen.text()
        sdt = self.tfSDT.text()
        email = self.tfEmail.text()
        diaChi = self.tfDiaChi.text()
        loai = self.cbLoai.currentText()
        username = self.tfUsername.text()
        password = self.tfPassword.text()
        role = self.cbRole.currentText()
        if(isRequiredFiled(id) == False):
            self.showdialog("Chọn giảng viên cần sửa.")
        if isRequiredFiled(ten) == False or isRequiredFiled(sdt) == False or isRequiredFiled(email) == False or isRequiredFiled(diaChi) == False or isRequiredFiled(username) == False or isRequiredFiled(password) == False or isRequiredFiled(role) == False:
            self.showdialog("Điền đầy đủ các trường.")
        elif isValidEmail(email) == False:
            self.showdialog("Email không hợp lệ.")
        elif isValidPhone(sdt) == False:
            self.showdialog("Số điện thoại không hợp lệ.")
        elif isValidUsername(username) == False:
            self.showdialog("Tên tài khoản không hợp lệ.")
        elif self.checkIfUsernameExist(username):
            self.showdialog("Tên tài khoản đã tồn tại.")
        elif isValidPassword(password) == False:
            self.showdialog("Mật khẩu không hợp lệ.")
        else:
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE teachers SET ten = ?, sdt = ?, diaChi = ?, email = ?, loai = ? WHERE id = ?", (ten, sdt, diaChi, email, loai, id))
            
                sqliteConnection.commit()
                cursor.close()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
            # edit account
            try:
                encrypt = base64.b85encode(password.encode("utf-8"))
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE account SET username = ?, password = ?, role = ? WHERE teacher_id = ?", (username, encrypt, role, id))
            
                sqliteConnection.commit()
                self.showdialog("Sửa thành công")
                self.loadData()
                self.refresh()
                cursor.close()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def delete(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.cbId.currentText()
            if(isRequiredFiled(id) == False):
                self.showdialog("Vui lòng chọn giảng viên cần xóa.")
            else:
                # delete account
                try:
                    sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM account WHERE teacher_id = ?", (id,))
                
                    sqliteConnection.commit()
                    cursor.close()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
                # delete teacher
                try:
                    sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM teachers WHERE id = ?", (id,))
                
                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Xóa thành công")
                    self.tableWidget.setRowCount(0)
                    self.loadData()
                    self.refresh()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    # search
    def search(self):
        criteria = self.cbSearch.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Chọn cột cần tìm.")
        else:
            if criteria == "ID giáo viên":
                id = self.tfSearch.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Nhập ID giáo viên.")
                elif isValidInteger(id) == False:
                    self.showdialog("ID giáo viên không hợp lệ.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM teachers WHERE id =" + id
                        self.tableWidget.setRowCount(1)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Tên giáo viên":
                name = self.tfSearch.text()
                if isRequiredFiled(name) == False:
                    self.showdialog("Nhập tên giáo viên.")
                elif isValidString(name) == False:
                    self.showdialog("Tên giáo viên không hợp lệ.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM teachers WHERE ten = '" + name + "'"
                        self.tableWidget.setRowCount(10)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)
    
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)

    def refresh(self):
        self.tfTen.setText("")
        self.tfSDT.setText("")
        self.tfEmail.setText("")
        self.tfDiaChi.setText("")
        self.cbLoai.setCurrentText("")
        self.cbId.clear()
        self.tfUsername.setText("")
        self.tfPassword.setText("")
        self.cbRole.setCurrentText("")
        self.UiComponents()
# subjects
class Subject(QDialog):
    def __init__(self):
        super(Subject, self).__init__()
        loadUi("./qt designer/quanlymonhoc.ui",self)
        self.btnSave1.clicked.connect(self.save1)
        self.btnRefresh1.clicked.connect(self.refresh1)
        self.btnEdit1.clicked.connect(self.edit1)
        self.btnLoadAll1.clicked.connect(self.loadData1)
        self.btnSearch1.clicked.connect(self.search1)
        self.btnDelete1.clicked.connect(self.delete1)
        self.btnExit.clicked.connect(self.exit)
        self.loadData1()
        self.UiComponents()
    def UiComponents(self):
        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
        cursor = sqliteConnection.cursor()
        print("Successfully Connected to SQLite")

        cursor.execute("SELECT id FROM subjects order by id")
        
        sqliteConnection.commit()
        rows = cursor.fetchall()

        for row in rows:
            self.cbId1.addItem(str(row[0]))
        cursor.close()
        self.cbId1.activated.connect(self.getInfor1)
    # mon hoc
    def getInfor1(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT * FROM subjects WHERE id = ?", (self.cbId1.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone();
            cursor.close()

            self.tfTenMon.setText(results[1])
            self.tfSoBuoi.setText(str(results[2]))
            self.cbKi.setCurrentText(str(results[3]))
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def save1(self):
        tenMon = self.tfTenMon.text()
        soBuoi = self.tfSoBuoi.text()
        ki = self.cbKi.currentText()
        if isRequiredFiled(tenMon) == False or isRequiredFiled(soBuoi) == False:
            self.showdialog("Nhập đầy đủ thông tin.")
        elif isValidString(tenMon) == False:
            self.showdialog("Tên môn học không hợp lệ.")
        elif isValidInteger(soBuoi) == False:
            self.showdialog("Số buổi không hợp lệ.")
        else:
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO subjects(ten, soBuoi, semester_id) VALUES(?,?,?)", (tenMon, soBuoi, int(ki)))   
            
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Thêm môn học thành công.")
                self.loadData1()
                self.refresh1()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def edit1(self):
        id = self.cbId1.currentText()
        tenMon = self.tfTenMon.text()
        soBuoi = self.tfSoBuoi.text()
        ky = self.cbKi.currentText()
        if isRequiredFiled(id):
            self.showdialog("Chọn môn học cần sửa.")
        elif isRequiredFiled(tenMon) == False or isRequiredFiled(soBuoi) == False:
            self.showdialog("Nhập đầy đủ thông tin.")
        elif isValidString(tenMon) == False:
            self.showdialog("Tên môn học không hợp lệ.")
        elif isValidInteger(soBuoi) == False:
            self.showdialog("Số buổi không hợp lệ.")
        else:
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE subjects SET ten = ?, soBuoi = ?, semester_id = ? WHERE id = ?", (tenMon, soBuoi, int(ky), id))   
            
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Sửa môn học thành công.")
                self.loadData1()
                self.refresh1()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def delete1(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.cbId1.currentText()
            if isRequiredFiled(id) == False:
                self.showdialog("Chọn môn học cần xóa.")
            else:
                try:
                    sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM subjects WHERE id = ?", (id,))
                
                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Xóa môn học thành công.")
                    self.tableWidget1.setRowCount(0)
                    self.loadData1()
                    self.refresh1()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def search1(self):
        criteria = self.cbSearch1.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Chọn tiêu chí tìm kiếm.")
        else:
            if criteria == "ID môn học":
                id = self.tfSearch1.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Nhập ID môn học.")
                elif isValidInteger(id) == False:
                    self.showdialog("ID môn học không hợp lệ.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM subjects WHERE id =" + id
                        self.tableWidget1.setRowCount(1)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget1.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget1.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget1.setItem(tablerow,2,QtWidgets.QTableWidgetItem(str(row[2])))
                            self.tableWidget1.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Tên môn học":
                name = self.tfSearch1.text()
                if isRequiredFiled(name) == False:
                    self.showdialog("Nhập tên môn học.")
                elif isValidString(name) == False:
                    self.showdialog("Tên môn học không hợp lệ.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM subjects WHERE ten = '" + name + "'"
                        self.tableWidget1.setRowCount(1)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget1.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget1.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget1.setItem(tablerow,2,QtWidgets.QTableWidgetItem(str(row[2])))
                            self.tableWidget1.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Kì":
                self.tableWidget1.setRowCount(0)
                ki = self.tfSearch1.text()
                if isRequiredFiled(ki) == False:
                    self.showdialog("Chọn kì.")
                elif isValidInteger(ki) == False:
                    self.showdialog("Kì không hợp lệ.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM subjects WHERE semester_id =" + ki 
                        self.tableWidget1.setRowCount(10)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget1.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget1.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget1.setItem(tablerow,2,QtWidgets.QTableWidgetItem(str(row[2])))
                            self.tableWidget1.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
    def loadData1(self):
        try:          
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            query = "SELECT * FROM subjects"
            self.tableWidget1.setRowCount(10)
            tablerow=0
            for row in cursor.execute(query):
                self.tableWidget1.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                self.tableWidget1.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                self.tableWidget1.setItem(tablerow,2,QtWidgets.QTableWidgetItem(str(row[2])))
                self.tableWidget1.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                tablerow+=1
            sqliteConnection.commit()
        
            cursor.close()

        except sqlite3.Error as error:
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def refresh1(self):
        self.tfTenMon.setText("")
        self.tfSoBuoi.setText("")
        self.cbKi.setCurrentText("1")
        self.cbId1.clear()
        self.UiComponents()
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)
# class
class LopHoc(QDialog):
    def __init__(self):
        super(LopHoc, self).__init__()
        loadUi("./qt designer/quanlylophoc.ui",self)
        self.btnRefresh1.clicked.connect(self.refresh1)
        self.btnAdd1.clicked.connect(self.add1)
        self.btnUpdate1.clicked.connect(self.update1)
        self.btnLoadAll1.clicked.connect(self.loadData1)
        self.btnDel1.clicked.connect(self.delete1)
        self.btnRefresh2.clicked.connect(self.refresh2)
        self.btnAdd2.clicked.connect(self.add2)
        self.btnUpdate2.clicked.connect(self.update2)
        self.btnLoadAll2.clicked.connect(self.loadData2)
        self.btnDel2.clicked.connect(self.delete2)
        self.btnSearch1.clicked.connect(self.search1)
        self.btnSearch2.clicked.connect(self.search2)
        self.btnExit.clicked.connect(self.Exit)
        self.loadData1()
        self.loadData2()
        self.UiComponents()
    def add1(self):
        tenLop = self.tfTenLop.text()
        diaDiem = self.tfDiaDiem.text()
        if isRequiredFiled(tenLop) == False or isRequiredFiled(diaDiem) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin.")
        else:
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO class (ten, diaDiem) values(?, ?)", (tenLop, diaDiem))
            
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Thêm thành công")
                self.loadData1()
                self.refresh1()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def loadData1(self):
        connection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
        cur = connection.cursor()
        sqlquery="select * from class"

        self.tableWidget.setRowCount(10)
        tablerow=0
        for row in cur.execute(sqlquery):
            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
            tablerow+=1
        connection.close()
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)

    def refresh1(self):
        self.tfTenLop.setText("")
        self.tfDiaDiem.setText("")
        self.cbIdLopHoc.clear()
        self.UiComponents()
    def UiComponents(self):
        # lay id class
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM class order by id")
            
            sqliteConnection.commit()
            rows = cursor.fetchall()

            for row in rows:
                self.cbIdLopHoc.addItem(str(row[0]))
                self.cbIdLopHoc2.addItem(str(row[0]))
            cursor.close()
            self.cbIdLopHoc.activated.connect(self.getInfor)
        except sqlite3.Error as error:
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
        # lay id sinh vien
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM students order by id")
            
            sqliteConnection.commit()
            rows = cursor.fetchall()

            for row in rows:
                self.cbIdSv.addItem(str(row[0]))
            cursor.close()
            self.cbIdSv.activated.connect(self.getInfor2)
        except sqlite3.Error as error:
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInfor(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT * FROM class WHERE id = ?", (self.cbIdLopHoc.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()

            self.tfTenLop.setText(results[1])
            self.tfDiaDiem.setText(results[2])
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def update1(self):
        id = self.cbIdLopHoc.currentText()
        tenLop = self.tfTenLop.text()
        diaDiem = self.tfDiaDiem.text()
        if isRequiredFiled(id) == False:
            self.showdialog("Vui lòng chọn lớp học cần sửa.")
        elif isRequiredFiled(tenLop) == False or isRequiredFiled(diaDiem) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin.")
        else:
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE class SET ten = ?, diaDiem = ? WHERE id = ?", (tenLop,diaDiem , id))
            
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Sửa thành công")
                self.loadData1()
                self.refresh1()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def delete1(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.cbIdLopHoc.currentText()
            if isRequiredFiled(id) == False:
                self.showdialog("Vui lòng chọn lớp học cần xóa.")
            else:
                try:
                    sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM class WHERE id = ?", (id,))
                
                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Xóa thành công")
                    self.tableWidget.setRowCount(0)
                    self.loadData1()
                    self.refresh1()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def search1(self):
        criteria = self.cbSearch1.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Vui lòng chọn tiêu chí cần tìm.")
        else:
            if criteria == "ID lớp học":
                id = self.tfSearch1.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Vui lòng nhập ID lớp học cần tìm.")
                elif isValidInteger(id) == False:
                    self.showdialog("ID lớp học phải là số nguyên.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM class WHERE id =" + id
                        self.tableWidget.setRowCount(1)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Tên lớp":
                name = self.tfSearch1.text()
                if isRequiredFiled(name) == False:
                    self.showdialog("Vui lòng nhập tên lớp học cần tìm.")
                elif isValidString(name) == False:
                    self.showdialog("Tên lớp học phải là chuỗi.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM class WHERE ten LIKE '%"+ name + "%'"
                        self.tableWidget.setRowCount(1)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
    def add2(self):
        idSV = self.cbIdSv.currentText()
        idLopHoc = self.cbIdLopHoc2.currentText()
        ngayVao = self.dateIn.text()
        ngayRa = self.dateOut.text()
        if isRequiredFiled(idSV) == False:
            self.showdialog("Vui lòng chọn sinh viên cần thêm.")
        elif isRequiredFiled(idLopHoc) == False:
            self.showdialog("Vui lòng chọn lớp học cần thêm.")
        else:
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO classMember (student_id,class_id, ngayRa, ngayVao) values(?,?, ?, ?)", (idSV,idLopHoc,ngayRa,ngayVao))
            
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Thêm thành công")
                self.loadData2()
                self.refresh2()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def refresh2(self):
        qDate=QDate(2015,1,1)
        self.cbIdSv.clear()
        self.cbIdLopHoc2.clear()
        self.tfTenSV.setText("")
        self.dateIn.setDate(qDate)
        self.dateOut.setDate(qDate)
        self.UiComponents()
    def loadData2(self):
        connection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
        cur = connection.cursor()
        sqlquery="select * from classMember"

        self.tableWidget2.setRowCount(10)
        tablerow=0
        for row in cur.execute(sqlquery):
            self.tableWidget2.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[1])))
            self.tableWidget2.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[2])))
            self.tableWidget2.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[3]))
            self.tableWidget2.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[4]))
            tablerow+=1
        connection.close()
    def getInfor2(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT ten FROM students WHERE id = ?", (self.cbIdSv.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()

            self.tfTenSV.setText(results[0])
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def update2(self):
        idSV = self.cbIdSv.currentText()
        idLopHoc = self.cbIdLopHoc2.currentText()
        ngayVao = self.dateIn.text()
        ngayRa =self.dateOut.text()
        if isRequiredFiled(idSV) == False:
            self.showdialog("Vui lòng chọn sinh viên cần sửa.")
        elif isRequiredFiled(idLopHoc) == False:
            self.showdialog("Vui lòng chọn lớp học cần sửa.")
        else:
            # lay id bang classMember
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("SELECT id FROM classMember WHERE student_id=? AND class_id=?",(idSV,idLopHoc))
                id=cursor.fetchone()
                sqliteConnection.commit()
                cursor.close()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
            # sua ban ghi
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE classMember set student_id = ?, class_id = ?, ngayRa = ?, ngayVao = ? where id = ?",(idSV,idLopHoc,ngayRa, ngayVao,id[0]))
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Sửa thành công")
                self.loadData2()
                self.refresh2()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def delete2(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            idSV = self.cbIdSv.currentText()
            idLopHoc = self.cbIdLopHoc2.currentText()
            if isRequiredFiled(idSV) == False:
                self.showdialog("Vui lòng chọn sinh viên cần xóa.")
            elif isRequiredFiled(idLopHoc) == False:
                self.showdialog("Vui lòng chọn lớp học cần xóa.")
            else:
                try:
                    sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM classMember WHERE  student_id=? AND class_id=?", (idSV,idLopHoc))
                
                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Xóa thành công")
                    self.tableWidget.setRowCount(0)
                    self.loadData2()
                    self.refresh2()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def search2(self):
        self.tableWidget2.setRowCount(0)
        criteria = self.cbSearch2.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Vui lòng chọn tiêu chí tìm kiếm.")
        else:
            if criteria == "ID SV":
                id = self.tfSearch2.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Vui lòng nhập ID sinh viên.")
                elif isValidInteger(id) == False:
                    self.showdialog("ID sinh viên phải là số.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                
                        self.tableWidget2.setRowCount(50)
                        tablerow=0
                        for row in cursor.execute("SELECT * FROM classMember WHERE student_id =?",(id,)):
                            self.tableWidget2.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget2.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[2])))
                            self.tableWidget2.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget2.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[4]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "ID lớp học":
                idLopHoc = self.tfSearch2.text()
                if isRequiredFiled(idLopHoc) == False:
                    self.showdialog("Vui lòng nhập ID lớp học.")
                elif isValidInteger(idLopHoc) == False:
                    self.showdialog("ID lớp học phải là số.")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        query = "SELECT * FROM classMember WHERE class_id =" + idLopHoc
                        self.tableWidget2.setRowCount(10)
                        tablerow=0
                        for row in cursor.execute(query):
                            self.tableWidget2.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget2.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[2])))
                            self.tableWidget2.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget2.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[4]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
    def Exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)
# schedule
class Schedule(QDialog):

    def __init__(self):
        super(Schedule, self).__init__()
        loadUi("./qt designer/thongtinlichhoc.ui",self)
        self.btnAdd.clicked.connect(self.add)
        self.btnLoadAll.clicked.connect(self.loadData)
        self.btnUpdate.clicked.connect(self.update)
        self.btnDelete.clicked.connect(self.delete)
        self.btnRefresh.clicked.connect(self.refresh)
        self.btnSearch.clicked.connect(self.search)
        self.btnExit.clicked.connect(self.exit)
        self.tableWidget.itemDoubleClicked.connect(self.on_click)
        self.UiComponents()
        self.loadData()
    def UiComponents(self):
        # lay id giao vien
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM teachers order by id")
        
            sqliteConnection.commit()
            rows = cursor.fetchall()

            for row in rows:
                self.cbIdGV.addItem(str(row[0]))
            cursor.close()
            self.cbIdGV.activated.connect(self.getInforGV)
        except sqlite3.Error as error:
              print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
        # lay id lop hoc
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM class order by id")
        
            sqliteConnection.commit()
            rows = cursor.fetchall()
           
            for row in rows:
                self.cbIdLop.addItem(str(row[0]))
            cursor.close()
            self.cbIdLop.activated.connect(self.getInforClass)
        except sqlite3.Error as error:
                print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
        # lay id mon hoc
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT id FROM subjects order by id")
        
            sqliteConnection.commit()
            rows = cursor.fetchall()
       
            for row in rows:
                self.cbIdMon.addItem(str(row[0]))
            cursor.close()
            self.cbIdMon.activated.connect(self.getInforSubject)
        except sqlite3.Error as error:
                print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInforSchedule(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT teacher_id, subject_id, class_id, batDau, ketThuc FROM schedule WHERE id = ?", (self.cbId.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()

            self.cbIdGV.setCurrentText(str(results[0]))
            self.cbIdMon.setCurrentText(str(results[1]))
            self.cbIdLop.setCurrentText(str(results[2]))           
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInforGV(self) :
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT ten FROM teachers WHERE id = ?", (self.cbIdGV.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()

            self.tfGV.setText(results[0])
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInforSubject(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT ten FROM subjects WHERE id = ?", (self.cbIdMon.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()

            self.tfTenMon.setText(results[0])
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInforClass(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            cursor.execute("SELECT ten FROM class WHERE id = ?", (self.cbIdLop.currentText(),)) 
        
            sqliteConnection.commit()
            results = cursor.fetchone()
            cursor.close()

            self.tfTenLop.setText(results[0])
        except sqlite3.Error as error:
           print("Failed to get data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def add(self):
        start = self.deStart.text()
        end = self.deEnd.text()
        idGV = self.cbIdGV.currentText()
        idLopHoc = self.cbIdLop.currentText()
        idMon = self.cbIdMon.currentText()
        if isRequiredFiled(idGV) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        elif isRequiredFiled(idLopHoc) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        elif isRequiredFiled(idMon) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        else:
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("INSERT INTO schedule (teacher_id, subject_id, class_id, batDau, ketThuc) values(?, ?, ?, ?, ?)", (idGV,idMon,idLopHoc,start,end))
            
                sqliteConnection.commit()
                print("Record inserted successfully into SqliteDb_developers table ", cursor.rowcount)
                cursor.close()
                self.showdialog("Thêm thành công")
                self.tableWidget.setRowCount(0)
                self.loadData()
                self.refresh()
            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def loadData(self):
        connection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
        cur = connection.cursor()
        sqlquery="select s.id, s.teacher_id, t.ten, s.subject_id, sb.ten, s.class_id, c.ten, s.batDau, s.ketThuc from schedule as s inner join teachers as t on s.teacher_id = t.id inner join subjects as sb on s.subject_id = sb.id inner join class as c on s.class_id = c.id "

        self.tableWidget.setRowCount(50)
        tablerow=0
        for row in cur.execute(sqlquery):
            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(str(row[5])))
            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))
            self.tableWidget.setItem(tablerow,8,QtWidgets.QTableWidgetItem(row[8]))
            tablerow+=1
        connection.close()
    @QtCore.pyqtSlot(QtWidgets.QTableWidgetItem)
    def on_click(self, item):
        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
        cursor = sqliteConnection.cursor()
        print("Successfully Connected to SQLite")

        cursor.execute("select s.id, s.teacher_id, t.ten, s.subject_id, sb.ten, s.class_id, c.ten, s.batDau, s.ketThuc from schedule as s inner join teachers as t on s.teacher_id = t.id inner join subjects as sb on s.subject_id = sb.id inner join class as c on s.class_id = c.id where s.id = ?", (item.text(),))
        
        sqliteConnection.commit()
        rows = cursor.fetchall()

        for row in rows:
            self.tfId.setText(str(row[0]))
            self.cbIdGV.setCurrentText(str(row[1]))
            self.tfGV.setText(row[2])
            self.cbIdMon.setCurrentText(str(row[3]))
            self.tfTenMon.setText(row[4])
            self.cbIdLop.setCurrentText(str(row[5]))
            self.tfTenLop.setText(row[6])
            dateStart = QtCore.QDateTime.fromString(row[7], 'yyyy-MM-dd hh:mm:ss')
            self.deStart.setDateTime(dateStart)
            dateEnd = QtCore.QDateTime.fromString(row[8], 'yyyy-MM-dd hh:mm:ss')
            self.deEnd.setDateTime(dateEnd)
        cursor.close()
    def update(self):
        id = self.tfId.text()
        idGV = self.cbIdGV.currentText()
        idLopHoc = self.cbIdLop.currentText()
        idMon = self.cbIdMon.currentText()
        start = self.deStart.text()
        end = self.deEnd.text()
        if isRequiredFiled(id) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        elif isRequiredFiled(idGV) == False or isRequiredFiled(idLopHoc) == False or isRequiredFiled(idMon) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        else:
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                cursor.execute("UPDATE schedule set teacher_id = ?, subject_id = ?, class_id = ?, batDau = ?, ketThuc = ? where id = ?", (idGV, idMon, idLopHoc,start ,end , id,))
                sqliteConnection.commit()
                cursor.close()
                self.showdialog("Sửa thành công")
                self.loadData()
                self.refresh()
            except sqlite3.Error as error:
                print("Failed to update data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                print("The SQLite connection is closed")
    def delete(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.tfId.text()
            if isRequiredFiled(id) == False:
                self.showdialog("Vui lòng nhập đầy đủ thông tin")
            else:
                try:
                    sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM schedule WHERE id = ?", (id,))
                
                    sqliteConnection.commit()
                    cursor.close()
                    self.tableWidget.setRowCount(0)
                    self.loadData()
                    self.refresh()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
    def search(self):
        self.tableWidget.setRowCount(0)
        criteria = self.cbSearch.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        else:
            if criteria == "ID giáo viên":
                id = self.tfSearch.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Vui lòng nhập đầy đủ thông tin")
                elif isValidInteger(id) == False:
                    self.showdialog("Vui lòng nhập số")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                    
                        self.tableWidget.setRowCount(50)
                        tablerow=0
                        for row in cursor.execute("select s.id, s.teacher_id, t.ten, s.subject_id, sb.ten, s.class_id, c.ten, s.batDau, s.ketThuc from schedule as s inner join teachers as t on s.teacher_id = t.id inner join subjects as sb on s.subject_id = sb.id inner join class as c on s.class_id = c.id where s.teacher_id = ?" , (id,)):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(str(row[5])))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))
                            self.tableWidget.setItem(tablerow,8,QtWidgets.QTableWidgetItem(row[8]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()
                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "ID môn":
                idMon = self.tfSearch.text()
                if isRequiredFiled(idMon) == False:
                    self.showdialog("Vui lòng nhập đầy đủ thông tin")
                elif isValidInteger(idMon) == False:
                    self.showdialog("Vui lòng nhập số")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        self.tableWidget.setRowCount(50)
                        tablerow=0
                        for row in cursor.execute("select s.id, s.teacher_id, t.ten, s.subject_id, sb.ten, s.class_id, c.ten, s.batDau, s.ketThuc from schedule as s inner join teachers as t on s.teacher_id = t.id inner join subjects as sb on s.subject_id = sb.id inner join class as c on s.class_id = c.id where s.subject_id = ?" , (idMon,)):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(str(row[5])))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))
                            self.tableWidget.setItem(tablerow,8,QtWidgets.QTableWidgetItem(row[8]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "ID lớp":
                idClass = self.tfSearch.text()
                if isRequiredFiled(idClass) == False:
                    self.showdialog("Vui lòng nhập đầy đủ thông tin")
                elif isValidInteger(idClass) == False:
                    self.showdialog("Vui lòng nhập số")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")

                        self.tableWidget.setRowCount(50)
                        tablerow=0
                        for row in cursor.execute("select s.id, s.teacher_id, t.ten, s.subject_id, sb.ten, s.class_id, c.ten, s.batDau, s.ketThuc from schedule as s inner join teachers as t on s.teacher_id = t.id inner join subjects as sb on s.subject_id = sb.id inner join class as c on s.class_id = c.id where s.class_id = ?" , (idClass,)):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(str(row[5])))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))
                            self.tableWidget.setItem(tablerow,8,QtWidgets.QTableWidgetItem(row[8]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
    def refresh(self):
        self.tfId.clear()
        self.cbIdGV.clear()
        self.cbIdLop.clear()
        self.cbIdMon.clear()
        self.tfGV.setText("")
        self.tfTenMon.setText("")
        self.tfTenLop.setText("")
        self.UiComponents()
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)
#popup
class Popup(QDialog):
    def __init__(self, id, parent):
        super().__init__(parent)
        self.resize(600, 300)
        self.label = QLabel(self)
        self.showImage(id)
    def showImage(self, id):
        try:          
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")
             
            cursor.execute("select image from attendance where id = ?", (id,))
            record = cursor.fetchone()[0]
            if record is not None:
                path = base64.b85decode(record).decode("utf-8")
                sqliteConnection.commit()
                self.label.setPixmap(QtGui.QPixmap(path))
                self.label.setMinimumSize(1, 1)
                self.label.setScaledContents(True)

            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
# attendance
class Attendence(QDialog):
    def __init__(self):
        super(Attendence, self).__init__()
        loadUi("./qt designer/quanlythongtindiemdanh.ui",self)
        self.btnExit.clicked.connect(self.exit)
        self.tableWidget.itemDoubleClicked.connect(self.on_click)
        self.btnDelete.clicked.connect(self.delete)
        self.btnRefresh.clicked.connect(self.refresh)
        self.btnLoadAll.clicked.connect(self.UiComponents)
        self.btnExport.clicked.connect(self.export)
        self.btnUpdate.clicked.connect(self.update)
        self.btnSearch.clicked.connect(self.search)
        self.btnFilter.clicked.connect(self.filter)   
        self.btnImage.clicked.connect(self.launchPopup)   
        self.UiComponents()
    
    def launchPopup(self):
        id = self.tfIdDiemDanh.text()
        if isRequiredFiled(id) == False:
            self.showdialog("Vui lòng nhập đầy đủ thông tin")
        else:
            self.popup = Popup(id, self)
            self.popup.show()
    def export(self):
        list = []
        listItem = []
        row = 0
        try:          
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")
             
            self.tableWidget.setRowCount(100)
            sql = "select count(a.id) from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id"
            for row in range(int(cursor.execute(sql).fetchone()[0])):
                for col in range(8):
                    item = self.tableWidget.item(row,col)
                    if item:
                        listItem.append(item.text())
                list.append(listItem)
                listItem = []
            sqliteConnection.commit()
            
            cursor.close()
        except sqlite3.Error as error:
            self.showdialog("Không thể export")
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")

        data = tuple(list)
        row = 1
        col = 0
        workbook = xlsxwriter.Workbook("C:\\Users\\Admin\\Downloads\\diem danh.xlsx")
 
        worksheet = workbook.add_worksheet("My sheet")
        worksheet.write('A1', 'ID')
        worksheet.write('B1', 'ID sinh viên')
        worksheet.write('C1', 'Tên')
        worksheet.write('D1', 'Lớp')
        worksheet.write('E1', 'Giờ vào')
        worksheet.write('F1', 'Giờ ra')
        worksheet.write('G1', 'Ngày')
        worksheet.write('H1', 'Điểm danh')
        # Iterate over the data and write it out row by row.
        for id, idSv, name, className, timeIn, timeOut, date, attendence in (data):
            worksheet.write(row, col, id)
            worksheet.write(row, col + 1, int(idSv))
            worksheet.write(row, col + 2, str(name))
            worksheet.write(row, col + 3, str(className))
            worksheet.write(row, col + 4, timeIn)
            worksheet.write(row, col + 5, timeOut) 
            worksheet.write(row, col + 6, date)
            worksheet.write(row, col + 7, attendence)
            row += 1
        workbook.close()
        self.showdialog("Tạo file excel thành công")
    def filter(self):
        self.tableWidget.setRowCount(0)
        today = date.today()
        d1 = today.strftime("%Y-%m-%d")
        try:          
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")
             
            self.tableWidget.setRowCount(100)
            sql = "select a.id, a.student_id, st.ten, c.ten, TIME(s.batDau), TIME(s.ketThuc), a.ngayDiemDanh, a.trangThai from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id where  DATE(a.ngayDiemDanh) = '" + d1 + "'"
            tablerow=0
            for row in cursor.execute(sql):
                self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
                self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))  
                tablerow+=1
            sqliteConnection.commit()
            
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
    def search(self):
        criteria = self.cbSearch.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Vui lòng chọn tiêu chí tìm kiếm")
        else:
            if criteria == "ID sinh viên":
                id = self.tfSearch.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Vui lòng nhập ID sinh viên")
                elif isValidInteger(id) == False:
                    self.showdialog("ID sinh viên phải là số")
                else:
                    self.tableWidget.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                    
                        self.tableWidget.setRowCount(100)
                        tablerow=0
                        for row in cursor.execute("select a.id, a.student_id, st.ten, c.ten, TIME(s.batDau), TIME(s.ketThuc), a.ngayDiemDanh, a.trangThai from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id where a.student_id = ?", [id]):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))  
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()
                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Tên sinh viên":
                ten = self.tfSearch.text()
                if isRequiredFiled(ten) == False:
                    self.showdialog("Vui lòng nhập tên sinh viên")
                elif isValidString(ten) == False:
                    self.showdialog("Tên sinh viên không hợp lệ")
                else:
                    self.tableWidget.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                        sql = "select a.id, a.student_id, st.ten, c.ten, TIME(s.batDau), TIME(s.ketThuc), a.ngayDiemDanh, a.trangThai from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id where st.ten like '%" + ten +  "%'"
                        self.tableWidget.setRowCount(100)
                        tablerow=0
                        for row in cursor.execute(sql):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))  
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Lớp":
                lop = self.tfSearch.text()
                if isRequiredFiled(lop) == False:
                    self.showdialog("Vui lòng nhập lớp")
                elif isValidString(lop) == False:
                    self.showdialog("Lớp không hợp lệ")
                else:
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                        sql = "select a.id, a.student_id, st.ten, c.ten, TIME(s.batDau), TIME(s.ketThuc), a.ngayDiemDanh, a.trangThai from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id where c.ten like '%" + lop+  "%'"
                        self.tableWidget.setRowCount(100)
                        tablerow=0
                        for row in cursor.execute(sql):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
                            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
                            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))  
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
    def update(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn sửa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.tfIdDiemDanh.text()
            time = self.tfNgay.text()
            diemDanh = self.tfDiemDanh.text()
            if isRequiredFiled(id) == False:
                self.showdialog("Vui lòng nhập id")
            elif isRequiredFiled(time) == False:
                self.showdialog("Vui lòng nhập ngày")
            elif isValidDateTime(time) == False:
                self.showdialog("Ngày giờ không hợp lệ")
            elif isRequiredFiled(diemDanh) == False:
                self.showdialog("Vui lòng nhập trạng thái")
            else:
                try:
                    sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("UPDATE attendance set ngayDiemDanh = ?, trangThai = ? where id = ?", (time, diemDanh, id))
                    sqliteConnection.commit()
                    cursor.close()
                    self.showdialog("Sửa thành công")
                    self.tableWidget.setRowCount(0)
                    self.UiComponents()
                    self.refresh()
                except sqlite3.Error as error:
                    print("Failed to update data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def delete(self):
        ret = QMessageBox.question(self, 'MessageBox', "Có muốn xóa không?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)

        if ret == QMessageBox.Yes:
            id = self.tfIdDiemDanh.text()
            if isRequiredFiled(id) == False:
                self.showdialog("Vui lòng nhập id")
            else:
                try:
                    sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                    cursor = sqliteConnection.cursor()
                    print("Successfully Connected to SQLite")

                    cursor.execute("DELETE FROM attendance WHERE id = ?", (id,))
                
                    sqliteConnection.commit()
                    cursor.close()
                    self.tableWidget.setRowCount(0)
                    self.UiComponents()
                    self.refresh()
                except sqlite3.Error as error:
                    print("Failed to delete data into sqlite table" , error)
                finally:
                    if sqliteConnection:
                        sqliteConnection.close()
                    print("The SQLite connection is closed")
    def refresh(self):
        self.tfIdDiemDanh.setText("")
        self.tfIdSV.setText("")
        self.tfTenSV.setText("")
        self.tfLop.setText("")
        self.tfGioVao.setText("")
        self.tfGioRa.setText("")
        self.tfNgay.setText("")
        self.tfDiemDanh.setText("")
    def UiComponents(self):
        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
        cursor = sqliteConnection.cursor()
        print("Successfully Connected to SQLite")

        sql = ("select a.id, a.student_id, st.ten, c.ten, TIME(s.batDau), TIME(s.ketThuc), a.ngayDiemDanh, a.trangThai from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id")
        
        self.tableWidget.setRowCount(50)
        tablerow = 0
        for row in cursor.execute(sql):
            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(str(row[1])))
            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
            self.tableWidget.setItem(tablerow,5,QtWidgets.QTableWidgetItem(row[5]))
            self.tableWidget.setItem(tablerow,6,QtWidgets.QTableWidgetItem(row[6]))
            self.tableWidget.setItem(tablerow,7,QtWidgets.QTableWidgetItem(row[7]))      
            tablerow+=1
        sqliteConnection.close()
    @QtCore.pyqtSlot(QtWidgets.QTableWidgetItem)
    def on_click(self, item):
        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
        cursor = sqliteConnection.cursor()
        print("Successfully Connected to SQLite")

        cursor.execute("select a.id, a.student_id, st.ten, c.ten, TIME(s.batDau), TIME(s.ketThuc), a.ngayDiemDanh, a.trangThai from attendance as a inner join schedule as s on a.schedule_id = s.id inner join class as c on s.class_id = c.id inner join students as st on a.student_id = st.id where a.id = ?", (item.text(),))
        
        sqliteConnection.commit()
        rows = cursor.fetchall()

        for row in rows:
            self.tfIdDiemDanh.setText(str(row[0]))
            self.tfIdSV.setText(str(row[1]))
            self.tfTenSV.setText(row[2])
            self.tfLop.setText(row[3])
            self.tfGioVao.setText(row[4])
            self.tfGioRa.setText(row[5])
            self.tfNgay.setText(row[6])
            self.tfDiemDanh.setText(row[7])
        cursor.close()
    
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1) 
# recognition
class Recognize(QDialog):
    def __init__(self):
        super(Recognize, self).__init__()
        loadUi("./qt designer/hethongdiemdanhkhuonmat.ui",self)
        self.btnDetection.clicked.connect(lambda: self.run('models', 'models/your_model.pkl', video_file=None, output_file='demo.avi'))
        self.btnExit.clicked.connect(self.exit)
        self.UiComponents()
    def UiComponents(self):
        try:
            date = datetime.today().strftime('%Y-%m-%d')
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT m.ten from schedule as s inner join subjects as m on s.subject_id = m.id where DATE(batDau) =" + "'" + date + "'"
            cursor.execute(sqlite_select_query)
            rows = cursor.fetchall()
            for row in rows:
                self.cbMon.addItem(str(row[0]))
            self.cbMon.activated.connect(self.getInforSubject)
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getInforSubject(self):
        try:
            tenMon = self.cbMon.currentText()
            date = datetime.today().strftime('%Y-%m-%d')

            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT s.class_id, m.ten, TIME(s.batDau), TIME(s.ketThuc) from schedule as s inner join subjects as m on s.subject_id = m.id where DATE(batDau) =" + "'" + date + "'" + "and m.ten = " + "'" + tenMon + "'"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchone()
            self.tfIdLop.setText(str(record[0]))
            self.tfTenMon.setText(str(record[1]))
            self.tfThoiGian.setText(str(record[2]) + " - " + str(record[3]))
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
    def add_overlays(self, frame, faces, frame_rate, colors, confidence=0.8):
        if faces is not None:
            for idx, face in enumerate(faces):
                face_bb = face.bounding_box.astype(int)
                cv2.rectangle(frame, (face_bb[0], face_bb[1]), (face_bb[2], face_bb[3]), colors[idx], 2)
                if face.name and face.prob:
                    if face.prob > confidence:
                        class_name = face.name
                    else:
                        class_name = 'Unknow'
                    cv2.putText(frame, class_name, (face_bb[0], face_bb[3] + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            colors[idx], thickness=2, lineType=2)
                    cv2.putText(frame, '{:.02f}'.format(face.prob * 100), (face_bb[0], face_bb[3] + 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors[idx], thickness=1, lineType=2)

        cv2.putText(frame, str(frame_rate) + " fps", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0),
                thickness=2, lineType=2)
    def getScheduleId(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT id from attendance"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchall()    
            # get max id
            if record == None:
                max_id = 1
            else:
                max_id = max(record)
            cursor.close()
            return max_id[0]
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed")
    def getStudentId(self, name):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            cursor.execute("select student_id from models where ten = ?", [name])
            record = cursor.fetchone()
    
            cursor.close()
            return record[0]
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
            print("The SQLite connection is closed") 
    def markAttendance(self, name, path):
        check = "X"
        # lay id sinh vien
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT s.id, s.ten from students as s inner join models as m on s.id = m.student_id where m.ten =" + "'" + name + "'"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchone()
            now = datetime.now().time()
            student_id = record[0]
            student_name = record[1]                      
            self.tfIdSV.setText(str(student_id))
            self.tfTenSV.setText(str(student_name))
            self.tfDD.setText(str(now))
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
        # lay id, thoi gian ket thuc schedule        
        try:
            tenMon = self.cbMon.currentText()
            today = datetime.today().strftime('%Y-%m-%d')

            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT s.id, TIME(s.ketThuc) from schedule as s inner join subjects as m on s.subject_id = m.id where DATE(batDau) =" + "'" + today + "'" + "and m.ten = " + "'" + tenMon + "'"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchone()
            schedule_id = record[0]  
            end = record[1]
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
        endTime = self.tfEnd.text()
        current_time = now.strftime("%H:%M:%S")
        stdPhoto =  base64.b85encode(path.encode("utf-8"))
        if(current_time < endTime):
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")

                sqlite_insert_blob_query = """insert into attendance (schedule_id, student_id, ngayDiemDanh, trangThai, image)  values(?, ?, ?, ?, ?)"""

                # Convert data into tuple format
                data_tuple = (schedule_id, student_id, today + " " + current_time, check, stdPhoto)
                cursor.execute(sqlite_insert_blob_query, data_tuple)
                sqliteConnection.commit()
                print("Record inserted successfully into table ")
                cursor.close()

            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                    print("The SQLite connection is closed")
        elif current_time > endTime and current_time < end:
            try:
                sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                cursor = sqliteConnection.cursor()
                print("Successfully Connected to SQLite")
                time_object = datetime.strptime(endTime, '%H:%M:%S').time()

                duration = datetime.combine(date.min, now) - datetime.combine(date.min, time_object)
                cursor.execute("INSERT INTO attendance (schedule_id, student_id, ngayDiemDanh, trangThai, image) values(?, ?, ?, ?, ?)", (schedule_id, student_id, today + " " + current_time, "Muộn " + str(round(duration.total_seconds() / 60)) + " phút", stdPhoto))

                sqliteConnection.commit()
                print("Record inserted successfully into table ")
                cursor.close()

            except sqlite3.Error as error:
                print("Failed to insert data into sqlite table" , error)
            finally:
                if sqliteConnection:
                    sqliteConnection.close()
                    print("The SQLite connection is closed")

    def run(self, model_checkpoint, classifier, video_file=None, output_file=None):
        mon = self.cbMon.currentText()
        endTime = self.tfEnd.text()
        if isRequiredFiled(mon) == False:
            self.showdialog("Bạn chưa chọn môn học")
        elif isRequiredFiled(endTime) == False:
            self.showdialog("Bạn chưa nhập thời gian kết thúc")
        else:
            frame_interval = 3  # Number of frames after which to run face detection
            fps_display_interval = 5  # seconds
            frame_rate = 0
            frame_count = 0
            if video_file is not None:
                video_capture = cv2.VideoCapture(video_file)
            else:
                # Use internal camera
                video_capture = cv2.VideoCapture(0)
            ret, frame = video_capture.read()
            width = frame.shape[1]
            height = frame.shape[0]
            if output_file is not None:
                video_format = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter(output_file, video_format, 30, (width, height))
            face_recognition = Recognition(model_checkpoint, classifier)
            start_time = time.time()
            colors = np.random.uniform(0, 255, size=(1, 3))
            count = self.getScheduleId()
            list = []
            while True:
                # Capture frame-by-frame
                ret, frame = video_capture.read()
                if (frame_count % frame_interval) == 0:
                    faces = face_recognition.identify(frame)
                    if faces is not None:
                        try:
                            for face in faces:
                                if face.name != 'Unknow' and face.name not in list:
                                    count+=1
                                    path = "./image/Photo" + str(count) + ".jpg"
                                    cv2.imwrite(path, frame)
                                    self.photo.setPixmap(QtGui.QPixmap(path))
                                    self.photo.setMinimumSize(1, 1)
                                    self.photo.setScaledContents(True)
                                    self.markAttendance(face.name, path)
                                    list.append(face.name)
                                    break
                        except:
                            pass  
                    for i in range(len(colors), len(faces)):
                        colors = np.append(colors, np.random.uniform(150, 255, size=(1, 3)), axis=0)
                    # Check our current fps
                    end_time = time.time()
                    if (end_time - start_time) > fps_display_interval:
                        frame_rate = int(frame_count / (end_time - start_time))
                        start_time = time.time()
                        frame_count = 0

                self.add_overlays(frame, faces, frame_rate, colors)

                frame_count += 1
                cv2.imshow('Video', frame)
                if output_file is not None:
                    out.write(frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.absent()
                    self.refresh()
                    break

            # When everything is done, release the capture
            if output_file is not None:
                out.release()
            video_capture.release()
            cv2.destroyAllWindows()

    def absent(self):
        try:
            tenMon = self.cbMon.currentText()
            today = datetime.today().strftime('%Y-%m-%d')

            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT s.id  from schedule as s inner join subjects as m on s.subject_id = m.id where DATE(batDau) =" + "'" + today + "'" + "and m.ten = " + "'" + tenMon + "'"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchone()
            schedule_id = record[0]  # id of schedule
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
        # lay sinh vien khong diem danh
        try:
            data = ()
            list = []

            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sql = "select cm.student_id from schedule as sc inner join class as c on sc.class_id = c.id inner join classMember as cm on cm.class_id = c.id inner join subjects as m on sc.subject_id = m.id  where  DATE(sc.batDau) ='" + today + "'" + "and m.ten = '" + tenMon + "'" + "EXCEPT select student_id from attendance as a inner join schedule as s on a.schedule_id = s.id  inner join subjects as m on s.subject_id = m.id  where  DATE(s.batDau) = '" + today + "'" + "and m.ten = '" + tenMon + "'"
                                                
            for row in cursor.execute(sql):
                data = data + (schedule_id, row[0], today, "Vắng")
                list.append(data)
                data = ()
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
        # insert vao bang attendance
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            cursor.executemany('INSERT INTO attendance (schedule_id, student_id, ngayDiemDanh, trangThai) VALUES(?,?,?,?);', list)
			
            sqliteConnection.commit()
            sqliteConnection.close()

        except sqlite3.Error as error:
            print("Failed to inseart data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
    def refresh(self):
        self.photo.setPixmap(QtGui.QPixmap(""))
        self.tfIdSV.setText("")
        self.tfTenSV.setText("")
        self.tfDD.setText("")
        self.tfIdLop.setText("")
        self.tfTenMon.setText("")
        self.tfThoiGian.setText("")
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)
# Analyst
class Analyst(QDialog):
    def __init__(self):
        super(Analyst, self).__init__()
        loadUi("./qt designer/thongke.ui",self)
        self.btnExit.clicked.connect(self.exit)
        self.btnSearch1.clicked.connect(self.search1)
        self.btnLoadAll1.clicked.connect(self.loadAll1)
        self.btnExport1.clicked.connect(self.export1)
        self.btnLoadAll_2.clicked.connect(self.loadAll_2)
        self.btnSearch_2.clicked.connect(self.search_2)
        self.btnExport_2.clicked.connect(self.export_2)
        self.UiComponents()
        self.showInforOfLateStudents()
        self.showInforOfAbsentStudents()
    def export_2(self):
        list = []
        listItem = []
        row = 0
        try:          
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")
             
            sql = "select count(id) from attendance where trangThai = 'Vắng'"
            for row in range(int(cursor.execute(sql).fetchone()[0])):
                for col in range(5):
                    item = self.tableWidget_2.item(row,col)
                    if item:
                        listItem.append(item.text())
                list.append(listItem)
                listItem = []
            sqliteConnection.commit()
            
            cursor.close()
        except sqlite3.Error as error:
            self.showdialog("Không thể export")
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")

        data = tuple(list)
        row = 1
        col = 0
        workbook = xlsxwriter.Workbook("C:\\Users\\Admin\\Downloads\\thong ke vang.xlsx")
 
        worksheet = workbook.add_worksheet("My sheet")
        worksheet.write('A1', 'ID')
        worksheet.write('B1', 'Tên sinh viên')
        worksheet.write('C1', 'Ngày')
        worksheet.write('D1', 'Môn học')
        worksheet.write('E1', 'ID môn')
        # Iterate over the data and write it out row by row.
        for idSv, name,  date, subject, idSubject in (data):
            worksheet.write(row, col, idSv)
            worksheet.write(row, col + 1, str(name))
            worksheet.write(row, col + 2, str(date))
            worksheet.write(row, col + 3, str(subject))
            worksheet.write(row, col + 4, int(idSubject))
            row += 1
        workbook.close()
        self.showdialog("Tạo file excel thành công")
    def search_2(self):
        criteria = self.cbSearch_2.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Vui lòng nhập tiêu chí")
        else:
            if criteria == "ID sinh viên":
                id = self.tfSearch_2.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Vui lòng nhập ID")
                elif isValidInteger(id) == False:
                    self.showdialog("ID không hợp lệ")
                else:
                    self.tableWidget_2.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                    
                        cursor.execute("select a.student_id, s.ten, DATE(a.ngayDiemDanh), sb.ten, sc.subject_id from attendance as a inner join students as s on a.student_id = s.id inner join schedule as sc on sc.id = a.schedule_id inner join subjects as sb on sb.id = sc.subject_id where a.trangThai = 'Vắng' and a.student_id = ?", (id,))
                        rows = cursor.fetchall()
                        self.tableWidget_2.setRowCount(50)
                        tablerow = 0
                        for row in rows:
                            self.tableWidget_2.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget_2.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget_2.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget_2.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget_2.setItem(tablerow,4,QtWidgets.QTableWidgetItem(str(row[4])))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()
                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Tên sinh viên":
                ten = self.tfSearch_2.text()
                if isRequiredFiled(ten) == False:
                    self.showdialog("Vui lòng nhập tên")
                elif isValidString(ten) == False:
                    self.showdialog("Tên không hợp lệ")
                else:
                    self.tableWidget_2.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                    
                        cursor.execute("select a.student_id, s.ten, DATE(a.ngayDiemDanh), sb.ten, sc.subject_id from attendance as a inner join students as s on a.student_id = s.id inner join schedule as sc on sc.id = a.schedule_id inner join subjects as sb on sb.id = sc.subject_id where a.trangThai = 'Vắng' and s.ten like ?", [ten])
                        rows = cursor.fetchall()
                        self.tableWidget_2.setRowCount(50)
                        tablerow = 0
                        for row in rows:
                            self.tableWidget_2.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget_2.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget_2.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget_2.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget_2.setItem(tablerow,4,QtWidgets.QTableWidgetItem(str(row[4])))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()
                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                            print("The SQLite connection is closed")
            elif criteria == "Ngày":
                ngay = self.tfSearch_2.text()
                if isRequiredFiled(ngay) == False:
                    self.showdialog("Vui lòng nhập ngày")
                elif isValidDate(ngay) == False:
                    self.showdialog("Ngày không hợp lệ")
                else:
                    self.tableWidget_2.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                    
                        cursor.execute("select a.student_id, s.ten, DATE(a.ngayDiemDanh), sb.ten, sc.subject_id from attendance as a inner join students as s on a.student_id = s.id inner join schedule as sc on sc.id = a.schedule_id inner join subjects as sb on sb.id = sc.subject_id where a.trangThai = 'Vắng' and a.ngayDiemDanh = ?", [ngay])
                        rows = cursor.fetchall()
                        self.tableWidget_2.setRowCount(50)
                        tablerow = 0
                        for row in rows:
                            self.tableWidget_2.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget_2.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget_2.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget_2.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget_2.setItem(tablerow,4,QtWidgets.QTableWidgetItem(str(row[4])))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()
                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                            print("The SQLite connection is closed")
            elif criteria == "Môn":
                mon = self.tfSearch_2.text()
                if isRequiredFiled(mon) == False:
                    self.showdialog("Vui lòng nhập môn")
                elif isValidString(mon) == False:
                    self.showdialog("Môn không hợp lệ")
                else:
                    self.tableWidget_2.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                    
                        cursor.execute("select a.student_id, s.ten, DATE(a.ngayDiemDanh), sb.ten, sc.subject_id from attendance as a inner join students as s on a.student_id = s.id inner join schedule as sc on sc.id = a.schedule_id inner join subjects as sb on sb.id = sc.subject_id where a.trangThai = 'Vắng' and sb.ten =  ?", [mon])
                        rows = cursor.fetchall()
                        self.tableWidget_2.setRowCount(50)
                        tablerow = 0
                        for row in rows:
                            self.tableWidget_2.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget_2.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget_2.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget_2.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                            self.tableWidget_2.setItem(tablerow,4,QtWidgets.QTableWidgetItem(str(row[4])))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()
                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                            print("The SQLite connection is closed")
    def loadAll_2(self):
        self.showInforOfAbsentStudents()
    def showInforOfAbsentStudents(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")
            cursor.execute("select a.student_id, s.ten, DATE(a.ngayDiemDanh), sb.ten, sc.subject_id from attendance as a inner join students as s on a.student_id = s.id inner join schedule as sc on sc.id = a.schedule_id inner join subjects as sb on sb.id = sc.subject_id where a.trangThai = 'Vắng'")
            rows = cursor.fetchall()
            self.tableWidget_2.setRowCount(50)
            tablerow = 0
            for row in rows:
                self.tableWidget_2.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                self.tableWidget_2.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                self.tableWidget_2.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                self.tableWidget_2.setItem(tablerow,3,QtWidgets.QTableWidgetItem(row[3]))
                self.tableWidget_2.setItem(tablerow,4,QtWidgets.QTableWidgetItem(str(row[4])))
                tablerow+=1
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
    def export1(self):
        list = []
        listItem = []
        row = 0
        try:          
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")
             
            self.tableWidget.setRowCount(100)
            sql = "select count(a.id) from attendance as a inner join students as s on a.student_id = s.id inner join schedule as sc on sc.id = a.schedule_id where a.trangThai like 'Muộn %'"
            for row in range(int(cursor.execute(sql).fetchone()[0])):
                for col in range(5):
                    item = self.tableWidget.item(row,col)
                    if item:
                        listItem.append(item.text())
                list.append(listItem)
                listItem = []
            sqliteConnection.commit()
            
            cursor.close()
        except sqlite3.Error as error:
            self.showdialog("Không thể export")
            print("Failed to select data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")

        data = tuple(list)
        print(data)
        row = 1
        col = 0
        workbook = xlsxwriter.Workbook("C:\\Users\\Admin\\Downloads\\thong ke.xlsx")
 
        worksheet = workbook.add_worksheet("My sheet")
        worksheet.write('A1', 'ID')
        worksheet.write('B1', 'Tên sinh viên')
        worksheet.write('C1', 'Ngày')
        worksheet.write('D1', 'ID buổi học')
        worksheet.write('E1', 'Trạng thái')
        # Iterate over the data and write it out row by row.
        for idSv, name,  date, idSubject, attendence in (data):
            worksheet.write(row, col, idSv)
            worksheet.write(row, col + 1, str(name))
            worksheet.write(row, col + 2, str(date))
            worksheet.write(row, col + 3, int(idSubject))
            worksheet.write(row, col + 4, attendence)
            row += 1
        workbook.close()
        self.showdialog("Tạo file excel thành công")
    def loadAll1(self):
        self.showInforOfLateStudents()
    def search1(self):
        criteria = self.cbSearch1.currentText()
        if isRequiredFiled(criteria) == False:
            self.showdialog("Vui lòng chọn tiêu chí")
        else:
            if criteria == "ID sinh viên":
                id = self.tfSearch1.text()
                if isRequiredFiled(id) == False:
                    self.showdialog("Vui lòng nhập ID")
                elif isValidInteger(id) == False:
                    self.showdialog("ID không hợp lệ")
                else:
                    self.tableWidget.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                    
                        cursor.execute("select a.student_id, s.ten, DATE(a.ngayDiemDanh), sc.subject_id, a.trangThai from attendance as a inner join students as s on a.student_id = s.id inner join schedule as sc on sc.id = a.schedule_id where a.trangThai like 'Muộn %' and a.student_id = ?", (id,))
                        rows = cursor.fetchall()
                        self.tableWidget.setRowCount(50)
                        tablerow = 0
                        for row in rows:
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()
                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Tên sinh viên":
                ten = self.tfSearch1.text()
                if isRequiredFiled(ten) == False:
                    self.showdialog("Vui lòng nhập tên")
                elif isValidString(ten) == False:
                    self.showdialog("Tên không hợp lệ")
                else:
                    self.tableWidget.setRowCount(0)
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                        sql = "select a.student_id, s.ten, DATE(a.ngayDiemDanh), sc.subject_id, a.trangThai from attendance as a inner join students as s on a.student_id = s.id inner join schedule as sc on sc.id = a.schedule_id where a.trangThai like 'Muộn %' and s.ten like '%" + ten +  "%'"
                        self.tableWidget.setRowCount(50)
                        tablerow = 0
                        for row in cursor.execute(sql):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
            elif criteria == "Ngày":
                ngay = self.tfSearch1.text()
                if isRequiredFiled(ngay) == False:
                    self.showdialog("Vui lòng nhập ngày")
                elif isValidDate(ngay) == False:
                    self.showdialog("Ngày không hợp lệ")
                else:
                    self.tableWidget.setRowCount(0) 
                    try:          
                        sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
                        cursor = sqliteConnection.cursor()
                        print("Successfully Connected to SQLite")
                        sql = "select a.student_id, s.ten, DATE(a.ngayDiemDanh), sc.subject_id, a.trangThai from attendance as a inner join students as s on a.student_id = s.id inner join schedule as sc on sc.id = a.schedule_id where a.trangThai like 'Muộn %' and DATE(a.ngayDiemDanh) = '" + ngay + "'"
                        self.tableWidget.setRowCount(100)
                        tablerow=0
                        for row in cursor.execute(sql):
                            self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                            self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                            self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                            self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                            self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                            tablerow+=1
                        sqliteConnection.commit()
                    
                        cursor.close()

                    except sqlite3.Error as error:
                        print("Failed to select data into sqlite table" , error)
                    finally:
                        if sqliteConnection:
                            sqliteConnection.close()
                        print("The SQLite connection is closed")
    def showInforOfLateStudents(self):
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")
            cursor.execute("select a.student_id, s.ten, DATE(a.ngayDiemDanh), sc.subject_id, a.trangThai from attendance as a inner join students as s on a.student_id = s.id inner join schedule as sc on sc.id = a.schedule_id where a.trangThai like 'Muộn %'")
            rows = cursor.fetchall()
            self.tableWidget.setRowCount(50)
            tablerow = 0
            for row in rows:
                self.tableWidget.setItem(tablerow,0,QtWidgets.QTableWidgetItem(str(row[0])))
                self.tableWidget.setItem(tablerow,1,QtWidgets.QTableWidgetItem(row[1]))
                self.tableWidget.setItem(tablerow,2,QtWidgets.QTableWidgetItem(row[2]))
                self.tableWidget.setItem(tablerow,3,QtWidgets.QTableWidgetItem(str(row[3])))
                self.tableWidget.setItem(tablerow,4,QtWidgets.QTableWidgetItem(row[4]))
                tablerow+=1
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table" , error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
    def UiComponents(self):
        # lay so luong sinh vien
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT count(id) from students"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchone()
            self.lbTong.setText(str(record[0]))
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
        # lay so ban diem danh
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT count(id) from attendance"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchone()
            self.lbTongDiemDanh.setText(str(record[0]))
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
        # lay so ban diem danh muon
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "SELECT count(id) from attendance where trangThai like 'Muộn %'"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchone()
            self.lbDiemDanhMuon.setText(str(record[0]))
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
        # lay so ban diem danh vang
        try:
            sqliteConnection = sqlite3.connect("D:\\code\\.vscode\\python\\simple_facenet\\db\\userdata.db")
            cursor = sqliteConnection.cursor()
            print("Connected to SQLite")

            sqlite_select_query = "select count(id) from attendance where trangThai = 'Vắng'"
            cursor.execute(sqlite_select_query)  
            record = cursor.fetchone()
            self.lbVang.setText(str(record[0]))
            cursor.close()
        except sqlite3.Error as error:
            print("Failed to select data from sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
    def showdialog(self, msg):
        QMessageBox.about(self, "Title", msg)
    def exit(self):
        main = Main()
        widget.addWidget(main)
        widget.setCurrentIndex(widget.currentIndex()+1)
#main
app = QApplication(sys.argv)
login = LoginScreen()
widget = QtWidgets.QStackedWidget()
widget.addWidget(login)
widget.setFixedHeight(841)
widget.setFixedWidth(1291)
widget.show()
app.exec_()