#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Manager 桌面版 — PySide6 原生应用
无浏览器、无后端服务：界面为原生控件，业务逻辑直接调用 token_core
双击exe直接运行，关闭窗口即退出
"""

import json
import sys

import token_core as tc
from PySide6.QtCore import Qt, QObject, QRunnable, QThreadPool, Signal
from PySide6.QtWidgets import QSplitter
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QInputDialog, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

APP_VERSION = '2.1.0'

# ==================== 中英双语（默认中文） ====================
_EN = {
    '选择服务商': 'Provider', '控制台': 'Console', 'API 密钥': 'API Key',
    '查询余额': 'Query Balance', '保存密钥': 'Save Key', '显示': 'Show', '隐藏': 'Hide',
    '已保存的Token': 'Saved Tokens', '查询全部': 'Query All', '删除选中': 'Delete Selected',
    '暂无保存的Token': 'No saved tokens yet',
    '余额信息': 'Balance', '全部余额汇总': 'All Balances', '用量统计': 'Usage',
    '实时价格': 'Live Pricing', '刷新': 'Refresh', '数据来源': 'Source',
    '评估时间': 'Evaluated at', '北京时间': 'Beijing time', '模型': 'Model',
    '厂商': 'Vendor', '输入价': 'Input', '输出价': 'Output',
    '性价比': 'Value score', '峰谷': 'Peak/Off-peak',
    '可用余额': 'Available', '总余额': 'Total', '赠送额度': 'Granted',
    '充值余额': 'Topped-up', '今日用量': 'Today', '本月用量': 'This month',
    '累计使用': 'Total used',
    '自定义服务商配置': 'Custom Provider', 'OpenAI 兼容': 'OpenAI compatible',
    '保存配置': 'Save Config', '删除服务商': 'Delete Provider',
    '新增自定义服务商': 'Add Custom Provider', '编辑自定义服务商': 'Edit Custom Provider',
    '请选择左侧的服务商': 'Select a provider on the left',
    '请填写 API 地址': 'API URL is required',
    '请先填写配置并保存，再查询': 'Fill in the config and save before querying',
    '请先输入 API Key': 'Enter your API Key first',
    '正在查询余额...': 'Querying balance...',
    '正在查询用量...': 'Querying usage...',
    '正在刷新价格...': 'Refreshing prices...',
    '该服务商暂无用量数据': 'No usage data for this provider',
    '请检查 API Key 是否正确': 'Please check your API Key',
    '余额信息不可用': 'Balance unavailable',
    'Token已保存': 'Token saved', 'Token已删除': 'Token deleted',
    '该Token已存在，备注已更新': 'Token already exists; note updated',
    'API Key 格式不正确': 'Invalid API Key format',
    '查询失败': 'Query failed', '网络错误': 'Network error',
    '删除成功': 'Deleted', '删除失败': 'Delete failed',
    '确认删除该自定义服务商？其已保存的密钥也会一并删除。':
        'Delete this custom provider? Its saved key will also be removed.',
    '没有已保存的Token': 'No saved tokens',
    '正在查询全部...': 'Querying all...',
    '价格为美元/百万tokens，按性价比降序排列；峰谷状态按北京时间判断':
        'USD per 1M tokens, sorted by value score; peak/off-peak judged by Beijing time',
    '输入或粘贴您的 API Key': 'Enter or paste your API Key',
    '备注（可选，随密钥保存）': 'Note (optional, saved with the key)',
    '显示名称（默认：自定义）': 'Display name (default: Custom)',
    'API 地址，如 https://api.example.com/v1': 'API URL, e.g. https://api.example.com/v1',
    '余额路径 默认/dashboard/billing/subscription': 'Balance path, default /dashboard/billing/subscription',
    '用量路径 默认/dashboard/billing/usage': 'Usage path, default /dashboard/billing/usage',
    '货币单位（默认 USD）': 'Currency (default USD)',
    '总可用余额': 'Total Available',
    '浅色': 'Light', '深色': 'Dark',
    '复制Token': 'Copy Token', '备注': 'Note', '备注已保存': 'Note saved',
    '已复制到剪贴板': 'Copied to clipboard',
    '输入该密钥的备注：': 'Enter a note for this key:',
}

PNAME_FORCE = {'腾讯': 'Tencent'}

_LANG = {'cur': 'zh'}
_THEME = {'cur': 'dark'}


def _load_ui_settings() -> dict:
    try:
        with open(os.path.join(tc.get_config_dir(), '.ui_settings.json'), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_ui_settings(settings: dict):
    try:
        with open(os.path.join(tc.get_config_dir(), '.ui_settings.json'), 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False)
    except Exception:
        pass


def t(s: str) -> str:
    return _EN.get(s, s) if _LANG['cur'] == 'en' else s


def pname(s: str) -> str:
    return PNAME_FORCE.get(s, s)


# ==================== 主题（深色/浅色调色板 + QSS模板） ====================
PALETTES = {
    'dark': {
        'BG': '#0b0b15', 'CARD': '#14141f', 'INNER': '#1b1b2c', 'INNERHOVER': '#20203a',
        'BORDER': '#26263f', 'HANDLE': '#2c2c47', 'TEXT': '#e5e7eb', 'TEXTSTRONG': '#ffffff',
        'MUTED': '#8b8fa3', 'TABLEALT': '#14141f', 'ROWBORDER': '#1e1e32', 'SEL': '#6d28d9',
        'TOOLTIPBG': '#1e1e32', 'BADGEV_BG': '#14532d', 'BADGEV_C': '#4ade80',
        'BADGEP_BG': '#78350f', 'BADGEP_C': '#fbbf24', 'TITLE': '#b57bff', 'STATBG': '#252542',
    },
    'light': {
        'BG': '#eef0f7', 'CARD': '#ffffff', 'INNER': '#f3f4fa', 'INNERHOVER': '#eceefc',
        'BORDER': '#dfe2ef', 'HANDLE': '#c9cde0', 'TEXT': '#1f2430', 'TEXTSTRONG': '#0b0b15',
        'MUTED': '#6b7280', 'TABLEALT': '#f7f8fd', 'ROWBORDER': '#eceef8', 'SEL': '#6d28d9',
        'TOOLTIPBG': '#ffffff', 'BADGEV_BG': '#dcfce7', 'BADGEV_C': '#15803d',
        'BADGEP_BG': '#fef3c7', 'BADGEP_C': '#b45309', 'TITLE': '#7c3aed', 'STATBG': '#f6f7fc',
    },
}

QSS_TEMPLATE = """
* { font-family: 'Microsoft YaHei UI', 'Segoe UI'; font-size: 13px; }
QMainWindow, QWidget { background-color: @BG@; color: @TEXT@; }
QToolTip { background-color: @TOOLTIPBG@; color: @TEXT@; border: 1px solid #a855f7; padding: 4px; border-radius: 4px; }

QGroupBox {
    background-color: @CARD@;
    border: 1px solid @BORDER@;
    border-radius: 14px;
    margin-top: 18px;
    padding: 16px 14px 14px 14px;
}
QGroupBox::title {
    subcontrol-origin: margin; left: 14px; top: 2px; padding: 0 6px;
    color: @TITLE@; font-weight: 600; font-size: 14px;
}

QLineEdit {
    background-color: @INNER@; border: 1px solid @BORDER@; border-radius: 8px;
    padding: 7px 10px; color: @TEXTSTRONG@; selection-background-color: #a855f7;
}
QLineEdit:focus { border: 1px solid #a855f7; background-color: @INNERHOVER@; }

QPushButton {
    background-color: @INNER@; color: @TEXT@; border: 1px solid @BORDER@;
    border-radius: 8px; padding: 7px 16px; font-weight: 500;
}
QPushButton:hover { border-color: #a855f7; color: @TEXTSTRONG@; }
QPushButton:pressed { background-color: @INNERHOVER@; }
QPushButton:disabled { color: #6b7280; border-color: @BORDER@; }
QPushButton#primary {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #a855f7, stop:1 #6366f1);
    color: #ffffff; border: none; font-weight: bold;
}
QPushButton#primary:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b56ffc, stop:1 #7c7ff5);
}
QPushButton#danger { background-color: #3b1220; color: #fda4af; border: 1px solid #7f1d1d; }
QPushButton#danger:hover { border-color: #f43f5e; }
QPushButton#langBtn { color: #c084fc; border: 1px solid #7c3aed; background-color: transparent; font-weight: bold; }

QListWidget { background-color: transparent; border: none; outline: 0; }
QListWidget::item {
    background-color: @INNER@; color: @TEXT@; border: 1px solid transparent;
    border-radius: 9px; padding: 8px 12px; margin: 3px 2px;
}
QListWidget::item:hover { border-color: #7c3aed; background-color: @INNERHOVER@; }
QListWidget::item:selected {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a855f7, stop:1 #6366f1);
    color: #ffffff; font-weight: bold; border: none;
}

QTableWidget {
    background-color: transparent; color: @TEXT@; border: none;
    gridline-color: transparent; alternate-background-color: @TABLEALT@;
    selection-background-color: @SEL@; selection-color: #ffffff;
}
QTableWidget::item { padding: 4px 6px; border-bottom: 1px solid @ROWBORDER@; }
QHeaderView::section {
    background-color: transparent; color: @MUTED@; border: none;
    border-bottom: 1px solid @BORDER@; padding: 8px 6px; font-weight: 600;
}

QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: @HANDLE@; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #a855f7; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar:horizontal { background: transparent; height: 8px; margin: 2px; }
QScrollBar::handle:horizontal { background: @HANDLE@; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #a855f7; }

QSplitter::handle { background-color: @BORDER@; }
QSplitter::handle:hover { background-color: #a855f7; }

QFrame#statBox { background-color: @STATBG@; border: 1px solid @BORDER@; border-radius: 10px; }
QLabel#statTitle { color: @MUTED@; font-size: 12px; }
QLabel#statValue { color: @TEXTSTRONG@; font-size: 22px; font-weight: bold; }
QLabel#note { color: @MUTED@; font-size: 12px; }
QLabel#statusPill {
    background-color: @CARD@; border: 1px solid @BORDER@; border-radius: 9px;
    padding: 5px 12px; color: @MUTED@; font-size: 12px;
}
QLabel#badgeValley { background-color: @BADGEV_BG@; color: @BADGEV_C@; border-radius: 9px; padding: 3px 12px; font-weight: bold; }
QLabel#badgePeak { background-color: @BADGEP_BG@; color: @BADGEP_C@; border-radius: 9px; padding: 3px 12px; font-weight: bold; }
"""


def build_qss(theme: str) -> str:
    palette = PALETTES.get(theme, PALETTES['dark'])
    qss = QSS_TEMPLATE
    for key, value in palette.items():
        qss = qss.replace('@' + key + '@', value)
    return qss


class _Signals(QObject):
    ok = Signal(object)
    err = Signal(str)


class Worker(QRunnable):
    """后台任务：网络请求不阻塞界面"""

    def __init__(self, fn):
        super().__init__()
        self.fn = fn
        self.sig = _Signals()

    def run(self):
        try:
            self.sig.ok.emit(self.fn())
        except Exception as e:
            self.sig.err.emit(str(e))


def _stat_box(title_zh):
    box = QFrame()
    box.setObjectName('statBox')
    v = QVBoxLayout(box)
    v.setContentsMargins(10, 8, 10, 8)
    title = QLabel(t(title_zh))
    title.setObjectName('statTitle')
    value = QLabel('0')
    value.setObjectName('statValue')
    cur = QLabel('')
    cur.setObjectName('note')
    v.addWidget(title)
    v.addWidget(value)
    v.addWidget(cur)
    return box, title, value, cur


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.current = None         # 当前选中的服务商
        self._editing_custom = ''   # 正在编辑的自定义服务商id
        self._tr = []               # (widget, zh) 静态文案

        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(4)
        self._workers = []  # 持有后台任务引用，防止信号对象被垃圾回收

        root_v = QVBoxLayout(self)
        root_v.setContentsMargins(14, 12, 14, 12)
        root_v.setSpacing(10)

        # ---------- 头部 ----------
        header = QHBoxLayout()
        title = QLabel('Token Manager')
        title.setStyleSheet('font-size: 20px; font-weight: bold; color: #a855f7;')
        ver = QLabel(f'v{APP_VERSION}')
        ver.setStyleSheet('color: #6b7280; font-size: 12px;')
        self.langBtn = QPushButton('EN')
        self.langBtn.setObjectName('langBtn')
        self.langBtn.setFixedWidth(56)
        self.langBtn.clicked.connect(self.toggle_lang)
        self.themeBtn = QPushButton(t('浅色'))
        self.themeBtn.setObjectName('langBtn')
        self.themeBtn.setFixedWidth(72)
        self.themeBtn.clicked.connect(self.toggle_theme)
        header.addWidget(title)
        header.addWidget(ver)
        header.addStretch(1)
        header.addWidget(self.themeBtn)
        header.addWidget(self.langBtn)
        root_v.addLayout(header)

        self.versionWarn = QLabel(t('前后端版本不一致，部分功能不可用'))
        self.versionWarn.setObjectName('warn')
        self.versionWarn.hide()
        root_v.addWidget(self.versionWarn)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(2)
        root_v.addWidget(self.splitter, 1)

        self.statusLabel = QLabel('')
        self.statusLabel.setObjectName('statusPill')
        self.statusLabel.setMaximumWidth(560)
        root_v.addWidget(self.statusLabel)

        # ---------- 左列 ----------
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setMinimumWidth(285)
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(10)
        left_scroll.setWidget(left)
        self.splitter.addWidget(left_scroll)

        self.grpProviders = QGroupBox(t('选择服务商'))
        self._tr.append((self.grpProviders, '选择服务商'))
        pv = QVBoxLayout(self.grpProviders)
        self.lstProviders = QListWidget()
        self.lstProviders.itemSelectionChanged.connect(self.on_provider_selected)
        # 点击已选中的同一项时不重置表单（避免覆盖正在编辑的内容）
        self.lstProviders.itemClicked.connect(self.on_provider_clicked)
        pv.addWidget(self.lstProviders)
        self.lstProviders.setMinimumHeight(200)
        lv.addWidget(self.grpProviders, 5)

        self.grpKey = QGroupBox(t('API 密钥'))
        self._tr.append((self.grpKey, 'API 密钥'))
        kv = QVBoxLayout(self.grpKey)
        self.apiInput = QLineEdit()
        self._ph(self.apiInput, '输入或粘贴您的 API Key')
        self.apiInput.setEchoMode(QLineEdit.Password)
        kv.addWidget(self.apiInput)
        self.noteInput = QLineEdit()
        self._ph(self.noteInput, '备注（可选，随密钥保存）')
        kv.addWidget(self.noteInput)
        krow = QHBoxLayout()
        self.btnQuery = QPushButton(t('查询余额'))
        self.btnQuery.setObjectName('primary')
        self.btnQuery.clicked.connect(self.query_balance)
        self.btnSaveKey = QPushButton(t('保存密钥'))
        self.btnSaveKey.clicked.connect(self.save_key)
        self.btnEcho = QPushButton(t('显示'))
        self.btnEcho.setFixedWidth(60)
        self.btnEcho.clicked.connect(self.toggle_echo)
        krow.addWidget(self.btnQuery, 3)
        krow.addWidget(self.btnSaveKey, 2)
        krow.addWidget(self.btnEcho, 1)
        kv.addLayout(krow)
        lv.addWidget(self.grpKey)

        # 自定义服务商配置（新增模式/编辑模式）
        self.grpCustom = QGroupBox(t('新增自定义服务商'))
        cv = QVBoxLayout(self.grpCustom)
        cv.setSpacing(6)
        self.cName = QLineEdit(); self.cName.setPlaceholderText(t('显示名称（默认：自定义）'))
        self.cBase = QLineEdit(); self.cBase.setPlaceholderText(t('API 地址，如 https://api.example.com/v1'))
        self.cBal = QLineEdit(); self.cBal.setPlaceholderText(t('余额路径 默认/dashboard/billing/subscription'))
        self.cUse = QLineEdit(); self.cUse.setPlaceholderText(t('用量路径 默认/dashboard/billing/usage'))
        self.cCur = QLineEdit(); self.cCur.setPlaceholderText(t('货币单位（默认 USD）'))
        for w in (self.cName, self.cBase, self.cBal, self.cUse, self.cCur):
            cv.addWidget(w)
        crow = QHBoxLayout()
        self.btnSaveCfg = QPushButton(t('保存配置'))
        self.btnSaveCfg.setObjectName('primary')
        self.btnSaveCfg.clicked.connect(self.save_custom)
        self.btnDeleteCfg = QPushButton(t('删除服务商'))
        self.btnDeleteCfg.setObjectName('danger')
        self.btnDeleteCfg.clicked.connect(self.delete_custom)
        crow.addWidget(self.btnSaveCfg, 3)
        crow.addWidget(self.btnDeleteCfg, 2)
        cv.addLayout(crow)
        lv.addWidget(self.grpCustom)
        self.grpCustom.hide()

        self.grpSaved = QGroupBox(t('已保存的Token'))
        sv = QVBoxLayout(self.grpSaved)
        self.lstSaved = QListWidget()
        self.lstSaved.itemClicked.connect(self.on_token_clicked)
        sv.addWidget(self.lstSaved)
        srow = QHBoxLayout()
        self.btnQueryAll = QPushButton(t('查询全部'))
        self.btnQueryAll.setObjectName('primary')
        self.btnQueryAll.clicked.connect(self.query_all)
        srow.addWidget(self.btnQueryAll)
        sv.addLayout(srow)
        brow = QHBoxLayout()
        self.btnCopy = QPushButton(t('复制Token'))
        self.btnCopy.clicked.connect(self.copy_saved_key)
        self.btnNote = QPushButton(t('备注'))
        self.btnNote.clicked.connect(self.edit_note)
        self.btnDeleteKey = QPushButton(t('删除选中'))
        self.btnDeleteKey.clicked.connect(self.delete_selected_key)
        brow.addWidget(self.btnCopy, 1)
        brow.addWidget(self.btnNote, 1)
        brow.addWidget(self.btnDeleteKey, 1)
        sv.addLayout(brow)
        self.lstSaved.setMinimumHeight(120)
        lv.addWidget(self.grpSaved, 2)
        lv.addStretch(1)

        # ---------- 右列 ----------
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(10)
        right_scroll.setWidget(right)
        self.splitter.addWidget(right_scroll)
        # 左右栏按3:7百分比自适应拉伸，分割条可拖动微调
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 7)
        self.splitter.setSizes([300, 700])

        self.grpBalance = QGroupBox(t('余额信息'))
        self._tr.append((self.grpBalance, '余额信息'))
        bv = QVBoxLayout(self.grpBalance)
        self.balanceHint = QLabel(t('请选择左侧的服务商'))
        self.balanceHint.setObjectName('note')
        self.balanceHint.setAlignment(Qt.AlignCenter)
        bv.addWidget(self.balanceHint)
        grid = QGridLayout()
        grid.setSpacing(8)
        self.balanceStats = {}
        for i, zh in enumerate(('可用余额', '总余额', '赠送额度', '充值余额')):
            box, t_title, t_value, t_cur = _stat_box(zh)
            self._tr.append((t_title, zh))
            grid.addWidget(box, 0, i)
            self.balanceStats[zh] = (t_value, t_cur)
        bv.addLayout(grid)
        self.balanceNote = QLabel('')
        self.balanceNote.setObjectName('note')
        self.balanceNote.setWordWrap(True)
        self.balanceNote.setAlignment(Qt.AlignCenter)
        self.balanceNote.hide()
        bv.addWidget(self.balanceNote)
        rv.addWidget(self.grpBalance)

        self.grpAll = QGroupBox(t('全部余额汇总'))
        self._tr.append((self.grpAll, '全部余额汇总'))
        av = QVBoxLayout(self.grpAll)
        self.allText = QLabel('')
        self.allText.setObjectName('note')
        self.allText.setWordWrap(True)
        av.addWidget(self.allText)
        rv.addWidget(self.grpAll)
        self.grpAll.hide()

        self.grpUsage = QGroupBox(t('用量统计'))
        self._tr.append((self.grpUsage, '用量统计'))
        uv = QVBoxLayout(self.grpUsage)
        self.usageHint = QLabel(t('查询余额后自动显示用量统计'))
        self.usageHint.setObjectName('note')
        self.usageHint.setAlignment(Qt.AlignCenter)
        uv.addWidget(self.usageHint)
        ugrid = QGridLayout()
        ugrid.setSpacing(8)
        self.usageStats = {}
        for i, zh in enumerate(('今日用量', '本月用量', '累计使用')):
            box, t_title, t_value, t_cur = _stat_box(zh)
            self._tr.append((t_title, zh))
            ugrid.addWidget(box, 0, i)
            self.usageStats[zh] = (t_value, t_cur)
        uv.addLayout(ugrid)
        rv.addWidget(self.grpUsage)
        self.grpUsage.hide()

        self.grpPricing = QGroupBox(t('实时价格'))
        self._tr.append((self.grpPricing, '实时价格'))
        p2v = QVBoxLayout(self.grpPricing)
        prow = QHBoxLayout()
        self.priceMeta = QLabel(t('数据来源') + ' traktoken.com')
        self.priceMeta.setObjectName('note')
        prow.addWidget(self.priceMeta, 1)
        self.btnPrice = QPushButton(t('刷新'))
        self.btnPrice.clicked.connect(self.load_pricing)
        prow.addWidget(self.btnPrice)
        p2v.addLayout(prow)
        self.priceTable = QTableWidget(0, 6)
        self.priceTable.setHorizontalHeaderLabels([t(x) for x in ('模型', '厂商', '输入价', '输出价', '性价比', '峰谷')])
        self.priceTable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.priceTable.verticalHeader().hide()
        self.priceTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.priceTable.setSelectionBehavior(QTableWidget.SelectRows)
        p2v.addWidget(self.priceTable)
        p2note = QLabel(t('价格为美元/百万tokens，按性价比降序排列；峰谷状态按北京时间判断'))
        p2note.setObjectName('note')
        p2note.setWordWrap(True)
        p2v.addWidget(p2note)
        rv.addWidget(self.grpPricing, 1)
        self.priceTable.setMinimumHeight(230)

        self._update_header_buttons()
        self.refresh_providers()
        self.refresh_tokens()
        self.load_pricing()

    # ---------- 工具 ----------
    def _ph(self, edit, zh):
        edit.setPlaceholderText(t(zh))
        self._tr.append((edit, zh))

    def status(self, msg):
        self.statusLabel.setText(msg)

    # ---------- 语言切换 ----------
    def toggle_lang(self):
        _LANG['cur'] = 'en' if _LANG['cur'] == 'zh' else 'zh'
        _save_ui_settings({'lang': _LANG['cur'], 'theme': _THEME['cur']})
        for w, zh in self._tr:
            if isinstance(w, QGroupBox):
                w.setTitle(t(zh))
            else:
                w.setText(t(zh))
        self._update_header_buttons()
        self.grpCustom.setTitle(t('编辑自定义服务商') if self._editing_custom else t('新增自定义服务商'))
        self.grpCustom.setVisible(self._editing_custom != '' or self.grpCustom.isVisible())
        self.refresh_providers()
        self.refresh_tokens()
        self.load_pricing()

    def _update_header_buttons(self):
        self.langBtn.setText('中文' if _LANG['cur'] == 'en' else 'EN')
        self.themeBtn.setText(t('浅色') if _THEME['cur'] == 'dark' else t('深色'))

    def toggle_theme(self):
        _THEME['cur'] = 'light' if _THEME['cur'] == 'dark' else 'dark'
        _save_ui_settings({'lang': _LANG['cur'], 'theme': _THEME['cur']})
        QApplication.instance().setStyleSheet(build_qss(_THEME['cur']))
        self._update_header_buttons()

    def _fill_custom_form(self, cfg: dict):
        """把自定义服务商配置填入表单"""
        self.cName.setText(cfg.get('name', ''))
        self.cBase.setText(cfg.get('base_url', ''))
        self.cBal.setText(cfg.get('balance_path', ''))
        self.cUse.setText(cfg.get('usage_path', ''))
        self.cCur.setText(cfg.get('currency', ''))

    # ---------- 服务商列表 ----------
    def refresh_providers(self):
        prev_key = self.current['key'] if self.current else ''
        self.lstProviders.blockSignals(True)
        self.lstProviders.clear()
        providers = tc.list_providers()
        selected_row = 0
        for i, p in enumerate(providers):
            item = QListWidgetItem(pname(p['name']))
            item.setData(Qt.UserRole, p['key'])
            self.lstProviders.addItem(item)
            if p['key'] == prev_key:
                selected_row = i
        self.lstProviders.setCurrentRow(selected_row)
        self.lstProviders.blockSignals(False)
        self.on_provider_selected()

    def on_provider_clicked(self, item):
        if self.current and item.data(Qt.UserRole) == self.current['key']:
            return
        self.on_provider_selected()

    def on_provider_selected(self):
        items = self.lstProviders.selectedItems()
        if not items:
            return
        key = items[0].data(Qt.UserRole)
        providers = {p['key']: p for p in tc.list_providers()}
        self.current = providers.get(key, {'key': key, 'name': key, 'dashboard': ''})
        # 控制台按钮状态（窗口状态栏提示）
        dashboard = self.current.get('dashboard') or ''
        if dashboard:
            self.status(f"{self.current['name']} -> {dashboard}")
        self.balanceHint.setText(t('请选择左侧的服务商'))
        self.balanceHint.show()
        self.grpUsage.hide()
        # 自定义配置区：custom=新增，custom_xxx=编辑
        if key == 'custom':
            self._editing_custom = ''
            self._fill_custom_form({})
            self.grpCustom.setTitle(t('新增自定义服务商'))
            self.grpCustom.show()
            self.btnDeleteCfg.hide()
        elif key.startswith('custom_'):
            self._editing_custom = key
            self._fill_custom_form(tc.get_custom_configs().get(key, {}))
            self.grpCustom.setTitle(t('编辑自定义服务商'))
            self.grpCustom.show()
            self.btnDeleteCfg.show()
        else:
            self._editing_custom = ''
            self.grpCustom.hide()
        provider_tokens = tc.list_tokens(key)
        if provider_tokens:
            self.apiInput.setText(provider_tokens[0]['token'])
            self.noteInput.setText(provider_tokens[0].get('note', ''))
        else:
            self.apiInput.clear()
            self.noteInput.clear()

    # ---------- 密钥 ----------
    def toggle_echo(self):
        if self.apiInput.echoMode() == QLineEdit.Password:
            self.apiInput.setEchoMode(QLineEdit.Normal)
            self.btnEcho.setText(t('隐藏'))
        else:
            self.apiInput.setEchoMode(QLineEdit.Password)
            self.btnEcho.setText(t('显示'))

    def save_key(self):
        if not self.current or self.current['key'] == 'custom':
            return
        ok, msg, _added = tc.add_token(self.current['key'], self.apiInput.text().strip(),
                                       self.noteInput.text().strip())
        if ok:
            self.refresh_tokens()
        self.status(t(msg))

    def refresh_tokens(self):
        """刷新已保存Token列表（同一服务商可有多条）"""
        self.lstSaved.clear()
        tokens = tc.list_tokens()
        if not tokens:
            self.lstSaved.addItem(QListWidgetItem(t('暂无保存的Token')))
            return
        names = {p['key']: p['name'] for p in tc.list_providers()}
        for tk in tokens:
            line = f"{pname(names.get(tk['provider'], tk['provider']))}  ·  {tk['token'][:8]}..."
            note = tk.get('note', '')
            if note:
                line += chr(10) + note
            item = QListWidgetItem(line)
            item.setData(Qt.UserRole, tk['id'])
            self.lstSaved.addItem(item)

    def on_token_clicked(self, item):
        entry = tc.get_token(item.data(Qt.UserRole))
        if not entry:
            self.refresh_tokens()
            return
        if not self.current or self.current['key'] != entry['provider']:
            for row in range(self.lstProviders.count()):
                if self.lstProviders.item(row).data(Qt.UserRole) == entry['provider']:
                    self.lstProviders.setCurrentRow(row)
                    break
        self.apiInput.setText(entry['token'])
        self.noteInput.setText(entry.get('note', ''))

    def copy_saved_key(self):
        item = self.lstSaved.currentItem()
        entry = tc.get_token(item.data(Qt.UserRole)) if item else None
        if not entry:
            self.status(t('没有已保存的Token'))
            return
        QApplication.clipboard().setText(entry['token'])
        self.status(t('已复制到剪贴板'))

    def edit_note(self):
        item = self.lstSaved.currentItem()
        entry = tc.get_token(item.data(Qt.UserRole)) if item else None
        if not entry:
            self.status(t('没有已保存的Token'))
            return
        text, ok = QInputDialog.getMultiLineText(
            self, t('备注'), t('输入该Token的备注：'), entry.get('note', ''))
        if ok:
            tc.update_token_note(entry['id'], text)
            self.refresh_tokens()
            self.status(t('备注已保存'))

    def delete_selected_key(self):
        item = self.lstSaved.currentItem()
        if not item:
            return
        if tc.delete_token(item.data(Qt.UserRole)):
            self.refresh_tokens()
            self.status(t('Token已删除'))
        else:
            self.status(t('删除失败'))

    # ---------- 余额 / 用量 ----------
    def query_balance(self):
        if not self.current:
            return
        if self.current['key'] == 'custom':
            self.status(t('请先填写配置并保存，再查询'))
            return
        api_key = self.apiInput.text().strip()
        if not api_key:
            self.status(t('请先输入 API Key'))
            return
        self.status(t('正在查询余额...'))
        pkey = self.current['key']
        w = Worker(lambda: tc.query_balance(pkey, api_key))
        self._workers.append(w)
        w.sig.ok.connect(self.on_balance)
        w.sig.err.connect(lambda e: self.status(t('查询失败') + ': ' + e))
        self.pool.start(w)

    def on_balance(self, result):
        ok, data, err = result
        if not ok:
            self.balanceHint.setText(t(err or '查询失败'))
            self.balanceHint.show()
            return
        if not data:
            self.balanceHint.setText(t('余额信息不可用'))
            self.balanceHint.show()
            return
        item = data[0]
        cur = item.get('currency', 'CNY')
        field_map = {'可用余额': 'available', '总余额': 'total', '赠送额度': 'granted', '充值余额': 'topped_up'}
        for zh, field in field_map.items():
            value_lbl, cur_lbl = self.balanceStats[zh]
            value_lbl.setText(str(item.get(field, 0)))
            cur_lbl.setText(cur)
        note = item.get('note', '')
        self.balanceNote.setText(t(note) if note else '')
        self.balanceNote.setVisible(bool(note))
        self.status(t('查询成功'))
        self.query_usage()

    def query_usage(self):
        if not self.current or self.current['key'] == 'custom':
            return
        api_key = self.apiInput.text().strip()
        if not api_key:
            return
        self.usageHint.setText(t('正在查询用量...'))
        self.usageHint.show()
        pkey = self.current['key']
        w = Worker(lambda: tc.query_usage(pkey, api_key))
        self._workers.append(w)
        w.sig.ok.connect(self.on_usage)
        w.sig.err.connect(lambda e: self.usageHint.setText(t('网络错误')))
        self.pool.start(w)

    def on_usage(self, result):
        ok, data, err = result
        if not ok or not data:
            self.usageHint.setText(t(err or '该服务商暂无用量数据'))
            self.usageHint.show()
            return
        cur = data.get('currency', 'CNY')
        field_map = {'今日用量': 'used_today', '本月用量': 'used_month', '累计使用': 'total_used'}
        for zh, field in field_map.items():
            value_lbl, cur_lbl = self.usageStats[zh]
            value_lbl.setText(str(data.get(field, 0)))
            cur_lbl.setText(cur)
        self.usageHint.hide()

    # ---------- 查询全部 ----------
    def query_all(self):
        if not tc.list_tokens():
            self.status(t('没有已保存的Token'))
            return
        self.status(t('正在查询全部...'))

        def fn():
            tokens = tc.list_tokens()
            names = {p['key']: p['name'] for p in tc.list_providers()}
            results = []
            for tk in tokens:
                ok, data, err = tc.query_balance(tk['provider'], tk['token'])
                results.append({'name': names.get(tk['provider'], tk['provider']),
                                'note': tk.get('note', ''), 'token': tk['token'],
                                'ok': ok, 'data': data if ok else None, 'err': err})
            return results

        w = Worker(fn)
        self._workers.append(w)
        w.sig.ok.connect(self.on_query_all)
        w.sig.err.connect(lambda e: self.status(t('查询失败') + ': ' + e))
        self.pool.start(w)

    def on_query_all(self, results):
        self.status(t('全部查询完成'))
        totals = {}
        lines = []
        for r in results:
            name = pname(r['name'])
            tag = f"({r['note']})" if r.get('note') else ''
            if r['ok'] and r['data']:
                item = r['data'][0]
                avail = float(item.get('available', 0) or 0)
                cur = item.get('currency', 'CNY')
                totals[cur] = totals.get(cur, 0) + avail
                lines.append(f"{name}{tag}: {avail} {cur}")
            else:
                lines.append(f"{name}{tag}: {t(r['err'] or '查询失败')}")
        total_line = '   |   '.join(f"{cur} {round(v, 2)}" for cur, v in sorted(totals.items()))
        text = '\n'.join(lines)
        if total_line:
            text += '\n\n' + t('总可用余额') + ': ' + total_line
        self.allText.setText(text)
        self.grpAll.show()

    # ---------- 自定义服务商增删改 ----------
    def save_custom(self):
        cfg = {
            'name': self.cName.text().strip(),
            'base_url': self.cBase.text().strip(),
            'balance_path': self.cBal.text().strip(),
            'usage_path': self.cUse.text().strip(),
            'currency': self.cCur.text().strip(),
        }
        if not cfg['base_url']:
            QMessageBox.warning(self, t('保存失败'), t('请填写 API 地址'))
            return
        cid, _ = tc.save_custom_config(cfg, self._editing_custom)

        self.refresh_providers()
        for row in range(self.lstProviders.count()):
            if self.lstProviders.item(row).data(Qt.UserRole) == cid:
                self.lstProviders.setCurrentRow(row)
                break
        self.refresh_tokens()
        self.status(t('自定义服务商配置已保存'))

    def delete_custom(self):
        if not self._editing_custom:
            return
        ret = QMessageBox.question(
            self, t('删除服务商'), t('确认删除该自定义服务商？其已保存的密钥也会一并删除。'))
        if ret != QMessageBox.Yes:
            return
        tc.delete_custom_config(self._editing_custom)
        for tk in tc.list_tokens(self._editing_custom):
            tc.delete_token(tk['id'])
        self._editing_custom = ''

        self.refresh_providers()
        self.refresh_tokens()
        self.status(t('删除成功'))

    # ---------- 实时价格 ----------
    def load_pricing(self):
        self.status(t('正在刷新价格...'))
        w = Worker(tc.get_pricing)
        self._workers.append(w)
        w.sig.ok.connect(self.on_pricing)
        w.sig.err.connect(lambda e: self.status(t('获取价格数据失败') + ': ' + e))
        self.pool.start(w)

    def on_pricing(self, data):
        if not data.get('success'):
            self.status(data.get('error', '获取价格数据失败'))
            return
        self.priceMeta.setText(
            f"{t('数据来源')} traktoken.com · {t('评估时间')} {data['now']}（{t('北京时间')}）")
        self.priceTable.setHorizontalHeaderLabels(
            [t(x) for x in ('模型', '厂商', '输入价', '输出价', '性价比', '峰谷')])
        rows = sorted(data['rows'], key=lambda r: -(float(r.get('score') or 0)))
        self.priceTable.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.priceTable.setItem(i, 0, QTableWidgetItem(r['model']))
            self.priceTable.setItem(i, 1, QTableWidgetItem(pname(r['vendor'])))
            self.priceTable.setItem(i, 2, QTableWidgetItem(f"${r['input']}"))
            self.priceTable.setItem(i, 3, QTableWidgetItem(f"${r['output']}"))
            self.priceTable.setItem(i, 4, QTableWidgetItem(str(r['score'])))
            if r.get('peak'):
                lbl = QLabel()
                lbl.setText(t(r['peak']))
                lbl.setObjectName('badgeValley' if r['peak'] == '谷' else 'badgePeak')
                lbl.setToolTip(r.get('peak_desc', ''))
                lbl.setAlignment(Qt.AlignCenter)
                self.priceTable.setCellWidget(i, 5, lbl)
            else:
                self.priceTable.setItem(i, 5, QTableWidgetItem('—'))
        self.status('')


def _excepthook(etype, value, tb):
    # 界面槽函数中的未捕获异常写入日志（打包后无控制台可见）
    import traceback
    line = traceback.format_exception(etype, value, tb)
    try:
        from token_core import get_config_dir
        with open(os.path.join(get_config_dir(), 'error.log'), 'a', encoding='utf-8') as f:
            f.write('\n' + '=' * 40 + '\n'.join(line))
    except Exception:
        pass
    sys.__excepthook__(etype, value, tb)


def main():
    sys.excepthook = _excepthook
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    settings = _load_ui_settings()
    _LANG['cur'] = settings.get('lang', 'zh') if settings.get('lang') in ('zh', 'en') else 'zh'
    _THEME['cur'] = settings.get('theme', 'dark') if settings.get('theme') in ('dark', 'light') else 'dark'
    app.setStyleSheet(build_qss(_THEME['cur']))
    win = QMainWindow()
    win.setWindowTitle(f'Token Manager v{APP_VERSION}')
    win.setMinimumSize(980, 640)
    # 窗口尺寸按屏幕可用区域百分比自适应，并居中显示
    screen = app.primaryScreen().availableGeometry()
    win.resize(int(screen.width() * 0.82), int(screen.height() * 0.85))
    win.move(screen.x() + (screen.width() - win.width()) // 2,
             screen.y() + (screen.height() - win.height()) // 2)
    win.setCentralWidget(App())
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
