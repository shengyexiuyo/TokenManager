# -*- coding: utf-8 -*-
"""离屏回归：自定义服务商增删改 + 多Token + 删除清理 + 切换"""
import os
import shutil
import sys

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
DATA = os.path.abspath('_rt')
os.environ['DATA_DIR'] = DATA
shutil.rmtree(DATA, ignore_errors=True)
os.makedirs(DATA, exist_ok=True)

sys.path.insert(0, '.')

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

app = QApplication([])

import token_core as tc
import desktop

w = desktop.App()
w.show()


def row_of(key):
    for row in range(w.lstProviders.count()):
        if w.lstProviders.item(row).data(Qt.UserRole) == key:
            return row
    return -1


# 1. 新增自定义服务商
row = row_of('custom')
w.lstProviders.setCurrentRow(row)
w.cName.setText('测试中转')
w.cBase.setText('https://t.example/v1')
w.save_custom()
cid = w._editing_custom
assert row_of(cid) >= 0
print('1. 新增自定义服务商 OK')

# 2. 同服务商保存两个Token
w.apiInput.setText('sk-one-aaaaaaaa')
w.noteInput.setText('一号')
w.save_key()
w.apiInput.setText('sk-two-bbbbbbbb')
w.noteInput.setText('二号')
w.save_key()
assert len(tc.list_tokens(cid)) == 2
print('2. 同服务商两个Token OK')

# 3. 点击已保存Token条目回填
w.lstSaved.setCurrentRow(0)
w.on_token_clicked(w.lstSaved.currentItem())
assert w.apiInput.text().startswith('sk-')
print('3. 点击回填 OK')

# 4. 编辑备注
desktop.QInputDialog.getMultiLineText = lambda *a, **k: ('一号-改', True)
w.lstSaved.setCurrentRow(0)
w.edit_note()
assert tc.list_tokens(cid)[0]['note'] == '一号-改'
print('4. 备注编辑 OK')

# 5. 复制（第1行=最新的二号，第2行=一号）
w.lstSaved.setCurrentRow(1)
w.copy_saved_key()
assert QApplication.clipboard().text() == 'sk-one-aaaaaaaa'
print('5. 一键复制 OK')

# 6. 删除服务商（名下Token一并清理）
desktop.QMessageBox.question = lambda *a, **k: desktop.QMessageBox.Yes
w.lstProviders.setCurrentRow(row_of(cid))
w.delete_custom()
assert tc.get_custom_configs().get(cid) is None
assert len(tc.list_tokens(cid)) == 0
assert row_of(cid) == -1
print('6. 删除服务商（含Token清理）OK')

# 7. 内置服务商：保存 + 删除Token
row = row_of('deepseek')
w.lstProviders.setCurrentRow(row)
w.apiInput.setText('sk-ds-test-12345678')
w.save_key()
assert len(tc.list_tokens('deepseek')) == 1
w.lstSaved.setCurrentRow(0)
w.delete_selected_key()
assert len(tc.list_tokens('deepseek')) == 0
print('7. 内置服务商Token保存/删除 OK')

# 8. 语言与主题切换
w.toggle_lang()
w.toggle_lang()
w.toggle_theme()
w.toggle_theme()
print('8. 语言/主题切换 OK')

print('ALL REGRESSION TESTS PASSED')
