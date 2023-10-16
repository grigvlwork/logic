import sys
import traceback
import subprocess
import autopep8
import sys
import re
from PyQt5 import uic  # Импортируем uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel

def run_text(text):
    with open('code.py', 'w') as c:
        c.write(text)
    completed_process = subprocess.run(['python', 'code.py'], capture_output=True, text=True)
    if completed_process.returncode == 0:
        return completed_process.stdout
    else:
        return completed_process.stderr


def remove_comments(code):
    return re.sub(r'#.*', '', code)


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('mainwindow.ui', self)
        self.incorrect_answer_te.textChanged.connect(self.create_my_answer)
        self.explanation_te.textChanged.connect(self.create_my_answer)
        self.correct_answer_te.textChanged.connect(self.create_my_answer)
        self.run_incorrect_btn.clicked.connect(self.run_incorrect)
        self.run_correct_btn.clicked.connect(self.run_correct)
        self.clear_answer.clicked.connect(self.clear)
        self.process_btn.clicked.connect(self.processing)
        self.incorrect_answer_tw.currentChanged.connect(self.incorrect_row_generator)
        self.correct_answer_tw.currentChanged.connect(self.correct_row_generator)
        self.correct_code = ''
        self.incorrect_code = ''
        self.correct_code_model = QStandardItemModel()
        self.incorrect_code_model = QStandardItemModel()

    def clear(self):
        self.teacher_answer_te.clear()

    def run_incorrect(self):

        code = self.incorrect_answer_te.toPlainText()
        self.incorrect_result.setText(run_text(remove_comments(code)))


    def run_correct(self):
        code = self.correct_answer_te.toPlainText()
        self.correct_result.setText(run_text(remove_comments(code)))

    def create_my_answer(self):
        text = '<incorrect_solution>\n\n```\n' + self.incorrect_answer_te.toPlainText() + '\n```\n</incorrect_solution>\n\n' + \
               '<explanation>\n' + self.explanation_te.toPlainText() + '\n</explanation>\n\n' + \
               '<correct_solution>\n\n```\n' + self.correct_answer_te.toPlainText() + '\n```\n</correct_solution>'
        self.incorrect_code = autopep8.fix_code(self.incorrect_answer_te.toPlainText().strip())
        self.correct_code = autopep8.fix_code(self.correct_answer_te.toPlainText().strip())
        self.my_answer_te.clear()
        self.my_answer_te.appendPlainText(text)

    def processing(self):
        t = self.teacher_answer_te.toPlainText()
        if all(x in t for x in ['<incorrect_solution>', '</incorrect_solution>']):
            code = t[t.find('<incorrect_solution>') + 20:t.find('</incorrect_solution>')]
            self.incorrect_answer_te.clear()
            code = code.replace('```', '').strip()
            self.incorrect_code = autopep8.fix_code(code)
            self.incorrect_answer_te.appendPlainText(code)
            self.incorrect_result.setText('Вывод: ' + run_text(remove_comments(self.incorrect_code)))
        if all(x in t for x in ['<explanation>', '</explanation>']):
            code = t[t.find('<explanation>') + 13:t.find('</explanation>')]
            self.explanation_te.clear()
            code = code.strip()
            self.explanation_te.appendPlainText(code)
        if all(x in t for x in ['<correct_solution>', '</correct_solution>']):
            code = t[t.find('<correct_solution>') + 18:t.find('</correct_solution>')]
            self.correct_answer_te.clear()
            code = code.replace('```', '').strip()
            code = autopep8.fix_code(code)
            self.correct_answer_te.appendPlainText(code)
            self.correct_result.setText('Вывод: ' + run_text(remove_comments(code)))

    def incorrect_row_generator(self):
        if self.incorrect_answer_tw.currentIndex() == 1:
            self.incorrect_code_model.clear()
            for row in self.incorrect_code.split('\n'):
                it = QStandardItem(row)
                self.incorrect_code_model.appendRow(it)
            self.incorrect_answer_tv.setModel(self.incorrect_code_model)
            self.incorrect_answer_tv.horizontalHeader().setVisible(False)
            self.incorrect_answer_tv.resizeColumnToContents(0)

    def correct_row_generator(self):
        if self.correct_answer_tw.currentIndex() == 1:
            self.correct_code_model.clear()
            for row in self.correct_code.split('\n'):
                it = QStandardItem(row)
                self.correct_code_model.appendRow(it)
            self.correct_answer_tv.setModel(self.correct_code_model)
            self.correct_answer_tv.horizontalHeader().setVisible(False)
            self.correct_answer_tv.resizeColumnToContents(0)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()


    def excepthook(exc_type, exc_value, exc_tb):
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        # tb += '\n'.join(ex.current_rec.get_row())
        print(tb)

        msg = QMessageBox.critical(
            None,
            "Error catched!:",
            tb
        )
        QApplication.quit()


    sys.excepthook = excepthook
    ex.show()
    sys.exit(app.exec_())
