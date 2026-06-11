#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Manager - AI API余额查询工具
Clash Verge风格极简界面设计
"""

import customtkinter as ctk
import requests
import json
import threading
from datetime import datetime
from abc import ABC, abstractmethod
import re
import sys
import os
import webbrowser

# 加载主题设置
def load_theme_setting():
    config_file = os.path.join(os.path.dirname(__file__), '.token_manager_settings')
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                settings = json.load(f)
                return settings.get('theme', 'dark')
    except Exception:
        pass
    return 'dark'

# 根据保存的设置设置外观模式
theme = load_theme_setting()
ctk.set_appearance_mode(theme)
ctk.set_default_color_theme("dark-blue")

# Windows隐藏子进程窗口
if sys.platform == 'win32':
    import ctypes
    from ctypes import wintypes
    
    class STARTUPINFO(ctypes.Structure):
        _fields_ = [
            ('cb', wintypes.DWORD),
            ('lpReserved', wintypes.LPWSTR),
            ('lpDesktop', wintypes.LPWSTR),
            ('lpTitle', wintypes.LPWSTR),
            ('dwX', wintypes.DWORD),
            ('dwY', wintypes.DWORD),
            ('dwXSize', wintypes.DWORD),
            ('dwYSize', wintypes.DWORD),
            ('dwXCountChars', wintypes.DWORD),
            ('dwYCountChars', wintypes.DWORD),
            ('dwFillAttribute', wintypes.DWORD),
            ('dwFlags', wintypes.DWORD),
            ('wShowWindow', wintypes.WORD),
            ('cbReserved2', wintypes.WORD),
            ('lpReserved2', wintypes.LPBYTE),
            ('hStdInput', wintypes.HANDLE),
            ('hStdOutput', wintypes.HANDLE),
            ('hStdError', wintypes.HANDLE),
        ]
    
    def get_startup_info():
        si = STARTUPINFO()
        si.cb = ctypes.sizeof(STARTUPINFO)
        si.dwFlags = 0x00000001 | 0x00000080
        si.wShowWindow = 0
        return si
    
    startupinfo = get_startup_info()
else:
    startupinfo = None


class APIProvider(ABC):
    """API提供商抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def balance_endpoint(self) -> str:
        pass
    
    @property
    @abstractmethod
    def auth_type(self) -> str:
        pass
    
    @property
    @abstractmethod
    def dashboard_url(self) -> str:
        pass
    
    @abstractmethod
    def parse_balance(self, data: dict) -> list:
        pass
    
    @abstractmethod
    def validate_api_key(self, api_key: str) -> bool:
        pass


class DeepSeekProvider(APIProvider):
    @property
    def name(self): return "DeepSeek"
    @property
    def balance_endpoint(self): return "https://api.deepseek.com/user/balance"
    @property
    def auth_type(self): return "bearer"
    @property
    def dashboard_url(self): return "https://platform.deepseek.com/"
    def parse_balance(self, data: dict) -> list:
        balance_list = data.get('balance_infos', [])
        result = []
        for item in balance_list:
            result.append({
                'currency': item.get('currency', 'CNY'),
                'total': float(item.get('total_balance', '0')),
                'granted': float(item.get('granted_balance', '0')),
                'topped_up': float(item.get('topped_up_balance', '0')),
                'available': float(item.get('total_balance', '0'))
            })
        return result
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('sk-')


class OpenAIProvider(APIProvider):
    @property
    def name(self): return "OpenAI"
    @property
    def balance_endpoint(self): return "https://api.openai.com/v1/dashboard/billing/subscription"
    @property
    def auth_type(self): return "bearer"
    @property
    def dashboard_url(self): return "https://platform.openai.com/"
    def parse_balance(self, data: dict) -> list:
        return [{
            'currency': 'USD',
            'total': 0, 'granted': 0, 'topped_up': 0, 'available': 0,
            'has_subscription': data.get('has_payment_method', False),
            'plan_name': data.get('plan', {}).get('title', 'N/A')
        }]
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('sk-')


class AnthropicProvider(APIProvider):
    @property
    def name(self): return "Anthropic"
    @property
    def balance_endpoint(self): return "https://api.anthropic.com/v1/account"
    @property
    def auth_type(self): return "api_key"
    @property
    def dashboard_url(self): return "https://console.anthropic.com/"
    def parse_balance(self, data: dict) -> list:
        return [{
            'currency': 'USD',
            'total': data.get('spending_limit', 0) / 100 if data.get('spending_limit') else 0,
            'granted': 0,
            'topped_up': 0,
            'available': data.get('spending_limit', 0) / 100 if data.get('spending_limit') else 0
        }]
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('sk-ant-')


API_PROVIDERS = {
    'deepseek': DeepSeekProvider(),
    'openai': OpenAIProvider(),
    'anthropic': AnthropicProvider(),
}


class TokenManagerApp(ctk.CTk):
    """Token Manager - Clash Verge风格"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Token Manager")
        self.geometry("1020x880")
        self.minsize(980, 820)
        
        self.current_provider = None
        self.balance_info = None
        self.api_key_history = {}
        self.is_dark_theme = (theme == 'dark')
        
        # 根据主题设置配色
        self._init_colors()
        self.configure(fg_color=self.colors['bg'])
        
        self.create_widgets()
        self.load_settings()
    
    def _init_colors(self):
        """初始化配色方案"""
        if self.is_dark_theme:
            # 深色主题
            self.colors = {
                'bg': '#000000',
                'bg_sidebar': '#0a0a0a',
                'bg_card': '#1c1c1e',
                'bg_hover': '#2c2c2e',
                'bg_input': '#2c2c2e',
                'bg_button': '#3a3a3c',
                'primary': '#a855f7',
                'primary_hover': '#9333ea',
                'accent': '#6366f1',
                'success': '#22c55e',
                'danger': '#ef4444',
                'warning': '#f59e0b',
                'text': '#ffffff',
                'text_secondary': '#a1a1aa',
                'text_muted': '#71717a',
                'border': '#27272a',
            }
        else:
            # 浅色主题
            self.colors = {
                'bg': '#f5f5f5',
                'bg_sidebar': '#ffffff',
                'bg_card': '#ffffff',
                'bg_hover': '#e5e5e5',
                'bg_input': '#e5e5e5',
                'bg_button': '#d4d4d4',
                'primary': '#a855f7',
                'primary_hover': '#9333ea',
                'accent': '#6366f1',
                'success': '#22c55e',
                'danger': '#ef4444',
                'warning': '#f59e0b',
                'text': '#18181b',
                'text_secondary': '#52525b',
                'text_muted': '#71717a',
                'border': '#e4e4e7',
            }
    
    def create_widgets(self):
        # 主容器
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=self.colors['bg'])
        self.main_frame.pack(fill="both", expand=True)
        
        # ========== 左侧边栏 ==========
        self.sidebar = ctk.CTkFrame(self.main_frame, corner_radius=0, width=200, fg_color=self.colors['bg_sidebar'])
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # 侧边栏标题
        sidebar_title = ctk.CTkFrame(self.sidebar, corner_radius=0, height=70, fg_color="transparent")
        sidebar_title.pack(fill="x", padx=20, pady=(20, 30))
        sidebar_title.pack_propagate(False)
        
        self.sidebar_title_label = ctk.CTkLabel(
            sidebar_title,
            text="⚡ Token Manager",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors['text']
        )
        self.sidebar_title_label.pack(anchor="w", pady=(10, 0))
        
        # 导航按钮
        self.nav_home = self._create_nav_button(self.sidebar, "🏠 首页", True)
        self.nav_home.configure(command=self._show_home)
        
        self.nav_settings = self._create_nav_button(self.sidebar, "⚙️ 设置", False)
        self.nav_settings.configure(command=self._show_settings)
        
        # 底部主题切换
        theme_frame = ctk.CTkFrame(self.sidebar, corner_radius=0, fg_color="transparent")
        theme_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        self.theme_btn = ctk.CTkButton(
            theme_frame,
            text="🌙 Dark" if self.is_dark_theme else "☀️ Light",
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors['bg_card'],
            hover_color=self.colors['bg_hover'],
            text_color=self.colors['text_secondary'],
            command=self.toggle_theme
        )
        self.theme_btn.pack(fill="x")
        
        # ========== 右侧内容区 ==========
        self.content_area = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color=self.colors['bg'])
        self.content_area.pack(side="left", fill="both", expand=True, padx=40, pady=30)
        
        # 创建页面
        self.home_page = self._create_home_page()
        self.settings_page = self._create_settings_page()
        
        self._show_home()
    
    def _create_nav_button(self, parent, text, active=False):
        fg = self.colors['bg_card'] if active else "transparent"
        tc = self.colors['text'] if active else self.colors['text_secondary']
        
        btn = ctk.CTkButton(
            parent,
            text=text,
            height=44,
            corner_radius=10,
            font=ctk.CTkFont(size=14),
            fg_color=fg,
            hover_color=self.colors['bg_card'],
            text_color=tc,
            anchor="w"
        )
        btn.pack(fill="x", padx=12, pady=2)
        return btn
    
    def _create_home_page(self):
        page = ctk.CTkFrame(self.content_area, corner_radius=0, fg_color="transparent")
        
        # 页面标题
        self.page_title = ctk.CTkLabel(
            page,
            text="查询余额",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.colors['text']
        )
        self.page_title.pack(anchor="w", pady=(0, 8))
        
        self.page_subtitle = ctk.CTkLabel(
            page,
            text="选择服务商并输入API密钥查询余额",
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_muted']
        )
        self.page_subtitle.pack(anchor="w", pady=(0, 30))
        
        # 提供商卡片
        self.provider_card = self._create_card(page)
        self.provider_card.pack(fill="x", pady=(0, 16))
        
        self.provider_label = ctk.CTkLabel(
            self.provider_card,
            text="服务商",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['text_secondary']
        )
        self.provider_label.pack(anchor="w", padx=24, pady=(20, 12))
        
        # 提供商选择行
        provider_row = ctk.CTkFrame(self.provider_card, corner_radius=0, fg_color="transparent")
        provider_row.pack(fill="x", padx=24, pady=(0, 20))
        
        provider_names = [""] + [p.name for p in API_PROVIDERS.values()]
        self.provider_combo = ctk.CTkOptionMenu(
            provider_row,
            values=provider_names,
            width=300,
            height=48,
            corner_radius=12,
            font=ctk.CTkFont(size=15),
            fg_color=self.colors['bg_input'],
            button_color=self.colors['primary'],
            button_hover_color=self.colors['primary_hover'],
            dropdown_fg_color=self.colors['bg_card'],
            dropdown_text_color=self.colors['text'],
            command=self.on_provider_changed
        )
        self.provider_combo.pack(side="left", padx=(0, 12))
        
        # Web跳转按钮
        self.web_btn = ctk.CTkButton(
            provider_row,
            text="🌐 官方Web",
            width=120,
            height=48,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors['bg_button'],
            hover_color=self.colors['primary'],
            text_color=self.colors['text_secondary'],
            state="disabled",
            command=self.open_dashboard
        )
        self.web_btn.pack(side="left")
        
        # API密钥卡片
        self.key_card = self._create_card(page)
        self.key_card.pack(fill="x", pady=(0, 16))
        
        self.key_label = ctk.CTkLabel(
            self.key_card,
            text="API 密钥",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['text_secondary']
        )
        self.key_label.pack(anchor="w", padx=24, pady=(20, 8))
        
        self.key_subtitle = ctk.CTkLabel(
            self.key_card,
            text="输入或选择已保存的密钥",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_muted']
        )
        self.key_subtitle.pack(anchor="w", padx=24, pady=(0, 12))
        
        key_row = ctk.CTkFrame(self.key_card, corner_radius=0, fg_color="transparent")
        key_row.pack(fill="x", padx=24, pady=(0, 20))
        
        self.api_key_combo = ctk.CTkComboBox(
            key_row,
            width=380,
            height=48,
            corner_radius=12,
            font=ctk.CTkFont(size=14),
            fg_color=self.colors['bg_input'],
            button_color=self.colors['primary'],
            button_hover_color=self.colors['primary_hover'],
            dropdown_fg_color=self.colors['bg_card'],
            dropdown_text_color=self.colors['text']
        )
        self.api_key_combo.set("")
        self.api_key_combo.pack(side="left", padx=(0, 10))
        
        self.save_btn = ctk.CTkButton(
            key_row,
            text="保存",
            width=80,
            height=48,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors['bg_button'],
            hover_color=self.colors['primary'],
            text_color=self.colors['text'],
            command=self.save_api_key
        )
        self.save_btn.pack(side="left", padx=(0, 8))
        
        self.del_btn = ctk.CTkButton(
            key_row,
            text="删除",
            width=80,
            height=48,
            corner_radius=12,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors['bg_button'],
            hover_color=self.colors['danger'],
            text_color=self.colors['text'],
            command=self.delete_api_key
        )
        self.del_btn.pack(side="left")
        
        # 查询按钮
        self.query_btn = ctk.CTkButton(
            page,
            text="查询余额",
            width=200,
            height=52,
            corner_radius=14,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.colors['primary'],
            hover_color=self.colors['primary_hover'],
            text_color="white",
            command=self.query_balance
        )
        self.query_btn.pack(anchor="w", pady=(8, 20))
        
        # 结果区域
        self.result_frame = self._create_card(page)
        self.result_frame.pack(fill="both", expand=True)
        
        self.result_label = ctk.CTkLabel(
            self.result_frame,
            text="查询结果将在这里显示",
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_muted']
        )
        self.result_label.pack(pady=60)
        
        self.info_container = ctk.CTkFrame(self.result_frame, corner_radius=0, fg_color="transparent")
        
        # 状态栏
        self.status_label = ctk.CTkLabel(
            page,
            text="就绪",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_muted']
        )
        self.status_label.pack(anchor="w", pady=(12, 0))
        
        return page
    
    def _create_settings_page(self):
        page = ctk.CTkFrame(self.content_area, corner_radius=0, fg_color="transparent")
        
        self.settings_title = ctk.CTkLabel(
            page,
            text="设置",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.colors['text']
        )
        self.settings_title.pack(anchor="w", pady=(0, 30))
        
        self.settings_card = self._create_card(page)
        self.settings_card.pack(fill="x")
        
        self.about_label = ctk.CTkLabel(
            self.settings_card,
            text="关于",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors['text']
        )
        self.about_label.pack(anchor="w", padx=24, pady=(24, 12))
        
        self.about_text = ctk.CTkLabel(
            self.settings_card,
            text="Token Manager v1.0\nAI API余额查询工具",
            font=ctk.CTkFont(size=13),
            text_color=self.colors['text_secondary']
        )
        self.about_text.pack(anchor="w", padx=24, pady=(0, 24))
        
        return page
    
    def _create_card(self, parent):
        return ctk.CTkFrame(
            parent,
            corner_radius=16,
            fg_color=self.colors['bg_card'],
            border_width=1,
            border_color=self.colors['border']
        )
    
    def _show_home(self):
        self.settings_page.pack_forget()
        self.home_page.pack(fill="both", expand=True)
        self.nav_home.configure(fg_color=self.colors['bg_card'], text_color=self.colors['text'])
        self.nav_settings.configure(fg_color="transparent", text_color=self.colors['text_secondary'])
    
    def _show_settings(self):
        self.home_page.pack_forget()
        self.settings_page.pack(fill="both", expand=True)
        self.nav_home.configure(fg_color="transparent", text_color=self.colors['text_secondary'])
        self.nav_settings.configure(fg_color=self.colors['bg_card'], text_color=self.colors['text'])
    
    def open_dashboard(self):
        """打开管理界面"""
        if not self.current_provider:
            self.status_label.configure(text="请先选择提供商", text_color=self.colors['danger'])
            return
        
        webbrowser.open(self.current_provider.dashboard_url)
        self.status_label.configure(text=f"已打开 {self.current_provider.name} 官网", text_color=self.colors['primary'])
    
    def on_provider_changed(self, provider_name):
        if not provider_name:
            self.current_provider = None
            self.web_btn.configure(state="disabled")
            self.api_key_combo.set("")
            self.api_key_combo.configure(values=[])
            return
        
        for key, provider in API_PROVIDERS.items():
            if provider.name == provider_name:
                self.current_provider = provider
                self.web_btn.configure(state="normal")
                break
        
        self.load_provider_key()
    
    def load_settings(self):
        self.provider_combo.set("")
        self.current_provider = None
        self.web_btn.configure(state="disabled")
        
        config_file = os.path.join(os.path.dirname(__file__), '.token_manager_settings')
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    settings = json.load(f)
                    
                    saved_provider = settings.get('provider', '')
                    if saved_provider and saved_provider in API_PROVIDERS:
                        self.provider_combo.set(API_PROVIDERS[saved_provider].name)
                        self.current_provider = API_PROVIDERS[saved_provider]
                        self.web_btn.configure(state="normal")
                    
                    self.load_provider_key()
        except Exception:
            pass
    
    def load_provider_key(self):
        if not self.current_provider:
            return
        
        provider_key = self.current_provider.name.lower()
        config_file = os.path.join(os.path.dirname(__file__), f'.{provider_key}_keys')
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    self.api_key_history[provider_key] = json.load(f)
            else:
                self.api_key_history[provider_key] = []
            
            self.api_key_combo.configure(values=self.api_key_history.get(provider_key, []))
            
            if self.api_key_history[provider_key]:
                self.api_key_combo.set(self.api_key_history[provider_key][0])
            else:
                self.api_key_combo.set("")
        except Exception:
            self.api_key_history[provider_key] = []
            self.api_key_combo.configure(values=[])
            self.api_key_combo.set("")
    
    def save_api_key(self):
        if not self.current_provider:
            self.status_label.configure(text="请先选择提供商", text_color=self.colors['danger'])
            return
        
        api_key = self.api_key_combo.get().strip()
        
        if not api_key:
            self.status_label.configure(text="请输入API密钥", text_color=self.colors['danger'])
            return
        
        if not self.current_provider.validate_api_key(api_key):
            self.status_label.configure(
                text=f"API密钥格式不正确",
                text_color=self.colors['danger']
            )
            return
        
        provider_key = self.current_provider.name.lower()
        
        if provider_key not in self.api_key_history:
            self.api_key_history[provider_key] = []
        
        if api_key not in self.api_key_history[provider_key]:
            self.api_key_history[provider_key].insert(0, api_key)
        
        if len(self.api_key_history[provider_key]) > 10:
            self.api_key_history[provider_key] = self.api_key_history[provider_key][:10]
        
        config_file = os.path.join(os.path.dirname(__file__), f'.{provider_key}_keys')
        
        try:
            with open(config_file, 'w') as f:
                json.dump(self.api_key_history[provider_key], f)
            
            self.api_key_combo.configure(values=self.api_key_history[provider_key])
            self.status_label.configure(text="API密钥已保存", text_color=self.colors['success'])
        except Exception as e:
            self.status_label.configure(text=f"保存失败: {str(e)}", text_color=self.colors['danger'])
    
    def delete_api_key(self):
        if not self.current_provider:
            self.status_label.configure(text="请先选择提供商", text_color=self.colors['danger'])
            return
        
        api_key = self.api_key_combo.get().strip()
        
        if not api_key:
            self.status_label.configure(text="请先选择要删除的密钥", text_color=self.colors['danger'])
            return
        
        provider_key = self.current_provider.name.lower()
        
        if provider_key not in self.api_key_history or not self.api_key_history[provider_key]:
            self.status_label.configure(text="没有可删除的密钥", text_color=self.colors['danger'])
            return
        
        if api_key in self.api_key_history[provider_key]:
            self.api_key_history[provider_key].remove(api_key)
            
            config_file = os.path.join(os.path.dirname(__file__), f'.{provider_key}_keys')
            try:
                with open(config_file, 'w') as f:
                    json.dump(self.api_key_history[provider_key], f)
                
                self.api_key_combo.configure(values=self.api_key_history[provider_key])
                self.api_key_combo.set("")
                
                self.status_label.configure(text="已删除密钥", text_color=self.colors['success'])
            except Exception as e:
                self.status_label.configure(text=f"删除失败: {str(e)}", text_color=self.colors['danger'])
        else:
            self.status_label.configure(text="该密钥不在历史记录中", text_color=self.colors['danger'])
    
    def query_balance(self):
        if not self.current_provider:
            self.status_label.configure(text="请先选择提供商", text_color=self.colors['danger'])
            return
        
        api_key = self.api_key_combo.get().strip()
        if not api_key:
            self.status_label.configure(text="请先输入API密钥", text_color=self.colors['danger'])
            return
        
        self.query_btn.configure(state="disabled", text="查询中...")
        self.status_label.configure(text="正在查询...", text_color=self.colors['primary'])
        
        thread = threading.Thread(target=self._query_balance_thread, args=(api_key,))
        thread.daemon = True
        thread.start()
    
    def _query_balance_thread(self, api_key: str):
        try:
            provider = self.current_provider
            url = provider.balance_endpoint
            
            if provider.auth_type == "bearer":
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            else:
                headers = {"x-api-key": api_key, "Content-Type": "application/json"}
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.balance_info = data
                self.after(0, self._display_balance, data)
            elif response.status_code == 401:
                self.after(0, self._show_error, "API密钥无效或已过期")
            elif response.status_code == 403:
                self.after(0, self._show_error, "没有权限访问此API")
            else:
                error_msg = "未知错误"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', error_msg)
                except:
                    pass
                self.after(0, self._show_error, f"查询失败: {error_msg}")
        except requests.exceptions.Timeout:
            self.after(0, self._show_error, "请求超时")
        except requests.exceptions.ConnectionError:
            self.after(0, self._show_error, "网络连接错误")
        except Exception as e:
            self.after(0, self._show_error, f"查询异常: {str(e)}")
    
    def _display_balance(self, data):
        self.query_btn.configure(state="normal", text="查询余额")
        self.status_label.configure(
            text=f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            text_color=self.colors['success']
        )
        
        for widget in self.info_container.winfo_children():
            widget.destroy()
        if self.result_label:
            self.result_label.destroy()
        
        try:
            balance_list = self.current_provider.parse_balance(data)
            
            if not balance_list:
                self.result_label = ctk.CTkLabel(
                    self.result_frame,
                    text="未找到余额信息",
                    font=ctk.CTkFont(size=14),
                    text_color=self.colors['text_muted']
                )
                self.result_label.pack(pady=40)
                return
            
            for balance_item in balance_list:
                self._create_balance_display(balance_item)
            
            self.info_container.pack(fill="both", expand=True, padx=24, pady=24)
            
        except Exception as e:
            self.result_label = ctk.CTkLabel(
                self.result_frame,
                text=f"数据解析错误: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color=self.colors['danger']
            )
            self.result_label.pack(pady=40)
    
    def _create_balance_display(self, balance_item: dict):
        currency = balance_item.get('currency', 'USD')
        total = balance_item.get('total', 0)
        granted = balance_item.get('granted', 0)
        topped_up = balance_item.get('topped_up', 0)
        available = balance_item.get('available', total)
        
        # 余额大数字
        big_balance = ctk.CTkFrame(self.info_container, corner_radius=0, fg_color="transparent")
        big_balance.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            big_balance,
            text=f"{available:.2f}",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color=self.colors['text']
        ).pack(side="left")
        
        ctk.CTkLabel(
            big_balance,
            text=f" {currency}",
            font=ctk.CTkFont(size=20),
            text_color=self.colors['text_secondary']
        ).pack(side="left", pady=(12, 0))
        
        # 详情网格
        grid = ctk.CTkFrame(self.info_container, corner_radius=0, fg_color="transparent")
        grid.pack(fill="x")
        
        items = []
        if total > 0:
            items.append(("总余额", f"{total:.2f}", self.colors['text']))
        if granted > 0:
            items.append(("赠送额度", f"{granted:.2f}", self.colors['success']))
        if topped_up > 0:
            items.append(("充值余额", f"{topped_up:.2f}", self.colors['warning']))
        
        for label, value, color in items:
            cell = ctk.CTkFrame(grid, corner_radius=12, fg_color=self.colors['bg'], border_width=1, border_color=self.colors['border'])
            cell.pack(side="left", fill="x", expand=True, padx=(0, 10))
            
            ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=11), text_color=self.colors['text_muted']).pack(pady=(14, 4))
            ctk.CTkLabel(cell, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color=color).pack(pady=(0, 14))
    
    def _show_error(self, error_msg: str):
        self.query_btn.configure(state="normal", text="查询余额")
        self.status_label.configure(text=error_msg, text_color=self.colors['danger'])
    
    def toggle_theme(self):
        """切换主题并立即刷新界面"""
        self.is_dark_theme = not self.is_dark_theme
        save_theme = 'light' if not self.is_dark_theme else 'dark'
        
        # 保存设置
        config_file = os.path.join(os.path.dirname(__file__), '.token_manager_settings')
        try:
            settings = {}
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    settings = json.load(f)
            settings['theme'] = save_theme
            with open(config_file, 'w') as f:
                json.dump(settings, f)
        except Exception:
            pass
        
        # 更新外观模式
        ctk.set_appearance_mode(save_theme)
        
        # 重新初始化配色
        self._init_colors()
        
        # 刷新所有组件颜色
        self._refresh_all_colors()
        
        # 更新主题按钮文字
        self.theme_btn.configure(text="☀️ Light" if not self.is_dark_theme else "🌙 Dark")
        self.status_label.configure(text="主题已切换", text_color=self.colors['success'])
    
    def _refresh_all_colors(self):
        """刷新所有组件的颜色"""
        # 主窗口
        self.configure(fg_color=self.colors['bg'])
        
        # 主容器
        self.main_frame.configure(fg_color=self.colors['bg'])
        
        # 侧边栏
        self.sidebar.configure(fg_color=self.colors['bg_sidebar'])
        self.sidebar_title_label.configure(text_color=self.colors['text'])
        
        # 导航按钮
        self.nav_home.configure(
            fg_color=self.colors['bg_card'] if self.home_page.winfo_ismapped() else "transparent",
            hover_color=self.colors['bg_card'],
            text_color=self.colors['text'] if self.home_page.winfo_ismapped() else self.colors['text_secondary']
        )
        self.nav_settings.configure(
            fg_color=self.colors['bg_card'] if self.settings_page.winfo_ismapped() else "transparent",
            hover_color=self.colors['bg_card'],
            text_color=self.colors['text'] if self.settings_page.winfo_ismapped() else self.colors['text_secondary']
        )
        
        # 主题按钮
        self.theme_btn.configure(
            fg_color=self.colors['bg_card'],
            hover_color=self.colors['bg_hover'],
            text_color=self.colors['text_secondary']
        )
        
        # 内容区域
        self.content_area.configure(fg_color=self.colors['bg'])
        
        # 首页标题
        self.page_title.configure(text_color=self.colors['text'])
        self.page_subtitle.configure(text_color=self.colors['text_muted'])
        
        # 提供商卡片
        self.provider_card.configure(fg_color=self.colors['bg_card'], border_color=self.colors['border'])
        self.provider_label.configure(text_color=self.colors['text_secondary'])
        self.provider_combo.configure(
            fg_color=self.colors['bg_input'],
            dropdown_fg_color=self.colors['bg_card'],
            dropdown_text_color=self.colors['text']
        )
        self.web_btn.configure(
            fg_color=self.colors['bg_button'],
            hover_color=self.colors['primary'],
            text_color=self.colors['text_secondary']
        )
        
        # API密钥卡片
        self.key_card.configure(fg_color=self.colors['bg_card'], border_color=self.colors['border'])
        self.key_label.configure(text_color=self.colors['text_secondary'])
        self.key_subtitle.configure(text_color=self.colors['text_muted'])
        self.api_key_combo.configure(
            fg_color=self.colors['bg_input'],
            dropdown_fg_color=self.colors['bg_card'],
            dropdown_text_color=self.colors['text']
        )
        self.save_btn.configure(fg_color=self.colors['bg_button'], text_color=self.colors['text'])
        self.del_btn.configure(fg_color=self.colors['bg_button'], text_color=self.colors['text'])
        
        # 查询按钮
        self.query_btn.configure(fg_color=self.colors['primary'])
        
        # 结果区域
        self.result_frame.configure(fg_color=self.colors['bg_card'], border_color=self.colors['border'])
        if hasattr(self, 'result_label') and self.result_label:
            self.result_label.configure(text_color=self.colors['text_muted'])
        
        # 状态栏
        self.status_label.configure(text_color=self.colors['text_muted'])
        
        # 设置页面
        self.settings_title.configure(text_color=self.colors['text'])
        self.settings_card.configure(fg_color=self.colors['bg_card'], border_color=self.colors['border'])
        self.about_label.configure(text_color=self.colors['text'])
        self.about_text.configure(text_color=self.colors['text_secondary'])


def main():
    app = TokenManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()