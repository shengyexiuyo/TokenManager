#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Manager - AI API余额查询工具
支持多种AI服务提供商的API余额查询
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

# 设置外观
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

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
        """获取Windows隐藏窗口的STARTUPINFO"""
        si = STARTUPINFO()
        si.cb = ctypes.sizeof(STARTUPINFO)
        si.dwFlags = 0x00000001 | 0x00000080  # STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        return si
    
    startupinfo = get_startup_info()
else:
    startupinfo = None


class APIProvider(ABC):
    """API提供商抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """提供商名称"""
        pass
    
    @property
    @abstractmethod
    def balance_endpoint(self) -> str:
        """余额查询API端点"""
        pass
    
    @property
    @abstractmethod
    def auth_type(self) -> str:
        """认证类型: bearer 或 api_key"""
        pass
    
    @property
    @abstractmethod
    def dashboard_url(self) -> str:
        """Web管理界面URL"""
        pass
    
    @abstractmethod
    def parse_balance(self, data: dict) -> list:
        """解析余额数据"""
        pass
    
    @abstractmethod
    def validate_api_key(self, api_key: str) -> bool:
        """验证API密钥格式"""
        pass


class DeepSeekProvider(APIProvider):
    """DeepSeek API提供商"""
    
    @property
    def name(self) -> str:
        return "DeepSeek"
    
    @property
    def balance_endpoint(self) -> str:
        return "https://api.deepseek.com/user/balance"
    
    @property
    def auth_type(self) -> str:
        return "bearer"
    
    @property
    def dashboard_url(self) -> str:
        return "https://platform.deepseek.com/"
    
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
    """OpenAI API提供商"""
    
    @property
    def name(self) -> str:
        return "OpenAI"
    
    @property
    def balance_endpoint(self) -> str:
        return "https://api.openai.com/v1/dashboard/billing/subscription"
    
    @property
    def auth_type(self) -> str:
        return "bearer"
    
    @property
    def dashboard_url(self) -> str:
        return "https://platform.openai.com/"
    
    def parse_balance(self, data: dict) -> list:
        # OpenAI返回的数据格式需要额外调用usage API
        return [{
            'currency': 'USD',
            'total': 0,
            'granted': 0,
            'topped_up': 0,
            'available': 0,
            'has_subscription': data.get('has_payment_method', False),
            'plan_name': data.get('plan', {}).get('title', 'N/A')
        }]
    
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('sk-')


class AnthropicProvider(APIProvider):
    """Anthropic API提供商"""
    
    @property
    def name(self) -> str:
        return "Anthropic"
    
    @property
    def balance_endpoint(self) -> str:
        return "https://api.anthropic.com/v1/account"
    
    @property
    def auth_type(self) -> str:
        return "api_key"
    
    @property
    def dashboard_url(self) -> str:
        return "https://console.anthropic.com/"
    
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


# 注册所有提供商
API_PROVIDERS = {
    'deepseek': DeepSeekProvider(),
    'openai': OpenAIProvider(),
    'anthropic': AnthropicProvider(),
}


class TokenManagerApp(ctk.CTk):
    """Token Manager 主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Token Manager - AI API余额查询")
        self.geometry("700x750")
        self.minsize(650, 700)  # 设置最小窗口大小
        
        # 当前选中的提供商
        self.current_provider = None
        self.balance_info = None
        
        # 创建界面
        self.create_widgets()
        
        # 加载保存的设置
        self.load_settings()
    
    def create_widgets(self):
        """创建界面组件"""
        
        # 主容器
        main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#ffffff")
        main_frame.pack(fill="both", expand=True)
        
        # 标题栏
        header_frame = ctk.CTkFrame(main_frame, corner_radius=0, height=70, fg_color="#0078d4")
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Token Manager",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=18)
        
        # 内容区域
        content_frame = ctk.CTkFrame(main_frame, corner_radius=0, fg_color="#f5f5f5")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 提供商选择
        provider_frame = ctk.CTkFrame(content_frame, corner_radius=12, fg_color="#ffffff")
        provider_frame.pack(fill="x", pady=(0, 20))
        
        provider_title = ctk.CTkLabel(
            provider_frame,
            text="选择AI服务提供商",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#333333"
        )
        provider_title.pack(anchor="w", padx=20, pady=(20, 15))
        
        # 提供商选择下拉框
        provider_select_frame = ctk.CTkFrame(provider_frame, corner_radius=0, fg_color="transparent")
        provider_select_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        provider_names = [""] + [p.name for p in API_PROVIDERS.values()]
        self.provider_combo = ctk.CTkOptionMenu(
            provider_select_frame,
            values=provider_names,
            width=220,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14),
            command=self.on_provider_changed
        )
        self.provider_combo.pack(side="left", padx=(0, 15))
        
        # 跳转管理界面按钮
        self.dashboard_button = ctk.CTkButton(
            provider_select_frame,
            text="官方web",
            width=100,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            state="disabled",
            command=self.open_dashboard
        )
        self.dashboard_button.pack(side="left")
        
        # API密钥输入区域
        key_frame = ctk.CTkFrame(content_frame, corner_radius=12, fg_color="#ffffff")
        key_frame.pack(fill="x", pady=(0, 20))
        
        key_title = ctk.CTkLabel(
            key_frame,
            text="API 密钥",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#333333"
        )
        key_title.pack(anchor="w", padx=20, pady=(20, 10))
        
        key_subtitle = ctk.CTkLabel(
            key_frame,
            text="输入API密钥以查询余额",
            font=ctk.CTkFont(size=13),
            text_color="#666666"
        )
        key_subtitle.pack(anchor="w", padx=20, pady=(0, 15))
        
        key_input_frame = ctk.CTkFrame(key_frame, corner_radius=0, fg_color="transparent")
        key_input_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.api_key_entry = ctk.CTkEntry(
            key_input_frame,
            width=400,
            height=36,
            corner_radius=6,
            font=ctk.CTkFont(size=12),
            placeholder_text="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        )
        self.api_key_entry.pack(side="left", padx=(0, 10))
        
        self.save_key_button = ctk.CTkButton(
            key_input_frame,
            text="保存",
            width=80,
            height=36,
            corner_radius=6,
            font=ctk.CTkFont(size=13),
            command=self.save_api_key
        )
        self.save_key_button.pack(side="left")
        
        # 查询按钮
        self.query_button = ctk.CTkButton(
            content_frame,
            text="查询余额",
            width=220,
            height=50,
            corner_radius=10,
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self.query_balance
        )
        self.query_button.pack(pady=(0, 20))
        
        # 余额显示区域
        self.balance_frame = ctk.CTkFrame(content_frame, corner_radius=8, fg_color="#ffffff")
        self.balance_frame.pack(fill="both", expand=True)
        
        self.balance_label = ctk.CTkLabel(
            self.balance_frame,
            text="请选择提供商、输入API密钥并点击查询按钮",
            font=ctk.CTkFont(size=14),
            text_color="#666666"
        )
        self.balance_label.pack(pady=30)
        
        # 详细信息区域（初始隐藏）
        self.info_frame = ctk.CTkFrame(self.balance_frame, corner_radius=0, fg_color="transparent")
        
        # 状态标签
        self.status_label = ctk.CTkLabel(
            content_frame,
            text="Token Manager - AI API余额查询工具",
            font=ctk.CTkFont(size=13),
            text_color="#666666"
        )
        self.status_label.pack(pady=(15, 5))
    
    def on_provider_changed(self, provider_name: str):
        """提供商改变时的回调"""
        # 如果选择空，禁用按钮
        if not provider_name:
            self.current_provider = None
            self.dashboard_button.configure(state="disabled")
            self.api_key_entry.delete(0, 'end')
            return
        
        # 找到对应的提供商
        for key, provider in API_PROVIDERS.items():
            if provider.name == provider_name:
                self.current_provider = provider
                self.dashboard_button.configure(state="normal")
                break
        
        # 加载该提供商的保存密钥
        self.load_provider_key()
    
    def open_dashboard(self):
        """打开管理界面"""
        if not self.current_provider:
            self.status_label.configure(text="请先选择提供商", text_color="#dc3545")
            return
        
        dashboard_url = self.current_provider.dashboard_url
        self.status_label.configure(
            text=f"正在打开 {self.current_provider.name} 管理界面...",
            text_color="#0078d4"
        )
        webbrowser.open(dashboard_url)
    
    def load_settings(self):
        """加载保存的设置"""
        # 默认选择空
        self.provider_combo.set("")
        self.current_provider = None
        self.dashboard_button.configure(state="disabled")
        
        config_file = os.path.join(os.path.dirname(__file__), '.token_manager_settings')
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    settings = json.load(f)
                    
                    # 加载选中的提供商
                    saved_provider = settings.get('provider', '')
                    if saved_provider and saved_provider in API_PROVIDERS:
                        self.provider_combo.set(API_PROVIDERS[saved_provider].name)
                        self.current_provider = API_PROVIDERS[saved_provider]
                        self.dashboard_button.configure(state="normal")
                    
                    # 加载密钥
                    self.load_provider_key()
        except Exception:
            pass
    
    def load_provider_key(self):
        """加载当前提供商的密钥"""
        if not self.current_provider:
            return
        
        provider_key = self.current_provider.name.lower()
        config_file = os.path.join(os.path.dirname(__file__), f'.{provider_key}_key')
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    api_key = f.read().strip()
                    if api_key:
                        self.api_key_entry.delete(0, 'end')
                        self.api_key_entry.insert(0, api_key)
        except Exception:
            pass
    
    def save_settings(self):
        """保存设置"""
        if not self.current_provider:
            return
        
        config_file = os.path.join(os.path.dirname(__file__), '.token_manager_settings')
        try:
            settings = {
                'provider': self.current_provider.name.lower()
            }
            with open(config_file, 'w') as f:
                json.dump(settings, f)
        except Exception:
            pass
    
    def save_api_key(self):
        """保存API密钥"""
        if not self.current_provider:
            self.status_label.configure(text="请先选择提供商", text_color="#dc3545")
            return
        
        api_key = self.api_key_entry.get().strip()
        
        if not api_key:
            self.status_label.configure(text="请输入API密钥", text_color="#dc3545")
            return
        
        if not self.current_provider.validate_api_key(api_key):
            self.status_label.configure(
                text=f"API密钥格式不正确，{self.current_provider.name}密钥应以'{self.current_provider.name}'的密钥格式开头",
                text_color="#dc3545"
            )
            return
        
        # 保存到对应提供商的密钥文件
        provider_key = self.current_provider.name.lower()
        config_file = os.path.join(os.path.dirname(__file__), f'.{provider_key}_key')
        
        try:
            with open(config_file, 'w') as f:
                f.write(api_key)
            self.status_label.configure(text=f"✓ {self.current_provider.name} API密钥已保存", text_color="#28a745")
        except Exception as e:
            self.status_label.configure(text=f"保存失败: {str(e)}", text_color="#dc3545")
    
    def query_balance(self):
        """查询余额"""
        if not self.current_provider:
            self.status_label.configure(text="请先选择提供商", text_color="#dc3545")
            return
        
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            self.status_label.configure(text="请先保存API密钥", text_color="#dc3545")
            return
        
        # 在新线程中执行查询
        self.query_button.configure(state="disabled", text="查询中...")
        self.status_label.configure(text="正在查询...", text_color="#0078d4")
        
        thread = threading.Thread(target=self._query_balance_thread, args=(api_key,))
        thread.daemon = True
        thread.start()
    
    def _query_balance_thread(self, api_key: str):
        """后台查询线程"""
        try:
            provider = self.current_provider
            url = provider.balance_endpoint
            
            # 构建请求头
            if provider.auth_type == "bearer":
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            else:
                headers = {
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                }
            
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
            self.after(0, self._show_error, "请求超时，请检查网络连接")
        except requests.exceptions.ConnectionError:
            self.after(0, self._show_error, "网络连接错误，请检查网络")
        except Exception as e:
            self.after(0, self._show_error, f"查询异常: {str(e)}")
    
    def _display_balance(self, data):
        """显示余额信息"""
        self.query_button.configure(state="normal", text="查询余额")
        self.status_label.configure(
            text=f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            text_color="#666666"
        )
        
        # 清空现有显示
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        self.balance_label.destroy()
        
        # 解析余额数据
        try:
            balance_list = self.current_provider.parse_balance(data)
            
            if not balance_list:
                self.balance_label = ctk.CTkLabel(
                    self.balance_frame,
                    text="未找到余额信息",
                    font=ctk.CTkFont(size=14),
                    text_color="#666666"
                )
                self.balance_label.pack(pady=30)
                return
            
            # 显示余额信息
            for balance_item in balance_list:
                self._create_balance_card(balance_item)
            
            self.info_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
        except Exception as e:
            self.balance_label = ctk.CTkLabel(
                self.balance_frame,
                text=f"数据解析错误: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color="#dc3545"
            )
            self.balance_label.pack(pady=30)
    
    def _create_balance_card(self, balance_item: dict):
        """创建余额卡片"""
        currency = balance_item.get('currency', 'USD')
        total = balance_item.get('total', 0)
        granted = balance_item.get('granted', 0)
        topped_up = balance_item.get('topped_up', 0)
        available = balance_item.get('available', total)
        
        # 创建余额卡片
        card = ctk.CTkFrame(self.info_frame, corner_radius=12, fg_color="#f8f9fa")
        card.pack(fill="x", padx=15, pady=8)
        
        # 提供商名称
        provider_label = ctk.CTkLabel(
            card,
            text=f"💰 {self.current_provider.name} ({currency})",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#333333"
        )
        provider_label.pack(anchor="w", padx=20, pady=(20, 15))
        
        # 余额详情
        details_frame = ctk.CTkFrame(card, corner_radius=0, fg_color="transparent")
        details_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # 账户余额
        available_text = f"账户余额: {available:.2f} {currency}"
        available_label = ctk.CTkLabel(
            details_frame,
            text=available_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#0078d4"
        )
        available_label.pack(anchor="w", pady=4)
        
        # 总余额
        if total > 0:
            total_text = f"总余额: {total:.2f} {currency}"
            total_label = ctk.CTkLabel(
                details_frame,
                text=total_text,
                font=ctk.CTkFont(size=14),
                text_color="#333333"
            )
            total_label.pack(anchor="w", pady=4)
        
        # 赠送余额
        if granted > 0:
            granted_text = f"赠送额度: {granted:.2f} {currency}"
            granted_label = ctk.CTkLabel(
                details_frame,
                text=granted_text,
                font=ctk.CTkFont(size=14),
                text_color="#28a745"
            )
            granted_label.pack(anchor="w", pady=4)
        
        # 充值余额
        if topped_up > 0:
            topped_up_text = f"充值余额: {topped_up:.2f} {currency}"
            topped_up_label = ctk.CTkLabel(
                details_frame,
                text=topped_up_text,
                font=ctk.CTkFont(size=14),
                text_color="#666666"
            )
            topped_up_label.pack(anchor="w", pady=4)
    
    def _show_error(self, error_msg: str):
        """显示错误信息"""
        self.query_button.configure(state="normal", text="查询余额")
        self.status_label.configure(text=f"✗ {error_msg}", text_color="#dc3545")


def main():
    """主函数"""
    app = TokenManagerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
