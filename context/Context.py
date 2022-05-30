_context_dict = {}
_callback_dict = {}


def _init():  # 初始化
    global _context_dict, _callback_dict
    _context_dict = {}
    _callback_dict = {}


def set_value(key, value):
    """ 定义一个全局变量 """
    if key in _callback_dict.keys():
        # 调用callback
        _callback_dict[key](key, value)
    _context_dict[key] = value


def get_value(key, default_value=None):
    """ 获得一个全局变量,不存在则返回默认值 """
    try:
        return _context_dict[key]
    except KeyError:
        return default_value


def register_value_change_callback(target_key, callback):
    """ 注册某个key的变化回调函数，当该key的数据发生变化时调用此callback, 调用格式为callback(key, new_value)"""
    global _callback_dict
    _callback_dict[target_key] = callback
