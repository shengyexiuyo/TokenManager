#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Token Manager Core - AI API余额查询核心功能
纯Python模块，无GUI依赖
"""

import requests
import json
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class APIProvider(ABC):
    """API提供商抽象基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def key(self) -> str:
        pass
    
    @property
    @abstractmethod
    def balance_endpoint(self) -> str:
        pass
    
    @property
    @abstractmethod
    def usage_endpoint(self) -> str:
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
    def parse_usage(self, data: dict) -> dict:
        pass
    
    @abstractmethod
    def validate_api_key(self, api_key: str) -> bool:
        pass


class DeepSeekProvider(APIProvider):
    @property
    def name(self): return "DeepSeek"
    @property
    def key(self): return "deepseek"
    @property
    def balance_endpoint(self): return "https://api.deepseek.com/user/balance"
    @property
    def usage_endpoint(self): return "https://api.deepseek.com/user/balance"
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
    def parse_usage(self, data: dict) -> dict:
        balance_list = data.get('balance_infos', [])
        if balance_list:
            item = balance_list[0]
            return {
                'currency': item.get('currency', 'CNY'),
                'used_today': 0,
                'used_month': 0,
                'total_used': float(item.get('total_balance', '0')) - float(item.get('available_balance', item.get('total_balance', '0')))
            }
        return {'currency': 'CNY', 'used_today': 0, 'used_month': 0, 'total_used': 0}
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('sk-')


class OpenAIProvider(APIProvider):
    @property
    def name(self): return "OpenAI"
    @property
    def key(self): return "openai"
    @property
    def balance_endpoint(self): return "https://api.openai.com/v1/dashboard/billing/subscription"
    @property
    def usage_endpoint(self): return "https://api.openai.com/v1/dashboard/billing/usage"
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
    def parse_usage(self, data: dict) -> dict:
        daily_costs = data.get('daily_costs', [])
        today_usage = 0
        month_usage = 0
        
        if daily_costs:
            for day in daily_costs:
                day_total = sum(item.get('cost', 0) for item in day.get('line_items', []))
                month_usage += day_total
            last_day = daily_costs[-1]
            today_usage = sum(item.get('cost', 0) for item in last_day.get('line_items', []))
        
        return {
            'currency': 'USD',
            'used_today': round(today_usage, 4),
            'used_month': round(month_usage, 4),
            'total_used': round(month_usage, 4)
        }
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('sk-')


class DoubaoLiteProvider(APIProvider):
    @property
    def name(self): return "Doubao-Lite"
    @property
    def key(self): return "doubao"
    @property
    def balance_endpoint(self): return "https://ark.cn-beijing.volces.com/api/usage/v1/balance"
    @property
    def usage_endpoint(self): return "https://ark.cn-beijing.volces.com/api/usage/v1/query"
    @property
    def auth_type(self): return "bearer"
    @property
    def dashboard_url(self): return "https://console.volcengine.com/ark"
    def parse_balance(self, data: dict) -> list:
        return [{
            'currency': data.get('currency', 'CNY'),
            'total': float(data.get('balance', 0)),
            'granted': float(data.get('granted_balance', 0)),
            'topped_up': float(data.get('topped_up_balance', 0)),
            'available': float(data.get('balance', 0))
        }]
    def parse_usage(self, data: dict) -> dict:
        return {
            'currency': data.get('currency', 'CNY'),
            'used_today': float(data.get('daily_used', 0)),
            'used_month': float(data.get('monthly_used', 0)),
            'total_used': float(data.get('total_used', 0))
        }
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('ak-') or len(api_key) > 20


class WenxinYiyanProvider(APIProvider):
    @property
    def name(self): return "文心一言"
    @property
    def key(self): return "wenxin"
    @property
    def balance_endpoint(self): return "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/balance"
    @property
    def usage_endpoint(self): return "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/usage"
    @property
    def auth_type(self): return "bearer"
    @property
    def dashboard_url(self): return "https://console.bce.baidu.com/qianfan/ais/console/overview"
    def parse_balance(self, data: dict) -> list:
        return [{
            'currency': data.get('currency', 'CNY'),
            'total': float(data.get('total_quota', 0)),
            'granted': float(data.get('granted_quota', 0)),
            'topped_up': float(data.get('used_quota', 0)),
            'available': float(data.get('total_quota', 0)) - float(data.get('used_quota', 0))
        }]
    def parse_usage(self, data: dict) -> dict:
        return {
            'currency': data.get('currency', 'CNY'),
            'used_today': float(data.get('daily_used', 0)),
            'used_month': float(data.get('monthly_used', 0)),
            'total_used': float(data.get('total_used', 0))
        }
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('API-Key') or api_key.startswith('bce-') or len(api_key) > 30


class QwenProvider(APIProvider):
    @property
    def name(self): return "通义千问"
    @property
    def key(self): return "qwen"
    @property
    def balance_endpoint(self): return "https://dashscope.aliyuncs.com/api/v1/usage"
    @property
    def usage_endpoint(self): return "https://dashscope.aliyuncs.com/api/v1/usage"
    @property
    def auth_type(self): return "bearer"
    @property
    def dashboard_url(self): return "https://bailian.console.aliyun.com"
    def parse_balance(self, data: dict) -> list:
        return [{
            'currency': data.get('currency', 'CNY'),
            'total': float(data.get('total_balance', 0)),
            'granted': float(data.get('granted_balance', 0)),
            'topped_up': float(data.get('topped_up_balance', 0)),
            'available': float(data.get('available_balance', 0))
        }]
    def parse_usage(self, data: dict) -> dict:
        return {
            'currency': data.get('currency', 'CNY'),
            'used_today': float(data.get('daily_cost', 0)),
            'used_month': float(data.get('monthly_cost', 0)),
            'total_used': float(data.get('total_cost', 0))
        }
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('sk-') and len(api_key) > 40


class GLMProvider(APIProvider):
    @property
    def name(self): return "GLM"
    @property
    def key(self): return "glm"
    @property
    def balance_endpoint(self): return "https://open.bigmodel.cn/api/paas/v4/usage"
    @property
    def usage_endpoint(self): return "https://open.bigmodel.cn/api/paas/v4/usage"
    @property
    def auth_type(self): return "bearer"
    @property
    def dashboard_url(self): return "https://open.bigmodel.cn/console"
    def parse_balance(self, data: dict) -> list:
        return [{
            'currency': data.get('currency', 'CNY'),
            'total': float(data.get('total_balance', 0)),
            'granted': float(data.get('granted_balance', 0)),
            'topped_up': float(data.get('topped_up_balance', 0)),
            'available': float(data.get('available_balance', 0))
        }]
    def parse_usage(self, data: dict) -> dict:
        return {
            'currency': data.get('currency', 'CNY'),
            'used_today': float(data.get('daily_used', 0)),
            'used_month': float(data.get('monthly_used', 0)),
            'total_used': float(data.get('total_used', 0))
        }
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('glm-') or len(api_key) > 30


class HunyuanProvider(APIProvider):
    @property
    def name(self): return "腾讯云混元"
    @property
    def key(self): return "hunyuan"
    @property
    def balance_endpoint(self): return "https://hunyuan.cloud.tencent.com/api/v1/balance"
    @property
    def usage_endpoint(self): return "https://hunyuan.cloud.tencent.com/api/v1/usage"
    @property
    def auth_type(self): return "bearer"
    @property
    def dashboard_url(self): return "https://console.cloud.tencent.com/hunyuan"
    def parse_balance(self, data: dict) -> list:
        return [{
            'currency': data.get('currency', 'CNY'),
            'total': float(data.get('total_balance', 0)),
            'granted': float(data.get('granted_balance', 0)),
            'topped_up': float(data.get('topped_up_balance', 0)),
            'available': float(data.get('available_balance', 0))
        }]
    def parse_usage(self, data: dict) -> dict:
        return {
            'currency': data.get('currency', 'CNY'),
            'used_today': float(data.get('daily_used', 0)),
            'used_month': float(data.get('monthly_used', 0)),
            'total_used': float(data.get('total_used', 0))
        }
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('sk-') and len(api_key) > 40


class ZhipuProvider(APIProvider):
    @property
    def name(self): return "智谱 AI"
    @property
    def key(self): return "zhipu"
    @property
    def balance_endpoint(self): return "https://open.bigmodel.cn/api/paas/v4/usage"
    @property
    def usage_endpoint(self): return "https://open.bigmodel.cn/api/paas/v4/usage"
    @property
    def auth_type(self): return "bearer"
    @property
    def dashboard_url(self): return "https://open.bigmodel.cn/console"
    def parse_balance(self, data: dict) -> list:
        return [{
            'currency': data.get('currency', 'CNY'),
            'total': float(data.get('total_balance', 0)),
            'granted': float(data.get('granted_balance', 0)),
            'topped_up': float(data.get('topped_up_balance', 0)),
            'available': float(data.get('available_balance', 0))
        }]
    def parse_usage(self, data: dict) -> dict:
        return {
            'currency': data.get('currency', 'CNY'),
            'used_today': float(data.get('daily_used', 0)),
            'used_month': float(data.get('monthly_used', 0)),
            'total_used': float(data.get('total_used', 0))
        }
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('glm-') or len(api_key) > 30


class MimoProvider(APIProvider):
    @property
    def name(self): return "Mimo"
    @property
    def key(self): return "mimo"
    @property
    def balance_endpoint(self): return "https://api.xiaomimimo.com/v1/balance"
    @property
    def usage_endpoint(self): return "https://api.xiaomimimo.com/v1/chat/completions"
    @property
    def auth_type(self): return "bearer"
    @property
    def dashboard_url(self): return "https://platform.xiaomimimo.com/console/balance"
    def parse_balance(self, data: dict) -> list:
        return [{
            'currency': data.get('currency', 'CNY'),
            'total': float(data.get('total_balance', 0)),
            'granted': float(data.get('granted_balance', 0)),
            'topped_up': float(data.get('topped_up_balance', 0)),
            'available': float(data.get('available_balance', 0)),
            'credits': float(data.get('credits', 0)),
            'credits_used': float(data.get('credits_used', 0))
        }]
    def parse_usage(self, data: dict) -> dict:
        return {
            'currency': 'CNY',
            'used_today': float(data.get('daily_usage', 0)),
            'used_month': float(data.get('monthly_usage', 0)),
            'total_used': float(data.get('total_used', 0))
        }
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('sk-') or api_key.startswith('tp-') or len(api_key) > 30


class KimiProvider(APIProvider):
    @property
    def name(self): return "Kimi"
    @property
    def key(self): return "kimi"
    @property
    def balance_endpoint(self): return "https://api.moonshot.cn/v1/balance"
    @property
    def usage_endpoint(self): return "https://api.moonshot.cn/v1/usage"
    @property
    def auth_type(self): return "bearer"
    @property
    def dashboard_url(self): return "https://platform.moonshot.cn"
    def parse_balance(self, data: dict) -> list:
        return [{
            'currency': data.get('currency', 'CNY'),
            'total': float(data.get('total_balance', 0)),
            'granted': float(data.get('granted_balance', 0)),
            'topped_up': float(data.get('topped_up_balance', 0)),
            'available': float(data.get('available_balance', 0))
        }]
    def parse_usage(self, data: dict) -> dict:
        return {
            'currency': data.get('currency', 'CNY'),
            'used_today': float(data.get('daily_used', 0)),
            'used_month': float(data.get('monthly_used', 0)),
            'total_used': float(data.get('total_used', 0))
        }
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('sk-') and '-moonshot-' in api_key


class ClaudeProvider(APIProvider):
    @property
    def name(self): return "Claude"
    @property
    def key(self): return "claude"
    @property
    def balance_endpoint(self): return "https://api.anthropic.com/v1/organizations/current/credit_summary"
    @property
    def usage_endpoint(self): return "https://api.anthropic.com/v1/users/credit_summary"
    @property
    def auth_type(self): return "bearer"
    @property
    def dashboard_url(self): return "https://console.anthropic.com/"
    def parse_balance(self, data: dict) -> list:
        return [{
            'currency': 'USD',
            'total': float(data.get('credit_balance', 0)),
            'granted': float(data.get('free_credits_remaining', 0)),
            'topped_up': float(data.get('purchased_credits', 0)),
            'available': float(data.get('credit_balance', 0))
        }]
    def parse_usage(self, data: dict) -> dict:
        return {
            'currency': 'USD',
            'used_today': float(data.get('daily_usage', 0)),
            'used_month': float(data.get('monthly_usage', 0)),
            'total_used': float(data.get('total_usage', 0))
        }
    def validate_api_key(self, api_key: str) -> bool:
        return api_key.startswith('sk-ant-')


API_PROVIDERS = {
    'deepseek': DeepSeekProvider(),
    'openai': OpenAIProvider(),
    'doubao': DoubaoLiteProvider(),
    'wenxin': WenxinYiyanProvider(),
    'qwen': QwenProvider(),
    'glm': GLMProvider(),
    'hunyuan': HunyuanProvider(),
    'zhipu': ZhipuProvider(),
    'mimo': MimoProvider(),
    'kimi': KimiProvider(),
    'claude': ClaudeProvider(),
}


class TokenBalanceChecker:
    """Token余额查询核心类"""
    
    def __init__(self, provider: APIProvider, api_key: str):
        self.provider = provider
        self.api_key = api_key
        self.session = requests.Session()
    
    def _get_headers(self) -> dict:
        """获取请求头"""
        if self.provider.auth_type == "bearer":
            return {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider.auth_type == "api_key":
            return {
                "api-key": self.api_key,
                "Content-Type": "application/json"
            }
        return {"Authorization": f"Bearer {self.api_key}"}
    
    def get_balance(self) -> tuple[bool, Any, str]:
        """查询余额"""
        try:
            headers = self._get_headers()
            response = self.session.get(
                self.provider.balance_endpoint,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                balance_list = self.provider.parse_balance(data)
                return True, balance_list, ""
            elif response.status_code == 401:
                return False, None, "API密钥无效或已过期"
            elif response.status_code == 403:
                return False, None, "API密钥权限不足"
            else:
                return False, None, f"请求失败: {response.status_code} - {response.text}"
        except requests.exceptions.Timeout:
            return False, None, "请求超时"
        except requests.exceptions.ConnectionError:
            return False, None, "网络连接失败"
        except Exception as e:
            return False, None, f"查询失败: {str(e)}"
    
    def get_usage(self) -> tuple[bool, Any, str]:
        """查询用量"""
        try:
            headers = self._get_headers()
            
            # OpenAI需要特殊处理
            if self.provider.key == 'openai':
                now = datetime.now()
                start_date = f"{now.year}-{now.month:02d}-01"
                next_month = now.month + 1 if now.month < 12 else 1
                next_year = now.year if now.month < 12 else now.year + 1
                end_date = f"{next_year}-{next_month:02d}-01"
                
                params = {
                    "start_date": start_date,
                    "end_date": end_date
                }
                response = self.session.get(
                    self.provider.usage_endpoint,
                    headers=headers,
                    params=params,
                    timeout=30
                )
            else:
                response = self.session.get(
                    self.provider.usage_endpoint,
                    headers=headers,
                    timeout=30
                )
            
            if response.status_code == 200:
                data = response.json()
                usage = self.provider.parse_usage(data)
                return True, usage, ""
            elif response.status_code == 401:
                return False, None, "API密钥无效或已过期"
            else:
                return False, None, f"请求失败: {response.status_code}"
        except requests.exceptions.Timeout:
            return False, None, "请求超时"
        except requests.exceptions.ConnectionError:
            return False, None, "网络连接失败"
        except Exception as e:
            return False, None, f"查询失败: {str(e)}"


def list_providers() -> List[Dict[str, str]]:
    """列出所有支持的提供商"""
    return [
        {
            'key': provider.key,
            'name': provider.name,
            'dashboard': provider.dashboard_url
        }
        for provider in API_PROVIDERS.values()
    ]


def get_provider_by_key(key: str) -> Optional[APIProvider]:
    """根据key获取提供商"""
    return API_PROVIDERS.get(key.lower())


def query_balance(provider_key: str, api_key: str) -> tuple[bool, Any, str]:
    """快速查询余额"""
    provider = get_provider_by_key(provider_key)
    if not provider:
        return False, None, f"未知提供商: {provider_key}"
    
    if not provider.validate_api_key(api_key):
        return False, None, "API密钥格式不正确"
    
    checker = TokenBalanceChecker(provider, api_key)
    return checker.get_balance()


def query_usage(provider_key: str, api_key: str) -> tuple[bool, Any, str]:
    """快速查询用量"""
    provider = get_provider_by_key(provider_key)
    if not provider:
        return False, None, f"未知提供商: {provider_key}"
    
    if not provider.validate_api_key(api_key):
        return False, None, "API密钥格式不正确"
    
    checker = TokenBalanceChecker(provider, api_key)
    return checker.get_usage()


if __name__ == "__main__":
    # 命令行测试
    print("支持的AI API提供商:")
    for p in list_providers():
        print(f"  - {p['name']} ({p['key']})")
    
    print("\n使用示例:")
    print("  from token_core import query_balance")
    print("  success, balance, error = query_balance('deepseek', 'sk-xxxxx')")
