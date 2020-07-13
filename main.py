"""
A tool to parse xmind file into testlink xml file, which will help
you generate a testlink recognized xml file, then you can import it
into testlink as test suites.

Usage:
 xmind2testlink [path_to_xmind_file] [-json]

Example:
 xmind2testlink C:\\tests\\testcase.xmind       => output xml
 xmind2testlink C:\\tests\\testcase.xmind -json => output json

"""

import json
import sys, argparse

from xmind2testlink.testlink_parser import to_testlink_xml_file
from xmind2testlink.xmind_parser import xmind_to_suite, xmind_to_flat_dict
from xmind2testlink.xray import xray_issue


csv_title = {
    'Name': [],
    'Objective': [],
    'Precondition': [],
    'Folder': [],
    'Status': [],
    'Priority': [],
    'Component': [],
    'Owner': [],
    'Estimated Time': [],
    'Labels': [],
    'Coverage (Issues)': [],
    'Test Script (Step-by-Step) - Step': [],
    'Test Script (Step-by-Step) - Test Data': [],
    'Test Script (Step-by-Step) - Expected Result': [],
}


def xmind_to_testlink(xmind):
    xml_out = xmind[:-5] + 'xml'
    suite = xmind_to_suite(xmind)
    to_testlink_xml_file(suite, xml_out)
    return xml_out


def xmind_to_json(xmind):
    json_out = xmind[:-5] + 'json'
    with open(json_out, 'w', encoding='utf8') as f:
        f.write(json.dumps(xmind_to_flat_dict(xmind), indent=2))

    return json_out


def get_issue_key(test_case_name):
    chn_index = str(test_case_name).find('：')

    en_index = str(test_case_name).find(':')

    if chn_index == -1 and en_index == -1:
        issue_key_index = -1
    elif chn_index == -1:
        issue_key_index = en_index
    elif en_index == -1:
        issue_key_index = chn_index
    else:
        issue_key_index = min(chn_index, en_index)

    if issue_key_index == -1:
        link_issue_key = ''
    else:
        link_issue_key = str(test_case_name)[:issue_key_index]
    return link_issue_key


def generate_csv_title(xmind):
    index = str(xmind).find('.', len(xmind)-10)
    csv_file = ''.join((str(xmind)[:index], '.csv'))
    with open(csv_file, 'w+') as f:
        for num, key in enumerate(csv_title.keys()):
            f.write(key)
            if num != len(csv_title) - 1:
                f.write(',')
            else:
                f.write('\n')
    return csv_file


def generate_tm4j_csv(csv_file, title_name, test_case, issue_key, component):
    for key in csv_title.keys():
        csv_title[key] = []
    csv_title['Name'].append(title_name)
    csv_title['Folder'].append(component)
    csv_title['Status'].append('Draft')
    if test_case.importance == 1:
        csv_title['Priority'].append('High')
    elif test_case.importance == 2:
        csv_title['Priority'].append('Normal')
    else:
        csv_title['Priority'].append('Low')
    csv_title['Component'].append(component)
    csv_title['Coverage (Issues)'].append(issue_key)
    for step in test_case.steps:
        csv_title['Test Script (Step-by-Step) - Step'].append(''.join(('"', step.action, '"')))
        csv_title['Test Script (Step-by-Step) - Expected Result'].append(''.join(('"', step.expected, '"')))

    with open(csv_file, 'a+') as f:
        for i in range(len(test_case.steps)):
            for j, key in enumerate(csv_title.keys()):
                if len(csv_title[key]) > i:
                    f.write(str(csv_title[key][i]))
                if j != len(csv_title) - 1:
                    f.write(',')
                else:
                    f.write('\n')


def main(xacpt, jira_token, project_name_key, xmind, components=None):
    # xacpt = ''
    # jira_token = 'XWGNZ4MgoeD1kfofTelQ72CD'
    # project_name_key = 'QUARD'
    # xmind = '/Users/wei.zhou/Documents/4x版本迭代/spirnt06/Kyligence Enterprise-sprint06.xmind'
    suite = xmind_to_suite(xmind)
    csv_file = generate_csv_title(xmind)
    for test_suit in suite.sub_suites:
        sub_title = test_suit.name
        for test_case in test_suit.testcase_list:
            test_case_name = test_case.name
            title_name = sub_title + ' > ' + test_case_name
            generate_tm4j_csv(csv_file, title_name, test_case, get_issue_key(test_case_name), sub_title)
            # xray_issue.create_xray_full_issue(project_name_key, title_name,
            #                                   test_case, get_issue_key(test_case_name), jira_token,
            #                                   xacpt, components)
        # for test_case in test_suit
    print()


def init_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('--xacpt', required=True,
                        help="访问 https://olapio.atlassian.net/browse/QUARD-277 =》浏览器按F12 或者右击检查=> 搜索 `testStepFields` 对应的请求（Request headers）字段X-acpt对应的值")
    parser.add_argument('--token', default="d2VpLnpob3VAa3lsaWdlbmNlLmlvOm8xeGh0M2owSVdheUdxWWx4bUUwNzU2Rg==",
                        help="默认使用代码者的KEY,建议改成自己的,通过jira 链接 https://id.atlassian.com/manage-profile/security/api-tokens 申请到自己的token,在base64编码 https://www.blitter.se/utils/basic-authentication-header-generator")
    parser.add_argument('--project', default='KE',
                        help="默认使用KE，访问 https://olapio.atlassian.net/projects 拿到对应项目的key")
    parser.add_argument('--xmind', required=True,
                        help="你的xmind的文件的全路径。for example：/Users/wei.zhou/Documents/4x版本迭代/spirnt06/Kyligence Enterprise-sprint06.xmind")
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    # eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1YzdlNzExYjU5N2MwYTFjZmRmOTA5MTkiLCJpc3MiOiJjZGVmNjk5Ny05NTQyLTMwODktOTM0Yy00ODViMWE3MTE3N2QiLCJjb250ZXh0Ijp7ImxpY2Vuc2UiOnsiYWN0aXZlIjp0cnVlfSwiamlyYSI6eyJpc3N1ZSI6eyJpc3N1ZXR5cGUiOnsiaWQiOiIxMDA0MyJ9LCJrZXkiOiJRVUFSRC0yNzciLCJpZCI6IjQwNDM0In0sInByb2plY3QiOnsia2V5IjoiUVVBUkQiLCJpZCI6IjEwMDQwIn19fSwiZXhwIjoxNTg3ODczMzMwLCJpYXQiOjE1ODc4NzI0MzB9.1dCncEn8BP0-YL-go1tik7Yh81O3aNfZ8Oal4yXIiY8
    # ARG = init_argument()
    # xacpt = ARG.xacpt
    # jira_token = ARG.token
    # project_name_key = ARG.project
    # xmind = ARG.xmind
    xacpt = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJjb20ueHBhbmRpdC5wbHVnaW5zLnhyYXkiLCJpYXQiOjE1OTE2MjUyOTEsInN1YiI6IjVhYzJlMWZjMDllZTM5MmI5MDVjMDk3MiIsImV4cCI6MTU5MTcxMTY5MSwiYXVkIjpbImNkZWY2OTk3LTk1NDItMzA4OS05MzRjLTQ4NWIxYTcxMTc3ZCJdLCJjb250ZXh0Ijp7ImxpY2Vuc2UiOnsiYWN0aXZlIjp0cnVlfSwiamlyYSI6eyJpc3N1ZSI6eyJpc3N1ZXR5cGUiOnsiaWQiOiIxMDA0MyJ9LCJrZXkiOiJLQy0zMjA1IiwiaWQiOiI0Mjg4MCJ9LCJwcm9qZWN0Ijp7ImtleSI6IktDIiwiaWQiOiIxMDAxMiJ9fX19._Xkmtka8UO4Q9xs6DX29CXnYmd-yKsftfk9iRFaWYzQ'
    jira_token = 'emhpZG9uZy5xaUBreWxpZ2VuY2UuaW86bUVLeUlLV2dtNHIxYkhLY3N3ZzRGMTU1'
    project_name_key = 'KC'
    xmind = '/Users/zhidong.qi/Documents/works/kc_testcase/3.2/sprint8/KC-Sprint8_本地用户.xmind'
    # components = 'Kyligence Cloud 2.x'
    components = 'Test Case | 测试用例'
    main(xacpt, jira_token, project_name_key, xmind, components)
    # while True:
    #     pass
