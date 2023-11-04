import sys
import traceback
import subprocess
import pyperclip
import black
import sys
import re
import enchant
import difflib
from PyQt5 import uic  # Импортируем uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from mainwindow import Ui_MainWindow


def run_text(text, timeout):
    with open('code.py', 'w') as c:
        c.write(text)
    try:
        completed_process = subprocess.run(['python', 'code.py'], capture_output=True, text=True, timeout=timeout)
        if completed_process.returncode == 0:
            if len(completed_process.stdout) > 25:
                return completed_process.stdout[:25] + '..'
            else:
                return completed_process.stdout
        else:
            if len(completed_process.stderr) > 50:
                return completed_process.stderr[:50] + '\n' + completed_process.stderr[50:]
            else:
                return completed_process.stderr
    except subprocess.TimeoutExpired:
        return f'Программа выполнялась более {timeout} секунд'


def remove_comments(code):
    return re.sub(r'#.*', '', code)


def spell_check(text):
    rus_alph = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    words = []
    word = ''
    for c in text:
        if c.lower() in rus_alph:
            word += c
        else:
            if len(word) > 0:
                words.append(word)
                word = ''
    result = []
    dictionary = enchant.Dict("ru_RU")
    for w in words:
        if not dictionary.check(w):
            sim = dict()
            suggestions = set(dictionary.suggest(w))
            for word in suggestions:
                measure = difflib.SequenceMatcher(None, w, word).ratio()
                sim[measure] = word
            result.append([w, sim[max(sim.keys())]])
    return result


class MyWidget(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # uic.loadUi('mainwindow.ui', self)
        self.setupUi(self)
        self.incorrect_answer_te.textChanged.connect(self.create_my_answer)
        self.explanation_te.textChanged.connect(self.create_my_answer)
        self.correct_answer_te.textChanged.connect(self.create_my_answer)
        self.run_incorrect_btn.clicked.connect(self.run_incorrect)
        self.run_correct_btn.clicked.connect(self.run_correct)
        self.insert_answer.clicked.connect(self.insert)
        self.process_btn.clicked.connect(self.processing)
        self.incorrect_answer_tw.currentChanged.connect(self.incorrect_row_generator)
        self.correct_answer_tw.currentChanged.connect(self.correct_row_generator)
        self.main_tw.currentChanged.connect(self.make_diff)
        self.copy_my_answer_btn.clicked.connect(self.copy_my_answer)
        self.pep8_btn.clicked.connect(self.pep8_correct)
        self.triple_ticking_btn.clicked.connect(self.triple_ticking)
        self.correct_code = ''
        self.incorrect_code = ''
        self.correct_code_model = QStandardItemModel()
        self.incorrect_code_model = QStandardItemModel()
        self.teacher_comment = ''

    def insert(self):
        self.teacher_answer_te.setPlainText(pyperclip.paste())
        self.processing()

    def run_incorrect(self):
        code = self.incorrect_answer_te.toPlainText()
        timeout = self.time_incorrect_sb.value()
        self.incorrect_result.setText('Вывод: ' + run_text(remove_comments(code), timeout))

    def run_correct(self):
        code = self.correct_answer_te.toPlainText()
        timeout = self.time_correct_sb.value()
        self.correct_result.setText('Вывод: ' + run_text(remove_comments(code), timeout))

    def create_my_answer(self):
        text = '<incorrect_solution>\n\n```\n' + self.incorrect_answer_te.toPlainText() + '\n```\n</incorrect_solution>\n\n' + \
               '<explanation>\n' + self.explanation_te.toPlainText() + '\n</explanation>\n\n' + \
               '<correct_solution>\n\n```\n' + self.correct_answer_te.toPlainText() + '\n```\n</correct_solution>\n\n' + \
               '<comment>\n' + self.teacher_comment + '\n</comment>'
        self.incorrect_code = self.incorrect_answer_te.toPlainText().strip()
        self.my_answer_te.clear()
        self.my_answer_te.appendPlainText(text)

    def processing(self):
        t = self.teacher_answer_te.toPlainText()
        self.teacher_comment = ''
        if all(x in t for x in ['<incorrect_solution>', '</incorrect_solution>']):
            code = t[t.find('<incorrect_solution>') + 20:t.find('</incorrect_solution>')]
            self.incorrect_answer_te.clear()
            code = code.replace('```', '').strip()
            self.incorrect_answer_te.appendPlainText(code)
            timeout = self.time_incorrect_sb.value()
            self.incorrect_result.setText('Вывод: ' + run_text(remove_comments(self.incorrect_code), timeout))
        if all(x in t for x in ['<explanation>', '</explanation>']):
            code = t[t.find('<explanation>') + 13:t.find('</explanation>')]
            self.explanation_te.clear()
            code = code.strip()
            self.explanation_te.appendPlainText(code)
        if all(x in t for x in ['<correct_solution>', '</correct_solution>']):
            code = t[t.find('<correct_solution>') + 18:t.find('</correct_solution>')]
            self.correct_answer_te.clear()
            code = code.replace('```', '').strip()
            try:
                code = black.format_str(code, mode=black.Mode(
                    target_versions={black.TargetVersion.PY310},
                    line_length=101,
                    string_normalization=False,
                    is_pyi=False,
                ), )
            except Exception as err:
                code = code.strip()
            self.correct_answer_te.appendPlainText(code)
            timeout = self.time_correct_sb.value()
            self.correct_result.setText('Вывод: ' + run_text(remove_comments(code), timeout))
        if all(x in t for x in ['<comment>', '</comment>']):
            self.teacher_comment = t[t.find('<comment>') + 9:t.find('</comment>')].strip()
        self.create_my_answer()

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
        self.pep8_correct()
        if self.correct_answer_tw.currentIndex() == 1:
            self.correct_code_model.clear()
            for row in self.correct_code.split('\n'):
                it = QStandardItem(row)
                self.correct_code_model.appendRow(it)
            self.correct_answer_tv.setModel(self.correct_code_model)
            self.correct_answer_tv.horizontalHeader().setVisible(False)
            self.correct_answer_tv.resizeColumnToContents(0)

    def copy_my_answer(self):
        errors = spell_check(self.explanation_te.toPlainText())
        if len(errors) > 0:
            s = 'Обнаружены ошибки в тексте, всё равно скопировать?\n'
            for err in errors:
                s += err[0] + ':    ' + err[1] + '\n'
            message = QMessageBox.question(self, "Орфографические ошибки", s,
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if message == QMessageBox.Yes:
                pyperclip.copy(self.my_answer_te.toPlainText())
        else:
            pyperclip.copy(self.my_answer_te.toPlainText())

    def pep8_correct(self):
        code = self.correct_answer_te.toPlainText()
        try:
            code = black.format_str(code, mode=black.Mode(
                target_versions={black.TargetVersion.PY310},
                line_length=101,
                string_normalization=False,
                is_pyi=False,
            ), )
        except Exception as err:
            code = code.strip()
        self.correct_answer_te.setPlainText(code)
        self.correct_code = code

    def triple_ticking(self):
        t = self.explanation_te.toPlainText()
        text = t.split('```')[1]
        t = t.replace('```' + text + '```', '\n```\n' + text + '\n```')
        if t[-1] == '.':
            t = t[:-1]
        self.explanation_te.clear()
        self.explanation_te.appendPlainText(t)

    def make_diff(self):
        if self.main_tw.currentIndex() == 1:
            self.incorrect_to_compare_te.clear()
            self.incorrect_to_compare_te.appendPlainText(self.incorrect_answer_te.toPlainText())
            self.correct_to_compare_te.clear()
            self.correct_to_compare_te.appendPlainText(self.correct_answer_te.toPlainText())
            diff = difflib.ndiff(self.incorrect_answer_te.toPlainText().splitlines(keepends=True),
                                 self.correct_answer_te.toPlainText().splitlines(keepends=True))
            self.difference_te.clear()
            self.difference_te.appendPlainText(''.join(diff))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()


    def excepthook(exc_type, exc_value, exc_tb):
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
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
