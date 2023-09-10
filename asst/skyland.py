import json
import os.path
import time
from getpass import getpass
import logging
import requests

from datetime import date

token_save_name = 'TOKEN.txt'
app_code = '4ca99fa6b56cc2ba'
is_github_action = os.environ.get('GitHub_Actions')
header = {
    'cred': '',
    'User-Agent': 'Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
    'Accept-Encoding': 'gzip',
    'Connection': 'close'
}
header_login = {
    'User-Agent': 'Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0',
    'Accept-Encoding': 'gzip',
    'Connection': 'close'
}
# 签到urlpip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
sign_url = "https://zonai.skland.com/api/v1/game/attendance"
# 绑定的角色url
binding_url = "https://zonai.skland.com/api/v1/game/player/binding"
# 验证码url
login_code_url = "https://as.hypergryph.com/general/v1/send_phone_code"
# 验证码登录
token_phone_code_url = "https://as.hypergryph.com/user/auth/v2/token_by_phone_code"
# 密码登录
token_password_url = "https://as.hypergryph.com/user/auth/v1/token_by_phone_password"
# 使用token获得认证代码
grant_code_url = "https://as.hypergryph.com/user/oauth2/v2/grant"
# 使用认证代码获得cred
cred_code_url = "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code"


def config_logger():
    current_date = date.today().strftime('%Y-%m-%d')
    if not os.path.exists('logs'):
        os.mkdir('logs')
    logger = logging.getLogger()

    file_handler = logging.FileHandler(f'./logs/{current_date}.log', encoding='utf-8')
    logger.addHandler(file_handler)
    logging.getLogger().setLevel(logging.DEBUG)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    if is_github_action:
        return

    def filter_code(text):
        filter_key = ['code', 'cred', 'token']
        try:
            j = json.loads(text)
            if not j.get('data'):
                return text
            data = j['data']
            for i in filter_key:
                if i in data:
                    data[i] = '*****'
            return json.dumps(j, ensure_ascii=False)
        except:
            return text

    _get = requests.get
    _post = requests.post

    def get(*args, **kwargs):
        response = _get(*args, **kwargs)
        logger.info(f'GET {args[0]} - {response.status_code} - {filter_code(response.text)}')
        return response

    def post(*args, **kwargs):
        response = _post(*args, **kwargs)
        logger.info(f'POST {args[0]} - {response.status_code} - {filter_code(response.text)}')
        return response

    # 替换 requests 中的方法
    requests.get = get
    requests.post = post


def login_by_code():
    phone = input('请输入手机号码：')
    resp = requests.post(login_code_url, json={'phone': phone, 'type': 2}, headers=header_login).json()
    if resp.get("status") != 0:
        raise Exception(f"发送手机验证码出现错误：{resp['msg']}")
    code = input("请输入手机验证码：")
    r = requests.get(token_phone_code_url, json={"phone": phone, "code": code}, headers=header_login).json()
    return get_token(r)


def login_by_token():
    token_code = input("请输入（登录森空岛电脑官网后请访问这个网址：https://web-api.skland.com/account/info/hg）:")
    return parse_user_token(token_code)


def parse_user_token(t):
    try:
        t = json.loads(t)
        return t['data']['content']
    except:
        pass
    return t


def login_by_password(phone=None, password=None):
    if phone is None:
        phone = input('请输入手机号码：')
        password = getpass('请输入密码：')
    r = requests.post(token_password_url, json={"phone": phone, "password": password}, headers=header_login).json()
    return get_token(r)


def get_cred_by_token(token):
    grant_code = get_grant_code(token)
    return get_cred(grant_code)


def get_token(resp):
    if resp.get('status') != 0:
        raise Exception(f'获得token失败：{resp["msg"]}')
    return resp['data']['token']


def get_grant_code(token):
    resp = requests.post(grant_code_url, json={
        'appCode': app_code,
        'token': token,
        'type': 0
    }, headers=header_login).json()
    if resp.get('status') != 0:
        raise Exception(f'获得认证代码失败：{resp["msg"]}')
    return resp['data']['code']


def get_cred(grant):
    resp = requests.post(cred_code_url, json={
        'code': grant,
        'kind': 1
    }, headers=header_login).json()
    if resp['code'] != 0:
        raise Exception(f'获得cred失败：{resp["messgae"]}')
    return resp['data']['cred']


def get_binding_list():
    v = []
    resp = requests.get(binding_url, headers=header).json()
    if resp['code'] != 0:
        print(f"请求角色列表出现问题：{resp['message']}")
        if resp.get('message') == '用户未登录':
            print(f'用户登录可能失效了，请重新运行此程序！')
            os.remove(token_save_name)
            return []
    for i in resp['data']['list']:
        if i.get('appCode') != 'arknights':
            continue
        v.extend(i.get('bindingList'))
    return v


def do_sign(cred):
    header['cred'] = cred
    characters = get_binding_list()
    for i in characters:
        body = {
            'uid': i.get('uid'),
            'gameId': i.get("channelMasterId")
        }
        resp = requests.post(sign_url, headers=header, json=body).json()
        if resp['code'] != 0:
            r = f'角色{i.get("nickName")}({i.get("channelName")})签到失败了！原因：{resp.get("message")}'
            continue
        awards = resp['data']['awards']
        for j in awards:
            res = j['resource']
            r = f'角色{i.get("nickName")}({i.get("channelName")})签到成功，获得了{res["name"]}×{j.get("count") or 1}'
    return r


def save(token):
    with open(token_save_name, 'w') as f:
        f.write(token)
    print(f'您的鹰角网络通行证已经保存在{token_save_name}, 打开这个可以把它复制到云函数服务器上执行!\n如果需要再次运行，删除创建的这个文件即可')


def read(path):
    v = []
    with open(path, 'r', encoding='utf-8') as f:
        for i in f.readlines():
            i = i.strip()
            i and i not in v and v.append(i)
    return v


def read_github_action():
    tokens = os.environ.get('TOKEN')
    if not tokens:
        print('请在"secrets and variables"里添加Token!')
        return []
    v = []
    token_list = tokens.split('\n')
    for i in token_list:
        i = i.strip()
        if i and i not in v:
            v.append(parse_user_token(i))
    print(f'从环境变量中读取到{len(v)}个token...')
    return v


def do_init():
    if is_github_action:
        print('使用Github Action')
        # 对于github action,不需要存储token,因为token在环境变量里
        return read_github_action()

    token = ''
    # 检测文件里是否有token
    if os.path.exists(token_save_name):
        v = read(token_save_name)
        if v:
            return v
    # 没有的话
    print("请输入你需要做什么：")
    print("1.使用用户名密码登录（非常推荐，但可能因为人机验证失败）")
    print("2.使用手机验证码登录（非常推荐，但可能因为人机验证失败）")
    print("3.手动输入鹰角网络通行证账号登录(推荐)")
    mode = input('请输入（1，2，3）：')
    if mode == '' or mode == '1':
        token = login_by_password()
    elif mode == '2':
        token = login_by_code()
    elif mode == '3':
        token = login_by_token()
    else:
        exit()
    save(token)
    return [token]


# def start():
#     try:
#         token = do_init()
#         for i in token:
#             do_sign(get_cred_by_token(i))
#         print("签到完成！")
#     except Exception as ex:
#         print(f'签到失败，原因：{str(ex)}')
#         logging.error(exc_info=ex)


# print('本项目源代码仓库：https://github.com/xxyz30/skyland-auto-sign')
# config_logger()
#
# logging.info('=========starting==========')
#
# start_time = time.time()
# start()
# end_time = time.time()
# logging.info(f'complete with {(end_time - start_time) * 1000} ms')
# logging.info('===========ending============')
